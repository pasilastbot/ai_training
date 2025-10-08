"""
FastAPI application for Gemini-powered chatbot.

Provides WebSocket-based real-time chat interface with AI agent integration.
"""

import os
import sys
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Add parent directory to path to import gemini_agent
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.config import config
from api.session_manager import SessionManager


# Initialize FastAPI app
app = FastAPI(
    title="Gemini Chatbot API",
    description="WebSocket-based chatbot powered by Google Gemini",
    version="1.0.0",
    debug=config.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize session manager
session_manager = SessionManager(timeout_seconds=config.SESSION_TIMEOUT)

# Get paths
BASE_DIR = Path(__file__).parent.parent
WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"
PUBLIC_DIR = BASE_DIR / "public"

# Ensure directories exist
PUBLIC_DIR.mkdir(exist_ok=True)


# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if PUBLIC_DIR.exists():
    app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")


# -------------------- HTTP Endpoints --------------------

@app.get("/")
async def root():
    """Serve the main chat interface."""
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(
        content={"message": "Chatbot API is running. Frontend not found."},
        status_code=200
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "gemini_agent_available": True,
        "active_sessions": session_manager.get_session_count()
    }


@app.post("/api/sessions/new")
async def create_new_session():
    """Create a new chat session."""
    session = session_manager.create_session()
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.timestamp()
    }


@app.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Retrieve conversation history for a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    # Convert history to serializable format
    messages = []
    for content in session.history:
        if hasattr(content, 'parts'):
            for part in content.parts:
                if hasattr(part, 'text'):
                    messages.append({
                        "role": content.role if hasattr(content, 'role') else "model",
                        "content": part.text,
                        "timestamp": session.last_activity.timestamp()
                    })

    return {
        "session_id": session_id,
        "messages": messages
    }


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its history."""
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "success": True,
        "session_id": session_id
    }


@app.post("/api/sessions/cleanup")
async def cleanup_sessions():
    """Clean up expired sessions (admin endpoint)."""
    count = session_manager.cleanup_expired_sessions()
    return {
        "cleaned_up": count,
        "remaining_sessions": session_manager.get_session_count()
    }


# -------------------- WebSocket Endpoint --------------------

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.

    Message format from client:
    {
        "type": "user_message" | "new_session" | "clear_history",
        "session_id": "uuid",  # optional for new_session
        "content": "message text",  # for user_message
        "timestamp": 1633024800000
    }

    Message format to client:
    {
        "type": "assistant_message" | "function_call" | "function_result" | "error",
        "session_id": "uuid",
        "content": "response text",
        "timestamp": 1633024805000,
        "complete": true
    }
    """
    await websocket.accept()

    try:
        # Import websocket handler (will implement later)
        from api.websocket_handler import handle_websocket_chat

        await handle_websocket_chat(websocket, session_manager)

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close(code=1011, reason="Internal server error")


# -------------------- Main --------------------

if __name__ == "__main__":
    import uvicorn

    # Load environment variables
    from gemini_agent import load_env_files
    load_env_files()

    print(f"Starting chatbot API server...")
    print(f"Web interface: http://{config.HOST}:{config.PORT}")
    print(f"WebSocket endpoint: ws://{config.HOST}:{config.PORT}/ws/chat")
    print(f"API documentation: http://{config.HOST}:{config.PORT}/docs")

    uvicorn.run(
        "api.app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info" if not config.DEBUG else "debug"
    )
