#!/usr/bin/env python3
"""
Destination Search Tool

Searches for holiday destinations using Gemini with Google Search grounding.
Returns structured destination information including activities, weather, and suitability.

Usage:
    python search_destinations.py --query "beach family holiday europe"
    python search_destinations.py --criteria '{"climate": "warm", "activities": ["beach", "kids"]}'
"""

import argparse
import json
import os
import sys
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


def search_destinations(
    query: str = None,
    criteria: dict = None,
    family_profile: dict = None,
    num_results: int = 5
) -> dict:
    """
    Search for destinations matching the query or criteria.
    
    Args:
        query: Natural language search query
        criteria: Structured criteria (climate, activities, budget, etc.)
        family_profile: Family profile to match against
        num_results: Number of destinations to return
    """
    client = get_client()
    
    prompt_parts = []
    
    if query:
        prompt_parts.append(f"Search query: {query}")
    
    if criteria:
        prompt_parts.append(f"Criteria: {json.dumps(criteria, ensure_ascii=False)}")
    
    if family_profile:
        members_desc = []
        for m in family_profile.get("members", []):
            role = m.get("role", "adult")
            age = m.get("age", "")
            prefs = m.get("preferences", {})
            activities = prefs.get("activity_types", [])
            members_desc.append(f"- {m.get('name', 'Member')}: {role}, age {age}, likes {', '.join(activities[:3]) if activities else 'various activities'}")
        
        constraints = family_profile.get("constraints", {})
        budget = constraints.get("budget", {})
        duration = constraints.get("duration", {})
        
        prompt_parts.append(f"""
Family profile:
{chr(10).join(members_desc)}

Constraints:
- Budget: {budget.get('min', 0)}-{budget.get('max', 'flexible')} {budget.get('currency', 'EUR')}
- Duration: {duration.get('preferred_days', duration.get('min_days', 7))} days
- Departure: {constraints.get('departure_location', 'flexible')}
""")
    
    system_prompt = """You are a travel expert helping find the perfect holiday destinations for families.
    
When searching for destinations, consider:
1. Suitability for all family members (kids, teens, adults, seniors)
2. Available activities matching interests
3. Weather and best time to visit
4. Budget considerations
5. Travel logistics (flight time, visa requirements)
6. Safety and family-friendliness

Return results as JSON with this structure:
{
    "destinations": [
        {
            "name": "Destination Name",
            "country": "Country",
            "region": "Region",
            "type": "beach|city|mountain|island|countryside",
            "description": "Brief description",
            "highlights": ["highlight1", "highlight2"],
            "best_for": ["families", "beach lovers", "etc"],
            "best_months": [6, 7, 8],
            "avg_temp_summer": 28,
            "avg_temp_winter": 15,
            "flight_time_from_europe_hours": 4,
            "budget_level": "budget|mid-range|luxury",
            "daily_budget_estimate_eur": 150,
            "kid_friendly_score": 4,
            "adventure_score": 3,
            "relaxation_score": 5,
            "culture_score": 3,
            "activities": [
                {"name": "Activity", "type": "beach|culture|adventure", "suitable_for": ["all"]}
            ],
            "family_considerations": "Notes about traveling with family",
            "visa_for_eu": "not_required|on_arrival|required"
        }
    ],
    "search_notes": "Any relevant notes about the search"
}"""
    
    search_prompt = f"""Find {num_results} holiday destinations matching these requirements:

{chr(10).join(prompt_parts)}

Search for current, accurate information about these destinations. Return as JSON."""
    
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[
            types.Tool(google_search=types.GoogleSearch())
        ],
        temperature=0.3,
        response_mime_type="application/json"
    )
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=search_prompt,
        config=config
    )
    
    try:
        result = json.loads(response.text)
        return result
    except json.JSONDecodeError:
        return {
            "destinations": [],
            "error": "Failed to parse response",
            "raw_response": response.text[:1000]
        }


def get_destination_details(name: str, country: str = None) -> dict:
    """Get detailed information about a specific destination."""
    client = get_client()
    
    location = f"{name}, {country}" if country else name
    
    prompt = f"""Get detailed travel information for {location} as a holiday destination.

Include:
1. Overview and main attractions
2. Best time to visit (by month)
3. Weather patterns throughout the year
4. Top activities for families
5. Accommodation options and areas to stay
6. Transportation (getting there and around)
7. Food and dining scene
8. Safety and health considerations
9. Visa requirements for EU citizens
10. Budget estimates (per day, per person)
11. Tips for families with children
12. Local customs and etiquette

Return as detailed JSON with all this information structured."""

    config = types.GenerateContentConfig(
        tools=[
            types.Tool(google_search=types.GoogleSearch())
        ],
        temperature=0.3,
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
    parser = argparse.ArgumentParser(description="Search for holiday destinations")
    parser.add_argument("--query", "-q", help="Search query")
    parser.add_argument("--criteria", "-c", help="JSON criteria")
    parser.add_argument("--family", "-f", help="Family profile JSON file")
    parser.add_argument("--details", "-d", help="Get details for specific destination")
    parser.add_argument("--country", help="Country for details lookup")
    parser.add_argument("--num", "-n", type=int, default=5, help="Number of results")
    
    args = parser.parse_args()
    
    if args.details:
        result = get_destination_details(args.details, args.country)
    elif args.query or args.criteria:
        criteria = json.loads(args.criteria) if args.criteria else None
        family = None
        if args.family:
            with open(args.family) as f:
                family = json.load(f)
        result = search_destinations(args.query, criteria, family, args.num)
    else:
        parser.print_help()
        sys.exit(1)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
