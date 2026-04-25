#!/usr/bin/env python3
"""
TES Agent API

FastAPI REST API for TES Agent operations.

Usage:
    uvicorn api.main:app --reload --port 8003
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_env import load_agent_environment
load_agent_environment()

from memory.memory import (
    get_tes, list_tes, search_tes, store_tes, get_stats,
    get_schema, get_salary_tables, init_database
)

from google import genai
from google.genai import types

# Import new tools
from tools.legal_references import (
    get_legal_references, get_all_references_for_tes,
    compare_to_statutory_minimum, LABOR_LAWS, TOPIC_TO_LAW
)
from tools.salary_calculators import (
    calculate_total_compensation, calculate_shift_work,
    calculate_overtime, compare_salaries, calculate_experience_progression,
    calculate_vacation_pay, calculate_part_time_salary,
    calculate_annual_employer_cost, get_tes_data
)

AGENT_DIR = Path(__file__).parent.parent
DEFAULT_MODEL = "gemini-3-flash-preview"

app = FastAPI(
    title="TES Agent API",
    description="API for Finnish Collective Bargaining Agreement (TES) management",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IndexRequest(BaseModel):
    query: str
    url: Optional[str] = None


class CompareRequest(BaseModel):
    tes_ids: List[str]
    fields: Optional[List[str]] = None


class SalaryRequest(BaseModel):
    tes_id: str
    role: str
    experience_years: int = 0
    use_ai: bool = False


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = None


class TotalCompensationRequest(BaseModel):
    tes_id: str
    base_salary: float
    evening_hours: int = 0
    night_hours: int = 0
    saturday_hours: int = 0
    sunday_hours: int = 0
    holiday_hours: int = 0
    daily_overtime: float = 0
    weekly_overtime: float = 0
    include_vacation_bonus: bool = True


class ShiftWorkRequest(BaseModel):
    tes_id: str
    hourly_rate: float
    evening_hours: int = 0
    night_hours: int = 0
    saturday_hours: int = 0
    sunday_hours: int = 0
    holiday_hours: int = 0


class OvertimeRequest(BaseModel):
    tes_id: str
    hourly_rate: float
    daily_overtime_hours: float = 0
    weekly_overtime_hours: float = 0


class SalaryCompareRequest(BaseModel):
    tes_names: List[str]
    job_group: Optional[str] = None
    experience_years: int = 0


class VacationPayRequest(BaseModel):
    tes_id: str
    monthly_salary: float
    employment_years: int = 1
    vacation_days: Optional[int] = None


class PartTimeRequest(BaseModel):
    tes_id: str
    full_time_salary: float
    weekly_hours: float


class EmployerCostRequest(BaseModel):
    tes_id: str
    monthly_salary: float
    include_shift_work: bool = False
    overtime_hours: int = 0
    sick_days: int = 10


class VectorSearchRequest(BaseModel):
    query: str
    num_results: int = 5
    tes_filter: Optional[str] = None


class TESData(BaseModel):
    id: Optional[str] = None
    name: str
    name_en: Optional[str] = None
    union: Optional[str] = None
    employer_org: Optional[str] = None
    industry: Optional[str] = None
    validity_start: Optional[str] = None
    validity_end: Optional[str] = None
    source_url: str
    salary_tables: Optional[List[dict]] = None
    working_hours: Optional[dict] = None
    vacation: Optional[dict] = None
    sick_leave: Optional[dict] = None
    notice_periods: Optional[dict] = None
    bonuses: Optional[dict] = None
    other_terms: Optional[dict] = None


def get_client() -> genai.Client:
    """Get Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    return genai.Client(api_key=api_key)


@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    try:
        init_database()
    except Exception as e:
        print(f"Database init warning: {e}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "tes-agent"
    }


@app.get("/stats")
async def stats():
    """Get database statistics."""
    return get_stats()


@app.get("/tes")
async def list_tes_endpoint(
    industry: Optional[str] = None,
    union: Optional[str] = None,
    valid_only: bool = False,
    limit: int = Query(default=100, le=500)
):
    """List all indexed TES documents."""
    results = list_tes(
        industry=industry,
        union=union,
        valid_only=valid_only,
        limit=limit
    )
    return {"count": len(results), "tes": results}


