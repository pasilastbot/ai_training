#!/usr/bin/env python3
"""
Tool: store_location

Save a favorite location for quick access.

Usage:
  python store_location.py --name Home --location "Helsinki, Finland"
  python store_location.py --name Work --location "San Francisco, CA" --lat 37.7749 --lon -122.4194
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "memory"))

from memory import MemoryStore


def main():
    parser = argparse.ArgumentParser(
        description="Store a favorite location"
    )
    parser.add_argument(
        "--name", "-n",
        required=True,
        help="Location nickname (e.g., 'Home', 'Work')"
    )
    parser.add_argument(
        "--location", "-l",
        required=True,
        help="City name or coordinates"
    )
    parser.add_argument(
        "--lat",
        type=float,
        help="Latitude"
    )
    parser.add_argument(
        "--lon",
        type=float,
        help="Longitude"
    )
    parser.add_argument(
        "--timezone", "-tz",
        help="Timezone (e.g., 'Europe/Helsinki')"
    )
    
    args = parser.parse_args()
    
    memory = MemoryStore()
    
    coordinates = None
    if args.lat is not None and args.lon is not None:
        coordinates = {"lat": args.lat, "lon": args.lon}
    
    result = memory.store_location(
        name=args.name,
        location=args.location,
        coordinates=coordinates,
        timezone=args.timezone
    )
    
    output = {
        **result,
        "name": args.name,
        "location": args.location
    }
    
    print(json.dumps(output, indent=2))
    
    if result.get("status") != "success":
        sys.exit(1)


if __name__ == "__main__":
    main()