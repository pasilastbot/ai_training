#!/usr/bin/env python3
"""
Subagent: weather_search

Search for weather data using Google Search when direct API fails.
Retrieves current weather and forecasts for any location.

Usage:
  python weather_search.py --location "Helsinki"
  python weather_search.py --location "New York" --days 5 --units imperial --pretty
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from google import genai
from google.genai import types


def parse_temperature(text: str, units: str = "metric") -> Optional[float]:
    """Extract temperature from text."""
    import re
    
    patterns = [
        r'(\d+)\s*(?:degrees?°?)?\s*(?:C|F)?',
        r'(-?\d+)°(?:\s*[CF])?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            temp = float(match.group(1))
            
            text_lower = text.lower()
            if 'f' in text_lower and units == "metric":
                temp = (temp - 32) * 5/9
            elif 'c' in text_lower and units == "imperial":
                temp = temp * 9/5 + 32
            
            return round(temp, 1)
    
    return None


def get_current_weather(client: genai.Client, location: str, units: str = "metric") -> Dict[str, Any]:
    """Get current weather using Google Search."""
    
    unit_suffix = "°C" if units == "metric" else "°F"
    
    prompt = f"""Get current weather conditions for {location}. 
Use Google Search to find real-time data.

Return a JSON object with these fields if available:
- temperature: current temperature in {unit_suffix}
- condition: weather description (e.g., "Sunny", "Cloudy", "Rain")
- humidity: percentage
- wind: wind speed and direction
- feels_like: what it feels like
- visibility: in km/miles
- pressure: atmospheric pressure
- location_name: the full location name

Only return the JSON, no other text."""
    
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        
        text = ""
        try:
            text = response.candidates[0].content.parts[0].text
        except:
            return {"error": "No response from API"}
        
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = text[json_start:json_end]
            return json.loads(json_str)
        
        return {"error": "Could not parse weather data", "raw": text}
    
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {str(e)}", "raw": text}
    except Exception as e:
        return {"error": str(e)}


def get_forecast(client: genai.Client, location: str, days: int, units: str = "metric") -> Dict[str, Any]:
    """Get weather forecast using Google Search."""
    
    unit_suffix = "°C" if units == "metric" else "°F"
    
    prompt = f"""Get {days}-day weather forecast for {location}.
Use Google Search to find accurate forecast data.

Return a JSON object with this structure:
{{
  "location": "{location}",
  "forecast": [
    {{
      "day": "Day name or date",
      "high": temperature in {unit_suffix},
      "low": temperature in {unit_suffix},
      "condition": weather description,
      "precipitation": chance of rain (%),
      "humidity": percentage (optional)
    }}
  ]
}}

Only return the JSON, no other text."""
    
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        
        text = ""
        try:
            text = response.candidates[0].content.parts[0].text
        except:
            return {"error": "No response from API"}
        
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = text[json_start:json_end]
            return json.loads(json_str)
        
        return {"error": "Could not parse forecast data", "raw": text}
    
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {str(e)}", "raw": text}
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Search for weather data using Google Search"
    )
    parser.add_argument(
        "--location", "-l",
        required=True,
        help="City name or coordinates"
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=0,
        help="Number of days for forecast (0 for current weather only)"
    )
    parser.add_argument(
        "--units", "-u",
        choices=["metric", "imperial"],
        default="metric",
        help="Temperature units"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print JSON output"
    )
    
    args = parser.parse_args()
    
    api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(json.dumps({"error": "API key not configured"}))
        sys.exit(1)
    
    client = genai.Client(api_key=api_key)
    
    result = {
        "location": args.location,
        "units": args.units,
        "fetched_at": datetime.utcnow().isoformat()
    }
    
    if args.days > 0:
        print(f"Fetching {args.days}-day forecast for {args.location}...", file=sys.stderr)
        forecast_data = get_forecast(client, args.location, args.days, args.units)
        
        if forecast_data.get("error"):
            result["error"] = forecast_data["error"]
            if "raw" in forecast_data:
                result["details"] = forecast_data["raw"]
        else:
            result["forecast"] = forecast_data.get("forecast", [])
            result["location_name"] = forecast_data.get("location")
    
    print(f"Fetching current weather for {args.location}...", file=sys.stderr)
    weather_data = get_current_weather(client, args.location, args.units)
    
    if weather_data.get("error"):
        result["error"] = weather_data["error"]
        if "raw" in weather_data:
            result["details"] = weather_data["raw"]
    else:
        result["weather"] = weather_data
        if not result.get("location_name"):
            result["location_name"] = weather_data.get("location_name", args.location)
    
    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))
    
    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()