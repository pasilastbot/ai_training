#!/usr/bin/env python3
"""Suggest substitutions for missing or restricted ingredients."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR))

from recipe_core import suggest_substitutions_for_missing


def _csv(value: str) -> List[str]:
    return [token.strip() for token in value.split(",") if token.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Suggest ingredient substitutions")
    parser.add_argument("--missing-ingredients", nargs="+", required=True)
    parser.add_argument("--dietary-restrictions", default="")
    parser.add_argument("--available-ingredients", nargs="*", default=[])
    args = parser.parse_args()

    try:
        data = suggest_substitutions_for_missing(
            missing_ingredients=args.missing_ingredients,
            dietary_restrictions=_csv(args.dietary_restrictions) if args.dietary_restrictions else None,
            available_ingredients=args.available_ingredients,
        )
        print(json.dumps({"status": "success", "data": data}, indent=2))
        sys.exit(0)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
