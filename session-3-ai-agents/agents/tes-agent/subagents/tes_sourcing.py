#!/usr/bin/env python3
"""
TES Sourcing Sub-Agent

Searches for, downloads, and extracts TES (Työehtosopimus) documents.
Uses Google Search to find PDFs and Gemini to extract structured data.

Usage:
    python tes_sourcing.py --search "Teknologiateollisuuden TES"
    python tes_sourcing.py --url "https://example.com/tes.pdf" --name "Example TES"
    python tes_sourcing.py --file "/path/to/tes.pdf" --name "Example TES"
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urljoin

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_env import load_agent_environment

load_agent_environment()

from google import genai
from google.genai import types

MEMORY_DIR = Path(__file__).parent.parent / "memory"
DATA_DIR = MEMORY_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
SCHEMA_PATH = MEMORY_DIR / "tes_schema.json"

DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"

# Known TES document sources - these are verified working URLs for common TES documents
# Note: Many public sector TES documents (SOTE, KVTES) are only available as HTML, not PDF
KNOWN_TES_SOURCES = {
    "sote": {
        "name": "SOTE-sopimus",
        "keywords": ["sote", "sosiaali", "terveys", "terveydenhuolto", "sairaanhoitaja", "lähihoitaja"],
        "sources": [
            # Main agreement page (2025-2028 version)
            "https://www.kt.fi/sopimukset/sote/2025-2028",
            # Index page
            "https://www.kt.fi/sopimukset/sote",
        ],
        "search_terms": ["SOTE-sopimus 2025 PDF kt.fi", "sosiaali terveydenhuollon työehtosopimus PDF"],
        "note": "SOTE-sopimus is primarily available as HTML on kt.fi"
    },
    "kvtes": {
        "name": "KVTES",
        "keywords": ["kvtes", "kunta", "kunnallinen", "kuntatyönantaja"],
        "sources": [
            "https://www.kt.fi/sopimukset/kvtes/2025-2028/kokoteksti",
            "https://www.kt.fi/sopimukset/kvtes/2025-2028",
        ],
        "search_terms": ["KVTES 2025 kokoteksti", "kunta-alan virka työehtosopimus kt.fi"],
        "note": "KVTES is primarily available as HTML on kt.fi"
    },
    "rakennusala": {
        "name": "Rakennusalan TES",
        "keywords": ["rakennus", "talonrakennus", "rakentaminen", "rakennusliitto"],
        "sources": [
            "https://rakennusliitto.fi/tyoehtosopimukset/",
        ],
        "search_terms": [
            "talonrakennusalan työehtosopimus 2024 PDF rakennusliitto",
            "rakennusalan TES PDF lataa",
            "talonrakennusala työehtosopimus filetype:pdf"
        ]
    },
    "teknologia": {
        "name": "Teknologiateollisuuden TES",
        "keywords": ["teknologia", "teollisuus", "metalliteollisuus", "koneenrakennus"],
        "sources": [
            "https://teknologiateollisuus.fi/fi/tyomarkkinat/tyoehtosopimukset",
        ],
        "search_terms": [
            "teknologiateollisuuden työehtosopimus 2024 PDF",
            "teknologiateollisuus TES PDF lataa"
        ]
    },
    "kauppa": {
        "name": "Kaupan alan TES",
        "keywords": ["kauppa", "vähittäiskauppa", "myyjä", "kaupan ala"],
        "sources": [
            "https://www.pam.fi/wiki/kaupan-alan-tyoehtosopimus.html",
        ],
        "search_terms": ["kaupan alan työehtosopimus 2024 PDF PAM"]
    },
    "marava": {
        "name": "MaRa TES",
        "keywords": ["ravintola", "hotelli", "matkailu", "mara", "vapaa-aika", "tarjoilija", "kokki"],
        "sources": [
            "https://www.pam.fi/wiki/matkailu-ravintola-ja-vapaa-ajan-palveluita-koskeva-tyontekijoiden-tyoehtosopimus.html",
        ],
        "search_terms": ["matkailu ravintola työehtosopimus 2024 PDF MaRa PAM"]
    },
    "kiinteisto": {
        "name": "Kiinteistöpalvelualan TES",
        "keywords": ["kiinteistö", "siivous", "huolto", "kiinteistönhoito"],
        "sources": [
            "https://www.pam.fi/wiki/kiinteistopalvelualan-tyontekijoita-koskeva-tyoehtosopimus.html",
        ],
        "search_terms": ["kiinteistöpalvelualan työehtosopimus 2024 PDF PAM"]
    },
}


def find_known_tes(query: str) -> Optional[dict]:
    """Check if query matches a known TES and return its sources."""
    query_lower = query.lower()
    for tes_id, tes_info in KNOWN_TES_SOURCES.items():
        # Check if any keyword matches
        if any(kw in query_lower for kw in tes_info["keywords"]):
            return tes_info
        # Check if TES name matches
        if tes_info["name"].lower() in query_lower:
            return tes_info
    return None


def get_client() -> genai.Client:
    """Get Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_AI_STUDIO_KEY required")
    return genai.Client(api_key=api_key)


