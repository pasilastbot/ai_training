#!/usr/bin/env python3
"""Rank candidate recipes for a user context."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR))

from recipe_core import rank_recipe_candidates


def _load_json(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        path = Path(value)
        return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Rank candidate recipes")
    parser.add_argument("--recipes", required=True, help="Recipes JSON or path to JSON")
    parser.add_argument("--available-ingredients", nargs="+", required=True)
    parser.add_argument("--user-preferences", default="{}", help="JSON object or file path")
    args = parser.parse_args()

    try:
        recipes_data: List[Dict[str, Any]] = _load_json(args.recipes)
        preferences: Dict[str, Any] = _load_json(args.user_preferences)
        ranked = rank_recipe_candidates(recipes_data, args.available_ingredients, preferences)
        print(json.dumps({"status": "success", "count": len(ranked), "data": ranked}, indent=2))
        sys.exit(0)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
