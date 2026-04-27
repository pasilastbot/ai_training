#!/usr/bin/env python3
"""
Subagent: alert_checker

Check for severe weather alerts in a region.

Usage:
  python alert_checker.py --location "Helsinki" --pretty
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

from google import genai
from google.genai import types


def check_weather_alerts(client: genai.Client, location: str) -> Dict[str, Any]:
    """Check for severe weather alerts using Google Search."""
    
    prompt = f"""Check for active weather alerts, warnings, and advisories for {location}.

Use Google Search to find real-time weather alert information from:
- National weather services (e.g., NWS, Met Office, FMI)
- Weather alert systems
- Official meteorological agencies

Return a JSON object with this structure:
{{
  "location": "{location}",
  "has_alerts": true/false,
  "alerts": [
    {{
      "severity": "severity level (Warning, Watch, Advisory)",
      "type": "type of alert (e.g., Thunderstorm, Flood, Heat)",
      "description": "brief description",
      "issued_by": "issuing authority",
      "valid_until": "expiry time if known",
      "urgency": "high/medium/low"
    }}
  ]
}}

If there are no active alerts, return: {{"has_alerts": false, "alerts": []}}

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
        
        return {
            "has_alerts": False,
            "alerts": [],
            "note": "No alerts found or could not parse alert data",
            "raw": text[:200]
        }
    
    except json.JSONDecodeError as e:
        return {
            "has_alerts": False,
            "alerts": [],
            "error": f"JSON parse error: {str(e)}",
            "raw": text[:200] if text else ""
        }
    except Exception as e:
        return {
            "has_alerts": False,
            "alerts": [],
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description="Check for weather alerts in a region"
    )
    parser.add_argument(
        "--location", "-l",
        required=True,
        help="City name or region"
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
    
    print(f"Checking weather alerts for {args.location}...", file=sys.stderr)
    
    client = genai.Client(api_key=api_key)
    
    result = check_weather_alerts(client, args.location)
    
    result["location"] = args.location
    result["checked_at"] = datetime.utcnow().isoformat()
    
    if args.pretty:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))
    
    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()