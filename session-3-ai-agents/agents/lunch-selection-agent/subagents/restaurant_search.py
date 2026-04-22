#!/usr/bin/env python3
"""
Restaurant Search Subagent

Uses Gemini's integrated tools (Google Search, Google Maps) to find
lunch restaurants in a specified city.

Usage:
  python restaurant_search.py --city Helsinki
  python restaurant_search.py --city "Tampere" --cuisine Italian
  python restaurant_search.py --city Oulu --query "best lunch spots"
"""

import argparse
import json
import os
import re
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


def build_search_prompt(city: str, cuisine: Optional[str] = None, 
                        custom_query: Optional[str] = None) -> str:
    """Build a search prompt for finding restaurants."""
    
    cuisine_filter = f"serving {cuisine} food" if cuisine else ""
    
    if custom_query:
        query_text = custom_query
    else:
        query_text = f"lunch restaurants {cuisine_filter} in {city}"
    
    return f"""Search for lunch restaurants in {city}{f' specializing in {cuisine} cuisine' if cuisine else ''}.

Query: {query_text}

IMPORTANT SEARCH GUIDELINES:
- Find restaurants that serve LUNCH (not just dinner-only places)
- Focus on restaurants with daily lunch menus or lunch specials
- Include a variety of cuisine types unless a specific cuisine is requested
- Get the actual website URL for each restaurant (important for menu extraction)
- Prioritize restaurants with accessible online menus

Return a JSON object with this structure:
{{
  "restaurants": [
    {{
      "name": "Restaurant Name",
      "address": "Full street address",
      "city": "{city}",
      "website": "https://restaurant-website.com",
      "menu_url": "https://restaurant-website.com/lunch (if different from main site)",
      "cuisine_types": ["Italian", "Mediterranean"],
      "price_range": "moderate",
      "average_price": 12.50,
      "description": "Brief description of the restaurant",
      "features": ["vegetarian options", "takeaway", "terrace"],
      "opening_hours": {{
        "lunch_start": "11:00",
        "lunch_end": "14:00"
      }},
      "rating": 4.2,
      "source": "URL where info was found"
    }}
  ],
  "search_summary": "Brief summary of restaurants found in {city}"
}}

Find 5-10 restaurants. Prioritize:
1. Restaurants with accessible websites for menu extraction
2. Places known for good lunch offerings
3. Variety of price ranges and cuisine types
4. Popular and well-reviewed establishments"""


def search_restaurants(
    city: str,
    cuisine: Optional[str] = None,
    custom_query: Optional[str] = None,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Search for restaurants using Gemini's integrated tools.
    
    Uses:
    - Google Search for finding restaurants
    - Google Maps for location-based discovery
    """
    api_key = load_api_key()
    client = genai.Client(api_key=api_key)
    
    tools = [
        types.Tool(google_search=types.GoogleSearch()),
    ]
    
    config = types.GenerateContentConfig(tools=tools)
    
    prompt = build_search_prompt(city, cuisine, custom_query)
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
        
        if not response.candidates or not response.candidates[0].content.parts:
            return {"error": "No response from model", "restaurants": []}
        
        response_text = response.candidates[0].content.parts[0].text
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    result = {"raw_response": response_text, "restaurants": []}
            else:
                result = {"raw_response": response_text, "restaurants": []}
        
        result["search_metadata"] = {
            "model": model,
            "timestamp": datetime.utcnow().isoformat(),
            "city": city,
            "cuisine": cuisine
        }
        
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
        
        for i, restaurant in enumerate(result.get("restaurants", [])):
            if "id" not in restaurant:
                restaurant["id"] = f"rest_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{i}"
            restaurant["city"] = city
            restaurant["created_at"] = datetime.utcnow().isoformat()
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "restaurants": [],
            "search_metadata": {
                "model": model,
                "timestamp": datetime.utcnow().isoformat(),
                "city": city,
                "error": True
            }
        }


def main():
    parser = argparse.ArgumentParser(
        description="Search for lunch restaurants using Gemini's integrated tools",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--city", "-c",
        required=True,
        help="City to search in"
    )
    parser.add_argument(
        "--cuisine",
        help="Specific cuisine type to search for"
    )
    parser.add_argument(
        "--query", "-q",
        help="Custom search query"
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Gemini model to use (default: {DEFAULT_MODEL})"
    )
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
    
    result = search_restaurants(
        city=args.city,
        cuisine=args.cuisine,
        custom_query=args.query,
        model=args.model
    )
    
    output_str = json.dumps(result, indent=2 if args.pretty else None, default=str)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output_str)
        print(json.dumps({
            "status": "success", 
            "output_file": args.output, 
            "restaurant_count": len(result.get("restaurants", []))
        }))
    else:
        print(output_str)


if __name__ == "__main__":
    main()
