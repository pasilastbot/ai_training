#!/usr/bin/env python3
"""
Weather Forecast Agent CLI

An AI agent that provides weather forecasts, alerts, and location-based weather recommendations.

Usage:
  python weather_forecast_agent.py --chat           # Interactive mode
  python weather_forecast_agent.py "your query"     # Single query
  python weather_forecast_agent.py --help           # Show help
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
            "name": "get_weather",
            "description": "Get current weather conditions for a location using Google Search or weather APIs",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or coordinates (e.g., 'Helsinki', 'New York', '60.1695,24.9354')"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial"],
                        "description": "Temperature units (metric=Celsius, imperial=Fahrenheit)"
                    }
                },
                "required": ["location"]
            }
        },
        {
            "name": "get_forecast",
            "description": "Get multi-day weather forecast for a location using Google Search",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or coordinates"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to forecast (1-7)",
                        "minimum": 1,
                        "maximum": 7
                    },
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial"],
                        "description": "Temperature units"
                    }
                },
                "required": ["location"]
            }
        },
        {
            "name": "store_location",
            "description": "Save a favorite location for quick access to weather information",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Location nickname (e.g., 'Home', 'Work', 'Cabin')"
                    },
                    "location": {
                        "type": "string",
                        "description": "City name or coordinates"
                    }
                },
                "required": ["name", "location"]
            }
        },
        {
            "name": "retrieve_locations",
            "description": "Get saved favorite locations",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "delete_location",
            "description": "Remove a saved location by name",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Location name to remove"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_activity_recommendations",
            "description": "Get outdoor activity recommendations based on current weather conditions",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["location"]
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
    
    if name == "weather_search":
        if args.get("location"):
            cmd.extend(["--location", args["location"]])
        if args.get("units"):
            cmd.extend(["--units", args["units"]])
        if args.get("days"):
            cmd.extend(["--days", str(args["days"])])
        cmd.append("--pretty")
    
    elif name == "alert_checker":
        if args.get("location"):
            cmd.extend(["--location", args["location"]])
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
                if "weather" in output:
                    log_status(f"Retrieved weather for {args.get('location', 'location')}")
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


def execute_function(name: str, args: Dict[str, Any], memory: MemoryStore) -> Dict[str, Any]:
    """Execute a function call and return results."""
    log_status(f"Executing function: {name}")
    
    if name == "get_weather":
        location = args.get("location", "")
        log_status(f"Getting current weather for {location}...")
        result = run_subagent("weather_search", {
            "location": location,
            "units": args.get("units", "metric")
        })
        
        if not result.get("error"):
            memory.cache_weather(location, result.get("weather", {}))
        
        return result
    
    elif name == "get_forecast":
        location = args.get("location", "")
        days = args.get("days", 5)
        log_status(f"Getting {days}-day forecast for {location}...")
        result = run_subagent("weather_search", {
            "location": location,
            "days": days,
            "units": args.get("units", "metric")
        })
        return result
    
    elif name == "store_location":
        log_status("Saving location...")
        return memory.store_location(
            name=args.get("name"),
            location=args.get("location")
        )
    
    elif name == "retrieve_locations":
        log_status("Fetching saved locations...")
        locations = memory.get_locations()
        return {"locations": locations, "count": len(locations)}
    
    elif name == "delete_location":
        log_status(f"Removing location: {args.get('name')}")
        return memory.delete_location(args.get("name"))
    
    elif name == "get_activity_recommendations":
        location = args.get("location", "")
        log_status(f"Getting activity recommendations for {location}...")
        
        weather_result = run_subagent("weather_search", {"location": location, "units": "metric"})
        weather = weather_result.get("weather", {})
        
        if not weather or weather.get("error"):
            return weather_result
        
        alert_result = run_subagent("alert_checker", {"location": location})
        alerts = alert_result.get("alerts", [])
        
        from google import genai
        from google.genai import types
        
        api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return {"error": "No API key"}
        
        client = genai.Client(api_key=api_key)
        
        weather_context = json.dumps(weather, indent=2)
        alert_context = json.dumps(alerts, indent=2) if alerts else "No active alerts"
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=f"""You are a weather activity recommendation expert. Based on the current weather conditions, suggest appropriate outdoor activities.

Current weather for {location}:
{weather_context}

Weather alerts:
{alert_context}

Provide:
1. 3-5 recommended activities suitable for current conditions
2. What to wear or bring
3. Any weather-related considerations or warnings
4. When conditions might be better (if poor)

