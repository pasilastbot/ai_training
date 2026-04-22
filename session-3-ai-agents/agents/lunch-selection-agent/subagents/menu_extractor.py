#!/usr/bin/env python3
"""
Menu Extractor Subagent

Uses Gemini's url_context tool to fetch and extract today's lunch menu
from restaurant websites.

Usage:
  python menu_extractor.py --url "https://restaurant.com/lounas"
  python menu_extractor.py --url "https://restaurant.com" --name "Ravintola Helsinki"
  python menu_extractor.py --restaurants-file restaurants.json
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


def get_today_info() -> Dict[str, str]:
    """Get today's date information."""
    now = datetime.now()
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekdays_fi = ["Maanantai", "Tiistai", "Keskiviikko", "Torstai", "Perjantai", "Lauantai", "Sunnuntai"]
    
    return {
        "date": now.strftime("%Y-%m-%d"),
        "weekday": weekdays[now.weekday()],
        "weekday_fi": weekdays_fi[now.weekday()],
        "day": now.day,
        "month": now.month,
        "week": now.isocalendar()[1]
    }


def build_extraction_prompt(url: str, restaurant_name: Optional[str] = None) -> str:
    """Build prompt for menu extraction."""
    today = get_today_info()
    name_context = f" ({restaurant_name})" if restaurant_name else ""
    
    return f"""Fetch and analyze the lunch menu from this restaurant website{name_context}: {url}

Today is {today['weekday']}, {today['date']} (Finnish: {today['weekday_fi']}, week {today['week']}).

TASK: Extract today's lunch menu. Look for:
1. Daily lunch specials / "Päivän lounas" / "Lounaslistat"
2. Weekly menus with today's offerings
3. Fixed lunch menu if no daily specials
4. Prices, dietary indicators (V=vegetarian, VG=vegan, G=gluten-free, L=lactose-free)

IMPORTANT:
- Focus on LUNCH offerings, not dinner menu
- Look for Finnish terms: lounas, päivän, viikon, buffet, salaattipöytä
- Extract ALL dishes available today, not just one
- Include prices in EUR if shown
- Note any dietary tags

Return a JSON object with this structure:
{{
  "restaurant": "{restaurant_name or 'Restaurant'}",
  "menu_date": "{today['date']}",
  "weekday": "{today['weekday']}",
  "menu_type": "daily_special | weekly_rotating | fixed | buffet",
  "dishes": [
    {{
      "name": "Dish name",
      "description": "Brief description of the dish",
      "price": 12.50,
      "dietary": ["vegetarian", "gluten-free"],
      "category": "main | soup | salad | dessert"
    }}
  ],
  "lunch_hours": "11:00-14:00",
  "includes": ["salad bar", "bread", "coffee"],
  "buffet_price": null,
  "source_url": "{url}",
  "extraction_notes": "Any relevant notes about the menu"
}}

If you cannot find a lunch menu:
- Return empty dishes array
- Set extraction_notes to explain what was found instead
- Don't make up dishes - only report what's actually on the website"""


def extract_menu(
    url: str,
    restaurant_name: Optional[str] = None,
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Extract today's lunch menu from a restaurant website.
    
    Uses Gemini's url_context tool to fetch and analyze the page.
    """
    api_key = load_api_key()
    client = genai.Client(api_key=api_key)
    
    tools = [
        types.Tool(url_context=types.UrlContext()),
        types.Tool(google_search=types.GoogleSearch()),
    ]
    
    config = types.GenerateContentConfig(tools=tools)
    
    prompt = build_extraction_prompt(url, restaurant_name)
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
        
        if not response.candidates or not response.candidates[0].content.parts:
            return {
                "error": "No response from model",
                "restaurant": restaurant_name,
                "source_url": url,
                "dishes": []
            }
        
        response_text = response.candidates[0].content.parts[0].text
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    result = {
                        "raw_response": response_text,
                        "restaurant": restaurant_name,
                        "source_url": url,
                        "dishes": [],
                        "extraction_notes": "Failed to parse structured response"
                    }
            else:
                result = {
                    "raw_response": response_text,
                    "restaurant": restaurant_name,
                    "source_url": url,
                    "dishes": [],
                    "extraction_notes": "No JSON found in response"
                }
        
        result["extraction_metadata"] = {
            "model": model,
            "timestamp": datetime.utcnow().isoformat(),
            "source_url": url
        }
        
        if response.candidates[0].grounding_metadata:
            meta = response.candidates[0].grounding_metadata
            if meta.grounding_chunks:
                result["grounding_sources"] = [
                    {
                        "title": getattr(getattr(chunk, "web", None), "title", None),
                        "url": getattr(getattr(chunk, "web", None), "uri", None)
                    }
                    for chunk in meta.grounding_chunks
                    if getattr(chunk, "web", None)
                ]
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "restaurant": restaurant_name,
            "source_url": url,
            "dishes": [],
            "extraction_metadata": {
                "model": model,
                "timestamp": datetime.utcnow().isoformat(),
                "error": True
            }
        }


def extract_menus_batch(
    restaurants: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL
) -> List[Dict[str, Any]]:
    """Extract menus for multiple restaurants."""
    results = []
    
    for restaurant in restaurants:
        url = restaurant.get("menu_url") or restaurant.get("website")
        if not url:
            results.append({
                "restaurant": restaurant.get("name"),
                "restaurant_id": restaurant.get("id"),
                "error": "No URL available",
                "dishes": []
            })
            continue
        
        result = extract_menu(
            url=url,
            restaurant_name=restaurant.get("name"),
            model=model
        )
        result["restaurant_id"] = restaurant.get("id")
        results.append(result)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Extract lunch menus from restaurant websites using Gemini's url_context",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--url", "-u",
        help="Restaurant website URL to extract menu from"
    )
    input_group.add_argument(
        "--restaurants-file", "-f",
        help="JSON file with list of restaurants (each needs 'website' or 'menu_url')"
    )
    input_group.add_argument(
        "--stdin",
        action="store_true",
        help="Read restaurant list from stdin"
    )
    
    parser.add_argument(
        "--name", "-n",
        help="Restaurant name (used with --url)"
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
    
    if args.url:
        result = extract_menu(
            url=args.url,
            restaurant_name=args.name,
            model=args.model
        )
    elif args.restaurants_file:
        with open(args.restaurants_file, "r") as f:
            data = json.load(f)
        restaurants = data if isinstance(data, list) else data.get("restaurants", [])
        result = {
            "menus": extract_menus_batch(restaurants, args.model),
            "extraction_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "total": len(restaurants)
        }
    else:
        data = json.load(sys.stdin)
        restaurants = data if isinstance(data, list) else data.get("restaurants", [])
        result = {
            "menus": extract_menus_batch(restaurants, args.model),
            "extraction_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "total": len(restaurants)
        }
    
    output_str = json.dumps(result, indent=2 if args.pretty else None, default=str)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output_str)
        dish_count = len(result.get("dishes", [])) if "dishes" in result else sum(
            len(m.get("dishes", [])) for m in result.get("menus", [])
        )
        print(json.dumps({
            "status": "success",
            "output_file": args.output,
            "dish_count": dish_count
        }))
    else:
        print(output_str)


if __name__ == "__main__":
    main()
