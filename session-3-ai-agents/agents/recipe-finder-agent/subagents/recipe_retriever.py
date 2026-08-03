#!/usr/bin/env python3
"""Subagent for recipe search and grounded lookups."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR))

from agent_env import load_agent_environment
from recipe_core import search_candidate_recipes

load_agent_environment()


def _csv(raw: str) -> List[str]:
    return [chunk.strip() for chunk in raw.split(",") if chunk.strip()]


def _try_grounded_lookup(query: str) -> Optional[str]:
    """Use Gemini built-in grounding tools when configured."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)
        tools = [
            types.Tool(google_search=types.GoogleSearch()),
            types.Tool(url_context=types.UrlContext()),
        ]
        config = types.GenerateContentConfig(
            tools=tools,
            include_server_side_tool_invocations=True,
            temperature=0.2,
        )
        prompt = (
            "Find reliable recipe ideas relevant to this request and return a short summary "
            "of the best directions to explore. Request: " + query
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt, config=config)
        return (response.text or "").strip() if hasattr(response, "text") else None
    except Exception:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Recipe retriever subagent")
    parser.add_argument("--ingredients", nargs="+", required=True)
    parser.add_argument("--dietary-filters", default="")
    parser.add_argument("--max-cook-time-minutes", type=int, default=None)
    parser.add_argument("--cuisine", default=None)
    parser.add_argument("--servings", type=int, default=None)
    parser.add_argument("--grounded-query", default="")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    recipes = search_candidate_recipes(
        ingredients=args.ingredients,
        dietary_filters=_csv(args.dietary_filters) if args.dietary_filters else None,
        max_cook_time_minutes=args.max_cook_time_minutes,
        cuisine=args.cuisine,
        servings=args.servings,
    )

    grounded_notes = _try_grounded_lookup(args.grounded_query) if args.grounded_query else None

    out: Dict[str, Any] = {
        "status": "success",
        "subagent": "recipe_retriever",
        "count": len(recipes),
        "data": recipes,
    }
    if grounded_notes:
        out["grounded_notes"] = grounded_notes

    if args.pretty:
        print(json.dumps(out, indent=2))
    else:
        print(json.dumps(out))


if __name__ == "__main__":
    main()
