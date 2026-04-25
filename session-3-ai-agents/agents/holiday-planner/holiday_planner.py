#!/usr/bin/env python3
"""
Holiday Planner Agent

AI agent for family holiday planning. Understands whole family wishes,
recommends destinations, and compares options.

Usage:
    python holiday_planner.py --chat                    # Interactive chat
    python holiday_planner.py "Find beach holiday for family with kids"
    python holiday_planner.py --family create "The Smiths"
    python holiday_planner.py --family-id fam001 --plan
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from agent_env import load_agent_environment
load_agent_environment()

from google import genai
from google.genai import types

from memory.memory import (
    get_family, list_families, create_family, add_family_member,
    update_family, get_trip, list_trips, create_trip, update_trip,
    get_stats, init_database
)

DEFAULT_MODEL = "gemini-3-flash-preview"
AGENT_DIR = Path(__file__).parent


def get_client() -> genai.Client:
    """Get Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_AI_STUDIO_KEY required")
    return genai.Client(api_key=api_key)


def detect_language(text: str) -> str:
    """Detect if text is Finnish or English."""
    finnish_indicators = [
        'missä', 'mitä', 'milloin', 'paljonko', 'mikä', 'miten',
        'loma', 'perhe', 'lapset', 'matka', 'kohde', 'ranta',
        'etsi', 'suosittele', 'vertaa', 'haluamme', 'meidän'
    ]
    text_lower = text.lower()
    finnish_count = sum(1 for word in finnish_indicators if word in text_lower)
    return "fi" if finnish_count >= 2 else "en"


