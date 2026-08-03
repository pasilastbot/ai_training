#!/usr/bin/env python3
"""
Energy Advisor API

FastAPI REST API for the Energy Advisor agent.
Provides endpoints for energy advice, apartment management, and video responses.

Usage:
    uvicorn api.main:app --reload --port 8005
    # Or directly:
    python api/main.py
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_env import load_agent_environment
load_agent_environment()

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field

from memory.memory import (
    init_database, get_apartment, get_apartment_by_customer, list_apartments,
    create_apartment, update_apartment, search_apartments, get_apartment_summary,
    get_recommendations, create_recommendation, get_stats, store_video_response,
    get_recent_video_responses
)

app = FastAPI(
    title="Energy Advisor API",
    description="AI-powered building energy advisor with Leanheat Building expertise",
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

class CreateApartmentRequest(BaseModel):
    customer_id: str
    customer_name: Optional[str] = None
    city: Optional[str] = None
    building_type: Optional[str] = Field(None, pattern="^(apartment|house|townhouse|row_house|commercial|office)$")
    size_sqm: Optional[float] = None
    heating_type: Optional[str] = Field(None, pattern="^(district_heating|electric|heat_pump|oil|gas|geothermal)$")
    construction_year: Optional[int] = None
    has_smart_controls: Optional[bool] = False


class UpdateApartmentRequest(BaseModel):
    customer_name: Optional[str] = None
    city: Optional[str] = None
    size_sqm: Optional[float] = None
    annual_heating_kwh: Optional[float] = None
    annual_cost_eur: Optional[float] = None
    preferred_temp_c: Optional[float] = None
    residents_count: Optional[int] = None
    energy_class: Optional[str] = None
    notes: Optional[str] = None


class CreateRecommendationRequest(BaseModel):
    apartment_id: str
    recommendation_type: str = Field(..., pattern="^(temperature_optimization|smart_controls|insulation|behavior_change|equipment_upgrade|demand_response)$")
    title: str
    description: Optional[str] = None
    estimated_savings_percent: Optional[float] = None
    estimated_savings_eur: Optional[float] = None
    priority: str = "medium"


class ChatRequest(BaseModel):
    message: str
    apartment_id: Optional[str] = None
    customer_id: Optional[str] = None
    history: Optional[list[dict]] = None
    generate_video: bool = False


class VideoRequest(BaseModel):
    script: str
    voice: str = "Puck (Male)"
    language: str = "English (US)"


class KnowledgeSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    use_google_fallback: bool = True


# ============ Startup ============

@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    init_database()


# ============ Health & Stats ============

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "energy-advisor"}


@app.get("/stats")
async def stats():
    """Get system statistics."""
    return get_stats()


# ============ Apartment Management ============

@app.get("/apartments")
async def get_apartments(limit: int = 50):
    """List all apartments."""
    return {"apartments": list_apartments(limit)}


@app.post("/apartments")
async def create_apartment_endpoint(request: CreateApartmentRequest):
    """Create a new apartment."""
    result = create_apartment(
        customer_id=request.customer_id,
        customer_name=request.customer_name,
        address={"city": request.city} if request.city else None,
        building_info={
            "building_type": request.building_type,
            "construction_year": request.construction_year
        } if request.building_type or request.construction_year else None,
        apartment_details={"size_sqm": request.size_sqm} if request.size_sqm else None,
        heating_system={
            "type": request.heating_type,
            "has_smart_controls": request.has_smart_controls
        } if request.heating_type else None
    )
    return result


@app.get("/apartments/{apartment_id}")
async def get_apartment_endpoint(apartment_id: str):
    """Get apartment details."""
    apartment = get_apartment(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail=f"Apartment not found: {apartment_id}")
    return apartment


@app.get("/apartments/{apartment_id}/summary")
async def get_apartment_summary_endpoint(apartment_id: str):
    """Get apartment summary for AI context."""
    summary = get_apartment_summary(apartment_id)
    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])
    return summary


@app.put("/apartments/{apartment_id}")
async def update_apartment_endpoint(apartment_id: str, request: UpdateApartmentRequest):
    """Update apartment details."""
    updates = {}
    
    if request.customer_name:
        updates["customer_name"] = request.customer_name
    if request.city:
        updates["address"] = {"city": request.city}
    if request.size_sqm:
        updates["apartment_details"] = {"size_sqm": request.size_sqm}
    if request.annual_heating_kwh or request.annual_cost_eur or request.energy_class:
        updates["energy_consumption"] = {}
        if request.annual_heating_kwh:
            updates["energy_consumption"]["annual_heating_kwh"] = request.annual_heating_kwh
        if request.annual_cost_eur:
            updates["energy_consumption"]["annual_cost_eur"] = request.annual_cost_eur
        if request.energy_class:
            updates["energy_consumption"]["energy_class"] = request.energy_class
    if request.preferred_temp_c:
        updates["preferences"] = {"preferred_temp_c": request.preferred_temp_c}
    if request.residents_count:
        updates["occupancy"] = {"residents_count": request.residents_count}
    if request.notes:
        updates["notes"] = request.notes
    
    result = update_apartment(apartment_id, updates)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.get("/apartments/search/{query}")
async def search_apartments_endpoint(query: str, limit: int = 20):
    """Search apartments."""
    return {"results": search_apartments(query, limit)}


@app.get("/apartments/customer/{customer_id}")
async def get_apartment_by_customer_endpoint(customer_id: str):
    """Get apartment by customer ID."""
    apartment = get_apartment_by_customer(customer_id)
    if not apartment:
        raise HTTPException(status_code=404, detail=f"No apartment found for customer: {customer_id}")
    return apartment


# ============ Recommendations ============

@app.get("/apartments/{apartment_id}/recommendations")
async def get_recommendations_endpoint(apartment_id: str):
    """Get recommendations for an apartment."""
    return {"recommendations": get_recommendations(apartment_id)}


@app.post("/recommendations")
async def create_recommendation_endpoint(request: CreateRecommendationRequest):
    """Create a new recommendation."""
    return create_recommendation(
        apartment_id=request.apartment_id,
        recommendation_type=request.recommendation_type,
        title=request.title,
        description=request.description,
        estimated_savings_eur=request.estimated_savings_eur,
        estimated_savings_percent=request.estimated_savings_percent,
        priority=request.priority
    )


# ============ Knowledge Search ============

@app.post("/knowledge/search")
async def search_knowledge_endpoint(request: KnowledgeSearchRequest):
    """Search Leanheat knowledge base."""
    from subagents.knowledge_search import search_knowledge
    return search_knowledge(
        request.query,
        use_google_fallback=request.use_google_fallback,
        synthesize=True
    )


# ============ Video Responses ============

@app.post("/video/generate")
async def generate_video_endpoint(request: VideoRequest, background_tasks: BackgroundTasks):
    """Generate a video response."""
    from tools.generate_video_response import generate_video_response
    
    result = generate_video_response(
        script=request.script,
        voice=request.voice,
        language=request.language
    )
    
    if result.get("status") == "success":
        store_video_response(
            question="API request",
            answer=request.script,
            video_path=result.get("video_path")
        )
    
    return result


@app.get("/video/recent")
async def get_recent_videos(limit: int = 10):
    """Get recent video responses."""
    return {"videos": get_recent_video_responses(limit)}


@app.get("/video/{video_id}")
async def get_video_file(video_id: str):
    """Stream a video file."""
    from memory.memory import AGENT_DIR
    
    video_dir = AGENT_DIR / "memory" / "data" / "videos"
    video_path = video_dir / f"{video_id}.mp4"
    
    if not video_path.exists():
        video_path = video_dir / video_id
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(video_path, media_type="video/mp4")


# ============ Chat ============

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat with the energy advisor."""
    from google import genai
    from energy_advisor import process_query, get_client
    
    try:
        client = get_client()
        response, _, video = process_query(
            request.message,
            client,
            request.apartment_id,
            request.customer_id,
            request.history,
            request.generate_video
        )
        
        result = {"response": response}
        if video and video.get("status") == "success":
            result["video"] = video
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Streaming chat with the energy advisor."""
    from energy_advisor import process_query, get_client
    
    async def generate():
        try:
            client = get_client()
            
            logs = []
            def log_callback(msg):
                logs.append({"type": "log", "message": msg})
            
            response, _, video = process_query(
                request.message,
                client,
                request.apartment_id,
                request.customer_id,
                request.history,
                request.generate_video,
                log_callback
            )
            
            for log in logs:
                yield f"data: {json.dumps(log)}\n\n"
            
            result = {"type": "response", "content": response}
            if video and video.get("status") == "success":
                result["video"] = video
            
            yield f"data: {json.dumps(result)}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


# ============ Main ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
