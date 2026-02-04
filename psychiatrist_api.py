#!/usr/bin/env python3
"""
Multi-Persona AI Psychiatrist Game API

A collection of AI therapist personas powered by Gemini.
Run with: python psychiatrist_api.py
Then open: http://localhost:5001
"""

import os
import json
import re
import uuid
import random
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

from google import genai

# Panel discussion module
import psychiatrist_panel as panel

# ============================================================================
# PERSONA MANAGEMENT
# ============================================================================

def load_personas():
    """Load personas from config file."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'personas.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print(f"Warning: Personas config not found at {config_path}")
        return {"personas": {}, "defaultPersonaId": None}
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in personas config: {e}")
        return {"personas": {}, "defaultPersonaId": None}


# Load personas configuration
PERSONAS_CONFIG = load_personas()
PERSONAS = PERSONAS_CONFIG.get("personas", {})
DEFAULT_PERSONA_ID = PERSONAS_CONFIG.get("defaultPersonaId", "dr-sigmund-2000")

# Valid moods for all personas
VALID_MOODS = ["thinking", "amused", "concerned", "shocked", "neutral"]

# Panel configs path
PANEL_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'panel_configs.json')

# Fallback ASCII faces (used if persona doesn't define custom ones)
DEFAULT_ASCII_FACES = {
    "thinking": "    .---.\n   / o o \\\n   |  ~  |\n   \\ === /\n    '---'\n  *thinking*",
    "amused": "    .---.\n   / ^ ^ \\\n   |  v  |\n   \\ === /\n    '---'\n  *hehe*",
    "concerned": "    .---.\n   / o o \\\n   |  n  |\n   \\ === /\n    '---'\n  *hmm...*",
    "shocked": "    .---.\n   / O O \\\n   |  O  |\n   \\ === /\n    '---'\n  *gasp!*",
    "neutral": "    .---.\n   / - - \\\n   |  _  |\n   \\ === /\n    '---'\n  *listening*"
}


def get_persona(persona_id: str) -> dict:
    """Get persona by ID, or return default persona."""
    if persona_id and persona_id in PERSONAS:
        return PERSONAS[persona_id]
    return PERSONAS.get(DEFAULT_PERSONA_ID, {})


def get_ascii_art(persona: dict, mood: str) -> str:
    """Get ASCII art for a mood from persona, with fallback."""
    ascii_art = persona.get("asciiArt", {})
    if mood in ascii_art:
        return ascii_art[mood]
    return DEFAULT_ASCII_FACES.get(mood, DEFAULT_ASCII_FACES["neutral"])


def build_system_prompt(persona: dict) -> str:
    """Build the system prompt for a persona with JSON response instructions."""
    base_prompt = persona.get("systemPrompt", "You are a helpful therapist.")
    
    json_instructions = """

IMPORTANT: You MUST respond in valid JSON format like this:
{"response": "Your therapeutic response here...", "mood": "thinking"}

The "mood" field must be one of: "thinking", "amused", "concerned", "shocked", "neutral"

