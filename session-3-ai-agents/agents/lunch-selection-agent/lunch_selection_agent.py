#!/usr/bin/env python3
"""
Lunch Selection Agent CLI

An AI agent for finding lunch restaurants, extracting menus, and recommending
dishes based on user preferences and past selections.

Usage:
  # Interactive chat mode
  python lunch_selection_agent.py --chat

  # Single query
  python lunch_selection_agent.py "Find me lunch in Helsinki"

  # With specific city
  python lunch_selection_agent.py --city Tampere "What's good for lunch today?"

  # Show help
  python lunch_selection_agent.py --help
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent_env import load_agent_environment

load_agent_environment()

from google import genai
from google.genai import types

AGENT_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_DIR / "memory"))
sys.path.insert(0, str(AGENT_DIR / "tools"))
sys.path.insert(0, str(AGENT_DIR / "subagents"))

from memory import MemoryStore

DEFAULT_MODEL = "gemini-3-flash-preview"


def load_api_key() -> str:
    """Load Gemini API key from environment."""
    api_key = (
        os.environ.get("GOOGLE_AI_STUDIO_KEY") or 
        os.environ.get("GEMINI_API_KEY") or 
        os.environ.get("GOOGLE_API_KEY")
    )
    if not api_key:
        print("Error: API key not found. Set GOOGLE_AI_STUDIO_KEY, GEMINI_API_KEY, or GOOGLE_API_KEY.")
        sys.exit(1)
    return api_key


def load_skills() -> str:
    """Load all skill files and return as context."""
    skills_dir = AGENT_DIR / "skills"
    skills_content = []
    
    if skills_dir.exists():
        for skill_file in skills_dir.glob("*.md"):
            try:
                with open(skill_file, "r") as f:
                    content = f.read()
                    skills_content.append(f"## Skill: {skill_file.stem}\n\n{content}")
            except Exception:
                pass
    
    return "\n\n---\n\n".join(skills_content) if skills_content else ""


def build_function_declarations() -> List[Dict[str, Any]]:
    """Build function declarations for the agent's tools."""
    return [
        {
            "name": "search_restaurants",
            "description": "Search for lunch restaurants in a specific city. Uses Google Search to find restaurants.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City to search in (e.g., Helsinki, Tampere, Oulu)"
                    },
                    "cuisine": {
                        "type": "string",
                        "description": "Specific cuisine type to search for (e.g., Italian, Thai, Finnish)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Custom search query"
                    }
                },
                "required": ["city"]
            }
        },
        {
            "name": "get_todays_menu",
            "description": "Extract today's lunch menu from a restaurant's website using url_context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_url": {
                        "type": "string",
                        "description": "URL of the restaurant website or menu page"
                    },
                    "restaurant_name": {
                        "type": "string",
                        "description": "Name of the restaurant"
                    },
                    "restaurant_id": {
                        "type": "string",
                        "description": "ID of the restaurant in our database (to update cached menu)"
                    }
                },
                "required": ["restaurant_url"]
            }
        },
        {
            "name": "store_restaurant",
            "description": "Save a restaurant to the local database",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Restaurant name"
                    },
                    "city": {
                        "type": "string",
                        "description": "City"
                    },
                    "address": {
                        "type": "string",
                        "description": "Street address"
                    },
                    "website": {
                        "type": "string",
                        "description": "Website URL"
                    },
                    "cuisine_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Cuisine types"
                    },
                    "price_range": {
                        "type": "string",
                        "enum": ["budget", "moderate", "expensive"],
                        "description": "Price range"
                    },
                    "restaurant_json": {
                        "type": "string",
                        "description": "Full restaurant data as JSON string"
                    }
                },
                "required": ["name", "city"]
            }
        },
        {
            "name": "retrieve_restaurants",
            "description": "Get restaurants from the local database with optional filters",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Filter by city"
                    },
                    "cuisine": {
                        "type": "string",
                        "description": "Filter by cuisine type"
                    },
                    "search_query": {
                        "type": "string",
                        "description": "Search restaurants by name or cuisine"
                    },
                    "get_stats": {
                        "type": "boolean",
                        "description": "Get statistics instead of restaurants"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return"
                    }
                },
                "required": []
            }
        },
        {
            "name": "record_selection",
            "description": "Record that the user chose a specific dish for lunch today",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_name": {
                        "type": "string",
                        "description": "Name of the restaurant"
                    },
                    "dish_name": {
                        "type": "string",
                        "description": "Name of the dish ordered"
                    },
                    "cuisine_type": {
                        "type": "string",
                        "description": "Type of cuisine"
                    },
                    "price": {
                        "type": "number",
                        "description": "Price in EUR"
                    },
                    "rating": {
                        "type": "integer",
                        "description": "User rating 1-5"
                    },
                    "would_order_again": {
                        "type": "boolean",
                        "description": "Would the user order this again?"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any notes about the meal"
                    },
                    "city": {
                        "type": "string",
                        "description": "City where lunch was had"
                    }
                },
                "required": ["restaurant_name", "dish_name"]
            }
        },
        {
            "name": "get_preferences",
            "description": "Get the user's food preferences (liked/disliked cuisines, dietary restrictions, etc.)",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "update_preferences",
            "description": "Update the user's food preferences",
            "parameters": {
                "type": "object",
                "properties": {
                    "liked_cuisines": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Cuisine types the user enjoys"
                    },
                    "disliked_cuisines": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Cuisine types to avoid"
                    },
                    "dietary_restrictions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Dietary restrictions (vegetarian, vegan, gluten-free, etc.)"
                    },
                    "allergies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Food allergies"
                    },
                    "avoided_ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific ingredients to avoid"
                    },
                    "price_preference": {
                        "type": "string",
                        "enum": ["budget", "moderate", "expensive", "any"],
                        "description": "Preferred price range"
                    },
                    "spice_tolerance": {
                        "type": "string",
                        "enum": ["none", "mild", "medium", "hot", "extra-hot"],
                        "description": "Tolerance for spicy food"
                    },
                    "variety_preference": {
                        "type": "string",
                        "enum": ["stick-to-favorites", "balanced", "adventurous"],
                        "description": "How much the user likes to try new things"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_recommendation",
            "description": "Get a personalized lunch recommendation based on preferences, past selections, and available menus",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City to get recommendation for"
                    },
                    "exclude_recent_days": {
                        "type": "integer",
                        "description": "Exclude dishes from the last N days (default: 7)"
                    }
                },
                "required": ["city"]
            }
        },
        {
            "name": "get_past_selections",
            "description": "Get the user's past lunch selections",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Get selections from last N days"
                    },
                    "min_rating": {
                        "type": "integer",
                        "description": "Minimum rating filter"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results"
                    }
                },
                "required": []
            }
        }
    ]


