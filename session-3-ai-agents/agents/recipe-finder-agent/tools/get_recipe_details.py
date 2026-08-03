#!/usr/bin/env python3
"""Fetch full recipe details by recipe id."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR))

from recipe_core import get_recipe_by_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Get recipe details")
    parser.add_argument("--recipe-id", required=True)
    parser.add_argument("--include-nutrition", action="store_true")
    args = parser.parse_args()

    try:
        recipe = get_recipe_by_id(args.recipe_id)
        if not recipe:
            print(json.dumps({"status": "error", "error": "Recipe not found"}))
            sys.exit(1)

        if not args.include_nutrition and "nutrition" in recipe:
            recipe.pop("nutrition")

        print(json.dumps({"status": "success", "data": recipe}, indent=2))
        sys.exit(0)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
