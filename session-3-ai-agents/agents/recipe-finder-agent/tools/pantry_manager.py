#!/usr/bin/env python3
"""Read and update pantry inventory in persistent memory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR / "memory"))

from memory import MemoryStore


def _load_items(items_raw: str) -> List[Dict[str, Any]]:
    if not items_raw:
        return []
    payload = json.loads(items_raw)
    if not isinstance(payload, list):
        raise ValueError("items must be a JSON array")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Pantry memory manager")
    parser.add_argument("--operation", choices=["add", "remove", "list", "clear"], required=True)
    parser.add_argument("--items", default="[]", help="JSON array for add/remove operations")
    parser.add_argument("--user-id", required=True)
    args = parser.parse_args()

    store = MemoryStore()

    try:
        if args.operation == "add":
            items = _load_items(args.items)
            result = store.add_pantry_items(args.user_id, items)
        elif args.operation == "remove":
            raw_items = _load_items(args.items)
            names = []
            for item in raw_items:
                if isinstance(item, dict):
                    name = item.get("ingredient_name")
                else:
                    name = str(item)
                if name:
                    names.append(str(name))
            result = store.remove_pantry_items(args.user_id, names)
        elif args.operation == "list":
            result = store.list_pantry(args.user_id)
        else:
            store.clear_pantry(args.user_id)
            result = {"cleared": True, "user_id": args.user_id}

        print(json.dumps({"status": "success", "data": result}, indent=2))
        sys.exit(0)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
