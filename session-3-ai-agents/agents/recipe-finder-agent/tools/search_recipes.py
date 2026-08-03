#!/usr/bin/env python3
"""Search candidate recipes from available ingredients and filters."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR))

from recipe_core import search_candidate_recipes


def _csv(values: str) -> List[str]:
    return [v.strip() for v in values.split(",") if v.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search candidate recipes")
    parser.add_argument("--ingredients", nargs="+", required=True, help="Canonical ingredient names")
    parser.add_argument("--dietary-filters", default="", help="Comma-separated dietary filters")
    parser.add_argument("--max-cook-time-minutes", type=int, default=None)
    parser.add_argument("--cuisine", default=None)
    parser.add_argument("--servings", type=int, default=None)
    args = parser.parse_args()

    try:
        recipes = search_candidate_recipes(
            ingredients=args.ingredients,
            dietary_filters=_csv(args.dietary_filters) if args.dietary_filters else None,
            max_cook_time_minutes=args.max_cook_time_minutes,
            cuisine=args.cuisine,
            servings=args.servings,
        )
        print(json.dumps({"status": "success", "count": len(recipes), "data": recipes}, indent=2))
        sys.exit(0)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