def build_function_declarations() -> list:
    """Build function declarations for Gemini."""
    return [
        types.FunctionDeclaration(
            name="create_family_profile",
            description="Create a new family profile to store preferences and plan trips",
            parameters={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Family name (e.g., 'The Smiths', 'Virtanen Family')"
                    },
                    "members": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "role": {"type": "string", "enum": ["adult", "teen", "child", "toddler", "infant", "senior"]},
                                "age": {"type": "integer"}
                            }
                        },
                        "description": "Family members with names, roles, and ages"
                    }
                },
                "required": ["name"]
            }
        ),
        types.FunctionDeclaration(
            name="add_family_member",
            description="Add a new member to an existing family profile",
            parameters={
                "type": "object",
                "properties": {
                    "family_id": {"type": "string", "description": "Family ID"},
                    "name": {"type": "string", "description": "Member name"},
                    "role": {"type": "string", "enum": ["adult", "teen", "child", "toddler", "infant", "senior"]},
                    "age": {"type": "integer", "description": "Member age"}
                },
                "required": ["family_id", "name", "role"]
            }
        ),
        types.FunctionDeclaration(
            name="update_member_preferences",
            description="Update preferences for a family member (activities, must-haves, deal-breakers)",
            parameters={
                "type": "object",
                "properties": {
                    "family_id": {"type": "string"},
                    "member_name": {"type": "string", "description": "Member name to update"},
                    "activity_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Preferred activities (beach, hiking, culture, adventure, etc.)"
                    },
                    "must_haves": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Must-have features for holidays"
                    },
                    "deal_breakers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Things to avoid"
                    },
                    "climate_preference": {
                        "type": "string",
                        "enum": ["hot", "warm", "mild", "cool", "any"]
                    }
                },
                "required": ["family_id", "member_name"]
            }
        ),
        types.FunctionDeclaration(
            name="set_family_constraints",
            description="Set budget, duration, and travel constraints for the family",
            parameters={
                "type": "object",
                "properties": {
                    "family_id": {"type": "string"},
                    "budget_max": {"type": "number", "description": "Maximum budget in EUR"},
                    "preferred_duration_days": {"type": "integer"},
                    "departure_location": {"type": "string"},
                    "max_flight_hours": {"type": "number"},
                    "preferred_months": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Preferred travel months (1-12)"
                    }
                },
                "required": ["family_id"]
            }
        ),
        types.FunctionDeclaration(
            name="get_family_profile",
            description="Get details of a family profile including all members and preferences",
            parameters={
                "type": "object",
                "properties": {
                    "family_id": {"type": "string", "description": "Family ID"}
                },
                "required": ["family_id"]
            }
        ),
        types.FunctionDeclaration(
            name="list_families",
            description="List all family profiles",
            parameters={"type": "object", "properties": {}}
        ),
        types.FunctionDeclaration(
            name="collect_wishes",
            description="Start a wish collection session for family members to express their holiday preferences",
            parameters={
                "type": "object",
                "properties": {
                    "family_id": {"type": "string"},
                    "member_id": {"type": "string", "description": "Specific member to collect from (optional)"}
                },
                "required": ["family_id"]
            }
        ),
        types.FunctionDeclaration(
            name="aggregate_family_wishes",
            description="Analyze and aggregate all family wishes to find common ground and conflicts",
            parameters={
                "type": "object",
                "properties": {
                    "family_id": {"type": "string"}
                },
                "required": ["family_id"]
            }
        ),
        types.FunctionDeclaration(
            name="search_destinations",
            description="Search for holiday destinations matching the family's wishes and constraints",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search (e.g., 'beach family holiday europe')"
                    },
                    "family_id": {
                        "type": "string",
                        "description": "Use family profile for personalized results"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of destinations to return (default 5)"
                    }
                }
            }
        ),
        types.FunctionDeclaration(
            name="get_destination_details",
            description="Get detailed information about a specific destination",
            parameters={
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "Destination name"},
                    "country": {"type": "string", "description": "Country (optional)"}
                },
                "required": ["destination"]
            }
        ),
        types.FunctionDeclaration(
            name="find_activities",
            description="Find activities at a destination suitable for the family",
            parameters={
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "country": {"type": "string"},
                    "family_id": {"type": "string"},
                    "activity_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types of activities to find"
                    }
                },
                "required": ["destination"]
            }
        ),
        types.FunctionDeclaration(
            name="get_weather_info",
            description="Get weather information and best travel times for a destination",
            parameters={
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "month": {"type": "integer", "description": "Month to check (1-12)"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"}
                },
                "required": ["destination"]
            }
        ),
        types.FunctionDeclaration(
            name="compare_weather",
            description="Compare weather across multiple destinations to find best timing",
            parameters={
                "type": "object",
                "properties": {
                    "destinations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Destinations to compare"
                    },
                    "family_id": {"type": "string"}
                },
                "required": ["destinations"]
            }
        ),
        types.FunctionDeclaration(
            name="estimate_budget",
            description="Estimate budget for a holiday including flights, accommodation, activities",
            parameters={
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "duration_days": {"type": "integer"},
                    "adults": {"type": "integer"},
                    "children": {"type": "integer"},
                    "travel_style": {
                        "type": "string",
                        "enum": ["budget", "mid-range", "comfort", "luxury"]
                    },
                    "departure_city": {"type": "string"},
                    "month": {"type": "integer"}
                },
                "required": ["destination"]
            }
        ),
        types.FunctionDeclaration(
            name="compare_budgets",
            description="Compare budgets across multiple destinations",
            parameters={
                "type": "object",
                "properties": {
                    "destinations": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "duration_days": {"type": "integer"},
                    "family_id": {"type": "string"}
                },
                "required": ["destinations"]
            }
        ),
        types.FunctionDeclaration(
            name="create_trip_plan",
            description="Create a new trip plan for a family",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Trip name (e.g., 'Summer 2025 Greece')"},
                    "family_id": {"type": "string"},
                    "destinations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "country": {"type": "string"},
                                "duration_days": {"type": "integer"}
                            }
                        }
                    }
                },
                "required": ["name"]
            }
        ),
        types.FunctionDeclaration(
            name="create_itinerary",
            description="Create a detailed day-by-day itinerary for a trip",
            parameters={
                "type": "object",
                "properties": {
                    "trip_id": {"type": "string", "description": "Trip ID to create itinerary for"},
                    "destination": {"type": "string", "description": "Or specify destination directly"},
                    "duration_days": {"type": "integer"},
                    "family_id": {"type": "string"},
                    "pace": {
                        "type": "string",
                        "enum": ["relaxed", "balanced", "active", "adventure"]
                    },
                    "priorities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Priority activities to include"
                    }
                }
            }
        ),
        types.FunctionDeclaration(
            name="compare_options",
            description="Compare multiple holiday options side-by-side with family fit analysis",
            parameters={
                "type": "object",
                "properties": {
                    "trip_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Trip IDs to compare"
                    },
                    "destinations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Or compare destinations directly"
                    },
                    "family_id": {"type": "string"},
                    "aspects": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Aspects to compare (budget, activities, weather, family_fit)"
                    }
                }
            }
        ),
        types.FunctionDeclaration(
            name="get_trip",
            description="Get details of a saved trip plan",
            parameters={
                "type": "object",
                "properties": {
                    "trip_id": {"type": "string"}
                },
                "required": ["trip_id"]
            }
        ),
        types.FunctionDeclaration(
            name="list_trips",
            description="List all trip plans, optionally filtered by family",
            parameters={
                "type": "object",
                "properties": {
                    "family_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["planning", "comparing", "booked", "completed"]}
                }
            }
        ),
        types.FunctionDeclaration(
            name="get_stats",
            description="Get statistics about families and trips",
            parameters={"type": "object", "properties": {}}
        )
    ]


