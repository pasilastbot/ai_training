#!/usr/bin/env python3
"""
Budget Calculator Tool

Estimates holiday budgets based on destination, duration, family size, and travel style.
Uses Gemini with Google Search for current pricing data.

Usage:
    python budget_calculator.py --destination "Barcelona" --days 7 --adults 2 --children 2
    python budget_calculator.py --destination "Thailand" --style luxury --family-profile profile.json
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


TRAVEL_STYLES = {
    "budget": {
        "description": "Hostels, street food, public transport, free activities",
        "accommodation_stars": "2-3",
        "dining": "Local eateries, markets, self-catering"
    },
    "mid-range": {
        "description": "3-4 star hotels, mix of restaurants, some tours",
        "accommodation_stars": "3-4",
        "dining": "Mix of local and tourist restaurants"
    },
    "comfort": {
        "description": "4 star hotels, good restaurants, guided tours",
        "accommodation_stars": "4",
        "dining": "Quality restaurants, some fine dining"
    },
    "luxury": {
        "description": "5 star hotels/resorts, fine dining, private tours",
        "accommodation_stars": "5",
        "dining": "Fine dining, exclusive experiences"
    }
}


def estimate_budget(
    destination: str,
    country: str = None,
    duration_days: int = 7,
    adults: int = 2,
    children: int = 0,
    teens: int = 0,
    travel_style: str = "mid-range",
    departure_city: str = "Helsinki",
    month: int = None,
    include_flights: bool = True,
    activities_level: str = "moderate"
) -> dict:
    """
    Estimate holiday budget.
    
    Args:
        destination: Destination name
        country: Country
        duration_days: Trip length
        adults: Number of adults
        children: Number of children (2-11)
        teens: Number of teens (12-17)
        travel_style: budget, mid-range, comfort, luxury
        departure_city: For flight estimates
        month: Travel month for seasonal pricing
        include_flights: Include flight costs
        activities_level: minimal, moderate, active
    """
    client = get_client()
    
    location = f"{destination}, {country}" if country else destination
    total_people = adults + children + teens
    
    style_info = TRAVEL_STYLES.get(travel_style, TRAVEL_STYLES["mid-range"])
    
    month_name = ""
    if month:
        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        month_name = month_names[month-1]
    
    prompt = f"""Estimate a realistic holiday budget for a trip to {location}.

Trip details:
- Duration: {duration_days} days / {duration_days - 1} nights
- Travelers: {adults} adults, {children} children (under 12), {teens} teenagers
- Travel style: {travel_style} ({style_info['description']})
- Accommodation: {style_info['accommodation_stars']} star level
- Departure from: {departure_city}
{f'- Travel month: {month_name}' if month_name else ''}
- Activity level: {activities_level}

Estimate costs in EUR. Search for current prices for {datetime.now().year}.

