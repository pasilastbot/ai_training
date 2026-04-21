#!/usr/bin/env python3
"""
Prospecting Agent Web UI

Flask-based web interface for the prospecting agent.

Usage:
  python ui/app.py
  # Or: FLASK_APP=ui/app.py flask run --port 5001

Open http://localhost:5001 in your browser.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS

# Add parent to path for imports
AGENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(AGENT_DIR / "memory"))

from memory import MemoryStore

# Initialize app
app = Flask(__name__)
CORS(app)

# Initialize memory store
memory = MemoryStore()


# ==================== Helper Functions ====================

def run_subagent(name: str, args: list, input_data: str = None) -> dict:
    """Run a subagent and return its output."""
    subagent_path = AGENT_DIR / "subagents" / f"{name}.py"
    
    if not subagent_path.exists():
        return {"error": f"Subagent not found: {name}"}
    
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
            return {"error": result.stderr or "Subagent failed"}
    except subprocess.TimeoutExpired:
        return {"error": "Subagent timed out"}
    except json.JSONDecodeError:
        return {"error": "Invalid subagent output", "raw": result.stdout}
    except Exception as e:
        return {"error": str(e)}


def run_tool(name: str, args: list, input_data: str = None) -> dict:
    """Run a tool and return its output."""
    tool_path = AGENT_DIR / "tools" / f"{name}.py"
    
    if not tool_path.exists():
        return {"error": f"Tool not found: {name}"}
    
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
            return {"error": result.stderr or "Tool failed"}
    except subprocess.TimeoutExpired:
        return {"error": "Tool timed out"}
    except json.JSONDecodeError:
        return {"error": "Invalid tool output", "raw": result.stdout}
    except Exception as e:
        return {"error": str(e)}


# ==================== Routes ====================

@app.route("/")
def index():
    """Dashboard home page."""
    # Get ICP
    icp = memory.get_icp() or {}
    
    # Get prospect stats
    stats = run_tool("retrieve_prospects", ["--stats"])
    
    # Get recent prospects
    recent = run_tool("retrieve_prospects", ["--limit", "10", "--pretty"])
    prospects = recent.get("prospects", []) if isinstance(recent, dict) else []
    
    return render_template("index.html",
        icp=icp,
        stats=stats if isinstance(stats, dict) else {},
        prospects=prospects
    )


@app.route("/search", methods=["GET", "POST"])
def search():
    """Prospect search page."""
    results = None
    query = ""
    
    if request.method == "POST":
        query = request.form.get("query", "")
        industries = request.form.get("industries", "")
        geography = request.form.get("geography", "")
        size = request.form.get("size", "")
        
        args = ["--pretty"]
        
        if query:
            args.extend(["--query", query])
        if industries:
            args.extend(["--industries", industries])
        if geography:
            args.extend(["--geography", geography])
        if size:
            args.extend(["--size", size])
        
        # Load ICP for context
        icp = memory.get_icp()
        if icp and not industries and icp.get("target_industries"):
            args.extend(["--industries", ",".join(icp["target_industries"])])
        if icp and not geography and icp.get("geography"):
            args.extend(["--geography", ",".join(icp["geography"])])
        
        results = run_subagent("prospect_search", args)
    
    icp = memory.get_icp() or {}
    return render_template("search.html", results=results, query=query, icp=icp)


@app.route("/prospects")
def prospects():
    """Prospects list page."""
    status = request.args.get("status", "")
    industry = request.args.get("industry", "")
    min_score = request.args.get("min_score", "")
    search_query = request.args.get("q", "")
    
    args = ["--pretty", "--limit", "50"]
    
    if search_query:
        args.extend(["--search", search_query])
    else:
        if status:
            args.extend(["--status", status])
        if industry:
            args.extend(["--industry", industry])
        if min_score:
            args.extend(["--min-score", min_score])
    
    result = run_tool("retrieve_prospects", args)
    prospects_list = result.get("prospects", []) if isinstance(result, dict) else []
    
    return render_template("prospects.html", 
        prospects=prospects_list,
        filters={"status": status, "industry": industry, "min_score": min_score, "q": search_query}
    )


@app.route("/prospects/<prospect_id>")
def prospect_detail(prospect_id):
    """Prospect detail page."""
    result = run_tool("retrieve_prospects", ["--id", prospect_id, "--pretty"])
    
    if "error" in result:
        return render_template("error.html", error=result["error"])
    
    prospect = result.get("prospect", result)
    return render_template("prospect_detail.html", prospect=prospect)


@app.route("/prospects/<prospect_id>/enrich", methods=["POST"])
def enrich_prospect(prospect_id):
    """Enrich a prospect."""
    # Get current prospect
    current = run_tool("retrieve_prospects", ["--id", prospect_id, "--pretty"])
    if "error" in current:
        return jsonify(current), 400
    
    prospect = current.get("prospect", current)
    
    # Run enrichment
    args = ["--pretty"]
    if prospect.get("company_name"):
        args.extend(["--company", prospect["company_name"]])
    if prospect.get("website"):
        args.extend(["--website", prospect["website"]])
    
    result = run_subagent("prospect_enrich", args)
    
    if "error" not in result:
        # Store enriched data
        result["id"] = prospect_id
        run_tool("store_prospect", [], input_data=json.dumps(result))
    
    return redirect(url_for("prospect_detail", prospect_id=prospect_id))


@app.route("/icp", methods=["GET", "POST"])
def icp_page():
    """ICP management page."""
    if request.method == "POST":
        # Update ICP
        icp = {
            "name": request.form.get("name", "default"),
            "target_industries": [i.strip() for i in request.form.get("industries", "").split(",") if i.strip()],
            "geography": [g.strip() for g in request.form.get("geography", "").split(",") if g.strip()],
            "keywords": [k.strip() for k in request.form.get("keywords", "").split(",") if k.strip()],
            "exclusions": [e.strip() for e in request.form.get("exclusions", "").split(",") if e.strip()],
            "funding_stage": [f.strip() for f in request.form.getlist("funding_stage") if f.strip()],
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Company size
        min_emp = request.form.get("min_employees", "")
        max_emp = request.form.get("max_employees", "")
        if min_emp or max_emp:
            icp["company_size"] = {}
            if min_emp:
                icp["company_size"]["min_employees"] = int(min_emp)
            if max_emp:
                icp["company_size"]["max_employees"] = int(max_emp)
        
        memory.set_icp(icp)
        return redirect(url_for("icp_page"))
    
    icp = memory.get_icp() or {}
    return render_template("icp.html", icp=icp)


@app.route("/chat")
def chat_page():
    """Chat interface for the prospecting agent."""
    icp = memory.get_icp() or {}
    return render_template("chat.html", icp=icp)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """API endpoint for chat with the agent (non-streaming fallback)."""
    data = request.get_json() or {}
    message = data.get("message", "")
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    # Run the main agent with the query
    agent_path = AGENT_DIR / "prospecting_agent.py"
    
    try:
        result = subprocess.run(
            ["python", str(agent_path), message],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(AGENT_DIR),
            env={**os.environ}
        )
        
        if result.returncode == 0:
            return jsonify({
                "response": result.stdout.strip(),
                "status": "success"
            })
        else:
            return jsonify({
                "response": result.stderr or "Agent encountered an error",
                "status": "error"
            })
    except subprocess.TimeoutExpired:
        return jsonify({
            "response": "Request timed out. The agent is still processing. Please try again.",
            "status": "timeout"
        })
    except Exception as e:
        return jsonify({
            "response": f"Error: {str(e)}",
            "status": "error"
        })


# Chat history storage (file-based for persistence)
CHAT_HISTORY_FILE = AGENT_DIR / "memory" / "data" / "chat_history.json"

def load_chat_history():
    """Load chat history from file."""
    try:
        if CHAT_HISTORY_FILE.exists():
            with open(CHAT_HISTORY_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_chat_history(history):
    """Save chat history to file."""
    try:
        CHAT_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CHAT_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving chat history: {e}")

@app.route("/api/chat/clear", methods=["POST"])
def api_chat_clear():
    """Clear chat history."""
    save_chat_history([])
    return jsonify({"status": "cleared"})

@app.route("/api/chat/stream", methods=["POST"])
def api_chat_stream():
    """Streaming API endpoint for chat with real-time status updates."""
    from flask import Response, stream_with_context
    import select
    
    data = request.get_json() or {}
    message = data.get("message", "")
    clear_history = data.get("clear_history", False)
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    # Load or clear history
    if clear_history:
        chat_history = []
    else:
        chat_history = load_chat_history()
    
    # Add user message to history
    chat_history.append({"role": "user", "content": message})
    
    # Keep last 10 exchanges (20 messages) to avoid context being too long
    if len(chat_history) > 20:
        chat_history = chat_history[-20:]
    
    # Save updated history
    save_chat_history(chat_history)
    
    # Build conversation context from history
    history_context = ""
    if len(chat_history) > 1:
        history_context = "CONVERSATION HISTORY (continue from this context):\n"
        for msg in chat_history[:-1]:  # Exclude current message
            role = "User" if msg["role"] == "user" else "Agent"
            # Truncate long messages in history
            content = msg["content"][:800] + "..." if len(msg["content"]) > 800 else msg["content"]
            history_context += f"{role}: {content}\n\n"
        history_context += "---\nContinue the conversation. Reference previous context when relevant.\n\n"
    
    # Combine history context with current message
    full_message = history_context + "CURRENT REQUEST: " + message if history_context else message
    
    def generate():
        agent_path = AGENT_DIR / "prospecting_agent.py"
        
        # Start the agent process with full conversation context
        process = subprocess.Popen(
            ["python", "-u", str(agent_path), full_message],  # -u for unbuffered output
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(AGENT_DIR),
            env={**os.environ},
            bufsize=1
        )
        
        yield f"data: {json.dumps({'type': 'status', 'message': '🚀 Starting agent...'})}\n\n"
        
        import threading
        import queue
        
        output_queue = queue.Queue()
        final_response = []
        
        def read_output(pipe, prefix):
            for line in iter(pipe.readline, ''):
                if line:
                    output_queue.put((prefix, line.strip()))
            pipe.close()
        
        # Start threads to read stdout and stderr
        stdout_thread = threading.Thread(target=read_output, args=(process.stdout, 'out'))
        stderr_thread = threading.Thread(target=read_output, args=(process.stderr, 'err'))
        stdout_thread.start()
        stderr_thread.start()
        
        # Stream output as it comes
        while stdout_thread.is_alive() or stderr_thread.is_alive() or not output_queue.empty():
            try:
                prefix, line = output_queue.get(timeout=0.1)
                
                # Detect status messages vs final response
                if prefix == 'err':
                    # Status/debug messages go to stderr
                    if 'Calling function' in line or 'function:' in line.lower():
                        yield f"data: {json.dumps({'type': 'tool', 'message': f'🔧 {line}'})}\n\n"
                    elif 'search' in line.lower():
                        yield f"data: {json.dumps({'type': 'status', 'message': f'🔍 {line}'})}\n\n"
                    elif 'enrich' in line.lower():
                        yield f"data: {json.dumps({'type': 'status', 'message': f'📊 {line}'})}\n\n"
                    elif 'store' in line.lower() or 'saving' in line.lower():
                        yield f"data: {json.dumps({'type': 'status', 'message': f'💾 {line}'})}\n\n"
                    elif 'error' in line.lower() or 'warning' in line.lower():
                        yield f"data: {json.dumps({'type': 'error', 'message': f'⚠️ {line}'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'status', 'message': f'ℹ️ {line}'})}\n\n"
                else:
                    # stdout is the final response
                    final_response.append(line)
                    
            except queue.Empty:
                continue
        
        stdout_thread.join()
        stderr_thread.join()
        process.wait()
        
        # Send the final response
        response_text = '\n'.join(final_response) if final_response else "No response from agent"
        
        # Save agent response to history
        try:
            current_history = load_chat_history()
            current_history.append({"role": "assistant", "content": response_text})
            # Keep last 20 messages
            if len(current_history) > 20:
                current_history = current_history[-20:]
            save_chat_history(current_history)
        except Exception as e:
            print(f"Error saving response to history: {e}")
        
        yield f"data: {json.dumps({'type': 'response', 'message': response_text})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route("/api/search", methods=["POST"])
def api_search():
    """API endpoint for search (AJAX)."""
    data = request.get_json() or {}
    
    args = ["--pretty"]
    if data.get("query"):
        args.extend(["--query", data["query"]])
    if data.get("industries"):
        args.extend(["--industries", data["industries"]])
    if data.get("geography"):
        args.extend(["--geography", data["geography"]])
    
    result = run_subagent("prospect_search", args)
    return jsonify(result)


@app.route("/api/enrich", methods=["POST"])
def api_enrich():
    """API endpoint for enrichment (AJAX)."""
    data = request.get_json() or {}
    
    args = ["--pretty"]
    if data.get("company_name"):
        args.extend(["--company", data["company_name"]])
    if data.get("website"):
        args.extend(["--website", data["website"]])
    
    result = run_subagent("prospect_enrich", args)
    return jsonify(result)


@app.route("/api/store", methods=["POST"])
def api_store():
    """API endpoint for storing prospects (AJAX)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result = run_tool("store_prospect", [], input_data=json.dumps(data))
    return jsonify(result)