@app.get("/tes/{tes_id}")
async def get_tes_endpoint(tes_id: str):
    """Get a specific TES document by ID."""
    tes = get_tes(tes_id)
    if not tes:
        raise HTTPException(status_code=404, detail=f"TES not found: {tes_id}")
    return tes


@app.get("/tes/{tes_id}/salaries")
async def get_tes_salaries(tes_id: str):
    """Get salary tables for a specific TES."""
    tes = get_tes(tes_id)
    if not tes:
        raise HTTPException(status_code=404, detail=f"TES not found: {tes_id}")
    
    tables = get_salary_tables(tes_id)
    return {
        "tes_id": tes_id,
        "tes_name": tes.get("name"),
        "count": len(tables),
        "salary_tables": tables
    }


@app.get("/search")
async def search_tes_endpoint(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, le=100)
):
    """Search TES documents."""
    results = search_tes(q, limit=limit)
    return {"query": q, "count": len(results), "results": results}


@app.post("/tes/index")
async def index_tes_endpoint(request: IndexRequest):
    """Index a new TES document."""
    cmd = [
        sys.executable,
        str(AGENT_DIR / "subagents" / "tes_sourcing.py")
    ]
    
    if request.url:
        cmd.extend(["--url", request.url, "--name", request.query])
    else:
        cmd.extend(["--search", request.query])
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(AGENT_DIR))
    
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Indexing failed: {result.stderr[:500]}"
        )
    
    try:
        tes_data = json.loads(result.stdout)
        if "error" in tes_data:
            raise HTTPException(status_code=400, detail=tes_data["error"])
        
        store_result = store_tes(tes_data)
        return {
            "status": "indexed",
            "tes_id": tes_data.get("id"),
            "name": tes_data.get("name"),
            "stored": store_result
        }
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse result: {result.stdout[:500]}"
        )


@app.post("/tes")
async def store_tes_endpoint(data: TESData):
    """Store a TES document directly."""
    tes_dict = data.model_dump(exclude_none=True)
    result = store_tes(tes_dict)
    return result


@app.post("/compare")
async def compare_tes_endpoint(request: CompareRequest):
    """Compare multiple TES documents."""
    if len(request.tes_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 TES IDs to compare")
    
    cmd = [
        sys.executable,
        str(AGENT_DIR / "subagents" / "tes_comparison.py"),
        "--ids", ",".join(request.tes_ids),
        "--format", "markdown",
        "--summarize"
    ]
    
    if request.fields:
        cmd.extend(["--fields", ",".join(request.fields)])
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(AGENT_DIR))
    
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {result.stderr[:500]}"
        )
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse result: {result.stdout[:500]}"
        )


@app.post("/calculate-salary")
async def calculate_salary_endpoint(request: SalaryRequest):
    """Calculate salary based on TES rules."""
    cmd = [
        sys.executable,
        str(AGENT_DIR / "subagents" / "salary_calculator.py"),
        "--tes", request.tes_id,
        "--role", request.role,
        "--experience", str(request.experience_years)
    ]
    
    if request.use_ai:
        cmd.append("--ai")
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(AGENT_DIR))
    
    if result.returncode != 0:
        error_msg = result.stderr[:500] if result.stderr else result.stdout[:500]
        raise HTTPException(status_code=500, detail=f"Calculation failed: {error_msg}")
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse result: {result.stdout[:500]}"
        )


@app.get("/schema")
async def get_schema_endpoint():
    """Get the current TES schema."""
    return get_schema()


# =============================================================================
# LEGAL REFERENCE ENDPOINTS
# =============================================================================

@app.get("/legal/topics")
async def list_legal_topics():
    """List all available legal topics with their law references."""
    topics = {}
    for topic, refs in TOPIC_TO_LAW.items():
        topics[topic] = [{"law": law, "section": section} for law, section in refs]
    return {"topics": topics}


