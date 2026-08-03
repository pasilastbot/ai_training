#!/usr/bin/env python3
"""
Recipe Finder Agent CLI

Usage:
  python recipe_finder_agent.py --chat
  python recipe_finder_agent.py "find vegetarian dinners with tomato and onion"
  python recipe_finder_agent.py --ingredients "tomato, onion, chickpeas" --dietary-filters vegan
  python recipe_finder_agent.py --help
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_env import load_agent_environment

load_agent_environment()

AGENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(AGENT_DIR))
sys.path.insert(0, str(AGENT_DIR / "memory"))

from memory import MemoryStore
from recipe_core import normalize_ingredient_list

DEFAULT_MODEL = "gemini-2.5-flash"


def load_skills() -> Dict[str, str]:
    """Load markdown skills from the skills folder."""
    skills_dir = AGENT_DIR / "skills"
    loaded: Dict[str, str] = {}
    for path in sorted(skills_dir.glob("*.md")):
        loaded[path.stem] = path.read_text(encoding="utf-8")
    return loaded


def run_subagent(name: str, args: List[str], stdin_text: Optional[str] = None) -> Dict[str, Any]:
    """Run a subagent script and parse structured JSON output."""
    script = AGENT_DIR / "subagents" / f"{name}.py"
    if not script.exists():
        raise FileNotFoundError(f"Subagent not found: {name}")

    cmd = [sys.executable, str(script)] + args
    result = subprocess.run(
        cmd,
        input=stdin_text,
        text=True,
        capture_output=True,
        cwd=str(AGENT_DIR),
        timeout=120,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "subagent failed"
        raise RuntimeError(f"{name} failed: {detail}")

    return json.loads(result.stdout)


def infer_ingredients(query: str, explicit_ingredients: Optional[str], pantry_items: List[Dict[str, Any]]) -> str:
    """Infer ingredient source preference for the current request."""
    if explicit_ingredients:
        return explicit_ingredients

    has_keywords = any(term in query.lower() for term in ["with", "have", "ingredients", "pantry"])
    if has_keywords and query.strip():
        return query

    pantry_names = [item.get("ingredient_name", "") for item in pantry_items if item.get("ingredient_name")]
    return ", ".join(pantry_names)


def run_recipe_flow(
    query: str,
    user_id: str,
    ingredients_text: Optional[str],
    dietary_filters: Optional[List[str]],
    cuisine: Optional[str],
    max_cook_time_minutes: Optional[int],
    servings: Optional[int],
    grounded_query: Optional[str],
) -> Dict[str, Any]:
    """Execute parse -> retrieve -> rank -> substitutions flow."""
    memory = MemoryStore()
    profile = memory.get_profile(user_id) or {}
    pantry = memory.list_pantry(user_id)

    source_text = infer_ingredients(query, ingredients_text, pantry)
    if not source_text:
        return {
            "status": "error",
            "message": "No ingredients found. Provide --ingredients or add pantry items first.",
        }

    parsed = run_subagent("ingredient_parser", ["--locale", os.environ.get("DEFAULT_LOCALE", "en-US")], stdin_text=source_text)
    parsed_items = parsed.get("data", [])
    canonical_ingredients = normalize_ingredient_list([item.get("canonical_name", "") for item in parsed_items])

    active_filters = dietary_filters or profile.get("dietary_restrictions", [])
    active_max_time = max_cook_time_minutes or profile.get("max_cook_time_minutes")

    retriever_args = ["--ingredients", *canonical_ingredients]
    if active_filters:
        retriever_args.extend(["--dietary-filters", ",".join(active_filters)])
    if active_max_time:
        retriever_args.extend(["--max-cook-time-minutes", str(active_max_time)])
    if cuisine:
        retriever_args.extend(["--cuisine", cuisine])
    if servings:
        retriever_args.extend(["--servings", str(servings)])
    if grounded_query:
        retriever_args.extend(["--grounded-query", grounded_query])

    retrieved = run_subagent("recipe_retriever", retriever_args)
    candidates = retrieved.get("data", [])

    ranker_args = [
        "--recipes",
        json.dumps(candidates),
        "--available-ingredients",
        *canonical_ingredients,
        "--user-preferences",
        json.dumps(profile),
    ]
    ranked_data = run_subagent("recipe_ranker", ranker_args)
    ranked = ranked_data.get("data", [])

    top_substitutions: List[Dict[str, Any]] = []
    if ranked:
        missing = ranked[0].get("missing_ingredients", [])
        if missing:
            sub_args = ["--missing-ingredients", *missing]
            if active_filters:
                sub_args.extend(["--dietary-restrictions", ",".join(active_filters)])
            sub_args.extend(["--available-ingredients", *canonical_ingredients])
            subs_data = run_subagent("substitution_advisor", sub_args)
            top_substitutions = subs_data.get("data", [])

    session = {
        "session_id": str(uuid.uuid4()),
        "query_text": query or "ingredient search",
        "parsed_ingredients": canonical_ingredients,
        "filters": {
            "dietary_filters": active_filters,
            "max_cook_time_minutes": active_max_time,
            "cuisine": cuisine,
            "servings": servings,
        },
        "result_recipe_ids": [recipe.get("id") for recipe in ranked],
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    memory.add_search_session(user_id, session)

    return {
        "status": "success",
        "query": query,
        "user_id": user_id,
        "ingredients": canonical_ingredients,
        "filters": session["filters"],
        "ranked_recipes": ranked,
        "top_recipe_substitutions": top_substitutions,
        "grounded_notes": retrieved.get("grounded_notes"),
    }


def handle_memory_ops(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    """Handle direct pantry/preferences operations from CLI flags."""
    store = MemoryStore()

    if args.pantry_op:
        if args.pantry_op == "list":
            return {"status": "success", "pantry": store.list_pantry(args.user_id)}
        if args.pantry_op == "clear":
            store.clear_pantry(args.user_id)
            return {"status": "success", "pantry": []}
        items = json.loads(args.pantry_items or "[]")
        if args.pantry_op == "add":
            pantry = store.add_pantry_items(args.user_id, items)
            return {"status": "success", "pantry": pantry}
        names: List[str] = []
        for item in items:
            if isinstance(item, dict) and item.get("ingredient_name"):
                names.append(str(item["ingredient_name"]))
            elif isinstance(item, str):
                names.append(item)
        pantry = store.remove_pantry_items(args.user_id, names)
        return {"status": "success", "pantry": pantry}

    if args.preferences_op:
        payload = json.loads(args.preferences or "{}")
        if args.preferences_op == "get":
            return {"status": "success", "preferences": store.get_profile(args.user_id)}
        if args.preferences_op == "set":
            return {"status": "success", "preferences": store.set_profile(args.user_id, payload)}
        if args.preferences_op == "update":
            return {"status": "success", "preferences": store.update_profile(args.user_id, payload)}
        return {"status": "success", "deleted": store.delete_profile(args.user_id)}

    return None


def print_readable(result: Dict[str, Any]) -> None:
    """Print user-friendly output for interactive usage."""
    if result.get("status") != "success":
        print(result.get("message") or result.get("error") or "Unknown error")
        return

    if "ranked_recipes" not in result:
        print(json.dumps(result, indent=2))
        return

    recipes = result.get("ranked_recipes", [])
    if not recipes:
        print("No recipes matched your request.")
        return

    print(f"Found {len(recipes)} recipe(s) for user '{result.get('user_id')}'.")
    for idx, recipe in enumerate(recipes[:5], start=1):
        missing = recipe.get("missing_ingredients", [])
        missing_text = ", ".join(missing) if missing else "none"
        print(
            f"{idx}. {recipe.get('title')} "
            f"(score={recipe.get('score')}, time={recipe.get('cook_time_minutes')}m, missing={missing_text})"
        )

    substitutions = result.get("top_recipe_substitutions") or []
    if substitutions:
        print("\nTop recipe substitution ideas:")
        for item in substitutions:
            subs = item.get("substitutions", [])
            if subs:
                best = subs[0]
                print(f"- {item.get('missing_ingredient')}: {best.get('substitute')} ({best.get('ratio')})")


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(description="Recipe Finder Agent")
    parser.add_argument("query", nargs="?", help="Single query for recipe finding")
    parser.add_argument("--chat", action="store_true", help="Interactive chat mode")
    parser.add_argument("--user-id", default="default", help="User identifier")
    parser.add_argument("--ingredients", help="Ingredient text (comma/newline separated)")
    parser.add_argument("--dietary-filters", nargs="*", default=None, help="Dietary filters")
    parser.add_argument("--cuisine", default=None)
    parser.add_argument("--max-cook-time-minutes", type=int, default=None)
    parser.add_argument("--servings", type=int, default=None)
    parser.add_argument("--grounded-query", default=None, help="Optional grounded web lookup prompt")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    parser.add_argument("--pantry-op", choices=["add", "remove", "list", "clear"], default=None)
    parser.add_argument("--pantry-items", default="[]", help="JSON array for pantry add/remove")
    parser.add_argument("--preferences-op", choices=["set", "get", "update", "delete"], default=None)
    parser.add_argument("--preferences", default="{}", help="JSON object for preferences set/update")

    return parser


def run_single(args: argparse.Namespace) -> int:
    """Run a single query or direct memory operation."""
    skills = load_skills()
    del skills

    try:
        memory_result = handle_memory_ops(args)
        if memory_result is not None:
            if args.json:
                print(json.dumps(memory_result, indent=2))
            else:
                print_readable(memory_result)
            return 0

        query = args.query or "Find recipes"
        result = run_recipe_flow(
            query=query,
            user_id=args.user_id,
            ingredients_text=args.ingredients,
            dietary_filters=args.dietary_filters,
            cuisine=args.cuisine,
            max_cook_time_minutes=args.max_cook_time_minutes,
            servings=args.servings,
            grounded_query=args.grounded_query,
        )
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print_readable(result)
        return 0 if result.get("status") == "success" else 1
    except Exception as exc:
        payload = {"status": "error", "error": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(str(exc))
        return 1


def run_chat(args: argparse.Namespace) -> int:
    """Run interactive chat mode."""
    print("Recipe Finder Agent chat mode. Type 'exit' to quit.")
    while True:
        try:
            line = input("recipe> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not line:
            continue
        if line.lower() in {"exit", "quit"}:
            return 0

        single_args = argparse.Namespace(
            query=line,
            chat=False,
            user_id=args.user_id,
            ingredients=args.ingredients,
            dietary_filters=args.dietary_filters,
            cuisine=args.cuisine,
            max_cook_time_minutes=args.max_cook_time_minutes,
            servings=args.servings,
            grounded_query=args.grounded_query,
            json=args.json,
            pantry_op=None,
            pantry_items="[]",
            preferences_op=None,
            preferences="{}",
        )
        run_single(single_args)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.chat:
        code = run_chat(args)
    else:
        code = run_single(args)
    sys.exit(code)


if __name__ == "__main__":
    main()
