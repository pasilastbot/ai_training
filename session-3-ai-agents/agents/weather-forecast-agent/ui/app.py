#!/usr/bin/env python3
"""
Weather Forecast Agent Web UI

Flask-based web interface for the weather forecast agent.

Usage:
  python ui/app.py
  # Or: FLASK_APP=ui/app.py flask run --port 5003

Open http://localhost:5003 in your browser.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS

AGENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(AGENT_DIR))
from agent_env import load_agent_environment

load_agent_environment()
sys.path.insert(0, str(AGENT_DIR / "memory"))

from memory import MemoryStore

app = Flask(__name__)
CORS(app)

memory = MemoryStore()


# ==================== Helper Functions ====================

def run_subagent(name: str, args: list) -> dict:
    """Run a subagent and return its output."""
    subagent_path = AGENT_DIR / "subagents" / f"{name}.py"
    
    if not subagent_path.exists():
        return {"error": f"Subagent not found: {name}"}
    
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
            return {"error": result.stderr or "Subagent failed"}
    except subprocess.TimeoutExpired:
        return {"error": "Subagent timed out"}
    except json.JSONDecodeError:
        return {"error": "Invalid subagent output", "raw": result.stdout}
    except Exception as e:
        return {"error": str(e)}


# ==================== Routes ====================

@app.route("/")
def index():
    """Dashboard home page."""
    locations = memory.get_locations()
    stats = memory.get_stats()
    
    today = datetime.now()
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    return render_template("index.html",
        locations=locations,
        stats=stats,
        today=weekdays[today.weekday()],
        today_date=today.strftime("%Y-%m-%d")
    )


@app.route("/weather/<path:location>")
def weather(location):
    """Weather details page for a location."""
    units = request.args.get("units", "metric")
    
    result = run_subagent("weather_search", [
        "--location", location,
        "--units", units,
        "--pretty"
    ])
    
    weather_data = result.get("weather", {})
    
    alert_result = run_subagent("alert_checker", [
        "--location", location,
        "--pretty"
    ])
    
    alerts = alert_result.get("alerts", [])
    
    return render_template("weather.html",
        location=location,
        location_name=result.get("location_name", location),
        weather=weather_data,
        alerts=alerts,
        forecast=result.get("forecast", []),
        units=units
    )


@app.route("/forecast")
def forecast():
    """Forecast page."""
    location = request.args.get("location", "")
    days = int(request.args.get("days", 5))
    units = request.args.get("units", "metric")
    
    if not location:
        return render_template("forecast.html", location=None)
    
    result = run_subagent("weather_search", [
        "--location", location,
        "--days", str(days),
        "--units", units,
        "--pretty"
    ])
    
    return render_template("forecast.html",
        location=location,
        location_name=result.get("location_name", location),
        forecast=result.get("forecast", []),
        weather=result.get("weather", {}),
        days=days,
        units=units
    )


@app.route("/activities")
def activities():
    """Activity recommendations page."""
    location = request.args.get("location", "")
    
    if not location:
        return render_template("activities.html", location=None)
    
    units = request.args.get("units", "metric")
    
    weather_result = run_subagent("weather_search", [
        "--location", location,
        "--units", units,
        "--pretty"
    ])
    
    weather = weather_result.get("weather", {})
    
    alert_result = get_alerts(location)
    alerts = alert_result.get("alerts", [])
    
    from google import genai
    from google.genai import types
    
    api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GEMINI_API_KEY")
    recommendations = "Could not generate recommendations"
    
    if api_key and not weather.get("error"):
        try:
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
            
            recommendations = response.candidates[0].content.parts[0].text
        except:
            pass
    
    return render_template("activities.html",
        location=location,
        location_name=weather.get("location_name", location),
        weather=weather,
        alerts=alerts,
        recommendations=recommendations
    )


@app.route("/locations")
def locations():
    """Locations management page."""
    locations_list = memory.get_locations()
    return render_template("locations.html", locations=locations_list)


@app.route("/locations/add", methods=["POST"])
def add_location():
    """Add a new location."""
    name = request.form.get("name")
    location = request.form.get("location")
    
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    
    coordinates = None
    if lat and lon:
        coordinates = {"lat": float(lat), "lon": float(lon)}
    
    timezone = request.form.get("timezone")
    
    memory.store_location(
        name=name,
        location=location,
        coordinates=coordinates,
        timezone=timezone
    )
    
    return redirect(url_for("locations"))


@app.route("/locations/<name>/delete", methods=["POST"])
def delete_location_route(name):
    """Delete a location."""
    memory.delete_location(name)
    return redirect(url_for("locations"))


@app.route("/search", methods=["GET", "POST"])
def search():
    """Search for weather by location."""
    if request.method == "POST":
        location = request.form.get("location", "")
        if location:
            return redirect(url_for("weather", location=location))
    
    return render_template("search.html")


@app.route("/chat")
def chat_page():
    """Chat interface page."""
    locations = memory.get_locations()
    return render_template("chat.html", locations=locations)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """API endpoint for chat with the agent."""
    from flask import Response, stream_with_context
    
    data = request.get_json() or {}
    message = data.get("message", "")
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    agent_path = AGENT_DIR / "weather_forecast_agent.py"
    
    def generate():
        process = subprocess.Popen(
            ["python", "-u", str(agent_path), message],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(AGENT_DIR),
            env={**os.environ},
            bufsize=1
        )
        
        yield f"data: {json.dumps({'type': 'status', 'message': 'Starting agent...'})}\n\n"
        
        import threading
        import queue
        
        output_queue = queue.Queue()
        final_response = []
        
        def read_output(pipe, prefix):
            for line in iter(pipe.readline, ''):
                if line:
                    output_queue.put((prefix, line.strip()))
            pipe.close()
        
        stdout_thread = threading.Thread(target=read_output, args=(process.stdout, 'out'))
        stderr_thread = threading.Thread(target=read_output, args=(process.stderr, 'err'))
        stdout_thread.start()
        stderr_thread.start()
        
        while stdout_thread.is_alive() or stderr_thread.is_alive() or not output_queue.empty():
            try:
                prefix, line = output_queue.get(timeout=0.1)
                
                if prefix == 'err':
                    if 'weather' in line.lower() or 'search' in line.lower():
                        yield f"data: {json.dumps({'type': 'status', 'message': f'🌤 {line}'})}\n\n"
                    elif 'forecast' in line.lower():
                        yield f"data: {json.dumps({'type': 'status', 'message': f'📅 {line}'})}\n\n"
                    elif 'error' in line.lower():
                        yield f"data: {json.dumps({'type': 'error', 'message': f'⚠️ {line}'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'status', 'message': f'ℹ️ {line}'})}\n\n"
                else:
                    final_response.append(line)
                    
            except queue.Empty:
                continue
        
        stdout_thread.join()
        stderr_thread.join()
        process.wait()
        
        response_text = '\n'.join(final_response) if final_response else "No response from agent"
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


def get_alerts(location: str):
    """Get alerts helper."""
    return run_subagent("alert_checker", ["--location", location, "--pretty"])


# ==================== Templates ====================

TEMPLATES_DIR = Path(__file__).parent / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

BASE_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Weather Forecast Agent{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .sidebar { min-height: 100vh; background: #f8f9fa; }
        .weather-card { transition: box-shadow 0.2s; }
        .weather-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .alert-banner { padding: 10px; border-radius: 8px; margin-bottom: 15px; }
        .alert-high { background: #fee; border-left: 4px solid #dc3545; }
        .alert-medium { background: #fff3cd; border-left: 4px solid #ffc107; }
        .alert-low { background: #d1e7dd; border-left: 4px solid #198754; }
        .chat-bubble { max-width: 85%; word-wrap: break-word; }
        .status-panel { background: #1a1a2e; color: #0f0; font-family: monospace; font-size: 12px; border-radius: 8px; padding: 12px; max-height: 150px; overflow-y: auto; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-2 sidebar py-3">
                <h5 class="mb-3">🌤 Weather Agent</h5>
                <ul class="nav flex-column">
                    <li class="nav-item"><a class="nav-link" href="/">Dashboard</a></li>
                    <li class="nav-item"><a class="nav-link" href="/chat">Chat</a></li>
                    <li class="nav-item"><a class="nav-link" href="/search">Search</a></li>
                    <li class="nav-item"><a class="nav-link" href="/locations">Locations</a></li>
                    <li class="nav-item"><a class="nav-link" href="/forecast">Forecast</a></li>
                    <li class="nav-item"><a class="nav-link" href="/activities">Activities</a></li>
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
{% block title %}Dashboard - Weather Agent{% endblock %}
{% block content %}
<h2>🌤 Weather Dashboard</h2>
<p class="lead">{{ today }}, {{ today_date }}</p>

<div class="row mb-4">
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Saved Locations</h5>
                <p class="display-6">{{ stats.get('total_locations', 0) }}</p>
                <a href="/locations" class="btn btn-sm btn-outline-primary">Manage</a>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Cached Data</h5>
                <p class="display-6">{{ stats.get('cached_weather_entries', 0) }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Quick Actions</h5>
                <a href="/search" class="btn btn-primary w-100 mb-2">Search Weather</a>
                <a href="/chat" class="btn btn-outline-primary w-100">Chat with Agent</a>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <h4>Your Locations</h4>
        {% if locations %}
        <ul class="list-group">
            {% for loc in locations %}
            <li class="list-group-item">
                <strong>{{ loc.name }}</strong> - {{ loc.city }}
                <a href="/weather/{{ loc.city }}" class="btn btn-sm btn-outline-primary float-end">View Weather</a>
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <p class="text-muted">No locations saved yet. <a href="/locations">Add your first location</a>.</p>
        {% endif %}
    </div>
</div>
{% endblock %}'''

WEATHER_TEMPLATE = '''{% extends "base.html" %}
{% block title %}{{ location_name }} - Weather{% endblock %}
{% block content %}
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="/">Home</a></li>
        <li class="breadcrumb-item active">{{ location_name }}</li>
    </ol>
</nav>

<h2>Weather for {{ location_name }}</h2>

{% if alerts and alerts|length > 0 %}
<div class="row mb-3">
    {% for alert in alerts %}
    <div class="col-12">
        <div class="alert-banner alert-{{ alert.urgency or 'medium' }}">
            <strong>⚠️ {{ alert.severity }}: {{ alert.type }}</strong>
            <p class="mb-0 mt-1">{{ alert.description }}</p>
            {% if alert.valid_until %}<small class="text-muted">Valid until: {{ alert.valid_until }}</small>{% endif %}
        </div>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if weather and not weather.error %}
<div class="card mb-4">
    <div class="card-body">
        <h3>{{ temperature }} {{ weather.get('condition', 'Unknown') }}</h3>
        <p class="text-muted">{{ location_name }}</p>
        
        <div class="row">
            <div class="col-md-3">
                <strong>Temperature</strong><br>
                {{ weather.get('temperature', 'N/A') }} {{ '°C' if units == 'metric' else '°F' }}
            </div>
            <div class="col-md-3">
                <strong>Feels Like</strong><br>
                {{ weather.get('feels_like', 'N/A') }} {{ '°C' if units == 'metric' else '°F' }}
            </div>
            <div class="col-md-3">
                <strong>Humidity</strong><br>
                {{ weather.get('humidity', 'N/A') }}%
            </div>
            <div class="col-md-3">
                <strong>Wind</strong><br>
                {{ weather.get('wind', 'N/A') }}
            </div>
        </div>
    </div>
</div>
{% elif weather.error %}
<div class="alert alert-danger">
    Could not fetch weather: {{ weather.error }}
</div>
{% else %}
<div class="alert alert-info">
    Loading weather data...
</div>
{% endif %}

{% if forecast and forecast|length > 0 %}
<h4 class="mt-4">Forecast</h4>
<div class="row">
    {% for day in forecast %}
    <div class="col-md-{{ '12//forecast|length' if forecast|length < 4 else '3' }} mb-3">
        <div class="card weather-card">
            <div class="card-body">
                <h5 class="card-title">{{ day.get('day', 'Day') }}</h5>
                <p class="text-muted">{{ day.get('condition', '') }}</p>
                <p>
                    <span class="badge bg-primary">{{ day.get('high', 'N/A') }}°</span>
                    <span class="badge bg-secondary">{{ day.get('low', 'N/A') }}°</span>
                </p>
                {% if day.get('precipitation') %}
                <small class="text-muted">Rain: {{ day.precipitation }}%</small>
                {% endif %}
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% endif %}

{% set temperature = weather.get('temperature', 'N/A') if weather else 'N/A' %}

<div class="row mt-4">
    <div class="col-md-6">
        <h5>Quick Actions</h5>
        <div class="list-group">
            <a href="/activities?location={{ location }}&units={{ units }}" class="list-group-item list-group-item-action">🏃 Activity Recommendations</a>
            <a href="/forecast?location={{ location }}&units={{ units }}" class="list-group-item list-group-item-action">📅 Full Forecast</a>
        </div>
    </div>
</div>
{% endblock %}'''

FORECAST_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Forecast - Weather Agent{% endblock %}
{% block content %}
<h2>Weather Forecast</h2>

<form method="GET" class="row g-3 mb-4">
    <div class="col-md-4">
        <label class="form-label">Location</label>
        <input type="text" name="location" class="form-control" placeholder="e.g., Helsinki, Tokyo" value="{{ location or '' }}" required>
    </div>
    <div class="col-md-3">
        <label class="form-label">Days</label>
        <select name="days" class="form-select">
            <option value="3" {{ 'selected' if days == 3 }}>3 days</option>
            <option value="5" {{ 'selected' if days == 5 }}>5 days</option>
            <option value="7" {{ 'selected' if days == 7 }}>7 days</option>
        </select>
    </div>
    <div class="col-md-3">
        <label class="form-label">Units</label>
        <select name="units" class="form-select">
            <option value="metric" {{ 'selected' if units == 'metric' }}>Celsius</option>
            <option value="imperial" {{ 'selected' if units == 'imperial' }}>Fahrenheit</option>
        </select>
    </div>
    <div class="col-md-2 d-flex align-items-end">
        <button type="submit" class="btn btn-primary w-100">Get Forecast</button>
    </div>
</form>

{% if forecast %}
<h3>Forecast for {{ location_name }}</h3>
<div class="row">
    {% for day in forecast %}
    <div class="col-md-4 mb-3">
        <div class="card weather-card">
            <div class="card-body">
                <h5 class="card-title">{{ day.get('day', 'Day') }}</h5>
                <p class="lead mb-2">{{ day.get('condition', '') }}</p>
                <div class="d-flex justify-content-between">
                    <span class="text-danger">H: {{ day.get('high', 'N/A') }}{{ '°C' if units == 'metric' else '°F' }}</span>
                    <span class="text-primary">L: {{ day.get('low', 'N/A') }}{{ '°C' if units == 'metric' else '°F' }}</span>
                </div>
                {% if day.get('precipitation') %}
                <small class="text-muted mt-2 d-block">Precipitation: {{ day.precipitation }}%</small>
                {% endif %}
                {% if day.get('humidity') %}
                <small class="text-muted d-block">Humidity: {{ day.humidity }}%</small>
                {% endif %}
            </div>
        </div>
    </div>
    {% endfor %}
</div>
{% elif location %}
<div class="alert alert-warning">
    Could not fetch forecast for {{ location }}. Please try again or check the location name.
</div>
{% endif %}
{% endblock %}'''

ACTIVITIES_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Activities - Weather Agent{% endblock %}
{% block content %}
<h2>🏃 Activity Recommendations</h2>

<form method="GET" class="row g-3 mb-4">
    <div class="col-md-5">
        <label class="form-label">Location</label>
        <input type="text" name="location" class="form-control" placeholder="e.g., Helsinki" value="{{ location or '' }}" required>
    </div>
    <div class="col-md-3 d-flex align-items-end">
        <button type="submit" class="btn btn-primary w-100">Get Recommendations</button>
    </div>
</form>

{% if location %}
    {% if weather and not weather.error %}
    <div class="card mb-4">
        <div class="card-body">
            <h4>Current Weather: {{ location_name }}</h4>
            <p><strong>{{ weather.get('temperature', 'N/A') }}°</strong> - {{ weather.get('condition', 'Unknown') }}</p>
        </div>
    </div>

    {% if alerts and alerts|length > 0 %}
    <div class="mb-3">
        <h5>Weather Alerts</h5>
        {% for alert in alerts %}
        <div class="alert-banner alert-{{ alert.urgency or 'medium' }}">
            <strong>{{ alert.severity }}:</strong> {{ alert.description }}
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="card">
        <div class="card-body">
            <h4>Recommended Activities</h4>
            <div class="mt-3" style="white-space: pre-wrap;">{{ recommendations }}</div>
        </div>
    </div>
    {% elif weather and weather.error %}
    <div class="alert alert-danger">
        Could not fetch weather: {{ weather.error }}
    </div>
    {% endif %}
{% endif %}
{% endblock %}'''

LOCATIONS_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Locations - Weather Agent{% endblock %}
{% block content %}
<h2>📍 Saved Locations</h2>

<div class="row mb-4">
    <div class="col-md-9">
        <h4>Add New Location</h4>
        <form method="POST" action="/locations/add" class="row g-3">
            <div class="col-md-4">
                <label class="form-label">Name</label>
                <input type="text" name="name" class="form-control" placeholder="e.g., Home, Work" required>
            </div>
            <div class="col-md-4">
                <label class="form-label">City/Location</label>
                <input type="text" name="location" class="form-control" placeholder="e.g., Helsinki, Finland" required>
            </div>
            <div class="col-md-2">
                <label class="form-label">Latitude (optional)</label>
                <input type="number" step="0.0001" name="lat" class="form-control" placeholder="60.1695">
            </div>
            <div class="col-md-2">
                <label class="form-label">Longitude (optional)</label>
                <input type="number" step="0.0001" name="lon" class="form-control" placeholder="24.9354">
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-primary">Add Location</button>
            </div>
        </form>
    </div>
</div>

<div class="row">
    {% if locations %}
    <div class="col-12">
        <h4>Your Locations</h4>
        <div class="list-group">
            {% for loc in locations %}
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <strong>{{ loc.name }}</strong>
                    <p class="text-muted mb-0">{{ loc.city }}</p>
                    {% if loc.get('coordinates') %}
                    <small class="text-muted">{{ loc.coordinates.lat }}, {{ loc.coordinates.lon }}</small>
                    {% endif %}
                </div>
                <div>
                    <a href="/weather/{{ loc.city }}" class="btn btn-sm btn-outline-primary me-2">View Weather</a>
                    <form method="POST" action="/locations/{{ loc.name }}/delete" class="d-inline">
                        <button type="submit" class="btn btn-sm btn-outline-danger" onclick="return confirm('Remove this location?')">Remove</button>
                    </form>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% else %}
    <div class="col-12">
        <div class="alert alert-info">
            <h5>No locations saved</h5>
            <p>Add your first location above to start tracking weather for your favorite places.</p>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}'''

SEARCH_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Search - Weather Agent{% endblock %}
{% block content %}
<h2>🔍 Search Weather</h2>

<form method="POST" class="mb-4">
    <div class="row g-3">
        <div class="col-md-8">
            <label class="form-label">Location</label>
            <input type="text" name="location" class="form-control form-control-lg" 
                   placeholder="Enter city name, e.g., Helsinki, Tokyo, New York" required>
        </div>
        <div class="col-md-4 d-flex align-items-end">
            <button type="submit" class="btn btn-primary btn-lg w-100">Search</button>
        </div>
    </div>
</form>

<div class="text-center py-5">
    <h3>Find Weather Anywhere</h3>
    <p class="text-muted">Enter a city name above to get current weather, forecasts, and activity recommendations.</p>
    <p class="small">Try: "Helsinki", "New York", "Tokyo", "Paris", "Sydney"</p>
</div>
{% endblock %}'''

CHAT_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Chat - Weather Agent{% endblock %}
{% block content %}
<div class="d-flex flex-column" style="height: calc(100vh - 100px);">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h2 class="mb-0">💬 Chat with Weather Agent</h2>
    </div>
    
    <div class="status-panel mb-3" id="status-panel" style="display: none;">
        <div id="status-messages"></div>
    </div>
    
    <div class="card flex-grow-1 mb-3">
        <div class="card-body overflow-auto" id="chat-messages" style="max-height: 50vh;">
            <div class="text-muted text-center py-5" id="welcome-message">
                <h5>Welcome to the Weather Agent!</h5>
                <p>Ask me about weather anywhere in the world.</p>
                <p class="small">Try: "What's the weather in Helsinki?" or "Is it going to rain tomorrow?"</p>
            </div>
        </div>
    </div>
    
    <form id="chat-form" class="d-flex gap-2">
        <input type="text" id="chat-input" class="form-control form-control-lg" 
               placeholder="Ask about weather..." autofocus>
        <button type="submit" class="btn btn-primary btn-lg px-4" id="send-btn">Send</button>
    </form>
</div>
{% endblock %}

{% block scripts %}
<script>
const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const welcomeMessage = document.getElementById('welcome-message');
const statusPanel = document.getElementById('status-panel');
const statusMessages = document.getElementById('status-messages');

function addStatusMessage(message) {
    statusPanel.style.display = 'block';
    const line = document.createElement('div');
    line.textContent = message;
    statusMessages.appendChild(line);
    statusMessages.scrollTop = statusMessages.scrollHeight;
}

function clearStatus() {
    statusMessages.innerHTML = '';
}

function addMessage(content, isUser) {
    if (welcomeMessage) welcomeMessage.remove();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `mb-3 ${isUser ? 'text-end' : ''}`;
    
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble d-inline-block p-3 rounded-3 ${isUser ? 'bg-primary text-white' : 'bg-light'}`;
    bubble.style.textAlign = 'left';
    bubble.style.whiteSpace = 'pre-wrap';
    bubble.textContent = content;
    
    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function setLoading(loading) {
    chatInput.disabled = loading;
    sendBtn.disabled = loading;
    sendBtn.textContent = loading ? '...' : 'Send';
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = chatInput.value.trim();
    if (!message) return;
    
    addMessage(message, true);
    chatInput.value = '';
    setLoading(true);
    clearStatus();
    
    try {
        const response = await fetch('/api/chat', {
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
            const lines = text.split('\\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.type === 'status' || data.type === 'error') {
                            addStatusMessage(data.message);
                        } else if (data.type === 'response') {
                            finalResponse = data.message;
                        } else if (data.type === 'done') {
                            addMessage(finalResponse || 'No response', false);
                        }
                    } catch (e) {}
                }
            }
        }
    } catch (error) {
        addMessage('Error communicating with agent. Please try again.', false);
    } finally {
        setLoading(false);
        chatInput.focus();
    }
});
</script>
{% endblock %}'''

templates = {
    "base.html": BASE_TEMPLATE,
    "index.html": INDEX_TEMPLATE,
    "weather.html": WEATHER_TEMPLATE,
    "forecast.html": FORECAST_TEMPLATE,
    "activities.html": ACTIVITIES_TEMPLATE,
    "locations.html": LOCATIONS_TEMPLATE,
    "search.html": SEARCH_TEMPLATE,
    "chat.html": CHAT_TEMPLATE
}

for name, content in templates.items():
    template_path = TEMPLATES_DIR / name
    if not template_path.exists():
        with open(template_path, "w") as f:
            f.write(content)


# ==================== Run ====================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)