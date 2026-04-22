#!/usr/bin/env python3
"""
Lunch Selection Agent Web UI

Flask-based web interface for the lunch selection agent.

Usage:
  python ui/app.py
  # Or: FLASK_APP=ui/app.py flask run --port 5002

Open http://localhost:5002 in your browser.
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
    prefs = memory.get_preferences() or {}
    stats = memory.get_stats()
    recent_selections = memory.get_selections(days=7, limit=5)
    
    today = datetime.now()
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    return render_template("index.html",
        prefs=prefs,
        stats=stats,
        recent_selections=recent_selections,
        today=weekdays[today.weekday()],
        today_date=today.strftime("%Y-%m-%d")
    )


@app.route("/restaurants")
def restaurants():
    """Restaurant list page."""
    city = request.args.get("city", "")
    cuisine = request.args.get("cuisine", "")
    search_query = request.args.get("q", "")
    
    if search_query:
        restaurants_list = memory.search_restaurants(search_query, 50)
    else:
        restaurants_list = memory.get_restaurants(city=city or None, cuisine=cuisine or None, limit=50)
    
    stats = memory.get_stats()
    cities = list(stats.get("restaurants_by_city", {}).keys())
    cuisines = list(stats.get("cuisines", {}).keys())
    
    return render_template("restaurants.html",
        restaurants=restaurants_list,
        cities=cities,
        cuisines=cuisines,
        filters={"city": city, "cuisine": cuisine, "q": search_query}
    )


@app.route("/restaurants/<restaurant_id>")
def restaurant_detail(restaurant_id):
    """Restaurant detail page."""
    restaurant = memory.get_restaurant(restaurant_id)
    if not restaurant:
        return render_template("error.html", error="Restaurant not found"), 404
    
    selections = memory.get_selections(restaurant_id=restaurant_id, limit=10)
    
    return render_template("restaurant_detail.html",
        restaurant=restaurant,
        selections=selections
    )


@app.route("/restaurants/<restaurant_id>/menu", methods=["POST"])
def fetch_menu(restaurant_id):
    """Fetch menu for a restaurant."""
    restaurant = memory.get_restaurant(restaurant_id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    
    url = restaurant.get("menu_url") or restaurant.get("website")
    if not url:
        return jsonify({"error": "No URL available"}), 400
    
    args = ["--url", url, "--name", restaurant.get("name", ""), "--pretty"]
    result = run_subagent("menu_extractor", args)
    
    if "dishes" in result and not result.get("error"):
        memory.update_restaurant_menu(restaurant_id, result)
    
    return redirect(url_for("restaurant_detail", restaurant_id=restaurant_id))


@app.route("/search", methods=["GET", "POST"])
def search():
    """Search for restaurants in a city."""
    results = None
    city = request.form.get("city", "") or request.args.get("city", "")
    cuisine = request.form.get("cuisine", "")
    
    if request.method == "POST" and city:
        args = ["--city", city, "--pretty"]
        if cuisine:
            args.extend(["--cuisine", cuisine])
        
        results = run_subagent("restaurant_search", args)
        
        if "restaurants" in results:
            for restaurant in results["restaurants"]:
                restaurant["city"] = city
                memory.store_restaurant(restaurant)
    
    return render_template("search.html", results=results, city=city, cuisine=cuisine)


@app.route("/preferences", methods=["GET", "POST"])
def preferences():
    """Preferences management page."""
    if request.method == "POST":
        prefs = memory.get_preferences() or {"user_id": "default"}
        
        prefs["liked_cuisines"] = [c.strip() for c in request.form.get("liked_cuisines", "").split(",") if c.strip()]
        prefs["disliked_cuisines"] = [c.strip() for c in request.form.get("disliked_cuisines", "").split(",") if c.strip()]
        prefs["dietary_restrictions"] = request.form.getlist("dietary_restrictions")
        prefs["allergies"] = [a.strip() for a in request.form.get("allergies", "").split(",") if a.strip()]
        prefs["avoided_ingredients"] = [i.strip() for i in request.form.get("avoided_ingredients", "").split(",") if i.strip()]
        prefs["price_preference"] = request.form.get("price_preference", "any")
        prefs["spice_tolerance"] = request.form.get("spice_tolerance", "medium")
        prefs["variety_preference"] = request.form.get("variety_preference", "balanced")
        
        memory.set_preferences(prefs)
        return redirect(url_for("preferences"))
    
    prefs = memory.get_preferences() or {}
    return render_template("preferences.html", prefs=prefs)


@app.route("/selections")
def selections():
    """Selection history page."""
    days = request.args.get("days", type=int)
    min_rating = request.args.get("min_rating", type=int)
    
    selections_list = memory.get_selections(days=days, min_rating=min_rating, limit=100)
    
    return render_template("selections.html",
        selections=selections_list,
        filters={"days": days, "min_rating": min_rating}
    )


@app.route("/selections/add", methods=["POST"])
def add_selection():
    """Record a new selection."""
    selection = {
        "restaurant_name": request.form.get("restaurant_name"),
        "dish_name": request.form.get("dish_name"),
        "cuisine_type": request.form.get("cuisine_type"),
        "city": request.form.get("city"),
        "rating": int(request.form.get("rating")) if request.form.get("rating") else None,
        "notes": request.form.get("notes"),
    }
    selection = {k: v for k, v in selection.items() if v}
    
    memory.store_selection(selection)
    return redirect(url_for("selections"))


@app.route("/recommend")
def recommend():
    """Get lunch recommendation page."""
    city = request.args.get("city", "")
    recommendation = None
    
    if city:
        from lunch_selection_agent import build_recommendation
        recommendation = build_recommendation(city, memory, exclude_days=7)
    
    stats = memory.get_stats()
    cities = list(stats.get("restaurants_by_city", {}).keys())
    
    return render_template("recommend.html",
        recommendation=recommendation,
        city=city,
        cities=cities
    )


@app.route("/chat")
def chat_page():
    """Chat interface page."""
    prefs = memory.get_preferences() or {}
    stats = memory.get_stats()
    cities = list(stats.get("restaurants_by_city", {}).keys())
    
    return render_template("chat.html", prefs=prefs, cities=cities)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """API endpoint for chat with the agent."""
    from flask import Response, stream_with_context
    
    data = request.get_json() or {}
    message = data.get("message", "")
    city = data.get("city", "")
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    if city:
        message = f"[City: {city}] {message}"
    
    agent_path = AGENT_DIR / "lunch_selection_agent.py"
    
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
                    if 'search' in line.lower() or 'restaurant' in line.lower():
                        yield f"data: {json.dumps({'type': 'status', 'message': f'🔍 {line}'})}\n\n"
                    elif 'menu' in line.lower() or 'extract' in line.lower():
                        yield f"data: {json.dumps({'type': 'status', 'message': f'📋 {line}'})}\n\n"
                    elif 'recommend' in line.lower():
                        yield f"data: {json.dumps({'type': 'status', 'message': f'💡 {line}'})}\n\n"
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


# ==================== Templates ====================

TEMPLATES_DIR = Path(__file__).parent / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

BASE_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Lunch Selection Agent{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .sidebar { min-height: 100vh; background: #f8f9fa; }
        .restaurant-card { transition: box-shadow 0.2s; }
        .restaurant-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .dietary-badge { font-size: 0.75rem; }
        .price-budget { color: #198754; }
        .price-moderate { color: #fd7e14; }
        .price-expensive { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <nav class="col-md-2 sidebar py-3">
                <h5 class="mb-3">🍽️ Lunch Agent</h5>
                <ul class="nav flex-column">
                    <li class="nav-item"><a class="nav-link" href="/">Dashboard</a></li>
                    <li class="nav-item"><a class="nav-link" href="/chat">Chat</a></li>
                    <li class="nav-item"><a class="nav-link" href="/search">Search</a></li>
                    <li class="nav-item"><a class="nav-link" href="/restaurants">Restaurants</a></li>
                    <li class="nav-item"><a class="nav-link" href="/recommend">Recommend</a></li>
                    <li class="nav-item"><a class="nav-link" href="/selections">History</a></li>
                    <li class="nav-item"><a class="nav-link" href="/preferences">Preferences</a></li>
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
{% block title %}Dashboard - Lunch Selection Agent{% endblock %}
{% block content %}
<h2>🍽️ Lunch Selection Dashboard</h2>
<p class="lead">{{ today }}, {{ today_date }}</p>

<div class="row mb-4">
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Restaurants</h5>
                <p class="display-6">{{ stats.get('total_restaurants', 0) }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Selections</h5>
                <p class="display-6">{{ stats.get('total_selections', 0) }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Avg Rating</h5>
                <p class="display-6">{{ stats.get('average_rating') or '-' }}</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Preferences</h5>
                <p class="text-muted">{{ 'Set' if prefs.get('liked_cuisines') else 'Not set' }}</p>
                <a href="/preferences" class="btn btn-sm btn-outline-primary">Configure</a>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <h4>Quick Actions</h4>
        <div class="list-group">
            <a href="/chat" class="list-group-item list-group-item-action">💬 Chat with agent</a>
            <a href="/search" class="list-group-item list-group-item-action">🔍 Search restaurants</a>
            <a href="/recommend" class="list-group-item list-group-item-action">💡 Get recommendation</a>
        </div>
    </div>
    <div class="col-md-6">
        <h4>Recent Selections</h4>
        {% if recent_selections %}
        <ul class="list-group">
            {% for sel in recent_selections %}
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <strong>{{ sel.dish_name }}</strong>
                    <small class="text-muted">at {{ sel.restaurant_name }}</small>
                </div>
                {% if sel.rating %}
                <span class="badge bg-primary">{{ sel.rating }}⭐</span>
                {% endif %}
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <p class="text-muted">No recent selections. Start recording your lunches!</p>
        {% endif %}
    </div>
</div>
{% endblock %}'''

RESTAURANTS_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Restaurants - Lunch Selection Agent{% endblock %}
{% block content %}
<h2>Restaurants</h2>

<form method="GET" class="row g-3 mb-4">
    <div class="col-md-3">
        <select name="city" class="form-select">
            <option value="">All Cities</option>
            {% for city in cities %}
            <option value="{{ city }}" {{ 'selected' if filters.city == city }}>{{ city }}</option>
            {% endfor %}
        </select>
    </div>
    <div class="col-md-3">
        <select name="cuisine" class="form-select">
            <option value="">All Cuisines</option>
            {% for cuisine in cuisines %}
            <option value="{{ cuisine }}" {{ 'selected' if filters.cuisine == cuisine }}>{{ cuisine }}</option>
            {% endfor %}
        </select>
    </div>
    <div class="col-md-4">
        <input type="text" name="q" class="form-control" placeholder="Search..." value="{{ filters.q }}">
    </div>
    <div class="col-md-2">
        <button type="submit" class="btn btn-primary w-100">Filter</button>
    </div>
</form>

<div class="row">
    {% for r in restaurants %}
    <div class="col-md-4 mb-3">
        <div class="card restaurant-card h-100">
            <div class="card-body">
                <h5 class="card-title">{{ r.name }}</h5>
                <p class="card-text text-muted">{{ r.city }}{% if r.address %} - {{ r.address }}{% endif %}</p>
                <p>
                    {% for cuisine in r.get('cuisine_types', [])[:3] %}
                    <span class="badge bg-info">{{ cuisine }}</span>
                    {% endfor %}
                    {% if r.price_range %}
                    <span class="badge bg-{{ 'success' if r.price_range == 'budget' else 'warning' if r.price_range == 'moderate' else 'danger' }}">{{ r.price_range }}</span>
                    {% endif %}
                </p>
                <a href="/restaurants/{{ r.id }}" class="btn btn-sm btn-outline-primary">View</a>
                {% if r.website %}
                <a href="{{ r.website }}" target="_blank" class="btn btn-sm btn-outline-secondary">Website</a>
                {% endif %}
            </div>
        </div>
    </div>
    {% else %}
    <div class="col-12">
        <p class="text-muted">No restaurants found. <a href="/search">Search for restaurants</a> first.</p>
    </div>
    {% endfor %}
</div>
{% endblock %}'''

RESTAURANT_DETAIL_TEMPLATE = '''{% extends "base.html" %}
{% block title %}{{ restaurant.name }} - Lunch Selection Agent{% endblock %}
{% block content %}
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="/restaurants">Restaurants</a></li>
        <li class="breadcrumb-item active">{{ restaurant.name }}</li>
    </ol>
</nav>

<div class="row">
    <div class="col-md-8">
        <h2>{{ restaurant.name }}</h2>
        <p class="lead">{{ restaurant.city }}{% if restaurant.address %} - {{ restaurant.address }}{% endif %}</p>
        
        <p>
            {% for cuisine in restaurant.get('cuisine_types', []) %}
            <span class="badge bg-info">{{ cuisine }}</span>
            {% endfor %}
            {% if restaurant.price_range %}
            <span class="badge bg-secondary">{{ restaurant.price_range }}</span>
            {% endif %}
        </p>
        
        {% if restaurant.website %}
        <p><a href="{{ restaurant.website }}" target="_blank">{{ restaurant.website }}</a></p>
        {% endif %}
        
        {% if restaurant.cached_menu and restaurant.cached_menu.dishes %}
        <h4 class="mt-4">Today's Menu</h4>
        <small class="text-muted">Last fetched: {{ restaurant.last_menu_fetch[:10] if restaurant.last_menu_fetch else 'Never' }}</small>
        <ul class="list-group mt-2">
            {% for dish in restaurant.cached_menu.dishes %}
            <li class="list-group-item d-flex justify-content-between align-items-start">
                <div>
                    <strong>{{ dish.name }}</strong>
                    {% if dish.description %}<br><small class="text-muted">{{ dish.description }}</small>{% endif %}
                    {% for tag in dish.get('dietary', []) %}
                    <span class="badge bg-success dietary-badge">{{ tag }}</span>
                    {% endfor %}
                </div>
                {% if dish.price %}
                <span class="badge bg-primary">€{{ dish.price }}</span>
                {% endif %}
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <div class="alert alert-info mt-4">
            <p>No menu cached. Fetch today's menu to see lunch options.</p>
            <form method="POST" action="/restaurants/{{ restaurant.id }}/menu">
                <button type="submit" class="btn btn-primary">Fetch Menu</button>
            </form>
        </div>
        {% endif %}
    </div>
    
    <div class="col-md-4">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Actions</h5>
                <form method="POST" action="/restaurants/{{ restaurant.id }}/menu" class="mb-3">
                    <button type="submit" class="btn btn-success w-100">🔄 Refresh Menu</button>
                </form>
                
                <h6 class="mt-4">Record Selection</h6>
                <form method="POST" action="/selections/add">
                    <input type="hidden" name="restaurant_name" value="{{ restaurant.name }}">
                    <input type="hidden" name="city" value="{{ restaurant.city }}">
                    <div class="mb-2">
                        <input type="text" name="dish_name" class="form-control" placeholder="Dish name" required>
                    </div>
                    <div class="mb-2">
                        <select name="rating" class="form-select">
                            <option value="">Rate (optional)</option>
                            <option value="5">⭐⭐⭐⭐⭐ (5)</option>
                            <option value="4">⭐⭐⭐⭐ (4)</option>
                            <option value="3">⭐⭐⭐ (3)</option>
                            <option value="2">⭐⭐ (2)</option>
                            <option value="1">⭐ (1)</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Record Selection</button>
                </form>
            </div>
        </div>
        
        {% if selections %}
        <div class="card mt-3">
            <div class="card-body">
                <h6>Your History Here</h6>
                <ul class="list-group list-group-flush">
                    {% for sel in selections %}
                    <li class="list-group-item d-flex justify-content-between">
                        <span>{{ sel.dish_name }}</span>
                        {% if sel.rating %}<span>{{ sel.rating }}⭐</span>{% endif %}
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}'''

SEARCH_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Search - Lunch Selection Agent{% endblock %}
{% block content %}
<h2>Search Restaurants</h2>

<form method="POST" class="row g-3 mb-4">
    <div class="col-md-5">
        <label class="form-label">City</label>
        <input type="text" name="city" class="form-control" value="{{ city }}" placeholder="e.g., Helsinki, Tampere, Oulu" required>
    </div>
    <div class="col-md-5">
        <label class="form-label">Cuisine (optional)</label>
        <input type="text" name="cuisine" class="form-control" value="{{ cuisine }}" placeholder="e.g., Italian, Thai, Finnish">
    </div>
    <div class="col-md-2 d-flex align-items-end">
        <button type="submit" class="btn btn-primary w-100">Search</button>
    </div>
</form>

{% if results %}
    {% if results.error %}
    <div class="alert alert-danger">{{ results.error }}</div>
    {% else %}
    <p class="text-muted">Found {{ results.get('restaurants', [])|length }} restaurants in {{ city }}</p>
    <div class="row">
        {% for r in results.get('restaurants', []) %}
        <div class="col-md-6 mb-3">
            <div class="card restaurant-card">
                <div class="card-body">
                    <h5 class="card-title">{{ r.name }}</h5>
                    <p class="card-text text-muted">{{ r.address or r.city }}</p>
                    <p>
                        {% for cuisine in r.get('cuisine_types', [])[:3] %}
                        <span class="badge bg-info">{{ cuisine }}</span>
                        {% endfor %}
                    </p>
                    {% if r.website %}
                    <a href="{{ r.website }}" target="_blank" class="btn btn-sm btn-outline-secondary">Website</a>
                    {% endif %}
                    <span class="badge bg-success">Saved ✓</span>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
    <a href="/restaurants?city={{ city }}" class="btn btn-primary">View All in {{ city }}</a>
    {% endif %}
{% endif %}
{% endblock %}'''

PREFERENCES_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Preferences - Lunch Selection Agent{% endblock %}
{% block content %}
<h2>Food Preferences</h2>
<p class="text-muted">Configure your preferences for better recommendations</p>

<form method="POST">
    <div class="row g-3">
        <div class="col-md-6">
            <label class="form-label">Liked Cuisines (comma-separated)</label>
            <input type="text" name="liked_cuisines" class="form-control" 
                   value="{{ prefs.get('liked_cuisines', [])|join(', ') }}"
                   placeholder="Italian, Thai, Finnish, Mexican">
        </div>
        
        <div class="col-md-6">
            <label class="form-label">Disliked Cuisines (comma-separated)</label>
            <input type="text" name="disliked_cuisines" class="form-control" 
                   value="{{ prefs.get('disliked_cuisines', [])|join(', ') }}"
                   placeholder="Fast food, Deep fried">
        </div>
        
        <div class="col-md-6">
            <label class="form-label">Dietary Restrictions</label>
            <div>
                {% for restriction in ['vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'nut-free', 'halal', 'kosher', 'pescatarian', 'low-carb'] %}
                <div class="form-check form-check-inline">
                    <input class="form-check-input" type="checkbox" name="dietary_restrictions" 
                           value="{{ restriction }}" {{ 'checked' if restriction in prefs.get('dietary_restrictions', []) }}>
                    <label class="form-check-label">{{ restriction }}</label>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="col-md-6">
            <label class="form-label">Allergies (comma-separated)</label>
            <input type="text" name="allergies" class="form-control" 
                   value="{{ prefs.get('allergies', [])|join(', ') }}"
                   placeholder="shellfish, peanuts, eggs">
        </div>
        
        <div class="col-md-6">
            <label class="form-label">Avoided Ingredients (comma-separated)</label>
            <input type="text" name="avoided_ingredients" class="form-control" 
                   value="{{ prefs.get('avoided_ingredients', [])|join(', ') }}"
                   placeholder="cilantro, mushrooms, olives">
        </div>
        
        <div class="col-md-3">
            <label class="form-label">Price Preference</label>
            <select name="price_preference" class="form-select">
                <option value="any" {{ 'selected' if prefs.get('price_preference') == 'any' }}>Any</option>
                <option value="budget" {{ 'selected' if prefs.get('price_preference') == 'budget' }}>Budget</option>
                <option value="moderate" {{ 'selected' if prefs.get('price_preference') == 'moderate' }}>Moderate</option>
                <option value="expensive" {{ 'selected' if prefs.get('price_preference') == 'expensive' }}>Expensive</option>
            </select>
        </div>
        
        <div class="col-md-3">
            <label class="form-label">Spice Tolerance</label>
            <select name="spice_tolerance" class="form-select">
                <option value="none" {{ 'selected' if prefs.get('spice_tolerance') == 'none' }}>None</option>
                <option value="mild" {{ 'selected' if prefs.get('spice_tolerance') == 'mild' }}>Mild</option>
                <option value="medium" {{ 'selected' if prefs.get('spice_tolerance') == 'medium' }}>Medium</option>
                <option value="hot" {{ 'selected' if prefs.get('spice_tolerance') == 'hot' }}>Hot</option>
                <option value="extra-hot" {{ 'selected' if prefs.get('spice_tolerance') == 'extra-hot' }}>Extra Hot</option>
            </select>
        </div>
        
        <div class="col-md-6">
            <label class="form-label">Variety Preference</label>
            <select name="variety_preference" class="form-select">
                <option value="stick-to-favorites" {{ 'selected' if prefs.get('variety_preference') == 'stick-to-favorites' }}>Stick to Favorites</option>
                <option value="balanced" {{ 'selected' if prefs.get('variety_preference') == 'balanced' }}>Balanced</option>
                <option value="adventurous" {{ 'selected' if prefs.get('variety_preference') == 'adventurous' }}>Adventurous</option>
            </select>
        </div>
    </div>
    
    <button type="submit" class="btn btn-primary mt-4">Save Preferences</button>
</form>
{% endblock %}'''

SELECTIONS_TEMPLATE = '''{% extends "base.html" %}
{% block title %}History - Lunch Selection Agent{% endblock %}
{% block content %}
<h2>Lunch History</h2>

<form method="GET" class="row g-3 mb-4">
    <div class="col-md-3">
        <select name="days" class="form-select">
            <option value="">All Time</option>
            <option value="7" {{ 'selected' if filters.days == 7 }}>Last 7 days</option>
            <option value="30" {{ 'selected' if filters.days == 30 }}>Last 30 days</option>
            <option value="90" {{ 'selected' if filters.days == 90 }}>Last 90 days</option>
        </select>
    </div>
    <div class="col-md-3">
        <select name="min_rating" class="form-select">
            <option value="">Any Rating</option>
            <option value="4" {{ 'selected' if filters.min_rating == 4 }}>4+ stars</option>
            <option value="3" {{ 'selected' if filters.min_rating == 3 }}>3+ stars</option>
        </select>
    </div>
    <div class="col-auto">
        <button type="submit" class="btn btn-outline-primary">Filter</button>
    </div>
</form>

<table class="table table-hover">
    <thead>
        <tr>
            <th>Date</th>
            <th>Restaurant</th>
            <th>Dish</th>
            <th>Rating</th>
            <th>Notes</th>
        </tr>
    </thead>
    <tbody>
        {% for sel in selections %}
        <tr>
            <td>{{ sel.date }}</td>
            <td>{{ sel.restaurant_name }}</td>
            <td>{{ sel.dish_name }}</td>
            <td>{% if sel.rating %}{{ '⭐' * sel.rating }}{% else %}-{% endif %}</td>
            <td>{{ sel.notes or '-' }}</td>
        </tr>
        {% else %}
        <tr><td colspan="5" class="text-muted">No selections recorded yet.</td></tr>
        {% endfor %}
    </tbody>
</table>

<h4 class="mt-4">Record New Selection</h4>
<form method="POST" action="/selections/add" class="row g-3">
    <div class="col-md-3">
        <input type="text" name="restaurant_name" class="form-control" placeholder="Restaurant name" required>
    </div>
    <div class="col-md-3">
        <input type="text" name="dish_name" class="form-control" placeholder="Dish name" required>
    </div>
    <div class="col-md-2">
        <input type="text" name="city" class="form-control" placeholder="City">
    </div>
    <div class="col-md-2">
        <select name="rating" class="form-select">
            <option value="">Rating</option>
            <option value="5">5 ⭐</option>
            <option value="4">4 ⭐</option>
            <option value="3">3 ⭐</option>
            <option value="2">2 ⭐</option>
            <option value="1">1 ⭐</option>
        </select>
    </div>
    <div class="col-md-2">
        <button type="submit" class="btn btn-primary w-100">Add</button>
    </div>
</form>
{% endblock %}'''

RECOMMEND_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Recommend - Lunch Selection Agent{% endblock %}
{% block content %}
<h2>💡 Get Lunch Recommendation</h2>

<form method="GET" class="row g-3 mb-4">
    <div class="col-md-4">
        <label class="form-label">City</label>
        <select name="city" class="form-select" required>
            <option value="">Select a city...</option>
            {% for c in cities %}
            <option value="{{ c }}" {{ 'selected' if city == c }}>{{ c }}</option>
            {% endfor %}
        </select>
    </div>
    <div class="col-md-2 d-flex align-items-end">
        <button type="submit" class="btn btn-primary">Get Recommendation</button>
    </div>
</form>

{% if recommendation %}
    {% if recommendation.recommendation %}
    <div class="card">
        <div class="card-body">
            <h3 class="card-title">🎯 {{ recommendation.recommendation.dish_name or 'Visit this restaurant' }}</h3>
            <h5 class="card-subtitle text-muted">at {{ recommendation.recommendation.restaurant_name }}</h5>
            
            {% if recommendation.recommendation.dish_description %}
            <p class="mt-3">{{ recommendation.recommendation.dish_description }}</p>
            {% endif %}
            
            {% if recommendation.recommendation.price %}
            <p><strong>Price:</strong> €{{ recommendation.recommendation.price }}</p>
            {% endif %}
            
            <p class="text-muted"><em>{{ recommendation.recommendation.reason }}</em></p>
            
            {% if recommendation.alternatives %}
            <h6 class="mt-4">Other options:</h6>
            <ul>
                {% for alt in recommendation.alternatives %}
                <li><strong>{{ alt.dish_name or 'Visit' }}</strong> at {{ alt.restaurant_name }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
    </div>
    {% else %}
    <div class="alert alert-info">
        {{ recommendation.message }}
        {% if recommendation.suggestion %}
        <p class="mb-0 mt-2"><strong>Suggestion:</strong> {{ recommendation.suggestion }}</p>
        {% endif %}
    </div>
    {% endif %}
{% elif city %}
<div class="alert alert-warning">
    No restaurants found for {{ city }}. <a href="/search?city={{ city }}">Search for restaurants</a> first.
</div>
{% endif %}
{% endblock %}'''

CHAT_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Chat - Lunch Selection Agent{% endblock %}
{% block content %}
<style>
    .chat-bubble {
        max-width: 85%;
        word-wrap: break-word;
    }
    .status-panel {
        background: #1a1a2e;
        color: #0f0;
        font-family: monospace;
        font-size: 12px;
        border-radius: 8px;
        padding: 12px;
        max-height: 150px;
        overflow-y: auto;
    }
</style>

<div class="d-flex flex-column" style="height: calc(100vh - 100px);">
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h2 class="mb-0">💬 Chat with Lunch Agent</h2>
        <select id="city-select" class="form-select w-auto">
            <option value="">No default city</option>
            {% for c in cities %}
            <option value="{{ c }}">{{ c }}</option>
            {% endfor %}
        </select>
    </div>
    
    <div class="status-panel mb-3" id="status-panel" style="display: none;">
        <div id="status-messages"></div>
    </div>
    
    <div class="card flex-grow-1 mb-3">
        <div class="card-body overflow-auto" id="chat-messages" style="max-height: 50vh;">
            <div class="text-muted text-center py-5" id="welcome-message">
                <h5>Welcome to the Lunch Agent!</h5>
                <p>Ask me to find restaurants, get menus, or recommend something to eat.</p>
                <p class="small">Try: "Find lunch places in Helsinki" or "What should I eat today?"</p>
            </div>
        </div>
    </div>
    
    <form id="chat-form" class="d-flex gap-2">
        <input type="text" id="chat-input" class="form-control form-control-lg" 
               placeholder="Ask about lunch..." autofocus>
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
const citySelect = document.getElementById('city-select');

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
            body: JSON.stringify({ message, city: citySelect.value })
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

ERROR_TEMPLATE = '''{% extends "base.html" %}
{% block title %}Error - Lunch Selection Agent{% endblock %}
{% block content %}
<div class="alert alert-danger">
    <h4>Error</h4>
    <p>{{ error }}</p>
</div>
<a href="/" class="btn btn-primary">Go to Dashboard</a>
{% endblock %}'''

templates = {
    "base.html": BASE_TEMPLATE,
    "index.html": INDEX_TEMPLATE,
    "restaurants.html": RESTAURANTS_TEMPLATE,
    "restaurant_detail.html": RESTAURANT_DETAIL_TEMPLATE,
    "search.html": SEARCH_TEMPLATE,
    "preferences.html": PREFERENCES_TEMPLATE,
    "selections.html": SELECTIONS_TEMPLATE,
    "recommend.html": RECOMMEND_TEMPLATE,
    "chat.html": CHAT_TEMPLATE,
    "error.html": ERROR_TEMPLATE
}

for name, content in templates.items():
    template_path = TEMPLATES_DIR / name
    if not template_path.exists():
        with open(template_path, "w") as f:
            f.write(content)


# ==================== Run ====================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
