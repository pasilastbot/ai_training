#!/usr/bin/env python3
"""Store and retrieve recipe user preferences."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR / "memory"))

from memory import MemoryStore


def _load_preferences(raw: str) -> Dict[str, Any]:
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("preferences must be a JSON object")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="User preference manager")
    parser.add_argument("--operation", choices=["set", "get", "update", "delete"], required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--preferences", default="{}")
    args = parser.parse_args()

    store = MemoryStore()

    try:
        if args.operation == "set":
            result = store.set_profile(args.user_id, _load_preferences(args.preferences))
        elif args.operation == "get":
            result = store.get_profile(args.user_id)
        elif args.operation == "update":
            result = store.update_profile(args.user_id, _load_preferences(args.preferences))
        else:
            result = {"deleted": store.delete_profile(args.user_id)}

        print(json.dumps({"status": "success", "data": result}, indent=2))
        sys.exit(0)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
