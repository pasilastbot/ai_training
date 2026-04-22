#!/usr/bin/env python3
"""
Store Restaurant Tool

Store a restaurant to the local database.

Usage:
  python store_restaurant.py --name "Ravintola Helsinki" --city Helsinki --website "https://example.com"
  python store_restaurant.py --file restaurant.json
  echo '{"name": "...", ...}' | python store_restaurant.py --stdin
"""

import argparse
import json
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(AGENT_DIR / "memory"))

from memory import MemoryStore


def main():
    parser = argparse.ArgumentParser(
        description="Store a restaurant to the database",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--file", "-f",
        help="JSON file with restaurant data"
    )
    input_group.add_argument(
        "--stdin",
        action="store_true",
        help="Read restaurant data from stdin"
    )
    
    parser.add_argument("--name", "-n", help="Restaurant name")
    parser.add_argument("--city", "-c", help="City")
    parser.add_argument("--address", "-a", help="Street address")
    parser.add_argument("--website", "-w", help="Website URL")
    parser.add_argument("--menu-url", help="Direct menu URL")
    parser.add_argument("--cuisines", help="Comma-separated cuisine types")
    parser.add_argument("--price-range", choices=["budget", "moderate", "expensive"])
    parser.add_argument("--average-price", type=float, help="Average lunch price in EUR")
    parser.add_argument("--features", help="Comma-separated features")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print output")
    
    args = parser.parse_args()
    
    if args.file:
        with open(args.file, "r") as f:
            data = json.load(f)
        restaurants = data if isinstance(data, list) else [data]
    elif args.stdin:
        data = json.load(sys.stdin)
        restaurants = data if isinstance(data, list) else [data]
    else:
        if not args.name or not args.city:
            print(json.dumps({"error": "Either --file/--stdin or --name and --city required"}))
            sys.exit(1)
        
        restaurant = {
            "name": args.name,
            "city": args.city
        }
        if args.address:
            restaurant["address"] = args.address
        if args.website:
            restaurant["website"] = args.website
        if args.menu_url:
            restaurant["menu_url"] = args.menu_url
        if args.cuisines:
            restaurant["cuisine_types"] = [c.strip() for c in args.cuisines.split(",")]
        if args.price_range:
            restaurant["price_range"] = args.price_range
        if args.average_price:
            restaurant["average_price"] = args.average_price
        if args.features:
            restaurant["features"] = [f.strip() for f in args.features.split(",")]
        
        restaurants = [restaurant]
    
    memory = MemoryStore()
    results = []
    
    for restaurant in restaurants:
        result = memory.store_restaurant(restaurant)
        results.append({
            "name": restaurant.get("name"),
            **result
        })
    
    if len(results) == 1:
        output = results[0]
    else:
        output = {"stored": len(results), "results": results}
    
    print(json.dumps(output, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