Return as JSON:
{{
    "destination": "{destination}",
    "duration_days": {duration_days},
    "travelers": {{
        "adults": {adults},
        "children": {children},
        "teens": {teens},
        "total": {total_people}
    }},
    "travel_style": "{travel_style}",
    "currency": "EUR",
    
    "flights": {{
        "included": {str(include_flights).lower()},
        "route": "{departure_city} - {destination}",
        "adult_return": 400,
        "child_return": 350,
        "teen_return": 400,
        "total": 1500,
        "notes": "Price notes, direct vs connecting",
        "booking_tip": "Best time to book"
    }},
    
    "accommodation": {{
        "type": "hotel/resort/apartment",
        "star_rating": 4,
        "rooms_needed": 2,
        "price_per_night": 150,
        "nights": {duration_days - 1},
        "total": 1050,
        "recommended_area": "Where to stay",
        "family_friendly_options": ["Hotel1", "Hotel2"]
    }},
    
    "food": {{
        "style": "{style_info['dining']}",
        "breakfast_included": true,
        "daily_per_adult": 50,
        "daily_per_child": 25,
        "daily_total": 150,
        "trip_total": 1050,
        "tips": "Dining tips"
    }},
    
    "activities": {{
        "level": "{activities_level}",
        "estimated_activities": 8,
        "total": 400,
        "included_examples": ["Activity1", "Activity2"],
        "free_options": ["Free1", "Free2"]
    }},
    
    "local_transport": {{
        "type": "taxi/public/rental",
        "daily_estimate": 30,
        "total": 210,
        "recommendation": "Best transport option"
    }},
    
    "other_costs": {{
        "travel_insurance": 100,
        "visa_fees": 0,
        "sim_card_data": 20,
        "tips_and_misc": 100,
        "shopping_buffer": 200,
        "total": 420
    }},
    
    "summary": {{
        "flights": 1500,
        "accommodation": 1050,
        "food": 1050,
        "activities": 400,
        "transport": 210,
        "other": 420,
        "grand_total": 4630,
        "per_person": 1157,
        "per_day": 661,
        "per_person_per_day": 165
    }},
    
    "budget_tiers": {{
        "budget_version": 3000,
        "mid_range_version": 4500,
        "comfort_version": 6500,
        "luxury_version": 12000
    }},
    
    "money_saving_tips": [
        "Tip 1",
        "Tip 2"
    ],
    
    "seasonal_notes": "Price variations by season",
    "confidence": "high|medium|low",
    "data_sources": "Where estimates come from"
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


def compare_budgets(
    destinations: list,
    duration_days: int = 7,
    adults: int = 2,
    children: int = 0,
    travel_style: str = "mid-range",
    departure_city: str = "Helsinki"
) -> dict:
    """Compare budgets across multiple destinations."""
    client = get_client()
    
    total_people = adults + children
    dest_str = ", ".join(destinations)
    
    prompt = f"""Compare holiday budgets for these destinations: {dest_str}

Trip details:
- Duration: {duration_days} days
- Travelers: {adults} adults, {children} children
- Travel style: {travel_style}
- Departure from: {departure_city}

Provide comparable estimates in EUR.

Return as JSON:
{{
    "destinations": [
        {{
            "name": "Destination",
            "total_budget": 4500,
            "per_person": 1125,
            "per_day": 643,
            "flights": 1200,
            "accommodation_per_night": 120,
            "daily_expenses": 150,
            "value_rating": 4,
            "pros": ["Affordable food", "Free beaches"],
            "cons": ["Expensive flights"],
            "best_value_months": [4, 5, 10]
        }}
    ],
    "comparison": {{
        "cheapest": "Destination name",
        "best_value": "Destination name",
        "most_expensive": "Destination name",
        "price_difference_percent": 35
    }},
    "recommendation": "Which destination offers best value and why"
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


from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Estimate holiday budget")
    parser.add_argument("--destination", "-d", help="Destination")
    parser.add_argument("--country", "-c", help="Country")
    parser.add_argument("--days", type=int, default=7, help="Duration")
    parser.add_argument("--adults", type=int, default=2, help="Number of adults")
    parser.add_argument("--children", type=int, default=0, help="Children under 12")
    parser.add_argument("--teens", type=int, default=0, help="Teenagers 12-17")
    parser.add_argument("--style", default="mid-range", 
                        choices=["budget", "mid-range", "comfort", "luxury"])
    parser.add_argument("--from", dest="departure", default="Helsinki", help="Departure city")
    parser.add_argument("--month", type=int, help="Travel month (1-12)")
    parser.add_argument("--compare", nargs="+", help="Compare multiple destinations")
    
    args = parser.parse_args()
    
    if args.compare:
        result = compare_budgets(
            args.compare,
            args.days,
            args.adults,
            args.children,
            args.style,
            args.departure
        )
    elif args.destination:
        result = estimate_budget(
            args.destination,
            args.country,
            args.days,
            args.adults,
            args.children,
            args.teens,
            args.style,
            args.departure,
            args.month
        )
    else:
        parser.print_help()
        sys.exit(1)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