@app.get("/legal/laws")
async def list_labor_laws():
    """List all supported labor laws."""
    laws = []
    for code, law in LABOR_LAWS.items():
        laws.append({
            "code": code,
            "name": law["name"],
            "name_en": law["name_en"],
            "number": law["number"],
            "url": law["url"],
            "section_count": len(law["sections"])
        })
    return {"laws": laws}


@app.get("/legal/topic/{topic}")
async def get_topic_references(topic: str):
    """Get legal references for a specific topic."""
    refs = get_legal_references(topic)
    if not refs:
        raise HTTPException(status_code=404, detail=f"No references found for topic: {topic}")
    return {"topic": topic, "references": refs}


@app.get("/legal/tes/{tes_id}")
async def get_tes_legal_references(tes_id: str):
    """Get all legal references relevant to a TES document."""
    tes = get_tes(tes_id)
    if not tes:
        raise HTTPException(status_code=404, detail=f"TES not found: {tes_id}")
    
    refs = get_all_references_for_tes(tes)
    comparisons = compare_to_statutory_minimum(tes)
    
    return {
        "tes_id": tes_id,
        "tes_name": tes.get("name"),
        "legal_references": refs,
        "statutory_comparisons": comparisons
    }


# =============================================================================
# VECTOR SEARCH ENDPOINTS
# =============================================================================

@app.post("/vector/search")
async def vector_search_endpoint(request: VectorSearchRequest):
    """Semantic search across TES content."""
    try:
        from tools.vector_search import search, get_client
        client = get_client()
        results = search(request.query, request.num_results, request.tes_filter, client)
        return {"query": request.query, "results": results}
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Vector search not available: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vector/index/{tes_id}")
async def vector_index_tes(tes_id: str):
    """Index a TES document for vector search."""
    tes = get_tes(tes_id)
    if not tes:
        raise HTTPException(status_code=404, detail=f"TES not found: {tes_id}")
    
    try:
        from tools.vector_search import index_tes, get_client
        client = get_client()
        result = index_tes(tes.get("name", tes_id), tes, client)
        return result
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Vector search not available: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/vector/reindex")
async def vector_reindex_all():
    """Reindex all TES documents for vector search."""
    try:
        from tools.vector_search import reindex_all
        result = reindex_all()
        return result
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Vector search not available: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/vector/stats")
async def vector_stats():
    """Get vector database statistics."""
    try:
        from tools.vector_search import get_stats
        return get_stats()
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"Vector search not available: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SALARY CALCULATOR ENDPOINTS
# =============================================================================

@app.post("/calc/total-compensation")
async def calc_total_compensation(request: TotalCompensationRequest):
    """Calculate total compensation including all components."""
    tes_data = get_tes_data(request.tes_id) or get_tes(request.tes_id)
    if not tes_data:
        raise HTTPException(status_code=404, detail=f"TES not found: {request.tes_id}")
    
    shift_work = None
    if any([request.evening_hours, request.night_hours, request.saturday_hours, 
            request.sunday_hours, request.holiday_hours]):
        shift_work = {
            "evening_hours": request.evening_hours,
            "night_hours": request.night_hours,
            "saturday_hours": request.saturday_hours,
            "sunday_hours": request.sunday_hours,
            "holiday_hours": request.holiday_hours
        }
    
    overtime = None
    if request.daily_overtime or request.weekly_overtime:
        overtime = {
            "daily_overtime_hours": request.daily_overtime,
            "weekly_overtime_hours": request.weekly_overtime
        }
    
    result = calculate_total_compensation(
        request.base_salary, tes_data,
        shift_work=shift_work,
        overtime_hours=overtime,
        include_vacation_bonus=request.include_vacation_bonus
    )
    return result


@app.post("/calc/shift-work")
async def calc_shift_work(request: ShiftWorkRequest):
    """Calculate shift work compensation."""
    tes_data = get_tes_data(request.tes_id) or get_tes(request.tes_id)
    if not tes_data:
        raise HTTPException(status_code=404, detail=f"TES not found: {request.tes_id}")
    
    result = calculate_shift_work(
        request.hourly_rate, tes_data,
        evening_hours=request.evening_hours,
        night_hours=request.night_hours,
        saturday_hours=request.saturday_hours,
        sunday_hours=request.sunday_hours,
        holiday_hours=request.holiday_hours
    )
    return result


