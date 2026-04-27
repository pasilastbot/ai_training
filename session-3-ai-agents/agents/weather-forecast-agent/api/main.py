#!/usr/bin/env python3
"""
Weather Forecast Agent API

FastAPI REST API for weather information and recommendations.

Usage:
  uvicorn api.main:app --reload --port 8003

Endpoints:
  GET  /health                     - Health check
  GET  /weather/{location}         - Get current weather
  GET  /forecast/{location}        - Get forecast
  GET  /activities/{location}      - Get activity recommendations
  GET  /alerts/{location}          - Get weather alerts
  GET  /locations                  - List saved locations
  POST /locations                  - Add a location
  DELETE /locations/{name}         - Remove a location
  POST /chat                       - Chat with the agent
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import subprocess

AGENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(AGENT_DIR))
from agent_env import load_agent_environment

load_agent_environment()
sys.path.insert(0, str(AGENT_DIR / "memory"))

from memory import MemoryStore

app = FastAPI(
    title="Weather Forecast Agent API",
    description="REST API for weather information and recommendations",
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

class LocationInput(BaseModel):
    name: str = Field(..., description="Location nickname (e.g., 'Home', 'Work')")
    location: str = Field(..., description="City name or coordinates")
    lat: Optional[float] = Field(None, description="Latitude")
    lon: Optional[float] = Field(None, description="Longitude")
    timezone: Optional[str] = Field(None, description="Timezone")


class ChatMessage(BaseModel):
    message: str
    units: Optional[str] = Field("metric", pattern="^(metric|imperial)$")


class ForecastRequest(BaseModel):
    days: int = Field(5, ge=1, le=7, description="Number of days (1-7)")
    units: Optional[str] = Field("metric", pattern="^(metric|imperial)$")


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
        "service": "weather-forecast-agent"
    }


# ---- Weather ----

@app.get("/weather/{location}")
async def get_weather(
    location: str,
    units: str = Query("metric", pattern="^(metric|imperial)$"),
    use_cache: bool = Query(True, description="Use cached data if available")
):
    """Get current weather for a location."""
    if use_cache:
        cached = memory.get_cached_weather(location)
        if cached:
            return {
                "location": location,
                "source": "cache",
                "weather": cached
            }
    
    result = run_subagent("weather_search", [
        "--location", location,
        "--units", units,
        "--pretty"
    ])
    
    weather = result.get("weather")
    if weather and not weather.get("error"):
        memory.cache_weather(location, weather)
    
    return result


@app.get("/forecast/{location}")
async def get_forecast(
    location: str,
    days: int = Query(5, ge=1, le=7),
    units: str = Query("metric", pattern="^(metric|imperial)$")
):
    """Get multi-day forecast for a location."""
    result = run_subagent("weather_search", [
        "--location", location,
        "--days", str(days),
        "--units", units,
        "--pretty"
    ])
    
    return result


@app.get("/alerts/{location}")
async def get_alerts(location: str):
    """Get weather alerts for a location."""
    result = run_subagent("alert_checker", [
        "--location", location,
        "--pretty"
    ])
    
    return result


@app.get("/activities/{location}")
async def get_activities(
    location: str,
    units: str = Query("metric", pattern="^(metric|imperial)$")
):
    """Get activity recommendations based on weather."""
    weather_result = run_subagent("weather_search", [
        "--location", location,
        "--units", units,
        "--pretty"
    ])
    
    weather = weather_result.get("weather", {})
    
    if not weather or weather.get("error"):
        return weather_result
    
    alert_result = get_alerts(location)
    alerts = alert_result.get("alerts", [])
    
    from google import genai
    from google.genai import types
    
    api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    client = genai.Client(api_key=api_key)
    
    weather_context = json.dumps(weather, indent=2)
    alert_context = json.dumps(alerts, indent=2) if alerts else "No active alerts"
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=f"""You are a weather activity recommendation expert. Based on the current weather conditions, suggest appropriate outdoor activities.

Current weather for {location}:
{weather_context}

Weather alerts:
{alert_context}

Provide:
1. 3-5 recommended activities suitable for current conditions
2. What to wear or bring
3. Any weather-related considerations or warnings
4. When conditions might be better (if poor)

Be concise and practical. Format as a clear list.""",
        config=types.GenerateContentConfig()
    )
    
    text = ""
    try:
        text = response.candidates[0].content.parts[0].text
    except:
        text = "Could not generate recommendations"
    
    return {
        "location": location,
        "weather": weather,
        "alerts": alerts,
        "recommendations": text
    }


# ---- Locations ----

@app.get("/locations")
async def list_locations():
    """Get all saved locations."""
    locations = memory.get_locations()
    return {
        "count": len(locations),
        "locations": locations
    }


@app.post("/locations")
async def add_location(loc: LocationInput):
    """Add a new saved location."""
    coordinates = None
    if loc.lat is not None and loc.lon is not None:
        coordinates = {"lat": loc.lat, "lon": loc.lon}
    
    result = memory.store_location(
        name=loc.name,
        location=loc.location,
        coordinates=coordinates,
        timezone=loc.timezone
    )
    
    if result.get("status") != "success":
        raise HTTPException(status_code=500, detail="Failed to store location")
    
    return result


@app.delete("/locations/{name}")
async def delete_location(name: str):
    """Remove a saved location."""
    result = memory.delete_location(name)
    
    if result.get("status") != "success":
        raise HTTPException(status_code=404, detail=result.get("message", "Location not found"))
    
    return result


# ---- Stats ----

@app.get("/stats")
async def get_stats():
    """Get usage statistics."""
    stats = memory.get_stats()
    return stats


# ---- Chat ----

@app.post("/chat")
async def chat(msg: ChatMessage):
    """Chat with the weather agent."""
    from google import genai
    from google.genai import types
    
    api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    client = genai.Client(api_key=api_key)
    
    locations = memory.get_locations()
    locations_context = f"\n\nUser's saved locations: {json.dumps(locations)}" if locations else ""
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=f"""You are a helpful weather assistant. Answer this question:

{msg.message}
{locations_context}

Keep your response concise and helpful. If they need weather data, summarize what you find.""",
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
    uvicorn.run(app, host="0.0.0.0", port=8003)