#!/usr/bin/env python3
"""Subagent for ingredient extraction and normalization."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR))

from recipe_core import parse_ingredients_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingredient parser subagent")
    parser.add_argument("--input-text", required=False)
    parser.add_argument("--locale", default="en-US")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    text = args.input_text
    if not text:
        text = sys.stdin.read().strip()

    if not text:
        print(json.dumps({"status": "error", "error": "No input text provided"}))
        sys.exit(1)

    data = parse_ingredients_text(text, locale=args.locale)
    output = {"status": "success", "subagent": "ingredient_parser", "data": data}
    if args.pretty:
        print(json.dumps(output, indent=2))
    else:
        print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
