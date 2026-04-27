#!/usr/bin/env python3
"""
Tool: delete_location

Remove a saved location.

Usage:
  python delete_location.py --name Home
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "memory"))

from memory import MemoryStore


def main():
    parser = argparse.ArgumentParser(
        description="Delete a saved location"
    )
    parser.add_argument(
        "--name", "-n",
        required=True,
        help="Location name to remove"
    )
    
    args = parser.parse_args()
    
    memory = MemoryStore()
    result = memory.delete_location(args.name)
    
    print(json.dumps(result, indent=2))
    
    if result.get("status") != "success":
        sys.exit(1)


if __name__ == "__main__":
    main()