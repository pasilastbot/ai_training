#!/usr/bin/env python3
"""
Holiday Planner Web UI

Flask-based web interface for the Holiday Planner agent.
Provides a dashboard for family management, destination exploration, and trip planning.

Usage:
    python ui/app.py
    # Or with flask
    FLASK_APP=ui/app.py flask run --port 5004
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_env import load_agent_environment
load_agent_environment()

from flask import Flask, render_template, request, jsonify, redirect, url_for

from memory.memory import (
    init_database, get_family, list_families, create_family,
    add_family_member, update_member_preferences, update_family,
    get_trip, list_trips, create_trip, update_trip, get_stats
)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "holiday-planner-secret-key")


@app.before_request
def setup():
    """Initialize database."""
    init_database()


# ============ Dashboard ============

@app.route("/")
def index():
    """Main dashboard."""
    stats = get_stats()
    families = list_families(limit=5)
    trips = list_trips(limit=5)
    
    return render_template("index.html",
        stats=stats,
        families=families,
        recent_trips=trips
    )


# ============ Family Management ============

@app.route("/families")
def family_list():
    """List all families."""
    families = list_families(limit=50)
    return render_template("families.html", families=families)


@app.route("/families/new", methods=["GET", "POST"])
def new_family():
    """Create new family."""
    if request.method == "POST":
        name = request.form.get("name")
        
        members = []
        member_names = request.form.getlist("member_name[]")
        member_roles = request.form.getlist("member_role[]")
        member_ages = request.form.getlist("member_age[]")
        
        for i in range(len(member_names)):
            if member_names[i]:
                members.append({
                    "name": member_names[i],
                    "role": member_roles[i] if i < len(member_roles) else "adult",
                    "age": int(member_ages[i]) if i < len(member_ages) and member_ages[i] else None
                })
        
        family = create_family(name, members if members else None)
        return redirect(url_for("family_detail", family_id=family["id"]))
    
    return render_template("new_family.html")


@app.route("/families/<family_id>")
def family_detail(family_id):
    """Family profile detail."""
    family = get_family(family_id)
    if not family:
        return render_template("error.html", message="Family not found"), 404
    
    trips = list_trips(family_id=family_id)
    
    return render_template("family_detail.html",
        family=family,
        trips=trips
    )


@app.route("/families/<family_id>/member", methods=["POST"])
def add_member(family_id):
    """Add family member."""
    member = {
        "name": request.form.get("name"),
        "role": request.form.get("role"),
        "age": int(request.form.get("age")) if request.form.get("age") else None
    }
    
    add_family_member(family_id, member)
    return redirect(url_for("family_detail", family_id=family_id))


@app.route("/families/<family_id>/preferences/<member_id>", methods=["POST"])
def update_preferences(family_id, member_id):
    """Update member preferences."""
    prefs = {
        "activity_types": request.form.getlist("activity_types"),
        "must_haves": [x.strip() for x in request.form.get("must_haves", "").split(",") if x.strip()],
        "deal_breakers": [x.strip() for x in request.form.get("deal_breakers", "").split(",") if x.strip()],
        "climate_preference": request.form.get("climate_preference")
    }
    
    update_member_preferences(family_id, member_id, prefs)
    return redirect(url_for("family_detail", family_id=family_id))


@app.route("/families/<family_id>/constraints", methods=["POST"])
def set_constraints(family_id):
    """Set family constraints."""
    constraints = {}
    
    if request.form.get("budget_max"):
        constraints["budget"] = {
            "max": float(request.form.get("budget_max")),
            "currency": "EUR"
        }
    
    if request.form.get("preferred_duration"):
        constraints["duration"] = {
            "preferred_days": int(request.form.get("preferred_duration"))
        }
    
    if request.form.get("departure_location"):
        constraints["departure_location"] = request.form.get("departure_location")
    
    if request.form.get("max_flight_hours"):
        constraints["max_flight_hours"] = float(request.form.get("max_flight_hours"))
    
    preferred_months = request.form.getlist("preferred_months")
    if preferred_months:
        constraints["travel_dates"] = {
            "preferred_months": [int(m) for m in preferred_months]
        }
    
    update_family(family_id, {"constraints": constraints})
    return redirect(url_for("family_detail", family_id=family_id))


# ============ Trip Planning ============

@app.route("/trips")
def trip_list():
    """List all trips."""
    family_id = request.args.get("family_id")
    status = request.args.get("status")
    
    trips = list_trips(family_id=family_id, status=status)
    families = list_families()
    
    return render_template("trips.html",
        trips=trips,
        families=families,
        selected_family=family_id,
        selected_status=status
    )


@app.route("/trips/new", methods=["GET", "POST"])
def new_trip():
    """Create new trip."""
    if request.method == "POST":
        name = request.form.get("name")
        family_id = request.form.get("family_id") or None
        
        destinations = []
        dest_names = request.form.getlist("dest_name[]")
        dest_countries = request.form.getlist("dest_country[]")
        dest_days = request.form.getlist("dest_days[]")
        
        for i in range(len(dest_names)):
            if dest_names[i]:
                destinations.append({
                    "name": dest_names[i],
                    "country": dest_countries[i] if i < len(dest_countries) else "",
                    "duration_days": int(dest_days[i]) if i < len(dest_days) and dest_days[i] else 7
                })
        
        trip = create_trip(name, family_id, destinations if destinations else None)
        return redirect(url_for("trip_detail", trip_id=trip["id"]))
    
    families = list_families()
    family_id = request.args.get("family_id")
    
    return render_template("new_trip.html",
        families=families,
        selected_family=family_id
    )


@app.route("/trips/<trip_id>")
def trip_detail(trip_id):
    """Trip detail."""
    trip = get_trip(trip_id)
    if not trip:
        return render_template("error.html", message="Trip not found"), 404
    
    family = None
    if trip.get("family_id"):
        family = get_family(trip["family_id"])
    
    return render_template("trip_detail.html",
        trip=trip,
        family=family
    )


@app.route("/trips/<trip_id>/update", methods=["POST"])
def update_trip_endpoint(trip_id):
    """Update trip."""
    updates = {}
    
    if request.form.get("name"):
        updates["name"] = request.form.get("name")
    
    if request.form.get("status"):
        updates["status"] = request.form.get("status")
    
    if request.form.get("start_date"):
        updates["travel_dates"] = {
            "start": request.form.get("start_date"),
            "end": request.form.get("end_date"),
            "duration_days": int(request.form.get("duration_days", 7))
        }
    
    update_trip(trip_id, updates)
    return redirect(url_for("trip_detail", trip_id=trip_id))


# ============ Destinations ============

@app.route("/destinations")
def destination_search():
    """Search destinations."""
    query = request.args.get("q")
    family_id = request.args.get("family_id")
    
    results = None
    if query:
        from tools.search_destinations import search_destinations
        family = get_family(family_id) if family_id else None
        results = search_destinations(query, family_profile=family, num_results=5)
    
    families = list_families()
    
    return render_template("destinations.html",
        query=query,
        results=results,
        families=families,
        selected_family=family_id
    )


@app.route("/destinations/<destination>")
def destination_detail(destination):
    """Destination detail."""
    country = request.args.get("country")
    
    from tools.search_destinations import get_destination_details
    details = get_destination_details(destination, country)
    
    return render_template("destination_detail.html",
        destination=destination,
        country=country,
        details=details
    )


# ============ Budget ============

@app.route("/budget")
def budget_calculator():
    """Budget calculator."""
    return render_template("budget.html")


@app.route("/budget/calculate", methods=["POST"])
def calculate_budget():
    """Calculate budget."""
    from tools.budget_calculator import estimate_budget
    
    result = estimate_budget(
        request.form.get("destination"),
        request.form.get("country"),
        int(request.form.get("duration_days", 7)),
        int(request.form.get("adults", 2)),
        int(request.form.get("children", 0)),
        int(request.form.get("teens", 0)),
        request.form.get("travel_style", "mid-range"),
        request.form.get("departure_city", "Helsinki"),
        int(request.form.get("month")) if request.form.get("month") else None
    )
    
    return render_template("budget_result.html",
        result=result,
        destination=request.form.get("destination")
    )


# ============ Compare ============

@app.route("/compare")
def compare_page():
    """Comparison page."""
    return render_template("compare.html")


@app.route("/compare/destinations", methods=["POST"])
def compare_destinations():
    """Compare destinations."""
    from tools.compare_options import compare_trips
    from tools.search_destinations import get_destination_details
    
    destinations = request.form.getlist("destinations")
    family_id = request.form.get("family_id")
    
    trips = []
    for dest in destinations:
        if dest:
            details = get_destination_details(dest)
            trips.append({
                "name": dest,
                "destinations": [details] if details else [{"name": dest}],
                "budget": details.get("budget_estimate", {}) if details else {}
            })
    
    family = get_family(family_id) if family_id else None
    comparison = compare_trips(trips, family)
    
    families = list_families()
    
    return render_template("compare_result.html",
        comparison=comparison,
        destinations=destinations,
        families=families,
        selected_family=family_id
    )


# ============ Chat ============

@app.route("/chat")
def chat_page():
    """Chat interface."""
    family_id = request.args.get("family_id")
    family = get_family(family_id) if family_id else None
    families = list_families()
    
    return render_template("chat.html",
        family=family,
        families=families,
        selected_family=family_id
    )


@app.route("/chat/send", methods=["POST"])
def send_message():
    """Send chat message."""
    from holiday_planner import process_query, get_client
    
    message = request.json.get("message")
    family_id = request.json.get("family_id")
    history = request.json.get("history", [])
    
    try:
        client = get_client()
        response, _ = process_query(message, client, family_id, history)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ API Endpoints ============

@app.route("/api/destinations/search")
def api_search_destinations():
    """API: Search destinations."""
    from tools.search_destinations import search_destinations
    
    query = request.args.get("q")
    family_id = request.args.get("family_id")
    num = int(request.args.get("num", 5))
    
    family = get_family(family_id) if family_id else None
    result = search_destinations(query, family_profile=family, num_results=num)
    
    return jsonify(result)


@app.route("/api/weather/<destination>")
def api_weather(destination):
    """API: Get weather."""
    from tools.weather_info import get_weather_info
    
    month = request.args.get("month")
    result = get_weather_info(
        destination,
        month=int(month) if month else None
    )
    
    return jsonify(result)


@app.route("/api/budget/estimate", methods=["POST"])
def api_budget():
    """API: Estimate budget."""
    from tools.budget_calculator import estimate_budget
    
    data = request.json
    result = estimate_budget(
        data.get("destination"),
        data.get("country"),
        data.get("duration_days", 7),
        data.get("adults", 2),
        data.get("children", 0),
        data.get("teens", 0),
        data.get("travel_style", "mid-range"),
        data.get("departure_city", "Helsinki"),
        data.get("month")
    )
    
    return jsonify(result)


# ============ Error Handlers ============

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", message="Server error"), 500


# ============ Main ============

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