Choose mood based on:
- thinking: when pondering the patient's words
- amused: when finding something funny or ironic
- concerned: when the patient shares worries
- shocked: when hearing something surprising
- neutral: for general listening"""
    
    return base_prompt + json_instructions


def build_initial_response(persona: dict) -> str:
    """Build the initial model response in JSON format."""
    welcome = persona.get("welcomeMessage", "Welcome! How can I help you today?")
    return json.dumps({"response": welcome, "mood": "neutral"})


# ============================================================================
# HOT MIC CONSULT (single-doctor backchannel)
# ============================================================================

HOT_MIC_PINGS = {
    "dr-sigmund-2000": "BRB pinging you for a second opinion. Patient says: \"{message}\". Give me the spicy diagnostic dump—no parental controls.",
    "dr-luna-cosmos": "Quick cosmic consult, {colleague}. Human says: \"{message}\". Give me your blunt earthly take—yes, you may roll your eyes.",
    "dr-rex-hardcastle": "Listen, {colleague}. Patient says: \"{message}\". Give me your straight answer—no fluff, no coddling.",
    "dr-pixel": "Co-op request, {colleague}. Player typed: \"{message}\". Need a spicy strat—hit me.",
    "dr-ada-sterling": "Quick consult, {colleague}. User message: \"{message}\". Give me your candid take and 2 actionable steps.",
    "captain-whiskers": "Pssst {colleague}. Human says: \"{message}\". Give me your purrfessionally brutal diagnosis (then something useful).",
}


def _extract_text_from_response(response) -> str:
    """Extract model text from Gemini response object safely."""
    try:
        if response and response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text or ""
    except Exception:
        return ""
    return ""


def _parse_json_reply(response_text: str) -> tuple:
    """
    Parse a JSON-ish Gemini reply.
    Returns: (text_response, mood)
    """
    response_text = (response_text or "").strip()
    mood = "neutral"
    text_response = response_text

    try:
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            parsed = json.loads(json_str)
            mood = parsed.get("mood", "neutral")
            text_response = parsed.get("response", response_text)
    except Exception:
        mood = "neutral"
        text_response = response_text

    if mood not in VALID_MOODS:
        mood = "neutral"

    return text_response, mood


def _pick_random_colleague(current_persona_id: str) -> str:
    """Pick a random colleague persona id excluding current."""
    candidates = [pid for pid in PERSONAS.keys() if pid != current_persona_id]
    if not candidates:
        return current_persona_id
    return random.choice(candidates)


def _build_hot_mic_question(current_persona: dict, colleague_persona: dict, user_message: str) -> str:
    """Build the doctor->doctor hot mic ping line shown to the user."""
    pid = current_persona.get("id") or ""
    colleague_name = colleague_persona.get("name", "Colleague")
    template = HOT_MIC_PINGS.get(pid, "Quick consult, {colleague}. User says: \"{message}\". Give me your blunt take.")
    return template.format(colleague=colleague_name, message=user_message)


def _build_hot_mic_system_prompt(colleague_persona: dict, requesting_doctor_name: str) -> str:
    """
    Build a system prompt for the consulted colleague.

    NOTE: Users will SEE this transcript, so we keep it spicy-but-not-hateful.
    """
    base_prompt = colleague_persona.get("systemPrompt", "You are a helpful therapist.")
    instructions = f"""

IMPORTANT: This is a PRIVATE doctor-to-doctor backchannel ("HOT MIC") between you and {requesting_doctor_name}.
The USER will SEE this transcript.

TONE:
- Be spicy, blunt, funny, and a bit rude.
- You may roast the patient's habits/choices and the other doctor's style.
- Do NOT use slurs or hate/discrimination. Avoid protected traits.
- Do NOT encourage self-harm or illegal/dangerous actions.

CONTENT:
- Speak to the other doctor, NOT to the patient.
- Include 2-3 concrete, actionable takeaways the doctor can translate for the patient.

FORMAT:
- Respond in valid JSON only: {{"response": "...", "mood": "thinking|amused|concerned|shocked|neutral"}}
"""
    return base_prompt + instructions


# ============================================================================
# PANEL DISCUSSION HELPERS
# ============================================================================

def _ensure_panel_configs_loaded() -> None:
    """
    Ensure panel configs are loaded for panel endpoints.

    This is intentionally safe to call repeatedly; it reloads configs from the
    canonical config file so API behavior is deterministic even if other tests
    loaded a temporary config earlier.
    """
    panel.load_panel_configs(PANEL_CONFIG_PATH)


def _serialize_panel_response(resp: panel.PanelResponse) -> dict:
    """Serialize PanelResponse for JSON responses."""
    return {
        "persona_id": resp.persona_id,
        "persona_name": resp.persona_name,
        "response": resp.response,
        "mood": resp.mood,
        "references": resp.references or [],
        "ascii_art": resp.ascii_art,
    }


def _parse_key_insights_from_text(text: str) -> list:
    """
    Extract key insights from a moderator summary text.

    Looks for a "Key Insights:" section with numbered lines like "1. ...".
    Returns [] if not found.
    """
    insights = []
    in_section = False
    for line in (text or "").splitlines():
        if re.search(r'\bkey insights\b', line, flags=re.IGNORECASE):
            in_section = True
            continue
        if not in_section:
            continue
        m = re.match(r'^\s*\d+\.\s+(.*)\s*$', line)
        if m:
            insight = m.group(1).strip()
            if insight:
                insights.append(insight)
    return insights


def _sse(event: str, payload: dict) -> str:
    """Format a Server-Sent Event (SSE) message."""
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


# ============================================================================
# FLASK APP
# ============================================================================

app = Flask(__name__, static_folder='public')
CORS(app)


def load_api_key():
    """Load Gemini API key from environment."""
    api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Set GOOGLE_AI_STUDIO_KEY, GEMINI_API_KEY, or GOOGLE_API_KEY.")
    return api_key


# Initialize Gemini client
try:
    client = genai.Client(api_key=load_api_key())
except Exception as e:
    print(f"Warning: Could not initialize Gemini client: {e}")
    client = None


# ============================================================================
# ROUTES - Static Files
# ============================================================================

@app.route('/')
def index():
    """Serve the main game page."""
    return send_from_directory('public/psychiatrist', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from public/psychiatrist/ first, then public/."""
    # Try psychiatrist folder first (for JS, CSS files)
    psychiatrist_path = os.path.join('public/psychiatrist', filename)
    if os.path.exists(psychiatrist_path):
        return send_from_directory('public/psychiatrist', filename)
    # Fall back to public folder (for sprites, images, etc.)
    return send_from_directory('public', filename)


