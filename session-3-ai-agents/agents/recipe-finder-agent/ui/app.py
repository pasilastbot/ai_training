#!/usr/bin/env python3
"""Flask UI for recipe-finder-agent."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, redirect, render_template, request, url_for

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR))
sys.path.insert(0, str(AGENT_DIR / "memory"))

from agent_env import load_agent_environment
from memory import MemoryStore
from recipe_core import get_recipe_by_id, rank_recipe_candidates, search_candidate_recipes, suggest_substitutions_for_missing

load_agent_environment()

UI_DIR = Path(__file__).resolve().parent
app = Flask(
    __name__,
    template_folder=str(UI_DIR / "templates"),
    static_folder=str(UI_DIR / "static"),
)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET", "recipe-finder-secret")
app.config["PORT"] = int(os.environ.get("PORT", os.environ.get("FLASK_RUN_PORT", "5001")))

memory = MemoryStore()


def _split_csv(raw: str) -> List[str]:
    return [value.strip() for value in raw.split(",") if value.strip()]


@app.route("/", methods=["GET", "POST"])
def home_search_view() -> str:
    """Primary recipe search page."""
    if request.method == "POST":
        ingredients = request.form.get("ingredients", "")
        user_id = request.form.get("user_id", "default")
        dietary = request.form.get("dietary_filters", "")
        cuisine = request.form.get("cuisine") or ""
        max_time = request.form.get("max_cook_time_minutes") or ""
        return redirect(
            url_for(
                "results_view",
                user_id=user_id,
                ingredients=ingredients,
                dietary_filters=dietary,
                cuisine=cuisine,
                max_cook_time_minutes=max_time,
            )
        )

    return render_template("home_search_view.html")


@app.route("/results")
def results_view() -> str:
    """Ranked result list view."""
    user_id = request.args.get("user_id", "default")
    ingredients_raw = request.args.get("ingredients", "")
    ingredients = _split_csv(ingredients_raw)
    dietary = _split_csv(request.args.get("dietary_filters", ""))
    cuisine = request.args.get("cuisine") or None
    max_time_raw = request.args.get("max_cook_time_minutes")
    max_time = int(max_time_raw) if max_time_raw and max_time_raw.isdigit() else None

    profile = memory.get_profile(user_id) or {}
    candidates = search_candidate_recipes(
        ingredients=ingredients,
        dietary_filters=dietary or profile.get("dietary_restrictions"),
        max_cook_time_minutes=max_time or profile.get("max_cook_time_minutes"),
        cuisine=cuisine,
    )
    ranked = rank_recipe_candidates(candidates, ingredients, profile)

    return render_template(
        "results_view.html",
        recipes=ranked,
        ingredients=ingredients,
        user_id=user_id,
    )


@app.route("/recipe/<recipe_id>")
def recipe_detail_view(recipe_id: str) -> str:
    """Detailed recipe view with substitutions."""
    user_id = request.args.get("user_id", "default")
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        return render_template("recipe_detail_view.html", recipe=None, substitutions=[], user_id=user_id)

    pantry = memory.list_pantry(user_id)
    available = [item.get("ingredient_name", "") for item in pantry]
    available_set = {name.lower().strip() for name in available}
    missing = [item for item in recipe.get("ingredients", []) if item.lower().strip() not in available_set]

    profile = memory.get_profile(user_id) or {}
    substitutions = suggest_substitutions_for_missing(
        missing_ingredients=missing,
        dietary_restrictions=profile.get("dietary_restrictions", []),
        available_ingredients=available,
    )

    return render_template(
        "recipe_detail_view.html",
        recipe=recipe,
        substitutions=substitutions,
        user_id=user_id,
    )


@app.route("/pantry", methods=["GET", "POST"])
def pantry_manager_view() -> str:
    """Pantry management page."""
    user_id = request.values.get("user_id", "default")

    if request.method == "POST":
        action = request.form.get("action", "add")
        ingredient_name = request.form.get("ingredient_name", "").strip().lower()
        quantity_raw = request.form.get("quantity", "").strip()
        unit = request.form.get("unit", "").strip() or None

        if action == "remove" and ingredient_name:
            memory.remove_pantry_items(user_id, [ingredient_name])
        elif action == "clear":
            memory.clear_pantry(user_id)
        elif ingredient_name:
            quantity = float(quantity_raw) if quantity_raw else None
            memory.add_pantry_items(
                user_id,
                [
                    {
                        "ingredient_name": ingredient_name,
                        "quantity": quantity,
                        "unit": unit,
                    }
                ],
            )

    items = memory.list_pantry(user_id)
    return render_template("pantry_manager_view.html", user_id=user_id, items=items)


@app.route("/preferences", methods=["GET", "POST"])
def preferences_view() -> str:
    """Preferences settings page."""
    user_id = request.values.get("user_id", "default")
    profile: Dict[str, Any] = memory.get_profile(user_id) or {}

    if request.method == "POST":
        update = {
            "dietary_restrictions": _split_csv(request.form.get("dietary_restrictions", "")),
            "disliked_ingredients": _split_csv(request.form.get("disliked_ingredients", "")),
            "favorite_cuisines": _split_csv(request.form.get("favorite_cuisines", "")),
            "max_cook_time_minutes": int(request.form["max_cook_time_minutes"]) if request.form.get("max_cook_time_minutes") else None,
        }
        profile = memory.set_profile(user_id, update)

    return render_template("preferences_view.html", user_id=user_id, profile=profile)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"], debug=False)