def load_schema() -> dict:
    """Load the current TES schema."""
    if SCHEMA_PATH.exists():
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def search_tes_pdf(query: str, client: genai.Client, attempt: int = 1) -> dict:
    """Search for TES PDF using Google Search with multiple strategies."""
    
    # Different search strategies based on attempt number
    search_strategies = [
        f"{query} työehtosopimus 2024 2025 PDF",
        f"{query} TES PDF site:finlex.fi",
        f"{query} työehtosopimus PDF",
        f"{query} kollektiivisopimus PDF",
        f"yleissitova työehtosopimus {query}",
    ]
    
    search_query = search_strategies[min(attempt - 1, len(search_strategies) - 1)]
    
    response = client.models.generate_content(
        model=DEFAULT_MODEL,
        contents=f"""Search for the latest Finnish collective bargaining agreement (TES/Työehtosopimus) for: {query}

Search query: {search_query}

CRITICAL INSTRUCTIONS:
1. Find the CURRENT/LATEST version (2024, 2025, or 2026)
2. Prefer these sources IN ORDER:
   - finlex.fi (most reliable, always works)
   - Official union websites (.fi domains)
   - Employer organization websites
3. If you find a landing page instead of direct PDF, return that URL - we can extract from HTML
4. VERIFY the URL looks current (contains recent year like 2024, 2025, 2026)

Return a JSON object with:
- "name": The official name of the TES (in Finnish)
- "url": URL to the PDF file OR the TES information page
- "union": The union/liitto name  
- "employer_org": The employer organization
- "validity_period": The validity period (e.g., "2024-2026")
- "source": The domain (e.g., "finlex.fi", "rakennusliitto.fi")
- "is_landing_page": true if URL is an info page rather than direct PDF

Return ONLY valid JSON, no other text.""",
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.1
        )
    )
    
    text = response.text.strip()
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group())
            result["_search_attempt"] = attempt
            result["_search_query"] = search_query
            return result
        except json.JSONDecodeError:
            pass
    
    return {"error": "Could not find TES", "query": query, "attempt": attempt}


def search_finlex_tes(query: str, client: genai.Client) -> dict:
    """Search specifically on Finlex for TES documents."""
    response = client.models.generate_content(
        model=DEFAULT_MODEL,
        contents=f"""Search Finlex.fi for the Finnish collective bargaining agreement (TES): {query}

Finlex URL format is usually: https://finlex.fi/fi/viranomaiset/tyoehto/

Find the specific TES and return JSON with:
- "name": Official TES name
- "url": Finlex URL to the TES
- "finlex_id": The Finlex document ID if found
- "validity_period": Validity period

Search: {query} site:finlex.fi työehtosopimus

Return ONLY valid JSON.""",
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.1
        )
    )
    
    text = response.text.strip()
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group())
            result["_source"] = "finlex"
            return result
        except json.JSONDecodeError:
            pass
    
    return {"error": "Not found on Finlex", "query": query}


