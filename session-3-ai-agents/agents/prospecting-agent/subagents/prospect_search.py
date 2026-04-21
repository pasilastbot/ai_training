#!/usr/bin/env python3
"""
Prospect Search Subagent

Uses Gemini's integrated tools (Google Search, URL Context, Maps) to find
prospects matching ICP criteria.

Usage:
  python prospect_search.py --icp-file ../memory/data/sample_icp.json
  python prospect_search.py --query "AI startups in San Francisco Series A"
  python prospect_search.py --industries "SaaS,Fintech" --geography "US" --size "50-500"
  echo '{"target_industries": ["SaaS"]}' | python prospect_search.py --icp-stdin
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
_AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_AGENT_DIR))
from agent_env import load_agent_environment

load_agent_environment()

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


def build_search_prompt(icp: Dict[str, Any], custom_query: Optional[str] = None) -> str:
    """Build a search prompt from ICP criteria."""
    if custom_query:
        return f"""Search for companies matching this query: {custom_query}

IMPORTANT SEARCH GUIDELINES:
- If a specific location is mentioned (city, country, region), find companies HEADQUARTERED or FOUNDED there
- DO NOT return large multinational corporations (Microsoft, Google, Salesforce, etc.) unless specifically requested
- Focus on local companies, startups, and mid-size businesses native to the specified region
- Prioritize companies that were actually founded in or are headquartered in the mentioned location
- If searching for "startups in X" or "companies in X", find companies that call X their home, not just offices there

Return a JSON object with this structure:
{{
  "prospects": [
    {{
      "company_name": "Company Name",
      "website": "https://...",
      "industry": "Industry",
      "description": "Brief description of what they do",
      "headquarters": "City, Country (where company is based)",
      "founded_location": "City where founded (if different)",
      "employee_estimate": "50-100",
      "founded_year": 2020,
      "signals": ["hiring", "recent funding", "product launch"],
      "why_relevant": "Why this company matches the search criteria",
      "source": "search result URL",
      "relevance_score": 85
    }}
  ],
  "search_summary": "Brief summary of what was found"
}}

Find 5-10 relevant companies. Focus on:
1. Companies actually based/headquartered in the specified location (not just having offices there)
2. Growing businesses, startups, scale-ups - not large multinationals
3. Verifiable, real companies with actual websites
4. Quality over quantity - only include genuinely relevant matches"""

    # Build prompt from ICP
    industries = ", ".join(icp.get("target_industries", ["technology"]))
    geography = ", ".join(icp.get("geography", []))
    keywords = ", ".join(icp.get("keywords", []))
    
    size_info = ""
    if "company_size" in icp:
        min_emp = icp["company_size"].get("min_employees", 10)
        max_emp = icp["company_size"].get("max_employees", 1000)
        size_info = f"Company size preference: {min_emp}-{max_emp} employees"
    
    funding_info = ""
    if "funding_stage" in icp:
        stages = ", ".join(icp["funding_stage"])
        funding_info = f"Funding stage preference: {stages}"
    
    exclusions = ""
    if "exclusions" in icp:
        exclusions = f"Exclude these types: {', '.join(icp['exclusions'])}"
    
    geography_note = f"**Target Geography:** {geography}" if geography else "**Target Geography:** Worldwide (no restriction)"
    
    return f"""Search for companies matching this Ideal Customer Profile (ICP):

**Target Industries:** {industries}
{geography_note}
**Keywords/Focus:** {keywords}
{size_info}
{funding_info}
{exclusions}

IMPORTANT SEARCH GUIDELINES:
- Find companies HEADQUARTERED in the target geography, not multinationals with offices there
- DO NOT return large corporations like Microsoft, Google, Salesforce, Deloitte, etc.
- Focus on startups, scale-ups, and mid-size businesses native to the region
- Prioritize companies that were founded in or are based in the specified locations

Search for companies that:
1. Are headquartered/based in the target regions (not just having offices)
2. Operate in the target industries
3. Are growing businesses - startups, scale-ups, or innovative mid-size companies
4. Show buying signals like hiring, funding, or product launches

Return a JSON object with this structure:
{{
  "prospects": [
    {{
      "company_name": "Company Name",
      "website": "https://company.com",
      "industry": "Primary Industry",
      "sub_industry": "Specific vertical",
      "description": "What the company does (2-3 sentences)",
      "headquarters": "City, Country",
      "founded_year": 2020,
      "employee_estimate": "50-100",
      "funding_info": "Series A, $10M (if known)",
      "signals": ["actively hiring", "recent product launch"],
      "why_relevant": "Why this company matches the ICP",
      "source_url": "URL where info was found",
      "relevance_score": 85
    }}
  ],
  "search_summary": "Brief summary of what was found",
  "search_queries_used": ["query1", "query2"]
}}

