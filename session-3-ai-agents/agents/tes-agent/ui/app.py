#!/usr/bin/env python3
"""
TES Agent Web UI

Flask-based web interface for TES Agent.

Usage:
    python app.py
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_env import load_agent_environment
load_agent_environment()

from memory.memory import (
    get_tes, list_tes, search_tes, store_tes, get_stats,
    get_schema, get_salary_tables, init_database
)

AGENT_DIR = Path(__file__).parent.parent

app = Flask(__name__)
CORS(app)

try:
    init_database()
except:
    pass


def run_subagent(name: str, args: list) -> dict:
    """Run a subagent and return result."""
    cmd = [sys.executable, str(AGENT_DIR / "subagents" / f"{name}.py")] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(AGENT_DIR))
    
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"error": "Parse error", "output": result.stdout[:1000]}
    return {"error": result.stderr[:500] or "Unknown error"}


@app.route("/")
def index():
    """Dashboard page."""
    stats = get_stats()
    recent_tes = list_tes(limit=5)
    
    valid_count = stats.get("valid_tes", 0)
    expiring_soon = []
    
    return render_template("index.html",
        stats=stats,
        recent_tes=recent_tes,
        valid_count=valid_count,
        expiring_soon=expiring_soon
    )


@app.route("/tes")
def tes_list():
    """TES list page."""
    industry = request.args.get("industry")
    union = request.args.get("union")
    valid_only = request.args.get("valid_only") == "true"
    
    tes_docs = list_tes(industry=industry, union=union, valid_only=valid_only, limit=100)
    
    industries = set()
    unions = set()
    for t in list_tes(limit=500):
        if t.get("industry"):
            industries.add(t["industry"])
        if t.get("union_name"):
            unions.add(t["union_name"])
    
    return render_template("tes_list.html",
        tes_docs=tes_docs,
        industries=sorted(industries),
        unions=sorted(unions),
        filters={
            "industry": industry,
            "union": union,
            "valid_only": valid_only
        }
    )


@app.route("/tes/<tes_id>")
def tes_detail(tes_id: str):
    """TES detail page."""
    tes = get_tes(tes_id)
    if not tes:
        return render_template("error.html", error="TES not found"), 404
    
    salary_tables = get_salary_tables(tes_id)
    
    return render_template("tes_detail.html",
        tes=tes,
        salary_tables=salary_tables
    )


@app.route("/chat")
def chat():
    """Chat page."""
    return render_template("chat.html")


@app.route("/compare")
def compare():
    """Comparison page."""
    tes_docs = list_tes(limit=100)
    return render_template("compare.html", tes_docs=tes_docs)


@app.route("/calculator")
def calculator():
    """Salary calculator page (legacy)."""
    tes_docs = list_tes(limit=100)
    return render_template("calculator.html", tes_docs=tes_docs)


@app.route("/calculators")
def calculators():
    """Comprehensive salary calculators page."""
    return render_template("calculators.html")


@app.route("/legal")
def legal():
    """Legal cross-references page."""
    return render_template("legal.html")


@app.route("/search")
def search():
    """Semantic search page."""
    return render_template("search.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Chat API endpoint with streaming and logging."""
    import threading
    import queue
    
    data = request.json
    message = data.get("message", "")
    history = data.get("history", [])
    
    log_queue = queue.Queue()
    result_holder = {"response": None, "error": None}
    
    def log_callback(msg):
        log_queue.put(msg)
    
    def run_agent(client):
        try:
            from tes_agent import process_query
            response, _ = process_query(message, client, history, log_callback)
            result_holder["response"] = response
        except Exception as e:
            result_holder["error"] = str(e)
        finally:
            log_queue.put(None)  # Signal completion
    
    def generate():
        try:
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting agent...'})}\n\n"
            
            from google import genai
            
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY")
            if not api_key:
                yield f"data: {json.dumps({'type': 'error', 'message': 'API key not configured'})}\n\n"
                return
            
            client = genai.Client(api_key=api_key)
            
            # Start agent in background thread
            thread = threading.Thread(target=run_agent, args=(client,))
            thread.start()
            
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
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/search")
def api_search():
    """Search API."""
    q = request.args.get("q", "")
    results = search_tes(q, limit=20)
    return jsonify({"query": q, "count": len(results), "results": results})


@app.route("/api/index", methods=["POST"])
def api_index():
    """Index new TES."""
    data = request.json
    query = data.get("query", "")
    url = data.get("url")
    
    args = ["--url", url, "--name", query] if url else ["--search", query]
    result = run_subagent("tes_sourcing", args)
    
    if "error" not in result:
        store_result = store_tes(result)
        return jsonify({
            "status": "indexed",
            "tes_id": result.get("id"),
            "name": result.get("name"),
            "stored": store_result
        })
    
    return jsonify(result), 400


