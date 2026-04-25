#!/usr/bin/env python3
"""
Holiday Planner API

FastAPI REST API for the Holiday Planner agent.
Provides endpoints for family management, destination search, and trip planning.

Usage:
    uvicorn api.main:app --reload --port 8004
    # Or directly:
    python api/main.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_env import load_agent_environment
load_agent_environment()

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from memory.memory import (
    init_database, get_family, list_families, create_family, update_family,
    add_family_member, update_member_preferences, get_trip, list_trips,
    create_trip, update_trip, delete_trip, get_stats
)

app = FastAPI(
    title="Holiday Planner API",
    description="AI-powered family holiday planning assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Pydantic Models ============

class FamilyMember(BaseModel):
    name: str
    role: str = Field(..., pattern="^(adult|teen|child|toddler|infant|senior)$")
    age: Optional[int] = None


class CreateFamilyRequest(BaseModel):
    name: str
    members: Optional[list[FamilyMember]] = None


class AddMemberRequest(BaseModel):
    name: str
    role: str
    age: Optional[int] = None


class MemberPreferencesRequest(BaseModel):
    activity_types: Optional[list[str]] = None
    must_haves: Optional[list[str]] = None
    deal_breakers: Optional[list[str]] = None
    climate_preference: Optional[str] = None


class FamilyConstraintsRequest(BaseModel):
    budget_max: Optional[float] = None
    preferred_duration_days: Optional[int] = None
    departure_location: Optional[str] = None
    max_flight_hours: Optional[float] = None
    preferred_months: Optional[list[int]] = None


class DestinationSearchRequest(BaseModel):
    query: Optional[str] = None
    family_id: Optional[str] = None
    num_results: int = 5


class CreateTripRequest(BaseModel):
    name: str
    family_id: Optional[str] = None
    destinations: Optional[list[dict]] = None


class ItineraryRequest(BaseModel):
    destination: Optional[str] = None
    destinations: Optional[list[dict]] = None
    duration_days: int = 7
    family_id: Optional[str] = None
    pace: str = "balanced"
    priorities: Optional[list[str]] = None
    start_date: Optional[str] = None


class BudgetRequest(BaseModel):
    destination: str
    country: Optional[str] = None
    duration_days: int = 7
    adults: int = 2
    children: int = 0
    teens: int = 0
    travel_style: str = "mid-range"
    departure_city: str = "Helsinki"
    month: Optional[int] = None


class CompareRequest(BaseModel):
    destinations: list[str]
    duration_days: int = 7
    family_id: Optional[str] = None
    aspects: Optional[list[str]] = None


class ChatRequest(BaseModel):
    message: str
    family_id: Optional[str] = None
    history: Optional[list[dict]] = None


# ============ Startup ============

@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_database()


# ============ Health & Stats ============

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "holiday-planner"}


@app.get("/stats")
async def stats():
    """Get database statistics."""
    return get_stats()


# ============ Family Management ============

@app.get("/families")
async def get_families():
    """List all families."""
    return {"families": list_families()}


@app.post("/families")
async def create_family_endpoint(request: CreateFamilyRequest):
    """Create a new family profile."""
    members = [m.model_dump() for m in request.members] if request.members else None
    result = create_family(request.name, members)
    return result


@app.get("/families/{family_id}")
async def get_family_endpoint(family_id: str):
    """Get family profile by ID."""
    family = get_family(family_id)
    if not family:
        raise HTTPException(status_code=404, detail=f"Family not found: {family_id}")
    return family


@app.put("/families/{family_id}")
async def update_family_endpoint(family_id: str, updates: dict):
    """Update family profile."""
    result = update_family(family_id, updates)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/families/{family_id}/members")
async def add_member_endpoint(family_id: str, request: AddMemberRequest):
    """Add a member to a family."""
    result = add_family_member(family_id, request.model_dump())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.put("/families/{family_id}/members/{member_id}/preferences")
async def update_preferences_endpoint(
    family_id: str,
    member_id: str,
    request: MemberPreferencesRequest
):
    """Update member preferences."""
    result = update_member_preferences(family_id, member_id, request.model_dump(exclude_none=True))
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.put("/families/{family_id}/constraints")
async def set_constraints_endpoint(family_id: str, request: FamilyConstraintsRequest):
    """Set family constraints."""
    constraints = {}
    if request.budget_max:
        constraints["budget"] = {"max": request.budget_max, "currency": "EUR"}
    if request.preferred_duration_days:
        constraints["duration"] = {"preferred_days": request.preferred_duration_days}
    if request.departure_location:
        constraints["departure_location"] = request.departure_location
    if request.max_flight_hours:
        constraints["max_flight_hours"] = request.max_flight_hours
    if request.preferred_months:
        constraints["travel_dates"] = {"preferred_months": request.preferred_months}
    
    result = update_family(family_id, {"constraints": constraints})
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ============ Destinations ============

@app.post("/destinations/search")
async def search_destinations_endpoint(request: DestinationSearchRequest):
    """Search for destinations."""
    from tools.search_destinations import search_destinations
    
    family = get_family(request.family_id) if request.family_id else None
    return search_destinations(
        query=request.query,
        family_profile=family,
        num_results=request.num_results
    )


@app.get("/destinations/{destination}")
async def get_destination_endpoint(destination: str, country: Optional[str] = None):
    """Get destination details."""
    from tools.search_destinations import get_destination_details
    return get_destination_details(destination, country)


@app.get("/destinations/{destination}/activities")
async def get_activities_endpoint(
    destination: str,
    country: Optional[str] = None,
    family_id: Optional[str] = None,
    types: Optional[str] = None
):
    """Find activities at a destination."""
    from tools.find_activities import find_activities
    
    family = get_family(family_id) if family_id else None
    activity_types = types.split(",") if types else None
    
    return find_activities(
        destination,
        country,
        activity_types,
        family
    )


@app.get("/destinations/{destination}/weather")
async def get_weather_endpoint(
    destination: str,
    month: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get weather information."""
    from tools.weather_info import get_weather_info
    return get_weather_info(destination, month=month, start_date=start_date, end_date=end_date)


