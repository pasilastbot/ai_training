#!/usr/bin/env python3
"""Subagent for recipe ranking and preference-aware scoring."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR))

from recipe_core import rank_recipe_candidates


def _load_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        path = Path(raw)
        return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Recipe ranker subagent")
    parser.add_argument("--recipes", required=True)
    parser.add_argument("--available-ingredients", nargs="+", required=True)
    parser.add_argument("--user-preferences", default="{}")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    recipes: List[Dict[str, Any]] = _load_json(args.recipes)
    prefs: Dict[str, Any] = _load_json(args.user_preferences)
    ranked = rank_recipe_candidates(recipes, args.available_ingredients, prefs)

    out = {
        "status": "success",
        "subagent": "recipe_ranker",
        "count": len(ranked),
        "data": ranked,
    }
    if args.pretty:
        print(json.dumps(out, indent=2))
    else:
        print(json.dumps(out))
    sys.exit(0)


if __name__ == "__main__":
    main()
