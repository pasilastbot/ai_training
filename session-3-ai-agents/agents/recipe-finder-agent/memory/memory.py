#!/usr/bin/env python3
"""Memory CLI and store for recipe-finder-agent."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


class MemoryStore:
    """File-based memory store for user profiles, pantry, and interactions."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _path(self, name: str) -> Path:
        return DATA_DIR / f"{name}.json"

    def _load(self, name: str) -> Dict[str, Any]:
        path = self._path(name)
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save(self, name: str, data: Dict[str, Any]) -> None:
        path = self._path(name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    # ---------------- Profiles ----------------

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._load("user_profiles").get(user_id)

    def set_profile(self, user_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        data = self._load("user_profiles")
        existing = data.get(user_id, {})
        now = self._now()
        merged = {
            "user_id": user_id,
            "dietary_restrictions": profile.get("dietary_restrictions", existing.get("dietary_restrictions", [])),
            "disliked_ingredients": profile.get("disliked_ingredients", existing.get("disliked_ingredients", [])),
            "favorite_cuisines": profile.get("favorite_cuisines", existing.get("favorite_cuisines", [])),
            "max_cook_time_minutes": profile.get("max_cook_time_minutes", existing.get("max_cook_time_minutes")),
            "created_at": existing.get("created_at", now),
            "updated_at": now,
        }
        data[user_id] = merged
        self._save("user_profiles", data)
        return merged

    def update_profile(self, user_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_profile(user_id) or {
            "user_id": user_id,
            "dietary_restrictions": [],
            "disliked_ingredients": [],
            "favorite_cuisines": [],
            "max_cook_time_minutes": None,
            "created_at": self._now(),
        }
        current.update({k: v for k, v in patch.items() if v is not None})
        return self.set_profile(user_id, current)

    def delete_profile(self, user_id: str) -> bool:
        data = self._load("user_profiles")
        if user_id not in data:
            return False
        del data[user_id]
        self._save("user_profiles", data)
        return True

    # ---------------- Pantry ----------------

    def list_pantry(self, user_id: str) -> List[Dict[str, Any]]:
        return list(self._load("pantry_items").get(user_id, []))

    def add_pantry_items(self, user_id: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        data = self._load("pantry_items")
        pantry = data.get(user_id, [])
        now = self._now()

        index = {entry.get("ingredient_name", "").lower(): idx for idx, entry in enumerate(pantry)}
        for item in items:
            ingredient_name = str(item.get("ingredient_name", "")).strip().lower()
            if not ingredient_name:
                continue
            updated = {
                "user_id": user_id,
                "ingredient_name": ingredient_name,
                "quantity": item.get("quantity"),
                "unit": item.get("unit"),
                "expires_on": item.get("expires_on"),
                "updated_at": now,
            }
            if ingredient_name in index:
                pantry[index[ingredient_name]] = updated
            else:
                pantry.append(updated)
                index[ingredient_name] = len(pantry) - 1

        data[user_id] = pantry
        self._save("pantry_items", data)
        return pantry

    def remove_pantry_items(self, user_id: str, ingredient_names: List[str]) -> List[Dict[str, Any]]:
        data = self._load("pantry_items")
        pantry = data.get(user_id, [])
        remove_set = {name.strip().lower() for name in ingredient_names if name.strip()}
        data[user_id] = [entry for entry in pantry if entry.get("ingredient_name", "").lower() not in remove_set]
        self._save("pantry_items", data)
        return list(data[user_id])

    def clear_pantry(self, user_id: str) -> None:
        data = self._load("pantry_items")
        data[user_id] = []
        self._save("pantry_items", data)

    # ---------------- Interactions ----------------

    def add_interaction(self, user_id: str, interaction: Dict[str, Any]) -> Dict[str, Any]:
        data = self._load("recipe_interactions")
        entries = data.get(user_id, [])
        entry = {
            "user_id": user_id,
            "recipe_id": interaction["recipe_id"],
            "action": interaction["action"],
            "rating": interaction.get("rating"),
            "timestamp": interaction.get("timestamp") or self._now(),
        }
        entries.append(entry)
        data[user_id] = entries
        self._save("recipe_interactions", data)
        return entry

    def get_interactions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        rows = list(self._load("recipe_interactions").get(user_id, []))
        rows.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return rows[:limit]

    # ---------------- Search Sessions ----------------

    def add_search_session(self, user_id: str, session: Dict[str, Any]) -> Dict[str, Any]:
        data = self._load("search_sessions")
        session_id = session.get("session_id") or str(uuid.uuid4())
        created_at = session.get("created_at") or self._now()
        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "query_text": session["query_text"],
            "parsed_ingredients": session.get("parsed_ingredients", []),
            "filters": session.get("filters", {}),
            "result_recipe_ids": session.get("result_recipe_ids", []),
            "created_at": created_at,
        }
        data[session_id] = payload
        self._save("search_sessions", data)
        return payload

    def get_user_sessions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        rows = [row for row in self._load("search_sessions").values() if row.get("user_id") == user_id]
        rows.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return rows[:limit]


# ---------------- CLI ----------------

def _json_loads(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Memory CLI for recipe-finder-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    profile_get = subparsers.add_parser("profile-get", help="Get user profile")
    profile_get.add_argument("--user-id", required=True)

    profile_set = subparsers.add_parser("profile-set", help="Set user profile")
    profile_set.add_argument("--user-id", required=True)
    profile_set.add_argument("--profile-json", required=True)

    profile_update = subparsers.add_parser("profile-update", help="Patch user profile")
    profile_update.add_argument("--user-id", required=True)
    profile_update.add_argument("--profile-json", required=True)

    profile_delete = subparsers.add_parser("profile-delete", help="Delete user profile")
    profile_delete.add_argument("--user-id", required=True)

    pantry_add = subparsers.add_parser("pantry-add", help="Add pantry items")
    pantry_add.add_argument("--user-id", required=True)
    pantry_add.add_argument("--items-json", required=True)

    pantry_remove = subparsers.add_parser("pantry-remove", help="Remove pantry ingredients")
    pantry_remove.add_argument("--user-id", required=True)
    pantry_remove.add_argument("--ingredients", nargs="+", required=True)

    pantry_list = subparsers.add_parser("pantry-list", help="List pantry items")
    pantry_list.add_argument("--user-id", required=True)

    pantry_clear = subparsers.add_parser("pantry-clear", help="Clear pantry items")
    pantry_clear.add_argument("--user-id", required=True)

    interaction_add = subparsers.add_parser("interaction-add", help="Add recipe interaction")
    interaction_add.add_argument("--user-id", required=True)
    interaction_add.add_argument("--interaction-json", required=True)

    interaction_list = subparsers.add_parser("interaction-list", help="List recipe interactions")
    interaction_list.add_argument("--user-id", required=True)
    interaction_list.add_argument("--limit", type=int, default=50)

    session_add = subparsers.add_parser("session-add", help="Add search session")
    session_add.add_argument("--user-id", required=True)
    session_add.add_argument("--session-json", required=True)

    session_list = subparsers.add_parser("session-list", help="List user search sessions")
    session_list.add_argument("--user-id", required=True)
    session_list.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()
    store = MemoryStore()

    try:
        if args.command == "profile-get":
            result = store.get_profile(args.user_id)
        elif args.command == "profile-set":
            result = store.set_profile(args.user_id, _json_loads(args.profile_json))
        elif args.command == "profile-update":
            result = store.update_profile(args.user_id, _json_loads(args.profile_json))
        elif args.command == "profile-delete":
            result = {"deleted": store.delete_profile(args.user_id)}
        elif args.command == "pantry-add":
            result = store.add_pantry_items(args.user_id, _json_loads(args.items_json))
        elif args.command == "pantry-remove":
            result = store.remove_pantry_items(args.user_id, args.ingredients)
        elif args.command == "pantry-list":
            result = store.list_pantry(args.user_id)
        elif args.command == "pantry-clear":
            store.clear_pantry(args.user_id)
            result = {"cleared": True, "user_id": args.user_id}
        elif args.command == "interaction-add":
            result = store.add_interaction(args.user_id, _json_loads(args.interaction_json))
        elif args.command == "interaction-list":
            result = store.get_interactions(args.user_id, args.limit)
        elif args.command == "session-add":
            result = store.add_search_session(args.user_id, _json_loads(args.session_json))
        elif args.command == "session-list":
            result = store.get_user_sessions(args.user_id, args.limit)
        else:
            raise ValueError(f"Unsupported command: {args.command}")
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        sys.exit(1)

    print(json.dumps({"status": "success", "data": result}, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
