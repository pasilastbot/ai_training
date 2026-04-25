#!/usr/bin/env python3
"""
Activity Finder Tool

Finds activities and experiences at a destination, filtered by family member preferences.
Uses Gemini with Google Maps and Search grounding.

Usage:
    python find_activities.py --destination "Barcelona" --types "beach,culture,kids"
    python find_activities.py --destination "Costa Rica" --family-profile profile.json
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


ACTIVITY_TYPES = [
    "beach", "water_sports", "snorkeling", "diving", "surfing",
    "hiking", "nature", "wildlife", "national_parks",
    "museums", "culture", "history", "art", "architecture",
    "theme_parks", "amusement", "playgrounds", "zoos", "aquariums",
    "adventure", "zip_line", "rafting", "climbing",
    "food_tours", "cooking_classes", "local_cuisine",
    "shopping", "markets", "crafts",
    "spa", "wellness", "relaxation",
    "sports", "golf", "tennis", "cycling",
    "boat_tours", "cruises", "sailing",
    "photography", "scenic_views",
    "nightlife", "entertainment"
]


def find_activities(
    destination: str,
    country: str = None,
    activity_types: list = None,
    family_profile: dict = None,
    duration_days: int = 7,
    include_prices: bool = True
) -> dict:
    """
    Find activities at a destination.
    
    Args:
        destination: Destination name
        country: Country (optional)
        activity_types: List of activity types to search for
        family_profile: Family profile with member preferences
        duration_days: Trip duration for activity planning
        include_prices: Include price estimates
    """
    client = get_client()
    
    location = f"{destination}, {country}" if country else destination
    
    prompt_parts = [f"Find activities and experiences in {location} for a {duration_days}-day family holiday."]
    
    if activity_types:
        prompt_parts.append(f"Focus on these activity types: {', '.join(activity_types)}")
    
    if family_profile:
        members_info = []
        all_interests = set()
        all_restrictions = []
        
        for m in family_profile.get("members", []):
            role = m.get("role", "adult")
            age = m.get("age")
            prefs = m.get("preferences", {})
            
            interests = prefs.get("activity_types", [])
            all_interests.update(interests)
            
            if prefs.get("mobility_requirements"):
                all_restrictions.append(f"{m.get('name')}: {prefs['mobility_requirements']}")
            
            age_str = f" (age {age})" if age else ""
            members_info.append(f"- {m.get('name', role)}: {role}{age_str}")
        
        prompt_parts.append(f"""
Family composition:
{chr(10).join(members_info)}

Family interests: {', '.join(all_interests) if all_interests else 'various'}
""")
        
        if all_restrictions:
            prompt_parts.append(f"Accessibility needs: {'; '.join(all_restrictions)}")
    
    system_prompt = """You are a travel activity expert. Find activities suitable for families.

For each activity, consider:
1. Age appropriateness (toddlers, kids, teens, adults, seniors)
2. Physical requirements
3. Duration and timing
4. Booking requirements
5. Prices (if requested)
6. Location within the destination

Return JSON:
{
    "destination": "Name",
    "activities": [
        {
            "name": "Activity Name",
            "type": "activity_type",
            "description": "What it is",
            "duration_hours": 2,
            "best_time": "morning|afternoon|evening|any",
            "suitable_for": {
                "toddler": false,
                "child": true,
                "teen": true,
                "adult": true,
                "senior": true
            },
            "physical_level": "easy|moderate|challenging",
            "price_range_eur": {"min": 20, "max": 50},
            "booking_required": true,
            "booking_advance_days": 3,
            "location": "Area/Address",
            "highlights": ["highlight1", "highlight2"],
            "tips": "Insider tips",
            "rating": 4.5,
            "family_friendly_features": ["feature1"],
            "website": "url if known"
        }
    ],
    "day_trip_options": [
        {
            "name": "Day trip name",
            "from": "starting point",
            "duration_hours": 8,
            "description": "What's included"
        }
    ],
    "rainy_day_options": ["activity1", "activity2"],
    "free_activities": ["activity1", "activity2"],
    "must_book_advance": ["activity1", "activity2"]
}"""
    
    search_prompt = f"""{chr(10).join(prompt_parts)}

{"Include price estimates in EUR." if include_prices else ""}

Search for current, accurate activity information. Return as detailed JSON."""
    
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
        
        if family_profile:
            result["family_recommendations"] = generate_family_recommendations(
                result.get("activities", []),
                family_profile
            )
        
        return result
    except json.JSONDecodeError:
        return {
            "error": "Failed to parse response",
            "raw_response": response.text[:1000]
        }


def generate_family_recommendations(activities: list, family_profile: dict) -> dict:
    """Generate activity recommendations for each family member."""
    recommendations = {}
    
    for member in family_profile.get("members", []):
        member_name = member.get("name", member.get("role", "member"))
        member_role = member.get("role", "adult")
        prefs = member.get("preferences", {})
        liked_types = set(prefs.get("activity_types", []))
        
        member_activities = []
        for activity in activities:
            suitable = activity.get("suitable_for", {})
            
            role_map = {
                "infant": "toddler",
                "toddler": "toddler",
                "child": "child",
                "teen": "teen",
                "adult": "adult",
                "senior": "senior"
            }
            mapped_role = role_map.get(member_role, "adult")
            
            if suitable.get(mapped_role, True):
                score = 0
                activity_type = activity.get("type", "").lower()
                
                if any(lt in activity_type for lt in liked_types):
                    score += 2
                
                if activity.get("physical_level") == "easy" and member_role in ["senior", "toddler"]:
                    score += 1
                
                if activity.get("family_friendly_features"):
                    score += 1
                
                member_activities.append({
                    "name": activity.get("name"),
                    "score": score,
                    "type": activity_type
                })
        
        member_activities.sort(key=lambda x: x["score"], reverse=True)
        recommendations[member_name] = [a["name"] for a in member_activities[:5]]
    
    return recommendations


def main():
    parser = argparse.ArgumentParser(description="Find activities at a destination")
    parser.add_argument("--destination", "-d", required=True, help="Destination name")
    parser.add_argument("--country", "-c", help="Country")
    parser.add_argument("--types", "-t", help="Comma-separated activity types")
    parser.add_argument("--family-profile", "-f", help="Family profile JSON file")
    parser.add_argument("--days", type=int, default=7, help="Trip duration")
    parser.add_argument("--no-prices", action="store_true", help="Skip price estimates")
    
    args = parser.parse_args()
    
    activity_types = args.types.split(",") if args.types else None
    
    family_profile = None
    if args.family_profile:
        with open(args.family_profile) as f:
            family_profile = json.load(f)
    
    result = find_activities(
        args.destination,
        args.country,
        activity_types,
        family_profile,
        args.days,
        not args.no_prices
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