@app.post("/calc/overtime")
async def calc_overtime(request: OvertimeRequest):
    """Calculate overtime compensation."""
    tes_data = get_tes_data(request.tes_id) or get_tes(request.tes_id)
    if not tes_data:
        raise HTTPException(status_code=404, detail=f"TES not found: {request.tes_id}")
    
    result = calculate_overtime(
        request.hourly_rate, tes_data,
        daily_overtime_hours=request.daily_overtime_hours,
        weekly_overtime_hours=request.weekly_overtime_hours
    )
    return result


@app.post("/calc/compare-salaries")
async def calc_compare_salaries(request: SalaryCompareRequest):
    """Compare salaries across multiple TES agreements."""
    result = compare_salaries(
        request.tes_names,
        request.job_group,
        request.experience_years
    )
    return result


@app.get("/calc/progression/{tes_id}")
async def calc_experience_progression(
    tes_id: str,
    job_group: Optional[str] = None,
    max_years: int = Query(default=15, le=30)
):
    """Get salary progression based on experience."""
    result = calculate_experience_progression(tes_id, job_group, max_years)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/calc/vacation-pay")
async def calc_vacation_pay(request: VacationPayRequest):
    """Calculate vacation pay and bonus."""
    tes_data = get_tes_data(request.tes_id) or get_tes(request.tes_id)
    if not tes_data:
        raise HTTPException(status_code=404, detail=f"TES not found: {request.tes_id}")
    
    result = calculate_vacation_pay(
        request.monthly_salary, tes_data,
        request.employment_years, request.vacation_days
    )
    return result


@app.post("/calc/part-time")
async def calc_part_time(request: PartTimeRequest):
    """Calculate part-time pro-rata salary."""
    tes_data = get_tes_data(request.tes_id) or get_tes(request.tes_id)
    if not tes_data:
        raise HTTPException(status_code=404, detail=f"TES not found: {request.tes_id}")
    
    result = calculate_part_time_salary(
        request.full_time_salary, tes_data, request.weekly_hours
    )
    return result


@app.post("/calc/employer-cost")
async def calc_employer_cost(request: EmployerCostRequest):
    """Calculate total annual employer cost."""
    tes_data = get_tes_data(request.tes_id) or get_tes(request.tes_id)
    if not tes_data:
        raise HTTPException(status_code=404, detail=f"TES not found: {request.tes_id}")
    
    result = calculate_annual_employer_cost(
        request.monthly_salary, tes_data,
        include_shift_work=request.include_shift_work,
        estimated_overtime_hours=request.overtime_hours,
        estimated_sick_days=request.sick_days
    )
    return result


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat with the TES agent with logging."""
    client = get_client()
    
    import threading
    import queue
    
    log_queue = queue.Queue()
    result_holder = {"response": None, "error": None}
    
    def log_callback(msg):
        log_queue.put(msg)
    
    def run_agent():
        try:
            import importlib
            import tes_agent
            importlib.reload(tes_agent)  # Force reload to pick up latest changes
            response, _ = tes_agent.process_query(request.message, client, request.history, log_callback)
            result_holder["response"] = response
        except Exception as e:
            result_holder["error"] = str(e)
        finally:
            log_queue.put(None)  # Signal completion
    
    async def generate():
        # Start agent in background thread
        thread = threading.Thread(target=run_agent)
        thread.start()
        
        yield f"data: {json.dumps({'type': 'status', 'message': 'Starting agent...'})}\n\n"
        
        # Stream logs as they come
        while True:
            try:
                msg = log_queue.get(timeout=0.1)
                if msg is None:
                    break
                yield f"data: {json.dumps({'type': 'status', 'message': msg})}\n\n"
            except queue.Empty:
                continue
        
        thread.join()
        
        if result_holder["error"]:
            yield f"data: {json.dumps({'type': 'error', 'message': result_holder['error']})}\n\n"
        elif result_holder["response"]:
            yield f"data: {json.dumps({'type': 'response', 'message': result_holder['response']})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No response generated'})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
