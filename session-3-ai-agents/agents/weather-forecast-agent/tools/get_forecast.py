#!/usr/bin/env python3
"""
Tool: get_forecast

Get multi-day weather forecast for a location.

Usage:
  python get_forecast.py --location "Helsinki" --days 5
  python get_forecast.py --location "Tokyo" --days 7 --units metric
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "subagents"))


def main():
    parser = argparse.ArgumentParser(
        description="Get weather forecast for a location"
    )
    parser.add_argument(
        "--location", "-l",
        required=True,
        help="City name or coordinates"
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=5,
        help="Number of days to forecast (1-7, default: 5)"
    )
    parser.add_argument(
        "--units", "-u",
        choices=["metric", "imperial"],
        default="metric",
        help="Temperature units"
    )
    
    args = parser.parse_args()
    
    if not 1 <= args.days <= 7:
        print(json.dumps({
            "status": "error",
            "message": "Days must be between 1 and 7"
        }, indent=2))
        sys.exit(1)
    
    try:
        import subprocess
        
        result = subprocess.run(
            [
                "python",
                str(Path(__file__).parent.parent / "subagents" / "weather_search.py"),
                "--location", args.location,
                "--days", str(args.days),
                "--units", args.units,
                "--pretty"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(json.dumps(data, indent=2))
            sys.exit(0)
        else:
            error_output = {
                "status": "error",
                "message": "Failed to get forecast",
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