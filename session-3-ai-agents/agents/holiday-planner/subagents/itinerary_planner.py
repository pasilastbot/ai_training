#!/usr/bin/env python3
"""
Itinerary Planner Subagent

Creates detailed day-by-day itineraries for family holidays.
Balances activities for all family members with rest time.

Usage:
    python itinerary_planner.py --destination "Barcelona" --days 7 --family-id "fam001"
    python itinerary_planner.py --trip-id "trip123" --generate
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
from memory.memory import get_family, get_trip, update_trip, create_trip


def get_client() -> genai.Client:
    """Get Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY required")
    return genai.Client(api_key=api_key)


def create_itinerary(
    destinations: list,
    duration_days: int,
    family_profile: dict = None,
    travel_dates: dict = None,
    pace: str = "balanced",
    priorities: list = None
) -> dict:
    """
    Create a detailed day-by-day itinerary.
    
    Args:
        destinations: List of destinations with duration per destination
        duration_days: Total trip duration
        family_profile: Family profile with member info
        travel_dates: Start and end dates
        pace: relaxed, balanced, active, adventure
        priorities: List of priority activities/experiences
    """
    client = get_client()
    
    dest_str = json.dumps(destinations, ensure_ascii=False)
    
    family_context = ""
    if family_profile:
        members_info = []
        all_activities = set()
        restrictions = []
        
        for m in family_profile.get("members", []):
            role = m.get("role", "adult")
            age = m.get("age")
            prefs = m.get("preferences", {})
            
            activities = prefs.get("activity_types", [])
            all_activities.update(activities)
            
            dietary = prefs.get("dietary_restrictions", [])
            if dietary:
                restrictions.append(f"{m.get('name', role)}: {', '.join(dietary)}")
            
            mobility = prefs.get("mobility_requirements")
            if mobility:
                restrictions.append(f"{m.get('name', role)}: {mobility}")
            
            age_str = f" (age {age})" if age else ""
            likes = f", likes: {', '.join(activities[:3])}" if activities else ""
            members_info.append(f"- {m.get('name', role)}: {role}{age_str}{likes}")
        
        family_context = f"""
Family members:
{chr(10).join(members_info)}

Combined activity interests: {', '.join(all_activities) if all_activities else 'varied'}
Dietary/mobility considerations: {'; '.join(restrictions) if restrictions else 'none noted'}
"""
    
    dates_context = ""
    if travel_dates:
        start = travel_dates.get("start")
        end = travel_dates.get("end")
        if start:
            dates_context = f"\nTravel dates: {start} to {end or 'flexible'}"
    
    priorities_str = ""
    if priorities:
        priorities_str = f"\nMust include: {', '.join(priorities)}"
    
    system_prompt = """You are a family travel itinerary expert. Create realistic, family-friendly itineraries.

Consider:
1. Appropriate pacing for families with children
2. Include rest/downtime (especially after travel days)
3. Balance activities for different ages
4. Account for meal times and snack breaks
5. Include rainy day alternatives
6. Consider opening hours and booking requirements
7. Group nearby activities to minimize travel
8. Include local tips and dining recommendations
9. Build in flexibility"""
    
    prompt = f"""Create a detailed {duration_days}-day itinerary for these destinations:
{dest_str}

{family_context}
{dates_context}
{priorities_str}

Pace: {pace}

Return as JSON:
{{
    "trip_overview": {{
        "total_days": {duration_days},
        "destinations_visited": ["list"],
        "theme": "Trip theme/description",
        "pace": "{pace}"
    }},
    
    "preparation": {{
        "book_in_advance": [
            {{"what": "Activity", "when": "X weeks before", "why": "Sells out"}}
        ],
        "packing_essentials": ["item1", "item2"],
        "documents_needed": ["passport", "etc"]
    }},
    
    "daily_itinerary": [
        {{
            "day": 1,
            "date": "Day of week, date if known",
            "title": "Arrival Day",
            "location": "Destination",
            "accommodation": "Where staying",
            
            "schedule": [
                {{
                    "time": "14:00",
                    "activity": "Check in to hotel",
                    "duration_hours": 1,
                    "suitable_for": ["all"],
                    "notes": "Room should be ready"
                }},
                {{
                    "time": "15:00",
                    "activity": "Explore neighborhood",
                    "duration_hours": 2,
                    "suitable_for": ["all"],
                    "notes": "Easy walk to stretch legs after travel"
                }}
            ],
            
            "meals": {{
                "breakfast": {{"where": "hotel/restaurant", "notes": ""}},
                "lunch": {{"where": "suggestion", "notes": ""}},
                "dinner": {{"where": "recommendation", "type": "casual/fine", "notes": "Book ahead if needed"}}
            }},
            
            "budget_estimate_eur": 150,
            "rainy_alternative": "What to do if weather is bad",
            "tips": "Day-specific tips",
            "energy_level": "low|medium|high"
        }}
    ],
    
    "optional_activities": [
        {{
            "name": "Activity",
            "best_day": 3,
            "instead_of": "What it could replace",
            "notes": ""
        }}
    ],
    
    "dining_recommendations": [
        {{
            "name": "Restaurant",
            "location": "Area",
            "cuisine": "Type",
            "family_friendly": true,
            "price_range": "€€",
            "best_for": "lunch/dinner",
            "reservation_needed": false,
            "kid_highlights": ""
        }}
    ],
    
    "practical_info": {{
        "best_transport": "How to get around",
        "tipping_culture": "",
        "safety_notes": "",
        "emergency_contacts": "Local emergency numbers"
    }},
    
    "budget_summary": {{
        "estimated_daily": 200,
        "estimated_total": 1400,
        "breakdown": {{
            "activities": 400,
            "food": 500,
            "transport": 200,
            "shopping": 200,
            "buffer": 100
        }}
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
        temperature=0.4,
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


def optimize_itinerary(
    current_itinerary: dict,
    feedback: str,
    family_profile: dict = None
) -> dict:
    """Optimize an existing itinerary based on feedback."""
    client = get_client()
    
    prompt = f"""Optimize this family holiday itinerary based on the feedback.

