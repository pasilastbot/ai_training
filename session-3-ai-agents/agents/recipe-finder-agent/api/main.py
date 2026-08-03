#!/usr/bin/env python3
"""FastAPI API for recipe-finder-agent."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

AGENT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_DIR))
sys.path.insert(0, str(AGENT_DIR / "memory"))

from agent_env import load_agent_environment
from memory import MemoryStore
from recipe_core import (
    get_recipe_by_id,
    rank_recipe_candidates,
    search_candidate_recipes,
    suggest_substitutions_for_missing,
)

load_agent_environment()


app = FastAPI(
    title="Recipe Finder Agent API",
    version="1.0.0",
    description="Find, rank, and personalize recipes from available ingredients.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory = MemoryStore()


def _dump(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)
    return model.dict(exclude_none=True)


class RecipeFindRequest(BaseModel):
    user_id: str = "default"
    ingredients: List[str]
    dietary_filters: Optional[List[str]] = None
    max_cook_time_minutes: Optional[int] = None
    cuisine: Optional[str] = None
    servings: Optional[int] = None


class RecipeRankRequest(BaseModel):
    user_id: str = "default"
    recipes: List[Dict[str, Any]]
    available_ingredients: List[str]
    user_preferences: Optional[Dict[str, Any]] = None


class SubstitutionRequest(BaseModel):
    missing_ingredients: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    available_ingredients: Optional[List[str]] = None


class PantryUpsertRequest(BaseModel):
    items: List[Dict[str, Any]]


class PreferenceRequest(BaseModel):
    dietary_restrictions: Optional[List[str]] = None
    disliked_ingredients: Optional[List[str]] = None
    favorite_cuisines: Optional[List[str]] = None
    max_cook_time_minutes: Optional[int] = None


class InteractionRequest(BaseModel):
    recipe_id: str
    action: str
    rating: Optional[int] = None
    timestamp: Optional[str] = None


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint for monitoring."""
    return {"status": "ok"}


@app.post("/recipes/find")
async def find_recipes(payload: RecipeFindRequest) -> Dict[str, Any]:
    """Find recipes from provided ingredients and optional filters."""
    profile = memory.get_profile(payload.user_id) or {}
    dietary_filters = payload.dietary_filters or profile.get("dietary_restrictions")
    max_time = payload.max_cook_time_minutes or profile.get("max_cook_time_minutes")

    candidates = search_candidate_recipes(
        ingredients=payload.ingredients,
        dietary_filters=dietary_filters,
        max_cook_time_minutes=max_time,
        cuisine=payload.cuisine,
        servings=payload.servings,
    )
    ranked = rank_recipe_candidates(candidates, payload.ingredients, profile)

    memory.add_search_session(
        payload.user_id,
        {
            "query_text": "find recipes",
            "parsed_ingredients": payload.ingredients,
            "filters": {
                "dietary_filters": dietary_filters,
                "max_cook_time_minutes": max_time,
                "cuisine": payload.cuisine,
                "servings": payload.servings,
            },
            "result_recipe_ids": [recipe.get("id") for recipe in ranked],
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        },
    )

    return {
        "count": len(ranked),
        "recipes": ranked,
    }


@app.post("/recipes/rank")
async def rank_recipes(payload: RecipeRankRequest) -> Dict[str, Any]:
    """Rank candidate recipes for a specific user context."""
    prefs = payload.user_preferences or memory.get_profile(payload.user_id) or {}
    ranked = rank_recipe_candidates(payload.recipes, payload.available_ingredients, prefs)
    return {"count": len(ranked), "recipes": ranked}


@app.get("/recipes/{recipe_id}")
async def get_recipe(recipe_id: str, include_nutrition: bool = True) -> Dict[str, Any]:
    """Fetch detailed recipe instructions and metadata."""
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if not include_nutrition and "nutrition" in recipe:
        recipe.pop("nutrition")
    return recipe


@app.post("/recipes/{recipe_id}/substitutions")
async def get_substitutions(recipe_id: str, payload: SubstitutionRequest) -> Dict[str, Any]:
    """Get substitutions for missing or restricted ingredients for a recipe."""
    recipe = get_recipe_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    missing = payload.missing_ingredients
    available = payload.available_ingredients or []
    if missing is None:
        available_set = {item.lower().strip() for item in available}
        missing = [
            ingredient for ingredient in recipe.get("ingredients", [])
            if ingredient.lower().strip() not in available_set
        ]

    suggestions = suggest_substitutions_for_missing(
        missing_ingredients=missing,
        dietary_restrictions=payload.dietary_restrictions,
        available_ingredients=available,
    )
    return {
        "recipe_id": recipe_id,
        "missing_ingredients": missing,
        "substitutions": suggestions,
    }


@app.get("/users/{user_id}/pantry")
async def get_user_pantry(user_id: str) -> Dict[str, Any]:
    """Get user pantry inventory."""
    items = memory.list_pantry(user_id)
    return {"user_id": user_id, "items": items, "count": len(items)}


@app.post("/users/{user_id}/pantry")
async def upsert_user_pantry(user_id: str, payload: PantryUpsertRequest) -> Dict[str, Any]:
    """Add or update pantry items."""
    items = memory.add_pantry_items(user_id, payload.items)
    return {"user_id": user_id, "items": items, "count": len(items)}


@app.delete("/users/{user_id}/pantry/{ingredient}")
async def delete_user_pantry_item(user_id: str, ingredient: str) -> Dict[str, Any]:
    """Remove ingredient from pantry."""
    items = memory.remove_pantry_items(user_id, [ingredient])
    return {"user_id": user_id, "items": items, "count": len(items)}


@app.get("/users/{user_id}/preferences")
async def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """Get stored user preferences."""
    profile = memory.get_profile(user_id)
    if not profile:
        return {
            "user_id": user_id,
            "dietary_restrictions": [],
            "disliked_ingredients": [],
            "favorite_cuisines": [],
            "max_cook_time_minutes": None,
        }
    return profile


@app.put("/users/{user_id}/preferences")
async def put_user_preferences(user_id: str, payload: PreferenceRequest) -> Dict[str, Any]:
    """Create or update user preferences."""
    profile = memory.set_profile(user_id, _dump(payload))
    return profile


@app.post("/users/{user_id}/interactions")
async def post_interaction(user_id: str, payload: InteractionRequest) -> Dict[str, Any]:
    """Record recipe interaction events for personalization."""
    interaction = memory.add_interaction(user_id, _dump(payload))
    return {"status": "recorded", "interaction": interaction}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", os.environ.get("API_PORT", "8001")))
    uvicorn.run(app, host="0.0.0.0", port=port)
