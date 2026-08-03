#!/usr/bin/env python3
"""
Energy Advisor Web UI

Flask-based web interface for the Energy Advisor agent.
Provides a dashboard for energy advice, apartment management, and video interactions.

Usage:
    python ui/app.py
    # Or with flask
    FLASK_APP=ui/app.py flask run --port 5005
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_env import load_agent_environment
load_agent_environment()

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, Response

from memory.memory import (
    init_database, get_apartment, get_apartment_by_customer, list_apartments,
    create_apartment, update_apartment, search_apartments, get_apartment_summary,
    get_recommendations, create_recommendation, get_stats, store_video_response,
    get_recent_video_responses
)

AGENT_DIR = Path(__file__).parent.parent

app = Flask(__name__, 
            template_folder=str(AGENT_DIR / "ui" / "templates"),
            static_folder=str(AGENT_DIR / "ui" / "static"))
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "energy-advisor-secret-key")


@app.before_request
def setup():
    """Initialize database."""
    init_database()


# ============ Dashboard ============

@app.route("/")
def index():
    """Main dashboard."""
    stats = get_stats()
    apartments = list_apartments(limit=5)
    videos = get_recent_video_responses(limit=3)
    
    return render_template("index.html",
        stats=stats,
        apartments=apartments,
        recent_videos=videos
    )


# ============ Apartments ============

@app.route("/apartments")
def apartment_list():
    """List all apartments."""
    query = request.args.get("q")
    
    if query:
        apartments = search_apartments(query)
    else:
        apartments = list_apartments(limit=50)
    
    return render_template("apartments.html", apartments=apartments, query=query)


@app.route("/apartments/new", methods=["GET", "POST"])
def new_apartment():
    """Create new apartment."""
    if request.method == "POST":
        result = create_apartment(
            customer_id=request.form.get("customer_id") or f"cust_{hash(request.form.get('customer_name'))}"[:12],
            customer_name=request.form.get("customer_name"),
            address={"city": request.form.get("city")} if request.form.get("city") else None,
            building_info={
                "building_type": request.form.get("building_type"),
                "construction_year": int(request.form.get("construction_year")) if request.form.get("construction_year") else None
            } if request.form.get("building_type") else None,
            apartment_details={
                "size_sqm": float(request.form.get("size_sqm")) if request.form.get("size_sqm") else None
            } if request.form.get("size_sqm") else None,
            heating_system={
                "type": request.form.get("heating_type"),
                "has_smart_controls": request.form.get("has_smart_controls") == "on"
            } if request.form.get("heating_type") else None
        )
        return redirect(url_for("apartment_detail", apartment_id=result["id"]))
    
    return render_template("new_apartment.html")


@app.route("/apartments/<apartment_id>")
def apartment_detail(apartment_id):
    """Apartment detail view."""
    apartment = get_apartment(apartment_id)
    if not apartment:
        return render_template("error.html", message="Apartment not found"), 404
    
    summary = get_apartment_summary(apartment_id)
    recommendations = get_recommendations(apartment_id)
    
    return render_template("apartment_detail.html",
        apartment=apartment,
        summary=summary,
        recommendations=recommendations
    )


@app.route("/apartments/<apartment_id>/update", methods=["POST"])
def update_apartment_endpoint(apartment_id):
    """Update apartment."""
    updates = {}
    
    if request.form.get("annual_heating_kwh"):
        updates["energy_consumption"] = {"annual_heating_kwh": float(request.form.get("annual_heating_kwh"))}
    if request.form.get("annual_cost_eur"):
        updates.setdefault("energy_consumption", {})["annual_cost_eur"] = float(request.form.get("annual_cost_eur"))
    if request.form.get("preferred_temp_c"):
        updates["preferences"] = {"preferred_temp_c": float(request.form.get("preferred_temp_c"))}
    if request.form.get("notes"):
        updates["notes"] = request.form.get("notes")
    
    update_apartment(apartment_id, updates)
    return redirect(url_for("apartment_detail", apartment_id=apartment_id))


# ============ Chat ============

@app.route("/chat")
def chat_page():
    """Chat interface."""
    apartment_id = request.args.get("apartment_id")
    apartment = get_apartment(apartment_id) if apartment_id else None
    apartments = list_apartments(limit=20)
    
    return render_template("chat.html",
        apartment=apartment,
        apartments=apartments,
        selected_apartment=apartment_id
    )


@app.route("/chat/send", methods=["POST"])
def send_message():
    """Send chat message."""
    from energy_advisor import process_query, get_client
    
    message = request.json.get("message")
    apartment_id = request.json.get("apartment_id")
    history = request.json.get("history", [])
    generate_video = request.json.get("generate_video", False)
    
    try:
        client = get_client()
        response, _, video = process_query(
            message, client, apartment_id, None, history, generate_video
        )
        
        result = {"response": response}
        if video and video.get("status") == "success":
            result["video"] = video
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chat/stream", methods=["POST"])
def stream_message():
    """Stream chat message with real-time logs."""
    from energy_advisor import process_query, get_client
    import queue
    import threading
    
    data = request.json
    message = data.get("message")
    apartment_id = data.get("apartment_id")
    history = data.get("history", [])
    generate_video = data.get("generate_video", False)
    
    log_queue = queue.Queue()
    result_holder = {"response": None, "video": None, "error": None}
    
    def log_callback(msg):
        log_queue.put({"type": "log", "message": msg})
    
    def run_agent():
        try:
            client = get_client()
            response, _, video = process_query(
                message, client, apartment_id, None, history, generate_video, log_callback
            )
            result_holder["response"] = response
            result_holder["video"] = video
        except Exception as e:
            result_holder["error"] = str(e)
        finally:
            log_queue.put(None)  # Signal completion
    
    thread = threading.Thread(target=run_agent)
    thread.start()
    
    def generate():
        while True:
            try:
                item = log_queue.get(timeout=120)
                if item is None:
                    break
                yield f"data: {json.dumps(item)}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'log', 'message': 'Still processing...'})}\n\n"
        
        thread.join()
        
        if result_holder["error"]:
            yield f"data: {json.dumps({'type': 'error', 'message': result_holder['error']})}\n\n"
        else:
            result = {"type": "response", "content": result_holder["response"]}
            if result_holder["video"] and result_holder["video"].get("status") == "success":
                result["video"] = result_holder["video"]
            yield f"data: {json.dumps(result)}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


# ============ Knowledge ============

@app.route("/knowledge")
def knowledge_search():
    """Knowledge search page."""
    query = request.args.get("q")
    results = None
    
    if query:
        from subagents.knowledge_search import search_knowledge
        results = search_knowledge(query)
    
    return render_template("knowledge.html", query=query, results=results)


# ============ Videos ============

@app.route("/videos")
def video_list():
    """List recent videos."""
    videos = get_recent_video_responses(limit=20)
    return render_template("videos.html", videos=videos)


@app.route("/videos/<path:filename>")
def serve_video(filename):
    """Serve video files."""
    video_dir = AGENT_DIR / "memory" / "data" / "videos"
    return send_from_directory(str(video_dir), filename)


@app.route("/videos/generate", methods=["POST"])
def generate_video():
    """Generate a video response."""
    from tools.generate_video_response import generate_video_response
    
    script = request.json.get("script")
    voice = request.json.get("voice", "Puck (Male)")
    
    result = generate_video_response(script=script, voice=voice)
    
    if result.get("status") == "success":
        store_video_response(
            question="UI request",
            answer=script,
            video_path=result.get("video_path")
        )
    
    return jsonify(result)


# ============ API Endpoints ============

@app.route("/api/stats")
def api_stats():
    """API: Get statistics."""
    return jsonify(get_stats())


@app.route("/api/apartments/search")
def api_search_apartments():
    """API: Search apartments."""
    query = request.args.get("q", "")
    results = search_apartments(query)
    return jsonify({"results": results})


@app.route("/api/knowledge/search")
def api_search_knowledge():
    """API: Search knowledge."""
    from subagents.knowledge_search import search_knowledge
    
    query = request.args.get("q", "")
    results = search_knowledge(query)
    return jsonify(results)


# ============ Error Handlers ============

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", message="Server error"), 500


# ============ Main ============

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
