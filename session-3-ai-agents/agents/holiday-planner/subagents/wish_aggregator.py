#!/usr/bin/env python3
"""
Wish Aggregator Subagent

Collects and aggregates holiday wishes from all family members.
Identifies common ground, conflicts, and priorities.

Usage:
    python wish_aggregator.py --family-id "fam001" --collect
    python wish_aggregator.py --family-id "fam001" --aggregate
    echo '{"member": "Mom", "wishes": {...}}' | python wish_aggregator.py --add
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
from memory.memory import (
    get_family, store_wishes, get_family_wishes, update_member_preferences
)


def get_client() -> genai.Client:
    """Get Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY required")
    return genai.Client(api_key=api_key)


def collect_wishes_interactive(family_id: str) -> dict:
    """
    Interactive session to collect wishes from family members.
    Returns structured wishes for each member.
    """
    family = get_family(family_id)
    if not family:
        return {"error": f"Family not found: {family_id}"}
    
    print(f"\n=== Holiday Wish Collection for {family['name']} ===\n")
    
    all_wishes = []
    
    for member in family.get("members", []):
        member_name = member.get("name", member.get("role", "Family member"))
        print(f"\n--- Collecting wishes from {member_name} ---")
        
        wishes = {
            "member_id": member.get("id"),
            "member_name": member_name,
            "destinations": [],
            "activities": [],
            "must_haves": [],
            "deal_breakers": [],
            "priority": None
        }
        
        print("Where would you like to go? (comma-separated, or 'skip'):")
        destinations = input("> ").strip()
        if destinations and destinations.lower() != "skip":
            wishes["destinations"] = [d.strip() for d in destinations.split(",")]
        
        print("What activities interest you? (beach, hiking, culture, adventure, etc.):")
        activities = input("> ").strip()
        if activities and activities.lower() != "skip":
            wishes["activities"] = [a.strip() for a in activities.split(",")]
        
        print("Any must-haves for this trip? (e.g., 'pool', 'kids club', 'quiet beach'):")
        must_haves = input("> ").strip()
        if must_haves and must_haves.lower() != "skip":
            wishes["must_haves"] = [m.strip() for m in must_haves.split(",")]
        
        print("Anything you definitely want to avoid? (e.g., 'long flights', 'crowds'):")
        deal_breakers = input("> ").strip()
        if deal_breakers and deal_breakers.lower() != "skip":
            wishes["deal_breakers"] = [d.strip() for d in deal_breakers.split(",")]
        
        print("What's your top priority? (relaxation/adventure/culture/family-time/budget):")
        priority = input("> ").strip()
        if priority:
            wishes["priority"] = priority
        
        all_wishes.append(wishes)
        
        store_wishes(family_id, member.get("id"), wishes)
    
    return {"family_id": family_id, "wishes_collected": len(all_wishes), "wishes": all_wishes}


def add_wishes(family_id: str, member_id: str, wishes: dict) -> dict:
    """Add wishes for a specific family member."""
    family = get_family(family_id)
    if not family:
        return {"error": f"Family not found: {family_id}"}
    
    result = store_wishes(family_id, member_id, wishes)
    
    prefs = {
        "activity_types": wishes.get("activities", []),
        "must_haves": wishes.get("must_haves", []),
        "deal_breakers": wishes.get("deal_breakers", [])
    }
    update_member_preferences(family_id, member_id, prefs)
    
    return {"status": "stored", **result}


def aggregate_wishes(family_id: str) -> dict:
    """
    Aggregate all family wishes to find common ground and conflicts.
    Uses AI to analyze and synthesize wishes.
    """
    family = get_family(family_id)
    if not family:
        return {"error": f"Family not found: {family_id}"}
    
    wishes = get_family_wishes(family_id)
    if not wishes:
        return {"error": "No wishes collected yet"}
    
    client = get_client()
    
    wishes_summary = json.dumps(wishes, ensure_ascii=False, indent=2)
    family_summary = json.dumps({
        "name": family.get("name"),
        "members": [
            {"name": m.get("name"), "role": m.get("role"), "age": m.get("age")}
            for m in family.get("members", [])
        ],
        "constraints": family.get("constraints", {})
    }, ensure_ascii=False, indent=2)
    
    prompt = f"""Analyze these holiday wishes from a family and find the best way to satisfy everyone.

Family Profile:
{family_summary}

Wishes from each member:
{wishes_summary}

Analyze and return JSON:
{{
    "common_ground": {{
        "destinations": ["destinations everyone likes or is okay with"],
        "activities": ["activities that work for all"],
        "shared_priorities": ["priorities most agree on"],
        "consensus_score": 85
    }},
    
    "conflicts": [
        {{
            "description": "What the conflict is",
            "members_involved": ["Member1", "Member2"],
            "possible_resolutions": ["Resolution 1", "Resolution 2"]
        }}
    ],
    
    "member_priorities": {{
        "MemberName": {{
            "top_wishes": ["wish1", "wish2"],
            "flexibility": "high|medium|low",
            "key_need": "What they need most"
        }}
    }},
    
    "recommended_approach": {{
        "destination_strategy": "How to pick destinations",
        "activity_balance": "How to balance different interests",
        "compromise_suggestions": ["Suggestion 1", "Suggestion 2"]
    }},
    
    "ideal_trip_profile": {{
        "destination_types": ["beach", "city"],
        "must_include": ["feature1", "feature2"],
        "must_avoid": ["thing1", "thing2"],
        "activity_mix": {{
            "relaxation": 40,
            "adventure": 30,
            "culture": 20,
            "other": 10
        }},
        "trip_style": "description of ideal trip"
    }},
    
    "search_criteria": {{
        "primary_criteria": ["criterion1", "criterion2"],
        "secondary_criteria": ["criterion3"],
        "deal_breakers": ["must avoid this"]
    }}
}}"""
    
    config = types.GenerateContentConfig(
        temperature=0.3,
        response_mime_type="application/json"
    )
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config=config
    )
    
    try:
        result = json.loads(response.text)
        result["family_id"] = family_id
        result["wishes_analyzed"] = len(wishes)
        return result
    except json.JSONDecodeError:
        return {"error": "Failed to parse", "raw": response.text[:1000]}