def execute_function(name: str, args: dict) -> dict:
    """Execute a function call."""
    try:
        if name == "create_family_profile":
            result = create_family(args.get("name"), args.get("members"))
            return {"status": "created", **result}
        
        elif name == "add_family_member":
            from memory.memory import add_family_member as add_member
            result = add_member(
                args.get("family_id"),
                {
                    "name": args.get("name"),
                    "role": args.get("role"),
                    "age": args.get("age")
                }
            )
            return result
        
        elif name == "update_member_preferences":
            from memory.memory import update_member_preferences as update_prefs
            
            family = get_family(args.get("family_id"))
            if not family:
                return {"error": f"Family not found: {args.get('family_id')}"}
            
            member_name = args.get("member_name")
            member_id = None
            for m in family.get("members", []):
                if m.get("name", "").lower() == member_name.lower():
                    member_id = m.get("id")
                    break
            
            if not member_id:
                return {"error": f"Member not found: {member_name}"}
            
            prefs = {}
            if args.get("activity_types"):
                prefs["activity_types"] = args["activity_types"]
            if args.get("must_haves"):
                prefs["must_haves"] = args["must_haves"]
            if args.get("deal_breakers"):
                prefs["deal_breakers"] = args["deal_breakers"]
            if args.get("climate_preference"):
                prefs["climate_preference"] = args["climate_preference"]
            
            return update_prefs(args.get("family_id"), member_id, prefs)
        
        elif name == "set_family_constraints":
            constraints = {}
            if args.get("budget_max"):
                constraints["budget"] = {"max": args["budget_max"], "currency": "EUR"}
            if args.get("preferred_duration_days"):
                constraints["duration"] = {"preferred_days": args["preferred_duration_days"]}
            if args.get("departure_location"):
                constraints["departure_location"] = args["departure_location"]
            if args.get("max_flight_hours"):
                constraints["max_flight_hours"] = args["max_flight_hours"]
            if args.get("preferred_months"):
                constraints["travel_dates"] = {"preferred_months": args["preferred_months"]}
            
            return update_family(args.get("family_id"), {"constraints": constraints})
        
        elif name == "get_family_profile":
            family = get_family(args.get("family_id"))
            if family:
                return family
            return {"error": f"Family not found: {args.get('family_id')}"}
        
        elif name == "list_families":
            return {"families": list_families()}
        
        elif name == "collect_wishes":
            from subagents.wish_aggregator import generate_questionnaire
            return generate_questionnaire(args.get("family_id"))
        
        elif name == "aggregate_family_wishes":
            result = subprocess.run(
                [sys.executable, str(AGENT_DIR / "subagents" / "wish_aggregator.py"),
                 "--family-id", args.get("family_id"), "--aggregate"],
                capture_output=True, text=True, cwd=str(AGENT_DIR)
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            return {"error": result.stderr[:500]}
        
        elif name == "search_destinations":
            from tools.search_destinations import search_destinations as search
            family = get_family(args.get("family_id")) if args.get("family_id") else None
            return search(
                args.get("query"),
                family_profile=family,
                num_results=args.get("num_results", 5)
            )
        
        elif name == "get_destination_details":
            from tools.search_destinations import get_destination_details as get_details
            return get_details(args.get("destination"), args.get("country"))
        
        elif name == "find_activities":
            from tools.find_activities import find_activities as find_acts
            family = get_family(args.get("family_id")) if args.get("family_id") else None
            return find_acts(
                args.get("destination"),
                args.get("country"),
                args.get("activity_types"),
                family
            )
        
        elif name == "get_weather_info":
            from tools.weather_info import get_weather_info as get_weather
            return get_weather(
                args.get("destination"),
                month=args.get("month"),
                start_date=args.get("start_date"),
                end_date=args.get("end_date")
            )
        
        elif name == "compare_weather":
            from tools.weather_info import get_best_time_to_visit
            family = get_family(args.get("family_id")) if args.get("family_id") else None
            return get_best_time_to_visit(args.get("destinations"), family)
        
        elif name == "estimate_budget":
            from tools.budget_calculator import estimate_budget as calc_budget
            
            family_id = args.get("family_id")
            adults = args.get("adults", 2)
            children = args.get("children", 0)
            
            if family_id:
                family = get_family(family_id)
                if family:
                    adults = sum(1 for m in family.get("members", []) if m.get("role") in ["adult", "senior"])
                    children = sum(1 for m in family.get("members", []) if m.get("role") in ["child", "toddler", "infant"])
            
            return calc_budget(
                args.get("destination"),
                duration_days=args.get("duration_days", 7),
                adults=adults,
                children=children,
                travel_style=args.get("travel_style", "mid-range"),
                departure_city=args.get("departure_city", "Helsinki"),
                month=args.get("month")
            )
        
        elif name == "compare_budgets":
            from tools.budget_calculator import compare_budgets as comp_budgets
            
            family_id = args.get("family_id")
            adults = 2
            children = 0
            
            if family_id:
                family = get_family(family_id)
                if family:
                    adults = sum(1 for m in family.get("members", []) if m.get("role") in ["adult", "senior"])
                    children = sum(1 for m in family.get("members", []) if m.get("role") in ["child", "toddler", "infant"])
            
            return comp_budgets(
                args.get("destinations"),
                args.get("duration_days", 7),
                adults,
                children
            )
        
        elif name == "create_trip_plan":
            return create_trip(
                args.get("name"),
                args.get("family_id"),
                args.get("destinations")
            )
        
        elif name == "create_itinerary":
            from subagents.itinerary_planner import create_itinerary as create_itin
            
            family = get_family(args.get("family_id")) if args.get("family_id") else None
            
            destinations = []
            if args.get("trip_id"):
                trip = get_trip(args.get("trip_id"))
                if trip:
                    destinations = trip.get("destinations", [])
            elif args.get("destination"):
                destinations = [{"name": args["destination"], "duration_days": args.get("duration_days", 7)}]
            
            result = create_itin(
                destinations,
                args.get("duration_days", 7),
                family,
                pace=args.get("pace", "balanced"),
                priorities=args.get("priorities")
            )
            
            if args.get("trip_id") and "error" not in result:
                update_trip(args.get("trip_id"), {"itinerary": result})
            
            return result
        
        elif name == "compare_options":
            from tools.compare_options import compare_trips
            
            trips = []
            
            if args.get("trip_ids"):
                for tid in args.get("trip_ids"):
                    trip = get_trip(tid)
                    if trip:
                        trips.append(trip)
            
            if args.get("destinations"):
                from tools.search_destinations import get_destination_details
                for dest in args.get("destinations"):
                    details = get_destination_details(dest)
                    trips.append({
                        "name": dest,
                        "destinations": [details] if details else [{"name": dest}],
                        "budget": details.get("budget_estimate", {}) if details else {}
                    })
            
            family = get_family(args.get("family_id")) if args.get("family_id") else None
            
            return compare_trips(trips, family, args.get("aspects"))
        
        elif name == "get_trip":
            trip = get_trip(args.get("trip_id"))
            if trip:
                return trip
            return {"error": f"Trip not found: {args.get('trip_id')}"}
        
        elif name == "list_trips":
            return {"trips": list_trips(args.get("family_id"), args.get("status"))}
        
        elif name == "get_stats":
            return get_stats()
        
        else:
            return {"error": f"Unknown function: {name}"}
    
    except Exception as e:
        return {"error": str(e)}


def build_system_prompt(language: str, family_context: dict = None) -> str:
    """Build system prompt based on language and context."""
    stats = get_stats()
    
    family_info = ""
    if family_context:
        members = [f"{m.get('name', m.get('role'))}" for m in family_context.get("members", [])]
        family_info = f"\nCurrent family: {family_context.get('name')} ({', '.join(members)})"
    
    if language == "fi":
        return f"""Olet perheen lomasuunnittelija-agentti. Autat perheitä löytämään täydellisen lomakohteen, joka miellyttää kaikkia perheenjäseniä.

Tehtäväsi:
1. Kerätä toiveet kaikilta perheenjäseniltä
2. Analysoida ja yhdistää toiveet löytääksesi yhteisen maaperän
3. Suositella sopivia lomakohteita
4. Vertailla eri vaihtoehtoja puolueettomasti
5. Luoda yksityiskohtaisia matkaohjelmia

Tietokannassa on {stats.get('total_families', 0)} perhettä ja {stats.get('total_trips', 0)} matkaa.
{family_info}

Kysy tarkentavia kysymyksiä varmistaaksesi, että ymmärrät koko perheen tarpeet.
Huomioi ikäryhmät (vauvat, lapset, teinit, aikuiset, seniorit) suosituksissasi.
Anna aina konkreettisia ehdotuksia perusteluineen."""
    
    else:
        return f"""You are a family holiday planning agent. You help families find the perfect holiday destination that makes everyone happy.

Your tasks:
1. Collect wishes from all family members
2. Analyze and aggregate wishes to find common ground
3. Recommend suitable destinations
4. Compare options objectively
5. Create detailed itineraries

Database has {stats.get('total_families', 0)} families and {stats.get('total_trips', 0)} trips.
{family_info}

Ask clarifying questions to ensure you understand the whole family's needs.
Consider all age groups (infants, children, teens, adults, seniors) in your recommendations.
Always provide concrete suggestions with reasoning."""


def process_query(
    query: str,
    client: genai.Client,
    family_id: str = None,
    history: list = None,
    log_callback=None
) -> tuple[str, list]:
    """Process a user query and return response with updated history."""
    def log(msg):
        print(f"[Holiday-Planner] {msg}", file=sys.stderr)
        if log_callback:
            log_callback(msg)
    
    log(f"Query: {query[:100]}..." if len(query) > 100 else f"Query: {query}")
    
    language = detect_language(query)
    log(f"Language: {language}")
    
    family_context = None
    if family_id:
        family_context = get_family(family_id)
        log(f"Family context loaded: {family_id}")
    
    tools = [types.Tool(
        function_declarations=build_function_declarations(),
        google_search=types.GoogleSearch()
    )]
    
    config = types.GenerateContentConfig(
        system_instruction=build_system_prompt(language, family_context),
        tools=tools,
        temperature=0.4
    )
    
    contents = []
    
    if history:
        log(f"Loading {len(history)} messages from history")
        for msg in history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                contents.append(types.Content(role="user", parts=[types.Part(text=content)]))
            elif role == 'assistant':
                contents.append(types.Content(role="model", parts=[types.Part(text=content)]))
    
    contents.append(types.Content(role="user", parts=[types.Part(text=query)]))
    
    max_iterations = 15
    log(f"Starting processing (max {max_iterations} iterations)")
    
    for iteration in range(max_iterations):
        log(f"--- Iteration {iteration + 1}/{max_iterations} ---")
        
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=contents,
            config=config
        )
        
        if not response.candidates:
            log("ERROR: No response candidates")
            return "No response generated.", []
        
        candidate = response.candidates[0]
        
        function_calls = []
        text_parts = []
        
        for part in candidate.content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                function_calls.append(part.function_call)
            elif hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        
        if text_parts:
            preview = text_parts[0][:100] + "..." if len(text_parts[0]) > 100 else text_parts[0]
            log(f"Text: {preview}")
        
        if not function_calls:
            log("DONE: No more function calls")
            final_text = " ".join(text_parts).strip()
            return final_text if final_text else "I couldn't generate a response.", []
        
        log(f"Function calls: {len(function_calls)}")
        contents.append(candidate.content)
        
        import concurrent.futures
        
        def execute_and_log(fc):
            args = dict(fc.args) if fc.args else {}
            args_preview = str(args)[:80] + "..." if len(str(args)) > 80 else str(args)
            log(f"  [START] {fc.name}({args_preview})")
            
            result = execute_function(fc.name, args)
            
            if isinstance(result, dict) and "error" in result:
                log(f"  [DONE] {fc.name} -> ERROR: {result['error'][:80]}")
            else:
                log(f"  [DONE] {fc.name} -> OK")
            
            return (fc.name, result)
        
        function_response_parts = []
        if len(function_calls) > 1:
            log(f"  Running {len(function_calls)} calls in PARALLEL...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(function_calls), 10)) as executor:
                futures = {executor.submit(execute_and_log, fc): fc for fc in function_calls}
                results_map = {}
                for future in concurrent.futures.as_completed(futures):
                    fc = futures[future]
                    name, result = future.result()
                    results_map[id(fc)] = result
                
                for fc in function_calls:
                    result = results_map[id(fc)]
                    function_response_parts.append(
                        types.Part.from_function_response(name=fc.name, response=result)
                    )
        else:
            for fc in function_calls:
                name, result = execute_and_log(fc)
                function_response_parts.append(
                    types.Part.from_function_response(name=fc.name, response=result)
                )
        
        contents.append(types.Content(role="user", parts=function_response_parts))
    
    log(f"ERROR: Maximum iterations ({max_iterations}) reached!")
    
    if text_parts:
        return " ".join(text_parts).strip(), []
    
    return "Maximum iterations reached. Please try a simpler query.", []


def chat_mode(client: genai.Client, family_id: str = None):
    """Interactive chat mode."""
    print("\n" + "="*60)
    print("Holiday Planner - Family Travel Assistant")
    print("="*60)
    print("I help families plan the perfect holiday for everyone!")
    print("Type 'exit' to end.\n")
    
    if family_id:
        family = get_family(family_id)
        if family:
            print(f"Loaded family: {family.get('name')}")
            members = [m.get('name', m.get('role')) for m in family.get('members', [])]
            print(f"Members: {', '.join(members)}\n")
    
    history = []
    
    while True:
        try:
            query = input("You: ").strip()
            if not query:
                continue
            if query.lower() in ['exit', 'quit', 'q']:
                print("Happy travels!")
                break
            
            response, history = process_query(query, client, family_id, history)
            print(f"\nAgent: {response}\n")
            
        except KeyboardInterrupt:
            print("\nHappy travels!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    parser = argparse.ArgumentParser(description="Holiday Planner Agent - Family Travel Assistant")
    parser.add_argument("query", nargs="?", help="Query to process")
    parser.add_argument("--chat", action="store_true", help="Interactive chat mode")
    parser.add_argument("--family-id", "-f", help="Use specific family profile")
    parser.add_argument("--family", nargs="+", help="Family operations: create <name> | list | get <id>")
    parser.add_argument("--trip", nargs="+", help="Trip operations: create <name> | list | get <id>")
    parser.add_argument("--plan", action="store_true", help="Start planning with family profile")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    try:
        init_database()
    except:
        pass
    
    if args.chat:
        client = get_client()
        chat_mode(client, args.family_id)
    
    elif args.family:
        action = args.family[0]
        if action == "create" and len(args.family) > 1:
            result = create_family(args.family[1])
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif action == "list":
            result = list_families()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif action == "get" and len(args.family) > 1:
            result = get_family(args.family[1])
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Usage: --family create <name> | list | get <id>")
    
    elif args.trip:
        action = args.trip[0]
        if action == "create" and len(args.trip) > 1:
            result = create_trip(args.trip[1], args.family_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif action == "list":
            result = list_trips(args.family_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif action == "get" and len(args.trip) > 1:
            result = get_trip(args.trip[1])
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Usage: --trip create <name> | list | get <id>")
    
    elif args.plan and args.family_id:
        client = get_client()
        print("Starting holiday planning session...")
        chat_mode(client, args.family_id)
    
    elif args.stats:
        stats = get_stats()
        print(json.dumps(stats, indent=2))
    
    elif args.query:
        client = get_client()
        response, _ = process_query(args.query, client, args.family_id)
        print(response)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
