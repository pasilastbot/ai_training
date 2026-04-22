#!/usr/bin/env python3
"""
Retrieve Restaurants Tool

Query restaurants from the local database.

Usage:
  python retrieve_restaurants.py --city Helsinki
  python retrieve_restaurants.py --city Tampere --cuisine Italian
  python retrieve_restaurants.py --id rest_123
  python retrieve_restaurants.py --search "thai food"
  python retrieve_restaurants.py --stats
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
        description="Retrieve restaurants from the database",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--id", help="Get specific restaurant by ID")
    parser.add_argument("--city", "-c", help="Filter by city")
    parser.add_argument("--cuisine", help="Filter by cuisine type")
    parser.add_argument("--price-range", choices=["budget", "moderate", "expensive"])
    parser.add_argument("--search", "-s", help="Search by name or cuisine")
    parser.add_argument("--stats", action="store_true", help="Get statistics")
    parser.add_argument("--limit", type=int, default=50, help="Max results")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print output")
    
    args = parser.parse_args()
    
    memory = MemoryStore()
    
    if args.stats:
        stats = memory.get_stats()
        output = {
            "total_restaurants": stats["total_restaurants"],
            "restaurants_by_city": stats["restaurants_by_city"],
            "cuisines": stats["cuisines"]
        }
    elif args.id:
        restaurant = memory.get_restaurant(args.id)
        if restaurant:
            output = {"restaurant": restaurant}
        else:
            output = {"error": f"Restaurant not found: {args.id}"}
            print(json.dumps(output))
            sys.exit(1)
    elif args.search:
        restaurants = memory.search_restaurants(args.search, args.limit)
        output = {"query": args.search, "count": len(restaurants), "restaurants": restaurants}
    else:
        restaurants = memory.get_restaurants(
            city=args.city,
            cuisine=args.cuisine,
            price_range=args.price_range,
            limit=args.limit
        )
        output = {
            "count": len(restaurants),
            "restaurants": restaurants,
            "filters": {
                "city": args.city,
                "cuisine": args.cuisine,
                "price_range": args.price_range
            }
        }
    
    print(json.dumps(output, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