# ============ Budget ============

@app.post("/budget/estimate")
async def estimate_budget_endpoint(request: BudgetRequest):
    """Estimate trip budget."""
    from tools.budget_calculator import estimate_budget
    return estimate_budget(
        request.destination,
        request.country,
        request.duration_days,
        request.adults,
        request.children,
        request.teens,
        request.travel_style,
        request.departure_city,
        request.month
    )


@app.post("/budget/compare")
async def compare_budgets_endpoint(request: CompareRequest):
    """Compare budgets across destinations."""
    from tools.budget_calculator import compare_budgets
    
    adults = 2
    children = 0
    
    if request.family_id:
        family = get_family(request.family_id)
        if family:
            adults = sum(1 for m in family.get("members", []) if m.get("role") in ["adult", "senior"])
            children = sum(1 for m in family.get("members", []) if m.get("role") in ["child", "toddler", "infant"])
    
    return compare_budgets(
        request.destinations,
        request.duration_days,
        adults,
        children
    )


# ============ Trips ============

@app.get("/trips")
async def list_trips_endpoint(
    family_id: Optional[str] = None,
    status: Optional[str] = None
):
    """List trips."""
    return {"trips": list_trips(family_id, status)}


@app.post("/trips")
async def create_trip_endpoint(request: CreateTripRequest):
    """Create a new trip."""
    return create_trip(request.name, request.family_id, request.destinations)


@app.get("/trips/{trip_id}")
async def get_trip_endpoint(trip_id: str):
    """Get trip details."""
    trip = get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip not found: {trip_id}")
    return trip


@app.put("/trips/{trip_id}")
async def update_trip_endpoint(trip_id: str, updates: dict):
    """Update trip."""
    result = update_trip(trip_id, updates)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.delete("/trips/{trip_id}")
async def delete_trip_endpoint(trip_id: str):
    """Delete a trip."""
    return delete_trip(trip_id)


@app.post("/trips/{trip_id}/itinerary")
async def create_itinerary_endpoint(trip_id: str, request: ItineraryRequest):
    """Create itinerary for a trip."""
    from subagents.itinerary_planner import create_itinerary
    
    trip = get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Trip not found: {trip_id}")
    
    family = get_family(request.family_id) if request.family_id else None
    destinations = trip.get("destinations", [])
    
    if not destinations and request.destination:
        destinations = [{"name": request.destination, "duration_days": request.duration_days}]
    
    travel_dates = None
    if request.start_date:
        from datetime import datetime, timedelta
        start = datetime.strptime(request.start_date, "%Y-%m-%d")
        end = start + timedelta(days=request.duration_days - 1)
        travel_dates = {
            "start": request.start_date,
            "end": end.strftime("%Y-%m-%d")
        }
    
    itinerary = create_itinerary(
        destinations,
        request.duration_days,
        family,
        travel_dates,
        request.pace,
        request.priorities
    )
    
    if "error" not in itinerary:
        update_trip(trip_id, {"itinerary": itinerary})
    
    return itinerary


# ============ Comparison ============

@app.post("/compare")
async def compare_endpoint(request: CompareRequest):
    """Compare destinations or trips."""
    from tools.compare_options import compare_trips
    from tools.search_destinations import get_destination_details
    
    trips = []
    for dest in request.destinations:
        details = get_destination_details(dest)
        trips.append({
            "name": dest,
            "destinations": [details] if details else [{"name": dest}],
            "budget": details.get("budget_estimate", {}) if details else {}
        })
    
    family = get_family(request.family_id) if request.family_id else None
    return compare_trips(trips, family, request.aspects)


@app.post("/compare/weather")
async def compare_weather_endpoint(request: CompareRequest):
    """Compare weather across destinations."""
    from tools.weather_info import get_best_time_to_visit
    family = get_family(request.family_id) if request.family_id else None
    return get_best_time_to_visit(request.destinations, family)


# ============ Wish Aggregation ============

@app.post("/families/{family_id}/wishes/aggregate")
async def aggregate_wishes_endpoint(family_id: str):
    """Aggregate family wishes."""
    from subagents.wish_aggregator import aggregate_wishes
    result = aggregate_wishes(family_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/families/{family_id}/wishes/questionnaire")
async def get_questionnaire_endpoint(family_id: str, language: str = "en"):
    """Get wish collection questionnaire."""
    from subagents.wish_aggregator import generate_questionnaire
    return generate_questionnaire(family_id, language)


# ============ Chat ============

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat with the holiday planner agent."""
    from google import genai
    from holiday_planner import process_query, get_client
    
    try:
        client = get_client()
        response, _ = process_query(
            request.message,
            client,
            request.family_id,
            request.history
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Streaming chat with the holiday planner agent."""
    from google import genai
    from holiday_planner import process_query, get_client
    
    async def generate():
        try:
            client = get_client()
            
            logs = []
            def log_callback(msg):
                logs.append({"type": "log", "message": msg})
            
            response, _ = process_query(
                request.message,
                client,
                request.family_id,
                request.history,
                log_callback
            )
            
            for log in logs:
                yield f"data: {json.dumps(log)}\n\n"
            
            yield f"data: {json.dumps({'type': 'response', 'content': response})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


# ============ Main ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