def extract_pdf_links_from_page(url: str, client: genai.Client, query: str = "") -> list:
    """Extract PDF links from a landing page using both regex and AI."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html_content = response.text
        
        # Find all PDF links with regex
        pdf_links = re.findall(r'href=["\']([^"\']*\.pdf)["\']', html_content, re.IGNORECASE)
        pdf_links += re.findall(r'href=["\']([^"\']*pdf[^"\']*)["\']', html_content, re.IGNORECASE)
        
        # Also find download links that might not have .pdf extension
        download_links = re.findall(r'href=["\']([^"\']*(?:download|lataa|tiedosto|document)[^"\']*)["\']', html_content, re.IGNORECASE)
        pdf_links.extend(download_links)
        
        # Make absolute URLs
        absolute_links = list(set([urljoin(url, link) for link in pdf_links]))
        
        # Filter for likely TES PDFs (contain keywords)
        tes_keywords = ['tes', 'työehtosopimus', 'tyoehtosopimus', 'sopimus', 'agreement', 
                       '2024', '2025', '2026', 'kokoteksti', 'allekirjoitus']
        filtered = [link for link in absolute_links if any(kw in link.lower() for kw in tes_keywords)]
        
        # If we have few results, use AI to find PDF links
        if len(filtered) < 2 and client:
            print(json.dumps({"status": "using_ai_to_find_pdfs", "url": url}), file=sys.stderr)
            try:
                ai_response = client.models.generate_content(
                    model=DEFAULT_MODEL,
                    contents=f"""Analyze this HTML page and find links to PDF documents related to Finnish collective bargaining agreements (työehtosopimus/TES).

Search query: {query}
Page URL: {url}

HTML content (first 50000 chars):
{html_content[:50000]}

Return a JSON array of PDF URLs found. Look for:
1. Direct PDF download links
2. Links to "kokoteksti" (full text)
3. Links to "allekirjoituspöytäkirja" (signing protocol)
4. Any document download links

Return ONLY a JSON array like: ["url1", "url2"]
If no PDFs found, return: []""",
                    config=types.GenerateContentConfig(temperature=0.1)
                )
                
                text = ai_response.text.strip()
                json_match = re.search(r'\[.*\]', text, re.DOTALL)
                if json_match:
                    ai_links = json.loads(json_match.group())
                    # Make absolute URLs
                    ai_absolute = [urljoin(url, link) for link in ai_links if isinstance(link, str)]
                    filtered.extend(ai_absolute)
                    filtered = list(set(filtered))
            except Exception as e:
                print(json.dumps({"warning": f"AI PDF extraction failed: {str(e)}"}), file=sys.stderr)
        
        return filtered if filtered else absolute_links[:5]
        
    except Exception as e:
        print(json.dumps({"error": f"Failed to extract PDF links: {str(e)}", "url": url}), file=sys.stderr)
        return []


def download_pdf(url: str, name: str) -> Optional[str]:
    """Download PDF from URL to local storage."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    safe_name = re.sub(r'[^\w\-_]', '_', name.lower())
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{safe_name}_{timestamp}.pdf"
    filepath = PDF_DIR / filename
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        response.raise_for_status()
        
        content_type = response.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
            if response.content[:4] != b'%PDF':
                return None
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        return str(filepath)
    
    except Exception as e:
        print(json.dumps({"error": f"Download failed: {str(e)}", "url": url}), file=sys.stderr)
        return None


