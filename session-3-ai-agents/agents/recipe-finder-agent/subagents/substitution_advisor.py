#!/usr/bin/env python3
"""Subagent for context-aware substitution suggestions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR))

from recipe_core import suggest_substitutions_for_missing


def _csv(raw: str) -> List[str]:
    return [chunk.strip() for chunk in raw.split(",") if chunk.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Substitution advisor subagent")
    parser.add_argument("--missing-ingredients", nargs="+", required=True)
    parser.add_argument("--dietary-restrictions", default="")
    parser.add_argument("--available-ingredients", nargs="*", default=[])
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    data = suggest_substitutions_for_missing(
        missing_ingredients=args.missing_ingredients,
        dietary_restrictions=_csv(args.dietary_restrictions) if args.dietary_restrictions else None,
        available_ingredients=args.available_ingredients,
    )

    out = {
        "status": "success",
        "subagent": "substitution_advisor",
        "data": data,
    }
    if args.pretty:
        print(json.dumps(out, indent=2))
    else:
        print(json.dumps(out))
    sys.exit(0)


if __name__ == "__main__":
    main()
