#!/usr/bin/env python3
"""
Retrieve TES Tool

Retrieves TES documents from the database.

Usage:
    python retrieve_tes.py --id "tes_example_2024"
    python retrieve_tes.py --list
    python retrieve_tes.py --search "teknologia"
    python retrieve_tes.py --list --industry "technology"
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory.memory import get_tes, list_tes, search_tes


def main():
    parser = argparse.ArgumentParser(description="Retrieve TES Tool")
    parser.add_argument("--id", help="Get TES by ID")
    parser.add_argument("--list", action="store_true", help="List all TES documents")
    parser.add_argument("--search", help="Search TES documents")
    parser.add_argument("--industry", help="Filter by industry")
    parser.add_argument("--union", help="Filter by union")
    parser.add_argument("--valid-only", action="store_true", help="Only show currently valid TES")
    parser.add_argument("--limit", type=int, default=100, help="Max results")
    
    args = parser.parse_args()
    
    if args.id:
        result = get_tes(args.id)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": "TES not found", "id": args.id}))
            sys.exit(1)
    
    elif args.search:
        results = search_tes(args.search, limit=args.limit)
        print(json.dumps({
            "count": len(results),
            "query": args.search,
            "results": results
        }, ensure_ascii=False, indent=2))
    
    elif args.list:
        results = list_tes(
            industry=args.industry,
            union=args.union,
            valid_only=args.valid_only,
            limit=args.limit
        )
        print(json.dumps({
            "count": len(results),
            "filters": {
                "industry": args.industry,
                "union": args.union,
                "valid_only": args.valid_only
            },
            "tes": results
        }, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
