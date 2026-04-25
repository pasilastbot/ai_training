#!/usr/bin/env python3
"""
Destination Finder Subagent

Finds and evaluates destinations based on family wishes and constraints.
Returns ranked options with detailed analysis.

Usage:
    python destination_finder.py --family-id "fam001" --num 5
    python destination_finder.py --wishes wishes.json --constraints constraints.json
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
from memory.memory import get_family, get_family_wishes, cache_destination


def get_client() -> genai.Client:
    """Get Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY required")
    return genai.Client(api_key=api_key)


def find_destinations(
    family_profile: dict = None,
    aggregated_wishes: dict = None,
    constraints: dict = None,
    num_results: int = 5,
    exclude: list = None
) -> dict:
    """
    Find destinations matching family needs.
    
    Args:
        family_profile: Full family profile
        aggregated_wishes: Output from wish_aggregator.aggregate_wishes()
        constraints: Budget, dates, duration constraints
        num_results: Number of destinations to return
        exclude: Destinations to exclude
    """
    client = get_client()
    
    context_parts = []
    
    if family_profile:
        members_desc = []
        for m in family_profile.get("members", []):
            role = m.get("role", "adult")
            age = m.get("age", "")
            age_str = f" (age {age})" if age else ""
            members_desc.append(f"- {m.get('name', role)}: {role}{age_str}")
        
        context_parts.append(f"""Family composition:
{chr(10).join(members_desc)}""")
        
        if family_profile.get("constraints"):
            c = family_profile["constraints"]
            budget = c.get("budget", {})
            duration = c.get("duration", {})
            context_parts.append(f"""
Constraints:
- Budget: {budget.get('max', 'flexible')} {budget.get('currency', 'EUR')} maximum
- Duration: {duration.get('preferred_days', duration.get('min_days', 7))} days
- Departure from: {c.get('departure_location', 'Europe')}
- Max flight time: {c.get('max_flight_hours', 'flexible')} hours
""")
    
    if aggregated_wishes:
        ideal = aggregated_wishes.get("ideal_trip_profile", {})
        criteria = aggregated_wishes.get("search_criteria", {})
        
        context_parts.append(f"""
Based on family wishes analysis:
- Destination types wanted: {', '.join(ideal.get('destination_types', ['varied']))}
- Must include: {', '.join(ideal.get('must_include', []))}
- Must avoid: {', '.join(ideal.get('must_avoid', []))}
- Activity mix: {json.dumps(ideal.get('activity_mix', {}))}
- Trip style: {ideal.get('trip_style', 'balanced')}

Search criteria:
- Primary: {', '.join(criteria.get('primary_criteria', []))}
- Secondary: {', '.join(criteria.get('secondary_criteria', []))}
- Deal breakers: {', '.join(criteria.get('deal_breakers', []))}

Common ground from family:
- Destinations they agree on: {', '.join(aggregated_wishes.get('common_ground', {}).get('destinations', []))}
- Activities for all: {', '.join(aggregated_wishes.get('common_ground', {}).get('activities', []))}
""")
    
    if constraints:
        context_parts.append(f"""
Additional constraints:
- Travel dates: {constraints.get('travel_dates', 'flexible')}
- Season preference: {constraints.get('season', 'any')}
""")
    
    exclude_str = ""
    if exclude:
        exclude_str = f"\n\nExclude these destinations: {', '.join(exclude)}"
    
    system_prompt = """You are an expert travel advisor finding perfect family holiday destinations.

Consider:
1. Safety and family-friendliness
2. Suitable activities for ALL family members
3. Travel logistics (visa, flight time, health)
4. Value for money
5. Weather during travel period
6. Infrastructure for families (healthcare, food options)

Search for real, current information about each destination."""
    
    search_prompt = f"""Find {num_results} holiday destinations for this family:

{chr(10).join(context_parts)}
{exclude_str}

For each destination, provide comprehensive evaluation.

Return as JSON:
{{
    "destinations": [
        {{
            "rank": 1,
            "name": "Destination Name",
            "country": "Country",
            "region": "Region",
            "type": "beach|city|island|mountain|mixed",
            
            "overview": "Why this destination suits this family",
            
            "family_fit": {{
                "overall_score": 92,
                "by_age_group": {{
                    "toddlers": {{"score": 85, "notes": ""}},
                    "children": {{"score": 95, "notes": ""}},
                    "teens": {{"score": 80, "notes": ""}},
                    "adults": {{"score": 95, "notes": ""}},
                    "seniors": {{"score": 90, "notes": ""}}
                }},
                "matching_wishes": ["wish1", "wish2"],
                "potential_concerns": ["concern1"]
            }},
            
            "highlights": [
                {{"name": "Highlight", "why_good_for_family": "reason"}}
            ],
            
            "activities_for_everyone": [
                {{"activity": "Activity name", "suits": ["all"], "description": ""}}
            ],
            
            "weather": {{
                "best_months": [5, 6, 9, 10],
                "avg_temp": 28,
                "considerations": "notes"
            }},
            
            "logistics": {{
                "flight_time_hours": 4,
                "visa_needed": false,
                "health_considerations": "",
                "language_barrier": "low|medium|high"
            }},
            
            "budget_estimate": {{
                "daily_per_person_eur": 100,
                "total_estimate_eur": 4500,
                "value_rating": "excellent|good|moderate|expensive"
            }},
            
            "pros": ["pro1", "pro2"],
            "cons": ["con1", "con2"],
            
            "best_areas_to_stay": ["Area1", "Area2"],
            "recommended_duration_days": 7,
            
            "insider_tip": "Local knowledge tip"
        }}
    ],
    
    "comparison_notes": "How these destinations compare to each other",
    
    "top_recommendation": {{
        "destination": "Name",
        "why": "Reasoning for family"
    }}
}}"""
    
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[
            types.Tool(
                google_search=types.GoogleSearch(),
                google_maps=types.GoogleMaps()
            )
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
        
        for dest in result.get("destinations", []):
            cache_destination(
                dest.get("name", ""),
                dest.get("country", ""),
                dest
            )
        
        return result
    except json.JSONDecodeError:
        return {"error": "Failed to parse", "raw": response.text[:1000]}


def evaluate_specific_destination(
    destination: str,
    country: str = None,
    family_profile: dict = None,
    aggregated_wishes: dict = None
) -> dict:
    """Evaluate a specific destination for the family."""
    client = get_client()
    
    location = f"{destination}, {country}" if country else destination
    
    family_context = ""
    if family_profile:
        members = [f"{m.get('name', m.get('role'))}: {m.get('role')}" 
                   for m in family_profile.get("members", [])]
        family_context = f"Family: {', '.join(members)}"
    
    wishes_context = ""
    if aggregated_wishes:
        ideal = aggregated_wishes.get("ideal_trip_profile", {})
        wishes_context = f"""
Family wants: {', '.join(ideal.get('must_include', []))}
Family avoids: {', '.join(ideal.get('must_avoid', []))}
Activity preference: {json.dumps(ideal.get('activity_mix', {}))}
"""
    
    prompt = f"""Evaluate {location} as a holiday destination for this family:

{family_context}
{wishes_context}

Provide detailed evaluation with:
1. How well it matches family wishes
2. Specific activities for each age group
3. Best areas to stay
4. Budget estimates
5. Weather and best time to visit
6. Practical tips for families
7. Potential challenges

Return detailed JSON evaluation."""
    
    config = types.GenerateContentConfig(
        tools=[
            types.Tool(
                google_search=types.GoogleSearch(),
                google_maps=types.GoogleMaps()
            )
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
    parser = argparse.ArgumentParser(description="Destination Finder Subagent")
    parser.add_argument("--family-id", "-f", help="Family ID to find destinations for")
    parser.add_argument("--wishes", "-w", help="Aggregated wishes JSON file")
    parser.add_argument("--constraints", "-c", help="Constraints JSON file")
    parser.add_argument("--num", "-n", type=int, default=5, help="Number of destinations")
    parser.add_argument("--exclude", nargs="+", help="Destinations to exclude")
    parser.add_argument("--evaluate", "-e", help="Evaluate specific destination")
    parser.add_argument("--country", help="Country for evaluation")
    
    args = parser.parse_args()
    
    family_profile = None
    aggregated_wishes = None
    constraints = None
    
    if args.family_id:
        family_profile = get_family(args.family_id)
        if not family_profile:
            print(json.dumps({"error": f"Family not found: {args.family_id}"}))
            sys.exit(1)
        
        from subagents.wish_aggregator import aggregate_wishes
        aggregated_wishes = aggregate_wishes(args.family_id)
    
    if args.wishes:
        with open(args.wishes) as f:
            aggregated_wishes = json.load(f)
    
    if args.constraints:
        with open(args.constraints) as f:
            constraints = json.load(f)
    
    if args.evaluate:
        result = evaluate_specific_destination(
            args.evaluate,
            args.country,
            family_profile,
            aggregated_wishes
        )
    else:
        result = find_destinations(
            family_profile,
            aggregated_wishes,
            constraints,
            args.num,
            args.exclude
        )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
