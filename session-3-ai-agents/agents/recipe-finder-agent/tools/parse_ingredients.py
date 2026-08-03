#!/usr/bin/env python3
"""Parse free-text ingredients into normalized objects."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR))

from recipe_core import parse_ingredients_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse ingredient text")
    parser.add_argument("--input-text", required=True, help="Raw ingredient text")
    parser.add_argument("--locale", default="en-US", help="Normalization locale")
    args = parser.parse_args()

    try:
        parsed = parse_ingredients_text(args.input_text, locale=args.locale)
        print(json.dumps({"status": "success", "data": parsed}, indent=2))
        sys.exit(0)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