def generate_questionnaire(family_id: str, language: str = "en") -> dict:
    """
    Generate a structured questionnaire for collecting wishes.
    Can be used in UI for guided input.
    """
    family = get_family(family_id)
    if not family:
        return {"error": f"Family not found: {family_id}"}
    
    questions = {
        "en": [
            {
                "id": "destinations",
                "question": "Which destinations interest you?",
                "type": "multi-select-or-text",
                "suggestions": ["Beach resort", "European city", "Tropical island", 
                               "Mountain retreat", "Safari", "Theme parks", "Cruise"],
                "allow_custom": True
            },
            {
                "id": "activities",
                "question": "What activities do you enjoy?",
                "type": "multi-select",
                "options": ["Beach/Swimming", "Hiking", "Museums/Culture", "Adventure sports",
                           "Relaxation/Spa", "Food experiences", "Shopping", "Wildlife",
                           "Water sports", "Theme parks", "Photography", "Local experiences"]
            },
            {
                "id": "climate",
                "question": "What climate do you prefer?",
                "type": "single-select",
                "options": ["Hot and sunny", "Warm", "Mild", "Cool", "Doesn't matter"]
            },
            {
                "id": "pace",
                "question": "What pace of travel do you prefer?",
                "type": "single-select",
                "options": ["Very relaxed - few activities", "Balanced - mix of activity and rest",
                           "Active - lots to see and do", "Adventure - packed schedule"]
            },
            {
                "id": "must_haves",
                "question": "What are your must-haves?",
                "type": "text",
                "placeholder": "e.g., pool, kids club, good food, nature..."
            },
            {
                "id": "avoid",
                "question": "What do you want to avoid?",
                "type": "text",
                "placeholder": "e.g., long flights, extreme heat, crowds..."
            },
            {
                "id": "priority",
                "question": "What's most important to you?",
                "type": "ranking",
                "items": ["Relaxation", "Adventure", "Culture", "Family time", 
                        "Value for money", "Unique experiences"]
            }
        ],
        "fi": [
            {
                "id": "destinations",
                "question": "Mitkä kohteet kiinnostavat sinua?",
                "type": "multi-select-or-text",
                "suggestions": ["Rantakohde", "Eurooppalainen kaupunki", "Trooppinen saari",
                               "Vuoristoloma", "Safari", "Huvipuistot", "Risteily"],
                "allow_custom": True
            },
            {
                "id": "activities",
                "question": "Mistä aktiviteeteista nautit?",
                "type": "multi-select",
                "options": ["Ranta/Uinti", "Vaellus", "Museot/Kulttuuri", "Seikkailulajit",
                           "Rentoutuminen/Kylpylä", "Ruokaelämykset", "Ostokset", "Villieläimet",
                           "Vesiurheilu", "Huvipuistot", "Valokuvaus", "Paikalliset kokemukset"]
            }
        ]
    }
    
    return {
        "family_id": family_id,
        "family_name": family.get("name"),
        "members": [
            {"id": m.get("id"), "name": m.get("name"), "role": m.get("role")}
            for m in family.get("members", [])
        ],
        "questions": questions.get(language, questions["en"])
    }


def main():
    parser = argparse.ArgumentParser(description="Wish Aggregator Subagent")
    parser.add_argument("--family-id", "-f", help="Family ID")
    parser.add_argument("--collect", action="store_true", help="Interactive wish collection")
    parser.add_argument("--aggregate", action="store_true", help="Aggregate collected wishes")
    parser.add_argument("--add", action="store_true", help="Add wishes from stdin JSON")
    parser.add_argument("--questionnaire", action="store_true", help="Generate questionnaire")
    parser.add_argument("--language", "-l", default="en", help="Language (en/fi)")
    
    args = parser.parse_args()
    
    if args.collect and args.family_id:
        result = collect_wishes_interactive(args.family_id)
    elif args.aggregate and args.family_id:
        result = aggregate_wishes(args.family_id)
    elif args.questionnaire and args.family_id:
        result = generate_questionnaire(args.family_id, args.language)
    elif args.add:
        data = json.load(sys.stdin)
        result = add_wishes(
            data.get("family_id", args.family_id),
            data.get("member_id"),
            data.get("wishes", {})
        )
    else:
        parser.print_help()
        sys.exit(1)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
