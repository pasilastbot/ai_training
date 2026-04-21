#!/usr/bin/env python3
"""
Prospect Enrich Subagent

Takes a prospect and enriches it with additional data using Gemini's
integrated tools (Google Search, URL Context).

Usage:
  python prospect_enrich.py --company "Acme Corp" --website "https://acme.com"
  python prospect_enrich.py --prospect-file prospect.json
  echo '{"company_name": "Acme", "website": "https://acme.com"}' | python prospect_enrich.py --stdin
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')
load_dotenv()

from google import genai
from google.genai import types

# Configuration
DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"


def load_api_key() -> str:
    """Load Gemini API key from environment."""
    api_key = (
        os.environ.get("GOOGLE_AI_STUDIO_KEY") or 
        os.environ.get("GEMINI_API_KEY") or 
        os.environ.get("GOOGLE_API_KEY")
    )
    if not api_key:
        print(json.dumps({
            "error": "API key not found",
            "message": "Set GOOGLE_AI_STUDIO_KEY, GEMINI_API_KEY, or GOOGLE_API_KEY"
        }))
        sys.exit(1)
    return api_key


def build_enrichment_prompt(prospect: Dict[str, Any]) -> str:
    """Build a prompt to enrich prospect data."""
    company_name = prospect.get("company_name", "Unknown")
    website = prospect.get("website", "")
    existing_info = prospect.get("description", "")
    
    website_instruction = ""
    if website:
        website_instruction = f"""
Visit and analyze the company website: {website}
Extract information directly from the website when possible."""

    return f"""Research and enrich this B2B prospect profile:

**Company:** {company_name}
**Website:** {website or "Not provided"}
**Existing Info:** {existing_info or "None"}
{website_instruction}

Find and verify the following information:

1. **Company Overview**
   - Full legal company name
   - Year founded
   - Company description (what they do, their value proposition)
   - Mission/vision if available

2. **Business Details**
   - Primary industry and sub-industry
   - Business model (B2B SaaS, marketplace, etc.)
   - Key products/services
   - Target customers

3. **Size & Financials**
   - Employee count (exact or estimate)
   - Revenue estimate if available
   - Funding history (total raised, last round, investors)
   - Funding stage (seed, Series A, B, C, etc.)

4. **Location**
   - Headquarters city, state/province, country
   - Full address if available
   - Other office locations

5. **Technology Stack**
   - Technologies they use (from job postings, website, etc.)
   - Tech stack indicators

6. **Key People**
   - CEO/Founder name and LinkedIn
   - CTO/Technical leader
   - Other relevant executives

7. **Signals & Recent Activity**
   - Recent news (funding, product launches, partnerships)
   - Hiring activity (are they growing?)
   - Recent blog posts or press releases
   - Awards or recognition

8. **Social Presence**
   - LinkedIn company page URL
   - Twitter/X handle
   - Other social profiles

Return a JSON object with this structure:
{{
  "company_name": "Full Legal Name",
  "website": "https://company.com",
  "description": "Detailed company description",
  "industry": "Primary Industry",
  "sub_industry": "Specific Vertical",
  "business_model": "B2B SaaS",
  "year_founded": 2020,
  "employee_count": 150,
  "employee_range": "100-200",
  "revenue_estimate_usd": 10000000,
  "funding_stage": "series-b",
  "total_funding_usd": 25000000,
  "last_funding": {{
    "round": "Series B",
    "amount_usd": 15000000,
    "date": "2024-06",
    "investors": ["Investor A", "Investor B"]
  }},
  "headquarters": {{
    "city": "San Francisco",
    "state": "CA",
    "country": "US",
    "address": "123 Main St"
  }},
  "other_locations": ["New York", "London"],
  "technologies": ["Python", "AWS", "Kubernetes", "React"],
  "products": ["Product A", "Product B"],
  "target_market": "Mid-market B2B companies",
  "contacts": [
    {{
      "name": "John Doe",
      "title": "CEO",
      "linkedin": "https://linkedin.com/in/johndoe"
    }},
    {{
      "name": "Jane Smith",
      "title": "CTO",
      "linkedin": "https://linkedin.com/in/janesmith"
    }}
  ],
  "signals": {{
    "hiring": true,
    "hiring_count": 15,
    "recent_funding": true,
    "recent_news": [
      "Raised Series B in June 2024",
      "Launched new AI feature"
    ],
    "growth_indicators": ["Expanding team", "New product launch"]
  }},
  "social": {{
    "linkedin": "https://linkedin.com/company/...",
    "twitter": "@companyhandle",
    "blog": "https://company.com/blog"
  }},
  "enrichment_confidence": 85,
  "sources": ["https://source1.com", "https://source2.com"],
  "enriched_at": "2024-01-15T10:30:00Z"
}}