def fetch_html_content(url: str, name: str) -> Optional[str]:
    """Fetch HTML page and save as text for processing."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    safe_name = re.sub(r'[^\w\-_]', '_', name.lower())
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{safe_name}_{timestamp}.html"
    filepath = DATA_DIR / "html" / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=120, allow_redirects=True)
        response.raise_for_status()
        
        html_content = response.text
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        return str(filepath)
    
    except Exception as e:
        print(json.dumps({"error": f"HTML fetch failed: {str(e)}", "url": url}), file=sys.stderr)
        return None


def fetch_kt_fi_multipage(base_url: str, name: str, client: genai.Client) -> tuple[Optional[str], Optional[str]]:
    """Fetch and combine multiple pages from kt.fi TES structure.
    
    kt.fi publishes TES documents as a series of linked pages (chapters/sections).
    This function fetches the index page, extracts section links, and combines them.
    Returns (pdf_path, html_path) - one or the other will be set.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    safe_name = re.sub(r'[^\w\-_]', '_', name.lower())
    timestamp = datetime.now().strftime("%Y%m%d")
    filepath = DATA_DIR / "html" / f"{safe_name}_combined_{timestamp}.html"
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    
    try:
        # Fetch index page
        print(json.dumps({"status": "fetching_kt_index", "url": base_url}), file=sys.stderr)
        response = requests.get(base_url, headers=headers, timeout=60)
        response.raise_for_status()
        index_html = response.text
        
        # Find section links (kt.fi uses predictable URL patterns)
        section_links = []
        pdf_links = []
        base_path = urlparse(base_url).path.rstrip('/')
        
        # Find all href links
        all_links = re.findall(r'href=["\']([^"\'#]+)["\']', index_html)
        
        for link in all_links:
            full_url = urljoin(base_url, link)
            
            # Check for PDF links
            if '.pdf' in link.lower():
                if full_url not in pdf_links:
                    pdf_links.append(full_url)
                continue
            
            # Check for section links under the same path
            parsed = urlparse(full_url)
            if parsed.netloc == '' or 'kt.fi' in parsed.netloc:
                # Links that are children of the base path or related agreement pages
                if (base_path in parsed.path or 
                    '/sopimukset/sote/' in parsed.path or
                    '/sopimukset/kvtes/' in parsed.path):
                    if full_url not in section_links and full_url != base_url:
                        section_links.append(full_url)
        
        # If we found PDFs, try to download them
        if pdf_links:
            print(json.dumps({"status": "found_kt_pdfs", "count": len(pdf_links), "links": pdf_links[:3]}), file=sys.stderr)
            for pdf_url in pdf_links[:3]:
                pdf_path = download_pdf(pdf_url, name)
                if pdf_path:
                    return pdf_path, None  # Return PDF path
        
        # Limit to most important sections
        priority_keywords = ['palka', 'tyoaika', 'loma', 'saira', 'liite', 'yleis']
        prioritized = [l for l in section_links if any(k in l.lower() for k in priority_keywords)]
        other = [l for l in section_links if l not in prioritized]
        section_links = prioritized[:10] + other[:5]  # Max 15 sections
        
        if not section_links:
            print(json.dumps({"status": "no_subsections_found", "url": base_url}), file=sys.stderr)
            # Save just the index page
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(index_html)
            return None, str(filepath)
        
        print(json.dumps({"status": "found_sections", "count": len(section_links)}), file=sys.stderr)
        
        # Combine content from all sections
        combined_html = f"<!-- Combined from {base_url} -->\n"
        combined_html += f"<!-- Index page -->\n{index_html}\n\n"
        
        for i, section_url in enumerate(section_links[:10]):  # Limit to 10 sections
            try:
                print(json.dumps({"status": "fetching_section", "num": i+1, "url": section_url}), file=sys.stderr)
                resp = requests.get(section_url, headers=headers, timeout=30)
                resp.raise_for_status()
                combined_html += f"\n\n<!-- Section: {section_url} -->\n{resp.text}\n"
            except Exception as e:
                print(json.dumps({"warning": f"Failed to fetch section: {str(e)}", "url": section_url}), file=sys.stderr)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(combined_html)
        
        print(json.dumps({"status": "combined_pages_saved", "sections": len(section_links), "path": str(filepath)}), file=sys.stderr)
        return None, str(filepath)
        
    except Exception as e:
        print(json.dumps({"error": f"kt.fi multipage fetch failed: {str(e)}", "url": base_url}), file=sys.stderr)
        return None, None