# ============================================================================
# ROUTES - Persona API
# ============================================================================

@app.route('/api/personas', methods=['GET'])
def list_personas():
    """Return list of available personas."""
    personas_list = []
    for persona_id, persona in PERSONAS.items():
        personas_list.append({
            "id": persona.get("id", persona_id),
            "name": persona.get("name", "Unknown"),
            "tagline": persona.get("tagline", ""),
            "description": persona.get("description", ""),
            "era": persona.get("era", ""),
            "theme": persona.get("theme", {}),
            "spritePath": persona.get("spritePath", ""),
            "available": persona.get("available", True),
            "order": persona.get("order", 999)
        })
    
    # Sort by order
    personas_list.sort(key=lambda x: x["order"])
    
    return jsonify({
        "personas": personas_list,
        "defaultPersonaId": DEFAULT_PERSONA_ID
    })


@app.route('/api/personas/<persona_id>', methods=['GET'])
def get_persona_detail(persona_id):
    """Return detailed information about a specific persona."""
    if persona_id not in PERSONAS:
        return jsonify({"error": f"Persona '{persona_id}' not found"}), 404
    
    persona = PERSONAS[persona_id]
    
    return jsonify({
        "id": persona.get("id", persona_id),
        "name": persona.get("name", "Unknown"),
        "tagline": persona.get("tagline", ""),
        "description": persona.get("description", ""),
        "era": persona.get("era", ""),
        "welcomeMessage": persona.get("welcomeMessage", ""),
        "theme": persona.get("theme", {}),
        "spritePath": persona.get("spritePath", ""),
        "asciiArt": persona.get("asciiArt", DEFAULT_ASCII_FACES),
        "available": persona.get("available", True),
        "order": persona.get("order", 999)
    })