Only include fields where you have actual information. Set enrichment_confidence 
based on how much verified data you found (0-100). Include source URLs."""


def enrich_prospect(
    prospect: Dict[str, Any],
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Enrich a prospect with additional data using Gemini's integrated tools.
    
    Uses:
    - Google Search for finding company information
    - URL Context for analyzing the company website
    """
    api_key = load_api_key()
    client = genai.Client(api_key=api_key)
    
    # Build tools list
    tools = [
        types.Tool(google_search=types.GoogleSearch()),
        types.Tool(url_context=types.UrlContext())
    ]
    
    # Note: response_mime_type="application/json" is not compatible with built-in tools
    config = types.GenerateContentConfig(
        tools=tools
    )
    
    # Build prompt
    prompt = build_enrichment_prompt(prospect)
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
        
        # Extract text response
        if not response.candidates or not response.candidates[0].content.parts:
            return {
                **prospect,
                "enrichment_error": "No response from model",
                "enrichment_confidence": 0
            }
        
        response_text = response.candidates[0].content.parts[0].text
        
        # Try to parse as JSON
        try:
            enriched = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    enriched = json.loads(json_match.group())
                except json.JSONDecodeError:
                    enriched = {"raw_response": response_text}
            else:
                enriched = {"raw_response": response_text}
        
        # Merge with original prospect data
        result = {**prospect}
        
        # Update with enriched data (don't overwrite existing good data with None)
        for key, value in enriched.items():
            if value is not None and value != "" and value != []:
                result[key] = value
        
        # Add metadata
        result["enriched_at"] = datetime.utcnow().isoformat()
        result["status"] = "enriched"
        result["enrichment_model"] = model
        
        # Preserve original ID
        if "id" in prospect:
            result["id"] = prospect["id"]
        
        # Extract grounding metadata if available
        if response.candidates[0].grounding_metadata:
            meta = response.candidates[0].grounding_metadata
            sources = []
            if meta.grounding_chunks:
                for chunk in meta.grounding_chunks:
                    web = getattr(chunk, "web", None)
                    if web:
                        sources.append({
                            "title": getattr(web, "title", None),
                            "url": getattr(web, "uri", None)
                        })
            if sources:
                result["enrichment_sources"] = sources
        
        return result
        
    except Exception as e:
        return {
            **prospect,
            "enrichment_error": str(e),
            "enrichment_confidence": 0,
            "enriched_at": datetime.utcnow().isoformat()
        }


def main():
    parser = argparse.ArgumentParser(
        description="Enrich a B2B prospect with additional data",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--prospect-file", "-f",
        help="Path to prospect JSON file"
    )
    input_group.add_argument(
        "--stdin",
        action="store_true",
        help="Read prospect from stdin"
    )
    
    # Direct input
    parser.add_argument(
        "--company", "-c",
        help="Company name"
    )
    parser.add_argument(
        "--website", "-w",
        help="Company website URL"
    )
    parser.add_argument(
        "--industry", "-i",
        help="Company industry"
    )
    
    # Model options
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Gemini model to use (default: {DEFAULT_MODEL})"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output"
    )
    
    args = parser.parse_args()
    
    # Build prospect from inputs
    prospect = {}
    
    if args.prospect_file:
        with open(args.prospect_file, "r") as f:
            prospect = json.load(f)
    elif args.stdin:
        prospect = json.load(sys.stdin)
    
    # Override with command-line arguments
    if args.company:
        prospect["company_name"] = args.company
    if args.website:
        prospect["website"] = args.website
    if args.industry:
        prospect["industry"] = args.industry
    
    # Validate minimum input
    if not prospect.get("company_name") and not prospect.get("website"):
        print(json.dumps({
            "error": "No prospect data",
            "message": "Provide --company and/or --website, or use --prospect-file/--stdin"
        }))
        sys.exit(1)
    
    # Add ID if missing
    if "id" not in prospect:
        prospect["id"] = f"prospect_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Run enrichment
    result = enrich_prospect(
        prospect=prospect,
        model=args.model
    )
    
    # Output
    output_str = json.dumps(result, indent=2 if args.pretty else None, default=str)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output_str)
        print(json.dumps({
            "status": "success",
            "output_file": args.output,
            "confidence": result.get("enrichment_confidence", 0)
        }))
    else:
        print(output_str)


if __name__ == "__main__":
    main()