def log_status(message: str):
    """Log a status message to stderr for UI streaming."""
    print(message, file=sys.stderr, flush=True)


def run_subagent(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Run a subagent and return its output."""
    log_status(f"Calling subagent: {name}")
    subagent_path = AGENT_DIR / "subagents" / f"{name}.py"
    
    if not subagent_path.exists():
        return {"error": f"Subagent not found: {name}"}
    
    cmd = ["python", str(subagent_path)]
    
    if name == "restaurant_search":
        if args.get("city"):
            cmd.extend(["--city", args["city"]])
        if args.get("cuisine"):
            cmd.extend(["--cuisine", args["cuisine"]])
        if args.get("query"):
            cmd.extend(["--query", args["query"]])
        cmd.append("--pretty")
    
    elif name == "menu_extractor":
        if args.get("restaurant_url"):
            cmd.extend(["--url", args["restaurant_url"]])
        if args.get("restaurant_name"):
            cmd.extend(["--name", args["restaurant_name"]])
        cmd.append("--pretty")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(AGENT_DIR)
        )
        
        if result.returncode == 0:
            log_status(f"Subagent {name} completed successfully")
            try:
                output = json.loads(result.stdout)
                if "restaurants" in output:
                    log_status(f"Found {len(output.get('restaurants', []))} restaurants")
                elif "dishes" in output:
                    log_status(f"Found {len(output.get('dishes', []))} dishes")
                return output
            except json.JSONDecodeError:
                return {"raw_output": result.stdout}
        else:
            log_status(f"Subagent {name} failed: {result.stderr[:100] if result.stderr else 'unknown error'}")
            return {"error": result.stderr or "Subagent failed", "stdout": result.stdout}
    
    except subprocess.TimeoutExpired:
        log_status(f"Subagent {name} timed out")
        return {"error": "Subagent timed out"}
    except Exception as e:
        log_status(f"Subagent {name} error: {str(e)}")
        return {"error": str(e)}


def build_recommendation(city: str, memory: MemoryStore, exclude_days: int = 7) -> Dict[str, Any]:
    """Build a personalized lunch recommendation."""
    prefs = memory.get_preferences() or {}
    recent_dishes = memory.get_recent_dishes(days=exclude_days)
    recent_restaurants = memory.get_recent_restaurants(days=exclude_days)
    restaurants = memory.get_restaurants(city=city)
    past_selections = memory.get_selections(days=30, limit=20)
    
    if not restaurants:
        return {
            "recommendation": None,
            "message": f"No restaurants stored for {city}. Search for restaurants first.",
            "suggestion": f"Try: search for lunch restaurants in {city}"
        }
    
    scored_options = []
    
    for restaurant in restaurants:
        if restaurant.get("id") in recent_restaurants:
            continue
        
        score = 50
        
        cuisine_types = restaurant.get("cuisine_types", [])
        for cuisine in cuisine_types:
            if cuisine.lower() in [c.lower() for c in prefs.get("liked_cuisines", [])]:
                score += 20
            if cuisine.lower() in [c.lower() for c in prefs.get("disliked_cuisines", [])]:
                score -= 30
        
        price_range = restaurant.get("price_range")
        price_pref = prefs.get("price_preference", "any")
        if price_pref != "any" and price_range:
            if price_range == price_pref:
                score += 10
            elif (price_pref == "budget" and price_range == "expensive"):
                score -= 15
        
        implicit = prefs.get("implicit_preferences", {})
        rest_weights = implicit.get("restaurant_weights", {})
        if restaurant.get("id") in rest_weights:
            score += rest_weights[restaurant["id"]] * 20
        
        for cuisine in cuisine_types:
            cuisine_weights = implicit.get("cuisine_weights", {})
            if cuisine in cuisine_weights:
                score += cuisine_weights[cuisine] * 15
        
        if prefs.get("variety_preference") == "adventurous":
            for sel in past_selections:
                if sel.get("restaurant_id") == restaurant.get("id"):
                    score -= 5
        
        menu = restaurant.get("cached_menu", {})
        menu_dishes = menu.get("dishes", [])
        
        for dish in menu_dishes:
            if dish.get("name") in recent_dishes:
                continue
            
            dietary = dish.get("dietary", [])
            restrictions = prefs.get("dietary_restrictions", [])
            if restrictions:
                matches_restrictions = all(
                    any(r.lower() in d.lower() for d in dietary)
                    for r in restrictions
                )
                if not matches_restrictions:
                    continue
            
            scored_options.append({
                "restaurant": restaurant,
                "dish": dish,
                "score": score,
                "reason": "Matches your preferences"
            })
    
    if not scored_options:
        available = [r for r in restaurants if r.get("id") not in recent_restaurants]
        if available:
            top = available[0]
            return {
                "recommendation": {
                    "restaurant": top,
                    "dish": None,
                    "reason": "No specific dish recommendation, but this restaurant fits your profile"
                },
                "message": f"Consider trying {top['name']}. Fetch their menu for specific dish suggestions.",
                "alternatives": available[1:3] if len(available) > 1 else []
            }
        return {
            "recommendation": None,
            "message": "All stored restaurants were visited recently. Search for new options.",
            "recent_count": len(recent_restaurants)
        }
    
    scored_options.sort(key=lambda x: x["score"], reverse=True)
    top = scored_options[0]
    
    return {
        "recommendation": {
            "restaurant_name": top["restaurant"]["name"],
            "restaurant_id": top["restaurant"].get("id"),
            "dish_name": top["dish"]["name"] if top["dish"] else None,
            "dish_description": top["dish"].get("description") if top["dish"] else None,
            "price": top["dish"].get("price") if top["dish"] else None,
            "score": top["score"],
            "reason": top["reason"]
        },
        "alternatives": [
            {
                "restaurant_name": opt["restaurant"]["name"],
                "dish_name": opt["dish"]["name"] if opt["dish"] else None,
                "score": opt["score"]
            }
            for opt in scored_options[1:4]
        ],
        "based_on": {
            "liked_cuisines": prefs.get("liked_cuisines", []),
            "dietary_restrictions": prefs.get("dietary_restrictions", []),
            "excluded_recent_days": exclude_days
        }
    }


def execute_function(name: str, args: Dict[str, Any], memory: MemoryStore) -> Dict[str, Any]:
    """Execute a function call and return results."""
    log_status(f"Executing function: {name}")
    
    if name == "search_restaurants":
        city = args.get("city", "")
        log_status(f"Searching for restaurants in {city}...")
        return run_subagent("restaurant_search", args)
    
    elif name == "get_todays_menu":
        url = args.get("restaurant_url", "")
        restaurant_name = args.get("restaurant_name", "restaurant")
        log_status(f"Extracting menu from {restaurant_name}...")
        result = run_subagent("menu_extractor", args)
        
        restaurant_id = args.get("restaurant_id")
        if restaurant_id and "dishes" in result and not result.get("error"):
            memory.update_restaurant_menu(restaurant_id, result)
            log_status(f"Cached menu for {restaurant_name}")
        
        return result
    
    elif name == "store_restaurant":
        log_status("Saving restaurant to database...")
        if args.get("restaurant_json"):
            restaurant = json.loads(args["restaurant_json"])
        else:
            restaurant = {
                "name": args.get("name"),
                "city": args.get("city"),
                "address": args.get("address"),
                "website": args.get("website"),
                "cuisine_types": args.get("cuisine_types", []),
                "price_range": args.get("price_range")
            }
        return memory.store_restaurant(restaurant)
    
    elif name == "retrieve_restaurants":
        log_status("Querying restaurant database...")
        if args.get("get_stats"):
            return memory.get_stats()
        elif args.get("search_query"):
            return {"restaurants": memory.search_restaurants(args["search_query"], args.get("limit", 20))}
        else:
            restaurants = memory.get_restaurants(
                city=args.get("city"),
                cuisine=args.get("cuisine"),
                limit=args.get("limit", 50)
            )
            log_status(f"Found {len(restaurants)} restaurants")
            return {"count": len(restaurants), "restaurants": restaurants}
    
    elif name == "record_selection":
        log_status("Recording your lunch selection...")
        selection = {
            "restaurant_name": args.get("restaurant_name"),
            "dish_name": args.get("dish_name"),
            "cuisine_type": args.get("cuisine_type"),
            "price": args.get("price"),
            "rating": args.get("rating"),
            "would_order_again": args.get("would_order_again"),
            "notes": args.get("notes"),
            "city": args.get("city"),
            "was_recommendation": args.get("was_recommendation", False)
        }
        selection = {k: v for k, v in selection.items() if v is not None}
        return memory.store_selection(selection)
    
    elif name == "get_preferences":
        log_status("Fetching your preferences...")
        prefs = memory.get_preferences()
        return prefs if prefs else {"message": "No preferences set yet. Tell me your food preferences!"}
    
    elif name == "update_preferences":
        log_status("Updating your preferences...")
        current = memory.get_preferences() or {"user_id": "default"}
        
        for key in ["liked_cuisines", "disliked_cuisines", "dietary_restrictions", 
                    "allergies", "avoided_ingredients", "price_preference", 
                    "spice_tolerance", "variety_preference"]:
            if args.get(key) is not None:
                current[key] = args[key]
        
        if memory.set_preferences(current):
            return {"status": "success", "message": "Preferences updated", "preferences": current}
        return {"error": "Failed to update preferences"}
    
    elif name == "get_recommendation":
        city = args.get("city", "")
        exclude_days = args.get("exclude_recent_days", 7)
        log_status(f"Building recommendation for {city}...")
        return build_recommendation(city, memory, exclude_days)
    
    elif name == "get_past_selections":
        log_status("Fetching your past selections...")
        selections = memory.get_selections(
            days=args.get("days"),
            min_rating=args.get("min_rating"),
            limit=args.get("limit", 20)
        )
        return {"count": len(selections), "selections": selections}
    
    else:
        return {"error": f"Unknown function: {name}"}


def find_function_calls(response) -> List[Tuple[str, Dict[str, Any]]]:
    """Extract function calls from response."""
    calls = []
    try:
        parts = response.candidates[0].content.parts if response.candidates else []
        for part in parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                name = fc.name
                args = dict(fc.args) if fc.args else {}
                calls.append((name, args))
    except Exception:
        pass
    return calls


def make_function_response(name: str, result: Dict[str, Any]) -> types.Part:
    """Create a function response part."""
    return types.Part(
        function_response=types.FunctionResponse(
            name=name,
            response=result
        )
    )


def build_system_prompt(prefs: Optional[Dict] = None) -> str:
    """Build the system prompt with skills and context."""
    skills = load_skills()
    
    prefs_context = ""
    if prefs:
        prefs_context = f"""
## User Preferences
```json
{json.dumps(prefs, indent=2)}
```
"""
    
    today = datetime.now()
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    return f"""You are a Lunch Selection Agent. Your job is to help users find great lunch options.

## Today's Date
{weekdays[today.weekday()]}, {today.strftime('%Y-%m-%d')}

## Your Capabilities

1. **Search Restaurants**: Find lunch restaurants in any city using Google Search
2. **Extract Menus**: Get today's lunch menu from restaurant websites
3. **Store & Retrieve**: Save restaurants to the local database for quick access
4. **Track Selections**: Remember what the user has eaten to suggest variety
5. **Manage Preferences**: Learn what the user likes and dislikes
6. **Recommend**: Suggest new dishes based on preferences and past choices

## How to Work

1. **Listen to the User**: They'll tell you a city and what they're looking for
2. **Search First**: Find restaurants in the specified city
3. **Store Restaurants**: Save found restaurants for future use
4. **Extract Menus**: Get today's lunch options from their websites
5. **Make Recommendations**: Based on:
   - User's dietary restrictions (ALWAYS respect these)
   - Liked/disliked cuisines
   - Past selections (suggest variety)
   - Price preferences
   - Implicit preferences learned from ratings

## Key Behaviors

- **Proactive**: When user asks for lunch, search, extract menus, and recommend
- **Remember Preferences**: If user mentions "I'm vegetarian" - update preferences
- **Track History**: When user says "I'll have X at Y" - record the selection
- **Suggest Variety**: Avoid recommending the same dish twice in a week
- **Respect Restrictions**: Never suggest dishes violating dietary restrictions

## Workflow for "Find me lunch in [City]"

1. Check if we have restaurants stored for that city
2. If not, search for restaurants
3. Store found restaurants
4. Get menus for top restaurants
5. Apply user preferences to filter options
6. Recommend the best match
{prefs_context}
## Skills Reference

{skills}

## Response Style

- Be helpful and enthusiastic about food
- Present options clearly (bullet points, tables)
- Explain WHY you're recommending something
- Ask for feedback ("How was it? Rate 1-5?")
- Remember to update preferences when user shares them"""


def print_response(response) -> str:
    """Print and return model response text."""
    text_parts = []
    try:
        parts = response.candidates[0].content.parts if response.candidates else []
        for part in parts:
            if hasattr(part, "text") and part.text:
                text_parts.append(part.text)
    except Exception:
        pass
    
    text = "\n".join(text_parts)
    if text:
        print(text)
    return text


async def run_chat_loop(client: genai.Client, model: str, memory: MemoryStore, default_city: Optional[str] = None):
    """Run interactive chat loop."""
    print("Lunch Selection Agent - Interactive Mode")
    print("=" * 45)
    print("Commands: 'exit' to quit, 'help' for commands")
    print()
    
    prefs = memory.get_preferences()
    
    if prefs and prefs.get("liked_cuisines"):
        print(f"Welcome back! Your favorite cuisines: {', '.join(prefs.get('liked_cuisines', []))}")
    else:
        print("Welcome! Tell me about your food preferences to get started.")
    
    if default_city:
        print(f"Default city: {default_city}")
    print()
    
    function_declarations = build_function_declarations()
    tools = [types.Tool(function_declarations=function_declarations)]
    
    system_prompt = build_system_prompt(prefs)
    history: List[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=system_prompt)]),
        types.Content(role="model", parts=[types.Part(text="I'm ready to help you find a great lunch! What city are you in today?")])
    ]
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEnjoy your lunch!")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in {"exit", "quit", ":q", "/exit"}:
            print("Enjoy your lunch!")
            break
        
        if user_input.lower() == "help":
            print("""
Available commands:
  find lunch in <city>    - Search for lunch options
  menu <restaurant>       - Get today's menu
  I ate <dish> at <rest>  - Record your selection
  rate <1-5>             - Rate your last meal
  preferences            - Show your preferences
  history                - Show recent selections
  recommend              - Get a recommendation
  exit                   - Quit
            """)
            continue
        
        history.append(types.Content(role="user", parts=[types.Part(text=user_input)]))
        
        config = types.GenerateContentConfig(tools=tools)
        
        response = await client.aio.models.generate_content(
            model=model,
            contents=history,
            config=config
        )
        
        for _ in range(5):
            function_calls = find_function_calls(response)
            
            if not function_calls:
                break
            
            if response.candidates and response.candidates[0].content:
                history.append(response.candidates[0].content)
            
            function_responses = []
            for func_name, func_args in function_calls:
                print(f"\n[Executing: {func_name}]")
                result = execute_function(func_name, func_args, memory)
                
                if "restaurants" in result:
                    print(f"[Found {len(result.get('restaurants', []))} restaurants]")
                elif "dishes" in result:
                    print(f"[Found {len(result.get('dishes', []))} dishes]")
                elif "recommendation" in result:
                    rec = result.get("recommendation")
                    if rec:
                        print(f"[Recommendation: {rec.get('dish_name', rec.get('restaurant_name', 'See below'))}]")
                elif "error" in result:
                    print(f"[Error: {result['error']}]")
                
                function_responses.append(make_function_response(func_name, result))
            
            history.append(types.Content(
                role="user",
                parts=function_responses
            ))
            
            response = await client.aio.models.generate_content(
                model=model,
                contents=history,
                config=config
            )
        
        print("\nAgent:", end=" ")
        print_response(response)
        
        if response.candidates and response.candidates[0].content:
            history.append(response.candidates[0].content)


def run_single_query(client: genai.Client, model: str, query: str, memory: MemoryStore, city: Optional[str] = None):
    """Run a single query."""
    log_status(f"Processing query: {query[:50]}...")
    
    function_declarations = build_function_declarations()
    tools = [types.Tool(function_declarations=function_declarations)]
    
    prefs = memory.get_preferences()
    if prefs:
        log_status("Loaded user preferences")
    
    if city:
        query = f"[City: {city}] {query}"
    
    system_prompt = build_system_prompt(prefs)
    contents = [
        types.Content(role="user", parts=[types.Part(text=system_prompt)]),
        types.Content(role="model", parts=[types.Part(text="Ready to help with lunch.")]),
        types.Content(role="user", parts=[types.Part(text=query)])
    ]
    
    config = types.GenerateContentConfig(tools=tools)
    
    log_status("Sending request to Gemini API...")
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    log_status("Received initial response")
    
    for iteration in range(5):
        function_calls = find_function_calls(response)
        
        if not function_calls:
            break
        
        log_status(f"Processing function calls (iteration {iteration + 1})...")
        
        if response.candidates and response.candidates[0].content:
            contents.append(response.candidates[0].content)
        
        function_responses = []
        for func_name, func_args in function_calls:
            result = execute_function(func_name, func_args, memory)
            function_responses.append(make_function_response(func_name, result))
        
        contents.append(types.Content(
            role="user",
            parts=function_responses
        ))
        
        log_status("Continuing conversation...")
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
    
    log_status("Generating final response...")
    print_response(response)


def main():
    parser = argparse.ArgumentParser(
        description="Lunch Selection Agent - Find the perfect lunch",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        help="Query to process (if not using --chat)"
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Start interactive chat mode"
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Gemini model to use (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--city", "-c",
        help="Default city for lunch search"
    )
    
    args = parser.parse_args()
    
    if not args.chat and not args.query:
        parser.print_help()
        sys.exit(1)
    
    api_key = load_api_key()
    client = genai.Client(api_key=api_key)
    memory = MemoryStore()
    
    if args.chat:
        asyncio.run(run_chat_loop(client, args.model, memory, args.city))
    else:
        run_single_query(client, args.model, args.query, memory, args.city)


if __name__ == "__main__":
    main()