def extract_tes_from_html(html_path: str, name: str, source_url: str, client: genai.Client) -> dict:
    """Extract structured data from TES HTML page using Gemini."""
    schema = load_schema()
    schema_str = json.dumps(schema.get("properties", {}), indent=2, ensure_ascii=False)
    
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    from html.parser import HTMLParser
    
    class TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text_parts = []
            self.skip_tags = {'script', 'style', 'nav', 'header', 'footer', 'aside'}
            self.current_skip = False
            self.skip_depth = 0
            
        def handle_starttag(self, tag, attrs):
            if tag in self.skip_tags:
                self.current_skip = True
                self.skip_depth += 1
                
        def handle_endtag(self, tag):
            if tag in self.skip_tags and self.skip_depth > 0:
                self.skip_depth -= 1
                if self.skip_depth == 0:
                    self.current_skip = False
                    
        def handle_data(self, data):
            if not self.current_skip:
                text = data.strip()
                if text:
                    self.text_parts.append(text)
    
    extractor = TextExtractor()
    extractor.feed(html_content)
    text_content = '\n'.join(extractor.text_parts)
    
    if len(text_content) > 500000:
        text_content = text_content[:500000] + "\n\n[TRUNCATED - Document too long]"
    
    prompt = f"""Analyze this Finnish collective bargaining agreement (TES/Työehtosopimus) document.
The TES is named: {name}
Source URL: {source_url}

Here is the full text content of the TES:

{text_content}

Extract all information matching this schema:
{schema_str}

IMPORTANT INSTRUCTIONS:
1. Extract ALL salary tables with experience levels and amounts
2. For each piece of data, note the section reference (e.g., "II luku 5 §")
3. Extract working hours, vacation rules, sick leave, notice periods
4. Include any bonuses or allowances (shift, evening, night, weekend, holiday)
5. Note the validity period (start and end dates)
6. If you find important terms NOT in the schema, add them to "other_terms" with descriptive keys
7. This is an HTML source, so use section references instead of page numbers

Return ONLY valid JSON matching the schema structure. Include:
- All standard fields from the schema
- "other_terms" for any industry-specific or unique terms
- "_extracted_fields" listing which fields you successfully extracted
- "_extraction_notes" with any important notes about the extraction

The JSON must be parseable. No markdown, no explanations outside the JSON."""

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=65536
            )
        )
        
        text = response.text.strip()
        
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
        
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(text)
        
        if "id" not in data:
            safe_name = re.sub(r'[^\w\-_]', '_', name.lower())
            validity = data.get("validity_start", datetime.now().strftime("%Y"))
            if isinstance(validity, str) and len(validity) >= 4:
                validity = validity[:4]
            data["id"] = f"tes_{safe_name}_{validity}"
        
        data["name"] = data.get("name", name)
        data["source_url"] = source_url
        data["html_path"] = html_path
        data["indexed_at"] = datetime.now().isoformat()
        data["_schema_version"] = 2
        data["_source_type"] = "html"
        
        return data
        
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse extracted data: {str(e)}",
            "name": name,
            "source_url": source_url,
            "html_path": html_path,
            "raw_response": text[:2000] if 'text' in dir() else None
        }
    except Exception as e:
        return {
            "error": f"Extraction failed: {str(e)}",
            "name": name,
            "source_url": source_url,
            "html_path": html_path
        }


def extract_tes_data(pdf_path: str, name: str, source_url: str, client: genai.Client) -> dict:
    """Extract structured data from TES PDF using Gemini."""
    schema = load_schema()
    schema_str = json.dumps(schema.get("properties", {}), indent=2, ensure_ascii=False)
    
    with open(pdf_path, "rb") as f:
        pdf_content = f.read()
    
    prompt = f"""Analyze this Finnish collective bargaining agreement (TES/Työehtosopimus) document.
The TES is named: {name}

Extract all information matching this schema:
{schema_str}

IMPORTANT INSTRUCTIONS:
1. Extract ALL salary tables with experience levels and amounts
2. For each piece of data, note the PDF page number and section reference
3. Extract working hours, vacation rules, sick leave, notice periods
4. Include any bonuses or allowances (shift, evening, night, weekend, holiday)
5. Note the validity period (start and end dates)
6. If you find important terms NOT in the schema, add them to "other_terms" with descriptive keys
7. Suggest any new schema fields that should be added (in "_suggested_fields")

Return ONLY valid JSON matching the schema structure. Include:
- All standard fields from the schema
- "other_terms" for any industry-specific or unique terms
- "_extracted_fields" listing which fields you successfully extracted
- "_extraction_notes" with any important notes about the extraction
- "_suggested_fields" with recommended new schema additions

The JSON must be parseable. No markdown, no explanations outside the JSON."""

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=[
                types.Part.from_bytes(data=pdf_content, mime_type="application/pdf"),
                prompt
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=65536
            )
        )
        
        text = response.text.strip()
        
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
        
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            data = json.loads(text)
        
        if "id" not in data:
            safe_name = re.sub(r'[^\w\-_]', '_', name.lower())
            validity = data.get("validity_start", datetime.now().strftime("%Y"))
            if isinstance(validity, str) and len(validity) >= 4:
                validity = validity[:4]
            data["id"] = f"tes_{safe_name}_{validity}"
        
        data["name"] = data.get("name", name)
        data["source_url"] = source_url
        data["pdf_path"] = pdf_path
        data["indexed_at"] = datetime.now().isoformat()
        data["_schema_version"] = 1
        
        return data
        
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse extracted data: {str(e)}",
            "name": name,
            "source_url": source_url,
            "pdf_path": pdf_path,
            "raw_response": text[:2000] if 'text' in dir() else None
        }
    except Exception as e:
        return {
            "error": f"Extraction failed: {str(e)}",
            "name": name,
            "source_url": source_url,
            "pdf_path": pdf_path
        }


