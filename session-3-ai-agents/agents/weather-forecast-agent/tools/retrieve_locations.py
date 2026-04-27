#!/usr/bin/env python3
"""
Tool: retrieve_locations

Get all saved favorite locations.

Usage:
  python retrieve_locations.py
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "memory"))

from memory import MemoryStore


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve all saved locations"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "compact"],
        default="json",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    memory = MemoryStore()
    locations = memory.get_locations()
    
    if args.format == "compact":
        for loc in locations:
            print(f"{loc['name']}: {loc['city']}")
        return
    
    output = {
        "count": len(locations),
        "locations": locations
    }
    
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()