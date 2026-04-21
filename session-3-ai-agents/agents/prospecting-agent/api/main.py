#!/usr/bin/env python3
"""
Prospecting Agent API

FastAPI REST API for the prospecting agent functionality.

Usage:
  uvicorn api.main:app --reload --port 8001

Or:
  python -m uvicorn api.main:app --reload --port 8001

Endpoints:
  GET  /health           - Health check
  GET  /icp              - Get current ICP
  POST /icp              - Update ICP
  POST /search           - Search for prospects
  POST /enrich           - Enrich a prospect
  GET  /prospects        - List prospects
  GET  /prospects/{id}   - Get specific prospect
  POST /prospects        - Store prospect(s)
  GET  /stats            - Get prospect statistics
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

# Add parent to path for imports
AGENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(AGENT_DIR / "memory"))

from memory import MemoryStore

# Initialize app
app = FastAPI(
    title="Prospecting Agent API",
    description="REST API for B2B prospect search and enrichment",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize memory store
memory = MemoryStore()


# ==================== Models ====================

class CompanySize(BaseModel):
    min_employees: Optional[int] = Field(None, ge=1)
    max_employees: Optional[int] = Field(None, ge=1)


class RevenueRange(BaseModel):
    min_usd: Optional[int] = Field(None, ge=0)
    max_usd: Optional[int] = Field(None, ge=0)


class Signals(BaseModel):
    hiring: Optional[bool] = None
    recent_funding: Optional[bool] = None
    tech_adoption: Optional[bool] = None
    growth: Optional[bool] = None


class ICPSchema(BaseModel):
    name: Optional[str] = "default"
    target_industries: List[str] = []
    company_size: Optional[CompanySize] = None
    revenue_range: Optional[RevenueRange] = None
    geography: List[str] = []
    keywords: List[str] = []
    technologies: List[str] = []
    exclusions: List[str] = []
    funding_stage: List[str] = []
    decision_makers: List[str] = []
    signals: Optional[Signals] = None


class SearchRequest(BaseModel):
    query: Optional[str] = None
    industries: Optional[List[str]] = None
    geography: Optional[List[str]] = None
    company_size: Optional[str] = None
    keywords: Optional[List[str]] = None
    use_icp: bool = True


class EnrichRequest(BaseModel):
    company_name: str
    website: Optional[str] = None
    industry: Optional[str] = None


class ProspectInput(BaseModel):
    id: Optional[str] = None
    company_name: str
    website: Optional[str] = None
    industry: Optional[str] = None
    sub_industry: Optional[str] = None
    description: Optional[str] = None
    employee_count: Optional[int] = None
    revenue_estimate_usd: Optional[int] = None
    funding_stage: Optional[str] = None
    headquarters: Optional[Dict[str, str]] = None
    technologies: Optional[List[str]] = None
    contacts: Optional[List[Dict]] = None
    signals: Optional[Dict] = None
    score: Optional[int] = Field(None, ge=0, le=100)
    status: str = "new"
    source: Optional[str] = None
    notes: Optional[str] = None


class ProspectFilter(BaseModel):
    status: Optional[str] = None
    industry: Optional[str] = None
    min_score: Optional[int] = Field(None, ge=0, le=100)
    max_score: Optional[int] = Field(None, ge=0, le=100)
    funding_stage: Optional[str] = None
    min_employees: Optional[int] = None
    max_employees: Optional[int] = None


# ==================== Helper Functions ====================

def run_subagent(name: str, args: List[str], input_data: Optional[str] = None) -> Dict[str, Any]:
    """Run a subagent and return its output."""
    subagent_path = AGENT_DIR / "subagents" / f"{name}.py"
    
    if not subagent_path.exists():
        raise HTTPException(status_code=500, detail=f"Subagent not found: {name}")
    
    cmd = ["python", str(subagent_path)] + args
    
    try:
        if input_data:
            result = subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(AGENT_DIR)
            )
        else:
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


def run_tool(name: str, args: List[str], input_data: Optional[str] = None) -> Dict[str, Any]:
    """Run a tool and return its output."""
    tool_path = AGENT_DIR / "tools" / f"{name}.py"
    
    if not tool_path.exists():
        raise HTTPException(status_code=500, detail=f"Tool not found: {name}")
    
    cmd = ["python", str(tool_path)] + args
    
    try:
        if input_data:
            result = subprocess.run(
                cmd + ["--stdin"],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(AGENT_DIR)
            )
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(AGENT_DIR)
            )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            raise HTTPException(status_code=500, detail=result.stderr or "Tool failed")
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Tool timed out")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid tool output")


# ==================== Endpoints ====================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "prospecting-agent"
    }


@app.get("/icp")
async def get_icp():
    """Get current ICP."""
    icp = memory.get_icp()
    if icp:
        return icp
    raise HTTPException(status_code=404, detail="No ICP defined")


@app.post("/icp")
async def update_icp(icp: ICPSchema):
    """Update ICP."""
    icp_dict = icp.model_dump(exclude_none=True)
    icp_dict["updated_at"] = datetime.utcnow().isoformat()
    
    if memory.set_icp(icp_dict):
        return {"status": "success", "icp": icp_dict}
    raise HTTPException(status_code=500, detail="Failed to update ICP")


@app.post("/search")
async def search_prospects(request: SearchRequest):
    """Search for prospects."""
    args = ["--pretty"]
    
    if request.query:
        args.extend(["--query", request.query])
    
    if request.use_icp:
        icp = memory.get_icp()
        if icp:
            # Use ICP criteria
            if request.industries:
                args.extend(["--industries", ",".join(request.industries)])
            elif icp.get("target_industries"):
                args.extend(["--industries", ",".join(icp["target_industries"])])
            
            if request.geography:
                args.extend(["--geography", ",".join(request.geography)])
            elif icp.get("geography"):
                args.extend(["--geography", ",".join(icp["geography"])])
            
            if request.keywords:
                args.extend(["--keywords", ",".join(request.keywords)])
            elif icp.get("keywords"):
                args.extend(["--keywords", ",".join(icp["keywords"])])
    else:
        if request.industries:
            args.extend(["--industries", ",".join(request.industries)])
        if request.geography:
            args.extend(["--geography", ",".join(request.geography)])
    
    if request.company_size:
        args.extend(["--size", request.company_size])
    
    return run_subagent("prospect_search", args)


@app.post("/enrich")
async def enrich_prospect(request: EnrichRequest):
    """Enrich a prospect."""
    args = ["--pretty"]
    
    args.extend(["--company", request.company_name])
    
    if request.website:
        args.extend(["--website", request.website])
    
    return run_subagent("prospect_enrich", args)


@app.get("/prospects")
async def list_prospects(
    status: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    max_score: Optional[int] = Query(None, ge=0, le=100),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List prospects with optional filters."""
    args = ["--pretty", "--limit", str(limit), "--offset", str(offset)]
    
    if search:
        args.extend(["--search", search])
    else:
        if status:
            args.extend(["--status", status])
        if industry:
            args.extend(["--industry", industry])
        if min_score is not None:
            args.extend(["--min-score", str(min_score)])
        if max_score is not None:
            args.extend(["--max-score", str(max_score)])
    
    return run_tool("retrieve_prospects", args)