@app.route("/api/compare", methods=["POST"])
def api_compare():
    """Compare TES documents."""
    data = request.json
    tes_ids = data.get("tes_ids", [])
    fields = data.get("fields")
    
    if len(tes_ids) < 2:
        return jsonify({"error": "Need at least 2 TES IDs"}), 400
    
    args = ["--ids", ",".join(tes_ids), "--format", "markdown", "--summarize"]
    if fields:
        args.extend(["--fields", ",".join(fields)])
    
    result = run_subagent("tes_comparison", args)
    return jsonify(result)


@app.route("/api/calculate", methods=["POST"])
def api_calculate():
    """Calculate salary."""
    data = request.json
    tes_id = data.get("tes_id", "")
    role = data.get("role", "")
    experience = data.get("experience", 0)
    use_ai = data.get("use_ai", False)
    
    args = ["--tes", tes_id, "--role", role, "--experience", str(experience)]
    if use_ai:
        args.append("--ai")
    
    result = run_subagent("salary_calculator", args)
    return jsonify(result)


# =============================================================================
# API Proxy endpoints (forward to FastAPI backend on port 8003)
# =============================================================================

import requests

API_BASE = "http://localhost:8003"

def proxy_get(path):
    """Proxy GET request to FastAPI."""
    try:
        resp = requests.get(f"{API_BASE}{path}", timeout=30)
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

def proxy_post(path, data):
    """Proxy POST request to FastAPI."""
    try:
        resp = requests.post(f"{API_BASE}{path}", json=data, timeout=60)
        return jsonify(resp.json()), resp.status_code
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tes")
def api_tes_list():
    """List TES documents."""
    tes_docs = list_tes(limit=100)
    return jsonify({"count": len(tes_docs), "tes": tes_docs})


@app.route("/api/tes/<tes_id>")
def api_tes_get(tes_id):
    """Get TES document."""
    tes = get_tes(tes_id)
    if not tes:
        return jsonify({"error": "TES not found"}), 404
    return jsonify(tes)


# Legal References API
@app.route("/api/legal/topics")
def api_legal_topics():
    return proxy_get("/legal/topics")


@app.route("/api/legal/laws")
def api_legal_laws():
    return proxy_get("/legal/laws")


@app.route("/api/legal/topic/<topic>")
def api_legal_topic(topic):
    return proxy_get(f"/legal/topic/{topic}")


@app.route("/api/legal/tes/<tes_id>")
def api_legal_tes(tes_id):
    return proxy_get(f"/legal/tes/{tes_id}")


# Vector Search API
@app.route("/api/vector/search", methods=["POST"])
def api_vector_search():
    return proxy_post("/vector/search", request.json)


@app.route("/api/vector/index/<tes_id>", methods=["POST"])
def api_vector_index(tes_id):
    return proxy_post(f"/vector/index/{tes_id}", {})


@app.route("/api/vector/reindex", methods=["POST"])
def api_vector_reindex():
    return proxy_post("/vector/reindex", {})


@app.route("/api/vector/stats")
def api_vector_stats():
    return proxy_get("/vector/stats")


# Salary Calculator APIs
@app.route("/api/calc/total-compensation", methods=["POST"])
def api_calc_total():
    return proxy_post("/calc/total-compensation", request.json)


@app.route("/api/calc/shift-work", methods=["POST"])
def api_calc_shift():
    return proxy_post("/calc/shift-work", request.json)


@app.route("/api/calc/overtime", methods=["POST"])
def api_calc_overtime():
    return proxy_post("/calc/overtime", request.json)


@app.route("/api/calc/compare-salaries", methods=["POST"])
def api_calc_compare():
    return proxy_post("/calc/compare-salaries", request.json)


@app.route("/api/calc/progression/<tes_id>")
def api_calc_progression(tes_id):
    job_group = request.args.get("job_group", "")
    max_years = request.args.get("max_years", "15")
    path = f"/calc/progression/{tes_id}?max_years={max_years}"
    if job_group:
        path += f"&job_group={job_group}"
    return proxy_get(path)


@app.route("/api/calc/vacation-pay", methods=["POST"])
def api_calc_vacation():
    return proxy_post("/calc/vacation-pay", request.json)


@app.route("/api/calc/part-time", methods=["POST"])
def api_calc_parttime():
    return proxy_post("/calc/part-time", request.json)


@app.route("/api/calc/employer-cost", methods=["POST"])
def api_calc_employer():
    return proxy_post("/calc/employer-cost", request.json)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