@app.route("/api/icp")
def api_get_icp():
    """API endpoint to get ICP."""
    icp = memory.get_icp()
    return jsonify(icp or {})


# ==================== Templates ====================

# Create templates directory and files
TEMPLATES_DIR = Path(__file__).parent / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

# Base template
BASE_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Prospecting Agent{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .sidebar { min-height: 100vh; background: #f8f9fa; }
        .prospect-card { transition: box-shadow 0.2s; }
        .prospect-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .score-badge { font-size: 0.8rem; }
        .status-new { background: #e3f2fd; }
        .status-enriched { background: #e8f5e9; }
        .status-qualified { background: #fff3e0; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-2 sidebar py-3">
                <h5 class="mb-3">Prospecting Agent</h5>
                <ul class="nav flex-column">
                    <li class="nav-item"><a class="nav-link" href="/">Dashboard</a></li>
                    <li class="nav-item"><a class="nav-link" href="/chat">Chat</a></li>
                    <li class="nav-item"><a class="nav-link" href="/search">Search</a></li>
                    <li class="nav-item"><a class="nav-link" href="/prospects">Prospects</a></li>
                    <li class="nav-item"><a class="nav-link" href="/icp">ICP Settings</a></li>
                </ul>
            </nav>
            <main class="col-md-10 py-4">
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''

INDEX_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Dashboard - Prospecting Agent{% endblock %}
{% block content %}
<h2>Dashboard</h2>

<div class="row mb-4">
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Total Prospects</h5>
                <p class="display-6">{{ stats.get('total', 0) }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Enriched</h5>
                <p class="display-6">{{ stats.get('by_status', {}).get('enriched', 0) }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Avg Score</h5>
                <p class="display-6">{{ stats.get('avg_score', '-') }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">ICP</h5>
                <p class="text-muted">{{ icp.get('name', 'Not set') }}</p>
                <a href="/icp" class="btn btn-sm btn-outline-primary">Configure</a>
            </div>
        </div>
    </div>
</div>

<h4>Recent Prospects</h4>
<div class="table-responsive">
    <table class="table">
        <thead>
            <tr>
                <th>Company</th>
                <th>Industry</th>
                <th>Status</th>
                <th>Score</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for p in prospects %}
            <tr>
                <td><a href="/prospects/{{ p.id }}">{{ p.company_name }}</a></td>
                <td>{{ p.industry or '-' }}</td>
                <td><span class="badge bg-secondary">{{ p.status }}</span></td>
                <td>{{ p.score or '-' }}</td>
                <td><a href="/prospects/{{ p.id }}" class="btn btn-sm btn-outline-primary">View</a></td>
            </tr>
            {% else %}
            <tr><td colspan="5" class="text-muted">No prospects yet. <a href="/search">Start searching</a></td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}'''

SEARCH_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Search - Prospecting Agent{% endblock %}
{% block content %}
<h2>Search Prospects</h2>

<form method="POST" class="mb-4">
    <div class="row g-3">
        <div class="col-md-6">
            <label class="form-label">Search Query</label>
            <input type="text" name="query" class="form-control" value="{{ query }}" placeholder="e.g., AI startups in San Francisco">
        </div>
        <div class="col-md-6">
            <label class="form-label">Industries</label>
            <input type="text" name="industries" class="form-control" placeholder="e.g., SaaS, Fintech" value="{{ icp.get('target_industries', [])|join(', ') }}">
        </div>
        <div class="col-md-6">
            <label class="form-label">Geography</label>
            <input type="text" name="geography" class="form-control" placeholder="e.g., US, UK" value="{{ icp.get('geography', [])|join(', ') }}">
        </div>
        <div class="col-md-6">
            <label class="form-label">Company Size</label>
            <input type="text" name="size" class="form-control" placeholder="e.g., 50-500">
        </div>
    </div>
    <button type="submit" class="btn btn-primary mt-3">Search</button>
</form>

{% if results %}
<h4>Results</h4>
{% if results.error %}
<div class="alert alert-danger">{{ results.error }}</div>
{% else %}
<p class="text-muted">Found {{ results.get('prospects', [])|length }} prospects</p>
<div class="row">
    {% for p in results.get('prospects', []) %}
    <div class="col-md-6 mb-3">
        <div class="card prospect-card">
            <div class="card-body">
                <h5 class="card-title">{{ p.company_name }}</h5>
                <p class="card-text text-muted">{{ p.description[:150] if p.description else '' }}...</p>
                <p>
                    <span class="badge bg-info">{{ p.industry or 'Unknown' }}</span>
                    {% if p.relevance_score %}<span class="badge bg-success">Score: {{ p.relevance_score }}</span>{% endif %}
                </p>
                {% if p.website %}<a href="{{ p.website }}" target="_blank" class="btn btn-sm btn-outline-secondary">Website</a>{% endif %}
                <form method="POST" action="/api/store" class="d-inline">
                    <input type="hidden" name="prospect" value="{{ p|tojson }}">
                    <button type="button" class="btn btn-sm btn-primary save-btn" data-prospect="{{ p|tojson|e }}">Save</button>
                </form>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% endif %}
{% endif %}
{% endblock %}

{% block scripts %}
<script>
document.querySelectorAll('.save-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        const prospect = JSON.parse(btn.dataset.prospect);
        const res = await fetch('/api/store', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(prospect)
        });
        const data = await res.json();
        if (data.status === 'success') {
            btn.textContent = 'Saved!';
            btn.disabled = true;
        }
    });
});
</script>
{% endblock %}'''

PROSPECTS_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Prospects - Prospecting Agent{% endblock %}
{% block content %}
<h2>Prospects</h2>

<form method="GET" class="row g-3 mb-4">
    <div class="col-md-3">
        <input type="text" name="q" class="form-control" placeholder="Search..." value="{{ filters.q }}">
    </div>
    <div class="col-md-2">
        <select name="status" class="form-select">
            <option value="">All Status</option>
            <option value="new" {{ 'selected' if filters.status == 'new' }}>New</option>
            <option value="enriched" {{ 'selected' if filters.status == 'enriched' }}>Enriched</option>
            <option value="qualified" {{ 'selected' if filters.status == 'qualified' }}>Qualified</option>
        </select>
    </div>
    <div class="col-md-2">
        <input type="number" name="min_score" class="form-control" placeholder="Min Score" value="{{ filters.min_score }}">
    </div>
    <div class="col-auto">
        <button type="submit" class="btn btn-outline-primary">Filter</button>
    </div>
</form>

<div class="table-responsive">
    <table class="table table-hover">
        <thead>
            <tr>
                <th>Company</th>
                <th>Industry</th>
                <th>Location</th>
                <th>Size</th>
                <th>Status</th>
                <th>Score</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for p in prospects %}
            <tr class="status-{{ p.status }}">
                <td><a href="/prospects/{{ p.id }}"><strong>{{ p.company_name }}</strong></a></td>
                <td>{{ p.industry or '-' }}</td>
                <td>{{ p.headquarters.city if p.headquarters else '-' }}</td>
                <td>{{ p.employee_count or '-' }}</td>
                <td><span class="badge bg-secondary">{{ p.status }}</span></td>
                <td>{% if p.score %}<span class="badge bg-{{ 'success' if p.score >= 70 else 'warning' if p.score >= 50 else 'secondary' }}">{{ p.score }}</span>{% else %}-{% endif %}</td>
                <td>
                    <a href="/prospects/{{ p.id }}" class="btn btn-sm btn-outline-primary">View</a>
                    {% if p.status != 'enriched' %}
                    <form method="POST" action="/prospects/{{ p.id }}/enrich" class="d-inline">
                        <button type="submit" class="btn btn-sm btn-outline-success">Enrich</button>
                    </form>
                    {% endif %}
                </td>
            </tr>
            {% else %}
            <tr><td colspan="7" class="text-muted">No prospects found</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}'''

PROSPECT_DETAIL_TEMPLATE = '''{% extends "base.html" %}
{% block title %}{{ prospect.company_name }} - Prospecting Agent{% endblock %}
{% block content %}
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="/prospects">Prospects</a></li>
        <li class="breadcrumb-item active">{{ prospect.company_name }}</li>
    </ol>
</nav>

<div class="row">
    <div class="col-md-8">
        <h2>{{ prospect.company_name }}</h2>
        <p class="lead">{{ prospect.description or 'No description available' }}</p>
        
        <div class="row mb-4">
            <div class="col-md-6">
                <h5>Company Info</h5>
                <ul class="list-unstyled">
                    <li><strong>Industry:</strong> {{ prospect.industry or '-' }}</li>
                    <li><strong>Sub-industry:</strong> {{ prospect.sub_industry or '-' }}</li>
                    <li><strong>Website:</strong> {% if prospect.website %}<a href="{{ prospect.website }}" target="_blank">{{ prospect.website }}</a>{% else %}-{% endif %}</li>
                    <li><strong>Employees:</strong> {{ prospect.employee_count or '-' }}</li>
                    <li><strong>Revenue:</strong> {{ '$' + '{:,.0f}'.format(prospect.revenue_estimate_usd) if prospect.revenue_estimate_usd else '-' }}</li>
                    <li><strong>Funding:</strong> {{ prospect.funding_stage or '-' }}</li>
                </ul>
            </div>
            <div class="col-md-6">
                <h5>Location</h5>
                {% if prospect.headquarters %}
                <p>
                    {{ prospect.headquarters.city or '' }}{% if prospect.headquarters.state %}, {{ prospect.headquarters.state }}{% endif %}<br>
                    {{ prospect.headquarters.country or '' }}
                </p>
                {% else %}
                <p class="text-muted">No location data</p>
                {% endif %}
            </div>
        </div>
        
        {% if prospect.technologies %}
        <h5>Technologies</h5>
        <p>
            {% for tech in prospect.technologies %}
            <span class="badge bg-info">{{ tech }}</span>
            {% endfor %}
        </p>
        {% endif %}
        
        {% if prospect.contacts %}
        <h5>Contacts</h5>
        <ul>
            {% for contact in prospect.contacts %}
            <li><strong>{{ contact.name }}</strong> - {{ contact.title }}
                {% if contact.linkedin %}<a href="{{ contact.linkedin }}" target="_blank">(LinkedIn)</a>{% endif %}
            </li>
            {% endfor %}
        </ul>
        {% endif %}
        
        {% if prospect.signals %}
        <h5>Signals</h5>
        <ul>
            {% if prospect.signals.hiring %}<li class="text-success">Actively hiring</li>{% endif %}
            {% if prospect.signals.recent_funding %}<li class="text-success">Recent funding</li>{% endif %}
            {% if prospect.signals.recent_news %}
                {% for news in prospect.signals.recent_news %}
                <li>{{ news }}</li>
                {% endfor %}
            {% endif %}
        </ul>
        {% endif %}
    </div>
    
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Status</h5>
                <p><span class="badge bg-{{ 'success' if prospect.status == 'enriched' else 'secondary' }} fs-5">{{ prospect.status }}</span></p>
                
                {% if prospect.score %}
                <h5>ICP Score</h5>
                <p class="display-4">{{ prospect.score }}</p>
                {% endif %}
                
                <hr>
                
                <p class="text-muted small">
                    Created: {{ prospect.created_at[:10] if prospect.created_at else '-' }}<br>
                    Updated: {{ prospect.updated_at[:10] if prospect.updated_at else '-' }}<br>
                    {% if prospect.enriched_at %}Enriched: {{ prospect.enriched_at[:10] }}{% endif %}
                </p>
                
                {% if prospect.status != 'enriched' %}
                <form method="POST" action="/prospects/{{ prospect.id }}/enrich">
                    <button type="submit" class="btn btn-success w-100">Enrich This Prospect</button>
                </form>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}'''

ICP_TEMPLATE = '''{% extends "base.html" %}
{% block title %}ICP Settings - Prospecting Agent{% endblock %}
{% block content %}
<h2>Ideal Customer Profile (ICP)</h2>
<p class="text-muted">Define your target customer criteria</p>

<form method="POST">
    <div class="row g-3">
        <div class="col-md-6">
            <label class="form-label">Profile Name</label>
            <input type="text" name="name" class="form-control" value="{{ icp.get('name', 'default') }}">
        </div>
        
        <div class="col-md-6">
            <label class="form-label">Target Industries (comma-separated)</label>
            <input type="text" name="industries" class="form-control" 
                   value="{{ icp.get('target_industries', [])|join(', ') }}"
                   placeholder="SaaS, Fintech, HealthTech">
        </div>
        
        <div class="col-md-6">
            <label class="form-label">Geography (comma-separated)</label>
            <input type="text" name="geography" class="form-control" 
                   value="{{ icp.get('geography', [])|join(', ') }}"
                   placeholder="US, UK, Germany">
        </div>
        
        <div class="col-md-6">
            <label class="form-label">Keywords (comma-separated)</label>
            <input type="text" name="keywords" class="form-control" 
                   value="{{ icp.get('keywords', [])|join(', ') }}"
                   placeholder="AI, automation, cloud">
        </div>
        
        <div class="col-md-3">
            <label class="form-label">Min Employees</label>
            <input type="number" name="min_employees" class="form-control" 
                   value="{{ icp.get('company_size', {}).get('min_employees', '') }}">
        </div>
        
        <div class="col-md-3">
            <label class="form-label">Max Employees</label>
            <input type="number" name="max_employees" class="form-control" 
                   value="{{ icp.get('company_size', {}).get('max_employees', '') }}">
        </div>
        
        <div class="col-md-6">
            <label class="form-label">Funding Stage</label>
            <div>
                {% for stage in ['seed', 'series-a', 'series-b', 'series-c', 'series-d+'] %}
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="checkbox" name="funding_stage" 
                           value="{{ stage }}" {{ 'checked' if stage in icp.get('funding_stage', []) }}>
                    <label class="form-check-label">{{ stage }}</label>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="col-md-6">
            <label class="form-label">Exclusions (comma-separated)</label>
            <input type="text" name="exclusions" class="form-control" 
                   value="{{ icp.get('exclusions', [])|join(', ') }}"
                   placeholder="consulting, agency">
        </div>
    </div>
    
    <button type="submit" class="btn btn-primary mt-4">Save ICP</button>
</form>
{% endblock %}'''

ERROR_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Error - Prospecting Agent{% endblock %}
{% block content %}
<div class="alert alert-danger">
    <h4>Error</h4>
    <p>{{ error }}</p>
</div>
<a href="/" class="btn btn-primary">Go to Dashboard</a>
{% endblock %}'''

CHAT_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Chat - Prospecting Agent{% endblock %}
{% block content %}
<style>
    .status-panel {
        background: #1a1a2e;
        color: #0f0;
        font-family: 'Monaco', 'Consolas', monospace;
        font-size: 12px;
        border-radius: 8px;
        padding: 12px;
        max-height: 200px;
        overflow-y: auto;
    }
    .status-line {
        margin: 2px 0;
        padding: 2px 4px;
    }
    .status-line.tool { color: #ff79c6; }
    .status-line.status { color: #8be9fd; }
    .status-line.error { color: #ff5555; }
    .status-line.response { color: #50fa7b; }
    .chat-bubble {
        max-width: 85%;
        word-wrap: break-word;
    }
    .agent-thinking {
        display: inline-block;
        padding: 8px 16px;
        background: #f0f0f0;
        border-radius: 16px;
        color: #666;
    }
    .agent-thinking .dots::after {
        content: '';
        animation: dots 1.5s infinite;
    }
    @keyframes dots {
        0%, 20% { content: '.'; }
        40% { content: '..'; }
        60%, 100% { content: '...'; }
    }
</style>

<div class="d-flex flex-column" style="height: calc(100vh - 100px);">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h2 class="mb-0">Chat with Prospecting Agent</h2>
        <div>
            <button class="btn btn-sm btn-outline-secondary me-2" onclick="clearChat()">Clear Chat</button>
            <span class="badge bg-info">ICP: {{ icp.get('name', 'Not set') }}</span>
        </div>
    </div>
    
    <!-- Status Panel -->
    <div class="status-panel mb-3" id="status-panel" style="display: none;">
        <div class="d-flex justify-content-between align-items-center mb-2">
            <strong style="color: #bd93f9;">Agent Activity</strong>
            <button class="btn btn-sm btn-outline-light" onclick="document.getElementById('status-panel').style.display='none'" style="font-size: 10px; padding: 2px 8px;">Hide</button>
        </div>
        <div id="status-messages"></div>
    </div>
    
    <div class="card flex-grow-1 mb-3">
        <div class="card-body overflow-auto" id="chat-messages" style="max-height: 50vh;">
            <div class="text-muted text-center py-5" id="welcome-message">
                <h5>Welcome to the Prospecting Agent</h5>
                <p>Ask me to search for prospects, enrich company data, or manage your ICP.</p>
                <p class="small">Try: "Find AI startups in Berlin" or "What companies do we have?"</p>
            </div>
        </div>
    </div>
    
    <form id="chat-form" class="d-flex gap-2">
        <input type="text" id="chat-input" class="form-control form-control-lg" 
               placeholder="Ask the agent to search, enrich, or manage prospects..." autofocus>
        <button type="submit" class="btn btn-primary btn-lg px-4" id="send-btn">
            <span id="send-text">Send</span>
            <span id="send-spinner" class="spinner-border spinner-border-sm d-none" role="status"></span>
        </button>
    </form>
</div>
{% endblock %}

{% block scripts %}
<script>
const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const sendText = document.getElementById('send-text');
const sendSpinner = document.getElementById('send-spinner');
const welcomeMessage = document.getElementById('welcome-message');
const statusPanel = document.getElementById('status-panel');
const statusMessages = document.getElementById('status-messages');

let thinkingIndicator = null;

function addStatusMessage(type, message) {
    statusPanel.style.display = 'block';
    const line = document.createElement('div');
    line.className = `status-line ${type}`;
    line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    statusMessages.appendChild(line);
    statusMessages.scrollTop = statusMessages.scrollHeight;
}

function clearStatus() {
    statusMessages.innerHTML = '';
}

function addMessage(content, isUser, isThinking = false) {
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    // Remove thinking indicator if exists
    if (thinkingIndicator) {
        thinkingIndicator.remove();
        thinkingIndicator = null;
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `mb-3 ${isUser ? 'text-end' : ''}`;
    
    if (isThinking) {
        messageDiv.innerHTML = `<div class="agent-thinking">Agent is working<span class="dots"></span></div>`;
        thinkingIndicator = messageDiv;
    } else {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble d-inline-block p-3 rounded-3 ${isUser ? 'bg-primary text-white' : 'bg-light'}`;
        bubble.style.textAlign = 'left';
        
        // Format the content - simple text formatting
        let formattedContent = content;
        // Handle both escaped and actual newlines
        formattedContent = formattedContent.split(String.fromCharCode(10)).join('<br>');
        formattedContent = formattedContent.split('\\\\n').join('<br>');
        // Bold and italic
        formattedContent = formattedContent.replace(/[*][*]([^*]+)[*][*]/g, '<strong>$1</strong>');
        formattedContent = formattedContent.replace(/[*]([^*]+)[*]/g, '<em>$1</em>');
        
        bubble.innerHTML = `<div style="white-space: pre-wrap;">${formattedContent}</div>`;
        
        const timestamp = document.createElement('small');
        timestamp.className = 'text-muted d-block mt-1';
        timestamp.textContent = new Date().toLocaleTimeString();
        
        messageDiv.appendChild(bubble);
        messageDiv.appendChild(timestamp);
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

function setLoading(loading) {
    chatInput.disabled = loading;
    sendBtn.disabled = loading;
    sendText.classList.toggle('d-none', loading);
    sendSpinner.classList.toggle('d-none', !loading);
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = chatInput.value.trim();
    if (!message) return;
    
    addMessage(message, true);
    chatInput.value = '';
    setLoading(true);
    clearStatus();
    
    // Show thinking indicator
    addMessage('', false, true);
    
    try {
        // Use streaming endpoint
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let finalResponse = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const text = decoder.decode(value);
            const lines = text.split(String.fromCharCode(10));
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'status' || data.type === 'tool' || data.type === 'error') {
                            addStatusMessage(data.type, data.message);
                        } else if (data.type === 'response') {
                            finalResponse = data.message;
                        } else if (data.type === 'done') {
                            // Show final response
                            addMessage(finalResponse || 'No response from agent', false);
                        }
                    } catch (e) {
                        // Ignore parse errors
                    }
                }
            }
        }
    } catch (error) {
        addMessage('Error: Failed to communicate with the agent. Please try again.', false);
    } finally {
        setLoading(false);
        chatInput.focus();
    }
});

async function clearChat() {
    if (!confirm('Clear conversation history?')) return;
    
    try {
        await fetch('/api/chat/clear', { method: 'POST' });
        chatMessages.innerHTML = `
            <div class="text-muted text-center py-5" id="welcome-message">
                <h5>Welcome to the Prospecting Agent</h5>
                <p>Ask me to search for prospects, enrich company data, or manage your ICP.</p>
                <p class="small">Try: "Find AI startups in Berlin" or "What companies do we have?"</p>
            </div>`;
        statusMessages.innerHTML = '';
        statusPanel.style.display = 'none';
    } catch (e) {
        alert('Failed to clear chat');
    }
}
</script>
{% endblock %}'''

# Write templates
templates = {
    "base.html": BASE_TEMPLATE,
    "index.html": INDEX_TEMPLATE,
    "search.html": SEARCH_TEMPLATE,
    "prospects.html": PROSPECTS_TEMPLATE,
    "prospect_detail.html": PROSPECT_DETAIL_TEMPLATE,
    "icp.html": ICP_TEMPLATE,
    "error.html": ERROR_TEMPLATE,
    "chat.html": CHAT_TEMPLATE
}

for name, content in templates.items():
    template_path = TEMPLATES_DIR / name
    if not template_path.exists():
        with open(template_path, "w") as f:
            f.write(content)


# ==================== Run ====================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