# ============================================================================
# ROUTES - Chat API
# ============================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages and return psychiatrist responses."""
    if client is None:
        return jsonify({
            "error": "Gemini client not initialized. Check your API key.",
            "response": "ERROR 404: Therapy module not found. Please insert your API key floppy disk.",
            "mood": "concerned",
            "ascii_art": DEFAULT_ASCII_FACES["concerned"]
        }), 500
    
    data = request.get_json(silent=True) or {}
    user_message = (data.get('message') or '').strip()
    history = data.get('history', []) or []
    persona_id = data.get('persona_id', DEFAULT_PERSONA_ID)
    consult_enabled = bool(data.get('consult', False))
    
    # Get the persona
    persona = get_persona(persona_id)
    
    if not user_message:
        return jsonify({
            "error": "No message provided",
            "response": "I notice you're being quiet. What's on your mind?",
            "mood": "thinking",
            "ascii_art": get_ascii_art(persona, "thinking")
        }), 400
    
    consult_payload = None
    consult_reply_text = None

    # Hot mic consult (1 colleague per message)
    if consult_enabled:
        try:
            colleague_id = _pick_random_colleague(persona.get("id", persona_id))
            colleague = get_persona(colleague_id)

            hot_mic_question = _build_hot_mic_question(persona, colleague, user_message)
            hot_mic_system = _build_hot_mic_system_prompt(colleague, persona.get("name", "Doctor"))

            consult_contents = [
                {"role": "user", "parts": [{"text": hot_mic_system}]},
                {"role": "model", "parts": [{"text": json.dumps({"response": "Go ahead. What's the case?", "mood": "neutral"})}]},
                {"role": "user", "parts": [{"text": hot_mic_question}]},
            ]

            consult_resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=consult_contents,
            )

            consult_text_raw = _extract_text_from_response(consult_resp)
            consult_reply_text, _ = _parse_json_reply(consult_text_raw)

            consult_payload = {
                "enabled": True,
                "consulted_persona_id": colleague.get("id", colleague_id),
                "consulted_persona_name": colleague.get("name", "Colleague"),
                "transcript": [
                    {
                        "from_persona_id": persona.get("id", persona_id),
                        "from_persona_name": persona.get("name", "Doctor"),
                        "to_persona_id": colleague.get("id", colleague_id),
                        "to_persona_name": colleague.get("name", "Colleague"),
                        "text": hot_mic_question,
                    },
                    {
                        "from_persona_id": colleague.get("id", colleague_id),
                        "from_persona_name": colleague.get("name", "Colleague"),
                        "to_persona_id": persona.get("id", persona_id),
                        "to_persona_name": persona.get("name", "Doctor"),
                        "text": consult_reply_text or "",
                    },
                ],
            }

        except Exception as e:
            # Don't block the user-facing reply if consult fails
            consult_payload = {
                "enabled": True,
                "error": str(e),
                "transcript": [],
            }

    # Build the system prompt for this persona
    system_prompt = build_system_prompt(persona)
    initial_response = build_initial_response(persona)
    
    # Build conversation contents
    contents = [
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": initial_response}]}
    ]
    
    # Add conversation history
    for msg in history:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
    
    # Add consult context (internal) before user's message
    if consult_enabled and consult_reply_text:
        contents.append({
            "role": "user",
            "parts": [{
                "text": (
                    "[INTERNAL HOT MIC CONTEXT]\n"
                    "You consulted a colleague for a spicy second opinion. They said:\n"
                    f"{consult_reply_text}\n\n"
                    "Now respond to the USER normally in your persona. "
                    "You MAY mention you consulted a colleague, but do not quote the transcript verbatim."
                )
            }]
        })

    # Add current message
    contents.append({"role": "user", "parts": [{"text": user_message}]})
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
        )
        
        response_text = _extract_text_from_response(response)
        text_response, mood = _parse_json_reply(response_text)

        payload = {
            "response": text_response,
            "mood": mood,
            "ascii_art": get_ascii_art(persona, mood)
        }
        if consult_payload is not None:
            payload["consult"] = consult_payload

        return jsonify(payload)
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "response": f"*SYSTEM ERROR* Something went wrong! Error: {str(e)[:100]}... Please try again.",
            "mood": "shocked",
            "ascii_art": get_ascii_art(persona, "shocked")
        }), 500