Find 5-10 relevant companies. Prioritize:
1. Local companies actually headquartered in target regions
2. Growing businesses, not large multinationals
3. Quality and accuracy over quantity
4. Only verifiable companies with real websites"""


def search_prospects(
    icp: Dict[str, Any],
    custom_query: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Dict[str, Any]:
    """
    Search for prospects using Gemini's integrated tools.
    
    Uses:
    - Google Search for finding companies
    - URL Context for analyzing company websites
    - Google Maps for location-based queries (if coordinates provided)
    """
    api_key = load_api_key()
    client = genai.Client(api_key=api_key)
    
    # Build tools list
    tools = []
    
    # Google Search - primary tool for finding prospects
    tools.append(types.Tool(google_search=types.GoogleSearch()))
    
    # URL Context - for analyzing specific company websites
    tools.append(types.Tool(url_context=types.UrlContext()))
    
    # Google Maps - for location-based queries
    if latitude and longitude:
        tools.append(types.Tool(google_maps=types.GoogleMaps()))
    
    # Build configuration
    # Note: response_mime_type="application/json" is not compatible with built-in tools
    config_kwargs = {
        "tools": tools
    }
    
    # Add location context for Maps if provided
    if latitude and longitude:
        config_kwargs["tool_config"] = types.ToolConfig(
            retrieval_config=types.RetrievalConfig(
                lat_lng=types.LatLng(latitude=latitude, longitude=longitude)
            )
        )
    
    config = types.GenerateContentConfig(**config_kwargs)
    
    # Build prompt
    prompt = build_search_prompt(icp, custom_query)
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
        
        # Extract text response
        if not response.candidates or not response.candidates[0].content.parts:
            return {"error": "No response from model", "prospects": []}
        
        response_text = response.candidates[0].content.parts[0].text
        
        # Try to parse as JSON
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    result = {"raw_response": response_text, "prospects": []}
            else:
                result = {"raw_response": response_text, "prospects": []}
        
        # Add metadata
        result["search_metadata"] = {
            "model": model,
            "timestamp": datetime.utcnow().isoformat(),
            "icp_name": icp.get("name", "custom")
        }
        
        # Extract grounding metadata if available
        if response.candidates[0].grounding_metadata:
            meta = response.candidates[0].grounding_metadata
            if meta.grounding_chunks:
                result["sources"] = [
                    {
                        "title": getattr(getattr(chunk, "web", None), "title", None),
                        "url": getattr(getattr(chunk, "web", None), "uri", None)
                    }
                    for chunk in meta.grounding_chunks
                    if getattr(chunk, "web", None)
                ]
            if meta.web_search_queries:
                result["search_queries"] = meta.web_search_queries
        
        # Add IDs to prospects
        for i, prospect in enumerate(result.get("prospects", [])):
            if "id" not in prospect:
                prospect["id"] = f"prospect_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{i}"
            prospect["status"] = "new"
            prospect["created_at"] = datetime.utcnow().isoformat()
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "prospects": [],
            "search_metadata": {
                "model": model,
                "timestamp": datetime.utcnow().isoformat(),
                "error": True
            }
        }


def main():
    parser = argparse.ArgumentParser(
        description="Search for B2B prospects using Gemini's integrated tools",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # ICP input options
    icp_group = parser.add_mutually_exclusive_group()
    icp_group.add_argument(
        "--icp-file", "-f",
        help="Path to ICP JSON file"
    )
    icp_group.add_argument(
        "--icp-stdin",
        action="store_true",
        help="Read ICP from stdin"
    )
    
    # Query options
    parser.add_argument(
        "--query", "-q",
        help="Custom search query (overrides ICP-based query)"
    )
    parser.add_argument(
        "--industries", "-i",
        help="Comma-separated list of target industries"
    )
    parser.add_argument(
        "--geography", "-g",
        help="Comma-separated list of target regions"
    )
    parser.add_argument(
        "--size",
        help="Company size range (e.g., '50-500')"
    )
    parser.add_argument(
        "--keywords", "-k",
        help="Comma-separated keywords"
    )
    
    # Location for Maps grounding
    parser.add_argument(
        "--latitude",
        type=float,
        help="Latitude for location-based search"
    )
    parser.add_argument(
        "--longitude",
        type=float,
        help="Longitude for location-based search"
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
    
    # Build ICP from inputs
    icp = {}
    
    if args.icp_file:
        with open(args.icp_file, "r") as f:
            icp = json.load(f)
    elif args.icp_stdin:
        icp = json.load(sys.stdin)
    
    # Override with command-line arguments
    if args.industries:
        icp["target_industries"] = [i.strip() for i in args.industries.split(",")]
    if args.geography:
        icp["geography"] = [g.strip() for g in args.geography.split(",")]
    if args.keywords:
        icp["keywords"] = [k.strip() for k in args.keywords.split(",")]
    if args.size:
        try:
            min_size, max_size = args.size.split("-")
            icp["company_size"] = {
                "min_employees": int(min_size),
                "max_employees": int(max_size)
            }
        except ValueError:
            pass
    
    # Ensure minimum ICP
    if not icp:
        if args.query:
            icp = {"name": "custom_query"}
        else:
            print(json.dumps({
                "error": "No ICP provided",
                "message": "Use --icp-file, --icp-stdin, or provide --industries and --geography"
            }))
            sys.exit(1)
    
    # Run search
    result = search_prospects(
        icp=icp,
        custom_query=args.query,
        model=args.model,
        latitude=args.latitude,
        longitude=args.longitude
    )
    
    # Output
    output_str = json.dumps(result, indent=2 if args.pretty else None, default=str)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output_str)
        print(json.dumps({"status": "success", "output_file": args.output, "prospect_count": len(result.get("prospects", []))}))
    else:
        print(output_str)


if __name__ == "__main__":
    main()
