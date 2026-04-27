#!/usr/bin/env python3
"""
Tool: get_weather

Get current weather conditions for a location.

Usage:
  python get_weather.py --location "Helsinki"
  python get_weather.py --location "New York" --units imperial
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "subagents"))
sys.path.insert(0, str(Path(__file__).parent.parent / "memory"))

from memory import MemoryStore


def main():
    parser = argparse.ArgumentParser(
        description="Get current weather for a location"
    )
    parser.add_argument(
        "--location", "-l",
        required=True,
        help="City name or coordinates"
    )
    parser.add_argument(
        "--units", "-u",
        choices=["metric", "imperial"],
        default="metric",
        help="Temperature units (metric=Celsius, imperial=Fahrenheit)"
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use cached weather data if available"
    )
    
    args = parser.parse_args()
    
    memory = MemoryStore()
    
    if args.use_cache:
        cached = memory.get_cached_weather(args.location)
        if cached:
            result = {
                "status": "success",
                "source": "cache",
                "location": args.location,
                "weather": cached
            }
            print(json.dumps(result, indent=2))
            sys.exit(0)
    
    try:
        import subprocess
        
        result = subprocess.run(
            [
                "python",
                str(Path(__file__).parent.parent / "subagents" / "weather_search.py"),
                "--location", args.location,
                "--units", args.units,
                "--pretty"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            weather = data.get("weather", {})
            
            if weather and not weather.get("error"):
                memory.cache_weather(args.location, weather)
            
            print(json.dumps(data, indent=2))
            sys.exit(0)
        else:
            error_output = {
                "status": "error",
                "message": "Failed to get weather",
                "details": result.stderr
            }
            print(json.dumps(error_output, indent=2))
            sys.exit(1)
    
    except subprocess.TimeoutExpired:
        print(json.dumps({"status": "error", "message": "Request timed out"}, indent=2))
        sys.exit(1)
    except FileNotFoundError:
        print(json.dumps({"status": "error", "message": "Weather search subagent not found"}, indent=2))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()