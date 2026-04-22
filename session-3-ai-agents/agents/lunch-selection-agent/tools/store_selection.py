#!/usr/bin/env python3
"""
Store Selection Tool

Record a lunch selection to track user's choices.

Usage:
  python store_selection.py --restaurant "Ravintola Helsinki" --dish "Salmon soup" --rating 4
  python store_selection.py --file selection.json
  echo '{"restaurant_name": "...", ...}' | python store_selection.py --stdin
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

AGENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(AGENT_DIR / "memory"))

from memory import MemoryStore


def main():
    parser = argparse.ArgumentParser(
        description="Store a lunch selection",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--file", "-f",
        help="JSON file with selection data"
    )
    input_group.add_argument(
        "--stdin",
        action="store_true",
        help="Read selection data from stdin"
    )
    
    parser.add_argument("--restaurant", "-r", help="Restaurant name")
    parser.add_argument("--restaurant-id", help="Restaurant ID (if known)")
    parser.add_argument("--dish", "-d", help="Dish name")
    parser.add_argument("--description", help="Dish description")
    parser.add_argument("--cuisine", "-c", help="Cuisine type")
    parser.add_argument("--price", "-p", type=float, help="Price in EUR")
    parser.add_argument("--rating", type=int, choices=[1, 2, 3, 4, 5], help="Rating 1-5")
    parser.add_argument("--would-order-again", type=lambda x: x.lower() == 'true', 
                        help="Would order again (true/false)")
    parser.add_argument("--notes", "-n", help="Notes about the meal")
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--city", help="City where lunch was had")
    parser.add_argument("--date", help="Date (YYYY-MM-DD, default: today)")
    parser.add_argument("--was-recommendation", action="store_true", 
                        help="Was this recommended by the agent")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print output")
    
    args = parser.parse_args()
    
    if args.file:
        with open(args.file, "r") as f:
            selection = json.load(f)
    elif args.stdin:
        selection = json.load(sys.stdin)
    else:
        if not args.restaurant or not args.dish:
            print(json.dumps({"error": "Either --file/--stdin or --restaurant and --dish required"}))
            sys.exit(1)
        
        selection = {
            "restaurant_name": args.restaurant,
            "dish_name": args.dish
        }
        if args.restaurant_id:
            selection["restaurant_id"] = args.restaurant_id
        if args.description:
            selection["dish_description"] = args.description
        if args.cuisine:
            selection["cuisine_type"] = args.cuisine
        if args.price:
            selection["price"] = args.price
        if args.rating:
            selection["rating"] = args.rating
        if args.would_order_again is not None:
            selection["would_order_again"] = args.would_order_again
        if args.notes:
            selection["notes"] = args.notes
        if args.tags:
            selection["tags"] = [t.strip() for t in args.tags.split(",")]
        if args.city:
            selection["city"] = args.city
        if args.date:
            selection["date"] = args.date
        if args.was_recommendation:
            selection["was_recommendation"] = True
    
    memory = MemoryStore()
    result = memory.store_selection(selection)
    
    output = {
        "restaurant": selection.get("restaurant_name"),
        "dish": selection.get("dish_name"),
        **result
    }
    
    print(json.dumps(output, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