def try_download_url(url: str, name: str, client: genai.Client, query: str = "") -> tuple[Optional[str], Optional[str], str]:
    """Try to download content from URL. Returns (pdf_path, html_path, status)."""
    pdf_path = None
    html_path = None
    
    # First try as PDF if URL looks like a PDF
    if url.lower().endswith('.pdf') or 'pdf' in url.lower():
        print(json.dumps({"status": "downloading_pdf", "url": url}), file=sys.stderr)
        pdf_path = download_pdf(url, name)
        if pdf_path:
            return pdf_path, None, "pdf_ok"
    
    # Special handling for kt.fi - use multi-page fetching
    if 'kt.fi/sopimukset' in url:
        print(json.dumps({"status": "kt_fi_detected", "url": url}), file=sys.stderr)
        kt_pdf, kt_html = fetch_kt_fi_multipage(url, name, client)
        if kt_pdf:
            return kt_pdf, None, "kt_fi_pdf"
        if kt_html:
            return None, kt_html, "kt_fi_multipage"
    
    # Try as HTML page
    print(json.dumps({"status": "fetching_html", "url": url}), file=sys.stderr)
    html_path = fetch_html_content(url, name)
    if html_path:
        # Check if it's a landing page with PDF links
        pdf_links = extract_pdf_links_from_page(url, client, query or name)
        if pdf_links:
            print(json.dumps({"status": "found_pdf_links", "count": len(pdf_links), "links": pdf_links[:5]}), file=sys.stderr)
            # Try downloading each PDF link (try more links)
            for pdf_url in pdf_links[:5]:
                print(json.dumps({"status": "trying_pdf_link", "url": pdf_url}), file=sys.stderr)
                pdf_path = download_pdf(pdf_url, name)
                if pdf_path:
                    return pdf_path, None, "pdf_from_landing"
        return None, html_path, "html_ok"
    
    return None, None, "failed"


