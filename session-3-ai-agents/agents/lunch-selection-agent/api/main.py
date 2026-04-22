#!/usr/bin/env python3
"""
Lunch Selection Agent API

FastAPI REST API for the lunch selection agent functionality.

Usage:
  uvicorn api.main:app --reload --port 8002

Or:
  python -m uvicorn api.main:app --reload --port 8002

Endpoints:
  GET  /health              - Health check
  GET  /preferences         - Get user preferences
  POST /preferences         - Update preferences
  GET  /restaurants         - List restaurants
  GET  /restaurants/{id}    - Get specific restaurant
  POST /restaurants         - Store restaurant(s)
  POST /restaurants/search  - Search for restaurants in city
  POST /restaurants/{id}/menu - Extract menu for restaurant
  GET  /selections          - List past selections
  POST /selections          - Record a selection
  GET  /recommend           - Get lunch recommendation
  POST /chat                - Chat with the agent
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

AGENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(AGENT_DIR))
from agent_env import load_agent_environment

load_agent_environment()
sys.path.insert(0, str(AGENT_DIR / "memory"))

from memory import MemoryStore

app = FastAPI(
    title="Lunch Selection Agent API",
    description="REST API for lunch restaurant discovery and recommendations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory = MemoryStore()


# ==================== Models ====================

class PreferencesInput(BaseModel):
    liked_cuisines: Optional[List[str]] = None
    disliked_cuisines: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    avoided_ingredients: Optional[List[str]] = None
    price_preference: Optional[str] = Field(None, pattern="^(budget|moderate|expensive|any)$")
    spice_tolerance: Optional[str] = Field(None, pattern="^(none|mild|medium|hot|extra-hot)$")
    variety_preference: Optional[str] = Field(None, pattern="^(stick-to-favorites|balanced|adventurous)$")


class RestaurantInput(BaseModel):
    name: str
    city: str
    address: Optional[str] = None
    website: Optional[str] = None
    menu_url: Optional[str] = None
    cuisine_types: Optional[List[str]] = None
    price_range: Optional[str] = Field(None, pattern="^(budget|moderate|expensive)$")
    average_price: Optional[float] = None
    features: Optional[List[str]] = None


class RestaurantSearchRequest(BaseModel):
    city: str
    cuisine: Optional[str] = None
    query: Optional[str] = None


class MenuExtractionRequest(BaseModel):
    url: Optional[str] = None


class SelectionInput(BaseModel):
    restaurant_name: str
    dish_name: str
    restaurant_id: Optional[str] = None
    dish_description: Optional[str] = None
    cuisine_type: Optional[str] = None
    price: Optional[float] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    would_order_again: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    city: Optional[str] = None
    date: Optional[str] = None
    was_recommendation: bool = False


class ChatMessage(BaseModel):
    message: str
    city: Optional[str] = None


# ==================== Helper Functions ====================

def run_subagent(name: str, args: List[str]) -> Dict[str, Any]:
    """Run a subagent and return its output."""
    subagent_path = AGENT_DIR / "subagents" / f"{name}.py"
    
    if not subagent_path.exists():
        raise HTTPException(status_code=500, detail=f"Subagent not found: {name}")
    
    cmd = ["python", str(subagent_path)] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(AGENT_DIR)
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            raise HTTPException(status_code=500, detail=result.stderr or "Subagent failed")
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Subagent timed out")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid subagent output")


# ==================== Endpoints ====================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "lunch-selection-agent"
    }


# ---- Preferences ----

@app.get("/preferences")
async def get_preferences():
    """Get user preferences."""
    prefs = memory.get_preferences()
    if prefs:
        return prefs
    return {"message": "No preferences set", "user_id": "default"}


@app.post("/preferences")
async def update_preferences(prefs: PreferencesInput):
    """Update user preferences."""
    current = memory.get_preferences() or {"user_id": "default"}
    
    update_data = prefs.model_dump(exclude_none=True)
    current.update(update_data)
    
    if memory.set_preferences(current):
        return {"status": "success", "preferences": current}
    raise HTTPException(status_code=500, detail="Failed to update preferences")


# ---- Restaurants ----

@app.get("/restaurants")
async def list_restaurants(
    city: Optional[str] = Query(None),
    cuisine: Optional[str] = Query(None),
    price_range: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """List restaurants with optional filters."""
    if search:
        restaurants = memory.search_restaurants(search, limit)
        return {"query": search, "count": len(restaurants), "restaurants": restaurants}
    
    restaurants = memory.get_restaurants(
        city=city,
        cuisine=cuisine,
        price_range=price_range,
        limit=limit
    )
    return {
        "count": len(restaurants),
        "restaurants": restaurants,
        "filters": {"city": city, "cuisine": cuisine, "price_range": price_range}
    }


@app.get("/restaurants/stats")
async def get_restaurant_stats():
    """Get restaurant statistics."""
    stats = memory.get_stats()
    return {
        "total_restaurants": stats["total_restaurants"],
        "restaurants_by_city": stats["restaurants_by_city"],
        "cuisines": stats["cuisines"]
    }


@app.get("/restaurants/{restaurant_id}")
async def get_restaurant(restaurant_id: str):
    """Get a specific restaurant by ID."""
    restaurant = memory.get_restaurant(restaurant_id)
    if restaurant:
        return restaurant
    raise HTTPException(status_code=404, detail="Restaurant not found")


@app.post("/restaurants")
async def store_restaurants(restaurants: List[RestaurantInput]):
    """Store one or more restaurants."""
    results = []
    for r in restaurants:
        data = r.model_dump(exclude_none=True)
        result = memory.store_restaurant(data)
        results.append({"name": r.name, **result})
    
    return {"stored": len(results), "results": results}


@app.post("/restaurants/search")
async def search_restaurants(request: RestaurantSearchRequest):
    """Search for restaurants in a city using the search subagent."""
    args = ["--city", request.city, "--pretty"]
    if request.cuisine:
        args.extend(["--cuisine", request.cuisine])
    if request.query:
        args.extend(["--query", request.query])
    
    result = run_subagent("restaurant_search", args)
    
    stored_count = 0
    for restaurant in result.get("restaurants", []):
        restaurant["city"] = request.city
        memory.store_restaurant(restaurant)
        stored_count += 1
    
    result["stored_count"] = stored_count
    return result


@app.post("/restaurants/{restaurant_id}/menu")
async def extract_menu(restaurant_id: str, request: MenuExtractionRequest):
    """Extract today's menu for a restaurant."""
    restaurant = memory.get_restaurant(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    url = request.url or restaurant.get("menu_url") or restaurant.get("website")
    if not url:
        raise HTTPException(status_code=400, detail="No URL available for this restaurant")
    
    args = ["--url", url, "--name", restaurant.get("name", ""), "--pretty"]
    result = run_subagent("menu_extractor", args)
    
    if "dishes" in result and not result.get("error"):
        memory.update_restaurant_menu(restaurant_id, result)
        result["cached"] = True
    
    return result


# ---- Selections ----

@app.get("/selections")
async def list_selections(
    days: Optional[int] = Query(None, ge=1),
    restaurant_id: Optional[str] = Query(None),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    limit: int = Query(50, ge=1, le=200)
):
    """List past lunch selections."""
    selections = memory.get_selections(
        days=days,
        restaurant_id=restaurant_id,
        min_rating=min_rating,
        limit=limit
    )
    return {"count": len(selections), "selections": selections}


@app.post("/selections")
async def record_selection(selection: SelectionInput):
    """Record a lunch selection."""
    data = selection.model_dump(exclude_none=True)
    result = memory.store_selection(data)
    return {
        "restaurant": selection.restaurant_name,
        "dish": selection.dish_name,
        **result
    }


# ---- Recommendations ----

@app.get("/recommend")
async def get_recommendation(
    city: str = Query(..., description="City to get recommendation for"),
    exclude_days: int = Query(7, ge=1, le=30, description="Exclude dishes from last N days")
):
    """Get a personalized lunch recommendation."""
    from lunch_selection_agent import build_recommendation
    
    result = build_recommendation(city, memory, exclude_days)
    return result


# ---- Chat ----

@app.post("/chat")
async def chat(msg: ChatMessage):
    """Chat with the lunch selection agent."""
    from google import genai
    from google.genai import types
    
    api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    client = genai.Client(api_key=api_key)
    
    message = msg.message
    if msg.city:
        message = f"[City: {msg.city}] {message}"
    
    prefs = memory.get_preferences()
    prefs_context = f"\nUser preferences: {json.dumps(prefs)}" if prefs else ""
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=f"""You are a helpful lunch selection assistant. Answer this question:

{message}
{prefs_context}

Keep your response concise and helpful. Focus on lunch recommendations.""",
        config=types.GenerateContentConfig(
            tools=[
                types.Tool(google_search=types.GoogleSearch()),
                types.Tool(url_context=types.UrlContext())
            ]
        )
    )
    
    text = ""
    try:
        text = response.candidates[0].content.parts[0].text
    except:
        text = "I couldn't generate a response."
    
    return {"response": text}


# ==================== Run ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