Current itinerary:
{json.dumps(current_itinerary, ensure_ascii=False, indent=2)}

Feedback:
{feedback}

{f'Family profile: {json.dumps(family_profile)}' if family_profile else ''}

Adjust the itinerary to address the feedback while maintaining:
1. Appropriate pacing
2. Balance for all family members
3. Logical geographical flow
4. Meal times

Return the optimized itinerary in the same JSON format."""
    
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
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


def add_day_details(
    itinerary: dict,
    day_number: int,
    focus: str = None
) -> dict:
    """Add more details to a specific day."""
    client = get_client()
    
    current_day = None
    for day in itinerary.get("daily_itinerary", []):
        if day.get("day") == day_number:
            current_day = day
            break
    
    if not current_day:
        return {"error": f"Day {day_number} not found"}
    
    prompt = f"""Enhance this day's itinerary with more specific details:

Current plan for Day {day_number}:
{json.dumps(current_day, ensure_ascii=False, indent=2)}

{f'Focus on: {focus}' if focus else ''}

Add:
1. Exact addresses/locations
2. Estimated costs for each activity
3. Time buffers for families with kids
4. Backup options if something is closed
5. Specific restaurant recommendations with family-friendly notes
6. Photo opportunity spots
7. Rest stop suggestions

Return enhanced day plan as JSON."""
    
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
    parser = argparse.ArgumentParser(description="Itinerary Planner Subagent")
    parser.add_argument("--destination", "-d", help="Main destination")
    parser.add_argument("--destinations", help="JSON array of destinations")
    parser.add_argument("--days", type=int, default=7, help="Trip duration")
    parser.add_argument("--family-id", "-f", help="Family ID")
    parser.add_argument("--trip-id", "-t", help="Trip ID to update")
    parser.add_argument("--pace", choices=["relaxed", "balanced", "active", "adventure"],
                        default="balanced")
    parser.add_argument("--priorities", nargs="+", help="Priority activities")
    parser.add_argument("--start-date", help="Trip start date (YYYY-MM-DD)")
    parser.add_argument("--optimize", action="store_true", help="Optimize existing itinerary")
    parser.add_argument("--feedback", help="Feedback for optimization")
    parser.add_argument("--day-details", type=int, help="Add details to specific day")
    
    args = parser.parse_args()
    
    family_profile = None
    if args.family_id:
        family_profile = get_family(args.family_id)
    
    existing_itinerary = None
    if args.trip_id:
        trip = get_trip(args.trip_id)
        if trip:
            existing_itinerary = trip.get("itinerary")
    
    if args.optimize and existing_itinerary and args.feedback:
        result = optimize_itinerary(existing_itinerary, args.feedback, family_profile)
    
    elif args.day_details and existing_itinerary:
        result = add_day_details(existing_itinerary, args.day_details)
    
    else:
        destinations = []
        if args.destinations:
            destinations = json.loads(args.destinations)
        elif args.destination:
            destinations = [{"name": args.destination, "duration_days": args.days}]
        else:
            print(json.dumps({"error": "Destination required"}))
            sys.exit(1)
        
        travel_dates = None
        if args.start_date:
            start = datetime.strptime(args.start_date, "%Y-%m-%d")
            end = start + timedelta(days=args.days - 1)
            travel_dates = {
                "start": args.start_date,
                "end": end.strftime("%Y-%m-%d")
            }
        
        result = create_itinerary(
            destinations,
            args.days,
            family_profile,
            travel_dates,
            args.pace,
            args.priorities
        )
        
        if args.trip_id and "error" not in result:
            update_trip(args.trip_id, {"itinerary": result})
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