def source_tes(
    query: Optional[str] = None,
    url: Optional[str] = None,
    file_path: Optional[str] = None,
    name: Optional[str] = None,
    is_html: bool = False
) -> dict:
    """Main function to source and extract a TES document with robust retry logic."""
    client = get_client()
    
    pdf_path = None
    html_path = None
    source_url = ""
    tes_name = name or query or "Unknown TES"
    
    # Handle local file
    if file_path:
        source_url = f"file://{file_path}"
        if not Path(file_path).exists():
            return {"error": f"File not found: {file_path}"}
        
        if file_path.endswith('.html') or file_path.endswith('.htm'):
            html_path = file_path
        else:
            pdf_path = file_path
    
    # Handle direct URL
    elif url:
        source_url = url
        
        if is_html:
            print(json.dumps({"status": "fetching_html", "url": url}), file=sys.stderr)
            html_path = fetch_html_content(url, tes_name)
            if not html_path:
                return {"error": f"Failed to fetch HTML from: {url}"}
        else:
            pdf_path, html_path, status = try_download_url(url, tes_name, client, tes_name)
            if not pdf_path and not html_path:
                return {"error": f"Failed to download from: {url}", "status": status}
    
    # Handle search query with retry logic
    elif query:
        all_tried_urls = []
        
        # Step 1: Check if this matches a known TES with verified sources
        known_tes = find_known_tes(query)
        if known_tes:
            print(json.dumps({"status": "found_known_tes", "name": known_tes["name"]}), file=sys.stderr)
            tes_name = known_tes["name"]
            
            # Try known sources first
            for known_url in known_tes.get("sources", []):
                if known_url in all_tried_urls:
                    continue
                all_tried_urls.append(known_url)
                print(json.dumps({"status": "trying_known_source", "url": known_url}), file=sys.stderr)
                
                pdf_path, html_path, status = try_download_url(known_url, tes_name, client, query)
                if pdf_path:
                    source_url = known_url
                    print(json.dumps({"status": "pdf_found_from_known", "url": known_url}), file=sys.stderr)
                    break
                elif html_path and status == "kt_fi_multipage":
                    # kt.fi multipage HTML is comprehensive - use it
                    source_url = known_url
                    print(json.dumps({"status": "kt_fi_multipage_found", "url": known_url}), file=sys.stderr)
                    break
                elif html_path and status == "html_ok":
                    # For simple HTML, we might want to keep searching for a PDF
                    source_url = known_url
                    print(json.dumps({"status": "html_found_continue_searching_pdf", "url": known_url}), file=sys.stderr)
            
            # If we only found simple HTML (not kt.fi multipage), try known search terms for a PDF
            # Skip if we got multipage content (status is tracked in the break condition above)
            search_for_pdf = html_path and not pdf_path
            if search_for_pdf and 'kt.fi/sopimukset' not in source_url:
                for search_term in known_tes.get("search_terms", []):
                    print(json.dumps({"status": "searching_known_term", "term": search_term}), file=sys.stderr)
                    search_result = search_tes_pdf(search_term, client, attempt=1)
                    
                    search_url = search_result.get("url", "")
                    if search_url and search_url not in all_tried_urls:
                        all_tried_urls.append(search_url)
                        pdf_result, _, status = try_download_url(search_url, tes_name, client, query)
                        if pdf_result:
                            pdf_path = pdf_result
                            source_url = search_url
                            html_path = None  # Prefer PDF over HTML
                            break
        
        # Step 2: If no known TES or known sources failed, do regular search
        if not pdf_path and not html_path:
            max_search_attempts = 3
            
            for attempt in range(1, max_search_attempts + 1):
                print(json.dumps({"status": "searching", "query": query, "attempt": attempt}), file=sys.stderr)
                search_result = search_tes_pdf(query, client, attempt)
                
                if "error" in search_result and attempt < max_search_attempts:
                    continue
                
                search_url = search_result.get("url", "")
                if not tes_name or tes_name == query:
                    tes_name = search_result.get("name", query)
                
                if not search_url:
                    continue
                
                # Skip if we already tried this URL
                if search_url in all_tried_urls:
                    print(json.dumps({"status": "skipping_duplicate_url", "url": search_url}), file=sys.stderr)
                    continue
                all_tried_urls.append(search_url)
                
                # Try to get content
                pdf_path, html_path, status = try_download_url(search_url, tes_name, client, query)
                
                if pdf_path or html_path:
                    source_url = search_url
                    break
                
                print(json.dumps({"status": "url_failed", "url": search_url, "attempt": attempt}), file=sys.stderr)
        
        # Step 3: Fallback to Finlex if regular search failed
        if not pdf_path and not html_path:
            print(json.dumps({"status": "trying_finlex", "query": query}), file=sys.stderr)
            finlex_result = search_finlex_tes(query, client)
            
            if "url" in finlex_result and finlex_result["url"]:
                finlex_url = finlex_result["url"]
                if finlex_url not in all_tried_urls:
                    all_tried_urls.append(finlex_url)
                    pdf_path, html_path, status = try_download_url(finlex_url, tes_name, client, query)
                    if pdf_path or html_path:
                        source_url = finlex_url
                        tes_name = finlex_result.get("name", tes_name)
        
        if not pdf_path and not html_path:
            return {
                "error": f"Failed to find working source",
                "query": query,
                "tried_urls": all_tried_urls
            }
    
    else:
        return {"error": "Must provide --search, --url, --html, or --file"}
    
    # Extract data from the content
    if html_path:
        print(json.dumps({"status": "extracting_html", "html": html_path}), file=sys.stderr)
        tes_data = extract_tes_from_html(html_path, tes_name, source_url, client)
    else:
        print(json.dumps({"status": "extracting_pdf", "pdf": pdf_path}), file=sys.stderr)
        tes_data = extract_tes_data(pdf_path, tes_name, source_url, client)
    
    if "error" not in tes_data:
        tes_data["_source_method"] = "search" if query else ("url" if url else "file")
    
    return tes_data


def main():
    parser = argparse.ArgumentParser(description="TES Sourcing Sub-Agent")
    parser.add_argument("--search", help="Search query for TES (e.g., 'Teknologiateollisuuden TES')")
    parser.add_argument("--url", help="Direct URL to TES (PDF or HTML)")
    parser.add_argument("--html", help="Direct URL to TES HTML page", dest="html_url")
    parser.add_argument("--file", help="Local path to TES PDF or HTML file")
    parser.add_argument("--name", help="TES name (optional, will be extracted if not provided)")
    
    args = parser.parse_args()
    
    if not any([args.search, args.url, args.html_url, args.file]):
        parser.print_help()
        sys.exit(1)
    
    url = args.html_url or args.url
    is_html = args.html_url is not None
    
    result = source_tes(
        query=args.search,
        url=url,
        file_path=args.file,
        name=args.name,
        is_html=is_html
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
