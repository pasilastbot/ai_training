#!/usr/bin/env python3
"""
Weather Information Tool

Gets weather information and best travel times for destinations.
Uses Gemini with Google Search for accurate, current data.

Usage:
    python weather_info.py --destination "Bali" --month 8
    python weather_info.py --destination "Iceland" --dates "2025-07-15" "2025-07-25"
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_env import load_agent_environment
load_agent_environment()

from google import genai
from google.genai import types


def get_client() -> genai.Client:
    """Get Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY required")
    return genai.Client(api_key=api_key)


def get_weather_info(
    destination: str,
    country: str = None,
    month: int = None,
    start_date: str = None,
    end_date: str = None
) -> dict:
    """
    Get weather information for a destination.
    
    Args:
        destination: Destination name
        country: Country (optional)
        month: Specific month (1-12)
        start_date: Trip start date (YYYY-MM-DD)
        end_date: Trip end date (YYYY-MM-DD)
    """
    client = get_client()
    
    location = f"{destination}, {country}" if country else destination
    
    time_context = ""
    if month:
        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        time_context = f"specifically for {month_names[month-1]}"
    elif start_date and end_date:
        time_context = f"for the period {start_date} to {end_date}"
    else:
        time_context = "throughout the year with month-by-month breakdown"
    
    prompt = f"""Get detailed weather information for {location} {time_context}.

Include:
1. Temperature ranges (high/low in Celsius)
2. Rainfall/precipitation
3. Humidity levels
4. Sea temperature (if coastal)
5. Sunshine hours
6. Weather warnings or considerations
7. Best activities for this weather
8. Packing recommendations
9. How weather affects family travel

Return as JSON:
{{
    "destination": "{destination}",
    "country": "{country or 'detected'}",
    {"monthly_data" if not month else f"month_{month}"}: {{
        "temp_high_c": 28,
        "temp_low_c": 22,
        "rainfall_mm": 50,
        "rainy_days": 8,
        "humidity_percent": 75,
        "sea_temp_c": 26,
        "sunshine_hours": 8,
        "uv_index": 8,
        "weather_description": "description",
        "crowd_level": "low|medium|high|peak",
        "price_level": "low|medium|high",
        "recommended_for": ["beach", "hiking", etc]
    }},
    "best_months": [4, 5, 10, 11],
    "avoid_months": [8, 9],
    "seasons": {{
        "high_season": {{"months": [12, 1, 2], "notes": ""}},
        "shoulder_season": {{"months": [3, 4, 10, 11], "notes": ""}},
        "low_season": {{"months": [5, 6, 7, 8, 9], "notes": ""}}
    }},
    "weather_warnings": ["monsoon season July-September", etc],
    "family_considerations": "Notes about weather for families with kids",
    "packing_essentials": ["item1", "item2"],
    "indoor_alternatives": ["activity1", "activity2"]
}}"""
    
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.2,
        response_mime_type="application/json"
    )
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config=config
    )
    
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {"error": "Failed to parse", "raw": response.text[:1000]}


def get_best_time_to_visit(
    destinations: list,
    family_preferences: dict = None
) -> dict:
    """
    Compare best times to visit multiple destinations.
    
    Args:
        destinations: List of destinations to compare
        family_preferences: Family constraints and preferences
    """
    client = get_client()
    
    dest_str = ", ".join(destinations)
    
    prefs_context = ""
    if family_preferences:
        constraints = family_preferences.get("constraints", {})
        travel_dates = constraints.get("travel_dates", {})
        
        if travel_dates.get("preferred_months"):
            months = [["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][m-1]
                     for m in travel_dates["preferred_months"]]
            prefs_context = f"The family prefers traveling in: {', '.join(months)}"
        
        if constraints.get("budget"):
            prefs_context += f"\nBudget level: {constraints['budget'].get('max', 'flexible')} EUR total"
    
    prompt = f"""Compare the best times to visit these destinations: {dest_str}

{prefs_context}

Consider:
1. Weather suitability for families
2. Avoiding extreme heat for children
3. School holiday periods (European calendar)
4. Price/crowd levels
5. Special events or festivals

Return as JSON:
{{
    "destinations": [
        {{
            "name": "Destination",
            "best_months": [4, 5, 10],
            "good_months": [3, 6, 9, 11],
            "avoid_months": [7, 8],
            "best_month_reason": "Why this month is best",
            "family_best_time": "Specific recommendation for families",
            "school_holiday_match": {{
                "summer": {{"suitable": true, "notes": ""}},
                "winter": {{"suitable": false, "notes": ""}},
                "easter": {{"suitable": true, "notes": ""}}
            }}
        }}
    ],
    "comparison_summary": "Overall comparison and recommendation",
    "recommendation": {{
        "destination": "Best choice",
        "when": "Best time",
        "why": "Reasoning"
    }}
}}"""
    
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.2,
        response_mime_type="application/json"
    )
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config=config
    )
    
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {"error": "Failed to parse", "raw": response.text[:1000]}


def main():
    parser = argparse.ArgumentParser(description="Get weather info for destinations")
    parser.add_argument("--destination", "-d", help="Destination name")
    parser.add_argument("--country", "-c", help="Country")
    parser.add_argument("--month", "-m", type=int, help="Month (1-12)")
    parser.add_argument("--dates", nargs=2, help="Start and end dates (YYYY-MM-DD)")
    parser.add_argument("--compare", nargs="+", help="Compare multiple destinations")
    
    args = parser.parse_args()
    
    if args.compare:
        result = get_best_time_to_visit(args.compare)
    elif args.destination:
        start_date, end_date = args.dates if args.dates else (None, None)
        result = get_weather_info(
            args.destination,
            args.country,
            args.month,
            start_date,
            end_date
        )
    else:
        parser.print_help()
        sys.exit(1)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