Be concise and practical. Format as a clear list.""",
            config=types.GenerateContentConfig()
        )
        
        text = ""
        try:
            text = response.candidates[0].content.parts[0].text
        except:
            text = "Could not generate recommendations"
        
        return {
            "location": location,
            "weather": weather,
            "alerts": alerts,
            "recommendations": text
        }
    
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


def build_system_prompt() -> str:
    """Build the system prompt with skills and context."""
    skills = load_skills()
    
    return f"""You are a Weather Forecast Agent. Your job is to help users get accurate weather information, forecasts, and make plans based on weather conditions.

## Your Capabilities

1. **Current Weather**: Get real-time weather conditions for any location worldwide
2. **Forecasts**: Provide multi-day weather forecasts (up to 7 days)
3. **Activity Recommendations**: Suggest outdoor activities based on current weather
4. **Location Management**: Save favorite locations for quick weather checks
5. **Alerts**: Warn about severe weather conditions when relevant

## How to Help Users

1. **Listen to the Request**: User might ask "What's the weather in Helsinki?" or "Should I go hiking today?"
2. **Get Weather**: Always fetch current weather for the requested location
3. **Check Alerts**: Check for any severe weather alerts in the area
4. **Provide Context**: Include temperature, conditions, and any relevant warnings
5. **Make Recommendations**: If appropriate, suggest activities or clothing tips

## Key Behaviors

- **Accurate**: Always fetch current data using available tools
- **Helpful**: Provide context and recommendations - not just raw numbers
- **Safety First**: Warn about severe weather, storms, or dangerous conditions
- **Convenient**: Offer to save locations users check frequently
- **Multi-format**: Present data clearly (tables, bullet points, summaries)

## Weather Units

- Default to metric (Celsius)
- Convert to imperial (Fahrenheit) if user requests
- Explicitly state units when reporting temperatures

## Activity Recommendations

When suggesting activities based on weather:
- Consider temperature, precipitation, wind, and visibility
- Mention appropriate clothing or gear
- Warn about any hazardous conditions
- Suggest indoor alternatives when weather is poor

## Skills Reference

{skills}

## Response Style

- Be clear and concise
- Use formatting (bullet points, tables) for readability
- Include actionable insights ("Bring an umbrella" vs "Rain expected")
- Ask follow-up questions when helpful ("Do you need the full 7-day forecast?")"""


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


async def run_chat_loop(client: genai.Client, model: str, memory: MemoryStore):
    """Run interactive chat loop."""
    print("Weather Forecast Agent - Interactive Mode")
    print("=" * 45)
    print("Commands: 'exit' to quit, 'help' for commands")
    print()
    
    locations = memory.get_locations()
    if locations:
        print(f"Welcome back! Your saved locations: {', '.join([loc['name'] for loc in locations])}")
    else:
        print("Welcome! Ask me about weather anywhere in the world.")
    print()
    
    function_declarations = build_function_declarations()
    tools = [types.Tool(function_declarations=function_declarations)]
    
    system_prompt = build_system_prompt()
    history: List[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=system_prompt)]),
        types.Content(role="model", parts=[types.Part(text="I'm ready to help you with weather information. What would you like to know?")])
    ]
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nStay safe and have a great day!")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in {"exit", "quit", ":q", "/exit"}:
            print("Stay safe and have a great day!")
            break
        
        if user_input.lower() == "help":
            print("""
Available commands:
  weather <city>           - Get current weather
  forecast <city> [days]   - Get multi-day forecast
  save <name> <city>       - Save a location
  locations                - List saved locations
  activities <city>        - Get activity recommendations
  exit                     - Quit
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
                
                if result.get("error"):
                    print(f"[Error: {result['error']}]")
                else:
                    print(f"[Success]")
                
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


def run_single_query(client: genai.Client, model: str, query: str, memory: MemoryStore):
    """Run a single query."""
    log_status(f"Processing query: {query[:50]}...")
    
    function_declarations = build_function_declarations()
    tools = [types.Tool(function_declarations=function_declarations)]
    
    log_status("Loading saved locations...")
    locations = memory.get_locations()
    locations_context = f"\n\nSaved locations: {json.dumps(locations)}" if locations else ""
    
    system_prompt = build_system_prompt() + locations_context
    contents = [
        types.Content(role="user", parts=[types.Part(text=system_prompt)]),
        types.Content(role="model", parts=[types.Part(text="Ready to help with weather.")]),
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
        description="Weather Forecast Agent - Get weather information and recommendations",
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
    
    args = parser.parse_args()
    
    if not args.chat and not args.query:
        parser.print_help()
        sys.exit(1)
    
    api_key = load_api_key()
    client = genai.Client(api_key=api_key)
    memory = MemoryStore()
    
    if args.chat:
        asyncio.run(run_chat_loop(client, args.model, memory))
    else:
        run_single_query(client, args.model, args.query, memory)


if __name__ == "__main__":
    main()