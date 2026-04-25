#!/usr/bin/env python3
"""
Store TES Tool

Stores a TES document in the database.

Usage:
    python store_tes.py --json tes_data.json
    echo '{"name": "Test TES", ...}' | python store_tes.py --stdin
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory.memory import store_tes, init_database


def main():
    parser = argparse.ArgumentParser(description="Store TES Tool")
    parser.add_argument("--json", help="Path to JSON file with TES data")
    parser.add_argument("--stdin", action="store_true", help="Read JSON from stdin")
    
    args = parser.parse_args()
    
    if args.stdin:
        data = json.load(sys.stdin)
    elif args.json:
        with open(args.json, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        parser.print_help()
        sys.exit(1)
    
    try:
        init_database()
    except:
        pass
    
    result = store_tes(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