@app.get("/prospects/{prospect_id}")
async def get_prospect(prospect_id: str):
    """Get a specific prospect by ID."""
    result = run_tool("retrieve_prospects", ["--id", prospect_id, "--pretty"])
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result.get("prospect", result)


@app.post("/prospects")
async def store_prospects(prospects: List[ProspectInput]):
    """Store one or more prospects."""
    prospects_data = [p.model_dump(exclude_none=True) for p in prospects]
    
    if len(prospects_data) == 1:
        return run_tool("store_prospect", [], input_data=json.dumps(prospects_data[0]))
    else:
        return run_tool("store_prospect", [], input_data=json.dumps(prospects_data))


@app.get("/stats")
async def get_stats():
    """Get prospect statistics."""
    return run_tool("retrieve_prospects", ["--stats", "--pretty"])


@app.post("/chat")
async def chat(message: Dict[str, str]):
    """Simple chat endpoint (non-streaming)."""
    from google import genai
    from google.genai import types
    
    api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    client = genai.Client(api_key=api_key)
    
    user_message = message.get("message", "")
    if not user_message:
        raise HTTPException(status_code=400, detail="Message required")
    
    # Simple response without function calling
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=f"""You are a helpful B2B prospecting assistant. Answer this question:

{user_message}

Keep your response concise and helpful.""",
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
    uvicorn.run(app, host="0.0.0.0", port=8001)