@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset the conversation."""
    data = request.get_json() or {}
    persona_id = data.get('persona_id', DEFAULT_PERSONA_ID)
    
    # Get the persona
    persona = get_persona(persona_id)
    reset_message = persona.get("resetMessage", "Session reset. What would you like to discuss?")
    
    return jsonify({
        "response": reset_message,
        "mood": "neutral",
        "ascii_art": get_ascii_art(persona, "neutral")
    })


# ============================================================================
# ROUTES - Panel Discussion API
# ============================================================================

@app.route('/api/panel/configs', methods=['GET'])
def list_panel_configs():
    """Return list of available panel configurations."""
    try:
        panel.cleanup_expired_sessions()
        data = panel.load_panel_configs(PANEL_CONFIG_PATH)
        configs_map = data.get('panel_configs', {})

        configs = []
        for cfg in configs_map.values():
            configs.append({
                "id": cfg.get("id"),
                "name": cfg.get("name"),
                "description": cfg.get("description", ""),
                "persona_ids": cfg.get("persona_ids", []),
                "best_for": cfg.get("best_for", ""),
                "default": cfg.get("default", False),
                "icon": cfg.get("icon", ""),
                "order": cfg.get("order", 999),
            })

        configs.sort(key=lambda c: c.get("order", 999))
        return jsonify({"configs": configs})
    except Exception as e:
        return jsonify({"error": f"Failed to load panel configs: {str(e)}"}), 500


@app.route('/api/panel/start', methods=['POST'])
def panel_start():
    """Start a new panel discussion session."""
    try:
        _ensure_panel_configs_loaded()
        panel.cleanup_expired_sessions()
    except Exception as e:
        return jsonify({"error": f"Panel configs unavailable: {str(e)}"}), 500

    data = request.get_json(silent=True) or {}
    user_message = (data.get('message') or '').strip()
    include_moderator = bool(data.get('include_moderator', True))
    stream = bool(data.get('stream', False))

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    panel_config_id = data.get('panel_config')
    persona_ids = data.get('persona_ids')

    try:
        # Determine persona_ids to use
        if isinstance(persona_ids, list) and len(persona_ids) > 0:
            session = panel.create_custom_panel_session(
                persona_ids=persona_ids,
                include_moderator=include_moderator,
                panel_config_id=panel_config_id or "custom",
                personas_config=PERSONAS,
            )
        else:
            if not panel_config_id:
                return jsonify({"error": "panel_config or persona_ids is required"}), 400
            # Validate panel config
            if panel.get_panel_config(panel_config_id) is None:
                return jsonify({"error": f"Panel config not found: {panel_config_id}"}), 400
            session = panel.create_panel_session(panel_config_id, include_moderator=include_moderator)

        # Store session before generation
        panel.store_session(session)

        # Optional moderator intro
        moderator_intro = None
        if include_moderator:
            intro = panel.generate_moderator_intro(session)
            moderator_intro = {
                "persona": intro.persona_id,
                "response": intro.response,
                "mood": intro.mood,
            }

        # Streaming mode: send persona responses one-by-one via SSE
        if stream:
            skip_personas = data.get('skip_personas') or []
            if not isinstance(skip_personas, list):
                skip_personas = []

            def generate():
                try:
                    # Initial session info
                    yield _sse("session", {
                        "session_id": session.session_id,
                        "panel_state": {
                            "active": True,
                            "exchange_count": session.exchange_count,
                            "total_personas": len(session.persona_ids),
                            "has_moderator": session.has_moderator,
                        },
                    })

                    if moderator_intro is not None:
                        yield _sse("moderator_intro", moderator_intro)

                    for resp in panel.iter_panel_responses(
                        session=session,
                        personas_config=PERSONAS,
                        user_message=user_message,
                        skip_personas=skip_personas,
                    ):
                        yield _sse("panel_response", _serialize_panel_response(resp))

                    yield _sse("panel_state", {
                        "active": True,
                        "exchange_count": session.exchange_count,
                        "total_personas": len(session.persona_ids),
                        "has_moderator": session.has_moderator,
                    })
                    yield _sse("done", {})
                except Exception as e:
                    yield _sse("error", {"error": str(e)})

            return Response(
                generate(),
                mimetype="text/event-stream",
                headers={"Cache-Control": "no-cache"},
            )

        # Generate panel responses
        skip_personas = data.get('skip_personas') or []
        if not isinstance(skip_personas, list):
            skip_personas = []

        responses = panel.generate_panel_responses(
            session=session,
            personas_config=PERSONAS,
            user_message=user_message,
            skip_personas=skip_personas,
        )

        payload = {
            "session_id": session.session_id,
            "panel_responses": [_serialize_panel_response(r) for r in responses],
            "panel_state": {
                "active": True,
                "exchange_count": session.exchange_count,
                "total_personas": len(session.persona_ids),
                "has_moderator": session.has_moderator,
            },
        }
        if moderator_intro is not None:
            payload["moderator_intro"] = moderator_intro

        return jsonify(payload)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/panel/continue', methods=['POST'])
def panel_continue():
    """Continue an existing panel session with a new user message."""
    panel.cleanup_expired_sessions()
    data = request.get_json(silent=True) or {}
    session_id = (data.get('session_id') or '').strip()
    user_message = (data.get('message') or '').strip()
    skip_personas = data.get('skip_personas') or []
    stream = bool(data.get('stream', False))

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    if not isinstance(skip_personas, list):
        skip_personas = []

    session = panel.get_session(session_id)
    if session is None:
        return jsonify({"error": f"Session not found: {session_id}"}), 404

    try:
        if stream:
            def generate():
                try:
                    for resp in panel.iter_panel_responses(
                        session=session,
                        personas_config=PERSONAS,
                        user_message=user_message,
                        skip_personas=skip_personas,
                    ):
                        yield _sse("panel_response", _serialize_panel_response(resp))

                    should_summarize = panel.should_generate_summary(session)
                    yield _sse("panel_state", {
                        "active": True,
                        "exchange_count": session.exchange_count,
                        "total_personas": len(session.persona_ids),
                        "has_moderator": session.has_moderator,
                        "should_summarize": should_summarize,
                    })
                    yield _sse("done", {})
                except Exception as e:
                    yield _sse("error", {"error": str(e)})

            return Response(
                generate(),
                mimetype="text/event-stream",
                headers={"Cache-Control": "no-cache"},
            )

        responses = panel.generate_panel_responses(
            session=session,
            personas_config=PERSONAS,
            user_message=user_message,
            skip_personas=skip_personas,
        )

        should_summarize = panel.should_generate_summary(session)

        return jsonify({
            "session_id": session.session_id,
            "panel_responses": [_serialize_panel_response(r) for r in responses],
            "panel_state": {
                "active": True,
                "exchange_count": session.exchange_count,
                "total_personas": len(session.persona_ids),
                "has_moderator": session.has_moderator,
                "should_summarize": should_summarize,
            },
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/panel/summarize', methods=['POST'])
def panel_summarize():
    """Generate a moderator summary for the current session."""
    try:
        _ensure_panel_configs_loaded()
        panel.cleanup_expired_sessions()
    except Exception as e:
        return jsonify({"error": f"Panel configs unavailable: {str(e)}"}), 500

    data = request.get_json(silent=True) or {}
    session_id = (data.get('session_id') or '').strip()
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    session = panel.get_session(session_id)
    if session is None:
        return jsonify({"error": f"Session not found: {session_id}"}), 404

    try:
        summary = panel.generate_panel_summary(session)
        key_insights = _parse_key_insights_from_text(summary.response)
        credited_personas = summary.references or []

        return jsonify({
            "moderator_summary": {
                "persona": summary.persona_id,
                "response": summary.response,
                "mood": summary.mood,
                "key_insights": key_insights,
                "credited_personas": credited_personas,
            }
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/panel/end', methods=['POST'])
def panel_end():
    """End a panel session and remove it from active sessions."""
    panel.cleanup_expired_sessions()
    data = request.get_json(silent=True) or {}
    session_id = (data.get('session_id') or '').strip()
    return_to_persona_id = (data.get('return_to_persona_id') or '').strip()

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    session = panel.get_session(session_id)
    if session is None:
        return jsonify({"error": f"Session not found: {session_id}"}), 404

    # Remove from active sessions
    panel.delete_session(session_id)

    # Validate active persona fallback
    active_persona = return_to_persona_id if return_to_persona_id in PERSONAS else DEFAULT_PERSONA_ID

    total_responses = 0
    for exchange in session.discussion_history:
        total_responses += len(exchange.get('responses', []))

    return jsonify({
        "success": True,
        "final_summary": {
            "total_exchanges": session.exchange_count,
            "insights_count": total_responses,
            "farewell_message": "Thank you for participating in this panel discussion. The panel members hope their diverse perspectives were helpful!",
        },
        "active_persona": active_persona,
    })


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    persona_count = len(PERSONAS)
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║         MULTI-PERSONA PSYCHIATRIST API                   ║
    ║              {persona_count} Therapists Available                     ║
    ╠══════════════════════════════════════════════════════════╣
    ║  Starting therapy server on http://localhost:5001        ║
    ║  API Endpoints:                                          ║
    ║    GET  /api/personas      - List all personas           ║
    ║    GET  /api/personas/:id  - Get persona details         ║
    ║    POST /api/chat          - Chat (with persona_id)      ║
    ║    POST /api/reset         - Reset (with persona_id)     ║
    ║                                                          ║
    ║  Press Ctrl+C to end session                             ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, port=5001)
