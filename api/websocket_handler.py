"""
WebSocket handler for real-time chat communication.
Manages message routing between client and Gemini agent.
"""

import json
from typing import Dict, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

from api.session_manager import SessionManager
from api.gemini_wrapper import get_agent
from api.config import config


async def handle_websocket_chat(websocket: WebSocket, session_manager: SessionManager):
    """
    Handle WebSocket chat communication.

    Args:
        websocket: WebSocket connection
        session_manager: Session manager instance

    Message format from client:
    {
        "type": "user_message" | "new_session" | "clear_history",
        "session_id": "uuid",  # optional for new_session
        "content": "message text",  # for user_message
        "timestamp": 1633024800000
    }
    """
    session_id = None
    agent = get_agent()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await send_error(
                    websocket,
                    "Invalid JSON format",
                    session_id
                )
                continue

            msg_type = message.get("type")

            # Handle new session
            if msg_type == "new_session":
                session = session_manager.create_session()
                session_id = session.session_id

                # Initialize with system prompt
                session.history = agent.get_initial_history()

                await websocket.send_json({
                    "type": "session_created",
                    "session_id": session_id,
                    "timestamp": datetime.now().timestamp()
                })
                continue

            # Handle clear history
            if msg_type == "clear_history":
                sid = message.get("session_id")
                if sid:
                    session = session_manager.get_session(sid)
                    if session:
                        session.history = agent.get_initial_history()
                        await websocket.send_json({
                            "type": "history_cleared",
                            "session_id": sid,
                            "timestamp": datetime.now().timestamp()
                        })
                    else:
                        await send_error(websocket, "Session not found", sid)
                continue

            # Handle user message
            if msg_type == "user_message":
                sid = message.get("session_id")
                content = message.get("content", "").strip()

                if not sid:
                    await send_error(websocket, "Session ID required", None)
                    continue

                if not content:
                    await send_error(websocket, "Message content required", sid)
                    continue

                # Validate message length
                if len(content) > config.MAX_MESSAGE_LENGTH:
                    await send_error(
                        websocket,
                        f"Message too long (max {config.MAX_MESSAGE_LENGTH} characters)",
                        sid
                    )
                    continue

                # Get or create session
                session = session_manager.get_session(sid)
                if not session:
                    await send_error(websocket, "Session not found or expired", sid)
                    continue

                # Echo user message back to client
                await websocket.send_json({
                    "type": "user_message_echo",
                    "session_id": sid,
                    "content": content,
                    "timestamp": datetime.now().timestamp()
                })

                # Show typing indicator
                await websocket.send_json({
                    "type": "typing",
                    "session_id": sid,
                    "timestamp": datetime.now().timestamp()
                })

                # Generate response using agent
                try:
                    assistant_text_parts = []

                    async for event in agent.generate_response(
                        history=session.history,
                        user_message=content,
                        max_iterations=5
                    ):
                        event_type = event.get("type")

                        if event_type == "function_call":
                            # Notify about function execution
                            await websocket.send_json({
                                "type": "function_call",
                                "session_id": sid,
                                "function_name": event.get("name"),
                                "function_args": event.get("args"),
                                "status": event.get("status"),
                                "timestamp": event.get("timestamp")
                            })

                        elif event_type == "function_result":
                            # Send function execution result
                            await websocket.send_json({
                                "type": "function_result",
                                "session_id": sid,
                                "function_name": event.get("name"),
                                "success": event.get("success"),
                                "output": event.get("output"),
                                "error": event.get("error"),
                                "timestamp": event.get("timestamp")
                            })

                        elif event_type == "text_chunk":
                            # Send text response
                            text = event.get("text", "")
                            assistant_text_parts.append(text)

                            await websocket.send_json({
                                "type": "assistant_message",
                                "session_id": sid,
                                "content": text,
                                "complete": False,
                                "timestamp": event.get("timestamp")
                            })

                        elif event_type == "grounding":
                            # Send grounding sources
                            await websocket.send_json({
                                "type": "grounding",
                                "session_id": sid,
                                "sources": event.get("sources", []),
                                "timestamp": event.get("timestamp")
                            })

                        elif event_type == "complete":
                            # Update session history
                            session.history = event.get("history", session.history)
                            session.update_activity()

                            # Send completion message
                            await websocket.send_json({
                                "type": "assistant_message",
                                "session_id": sid,
                                "content": "",  # Already sent in chunks
                                "complete": True,
                                "timestamp": event.get("timestamp")
                            })

                except Exception as e:
                    print(f"Error generating response: {e}")
                    await send_error(
                        websocket,
                        f"Error generating response: {str(e)}",
                        sid
                    )

            else:
                await send_error(
                    websocket,
                    f"Unknown message type: {msg_type}",
                    session_id
                )

    except WebSocketDisconnect:
        print(f"Client disconnected (session: {session_id})")
        raise

    except Exception as e:
        print(f"WebSocket error: {e}")
        await send_error(websocket, f"Server error: {str(e)}", session_id)
        raise


async def send_error(websocket: WebSocket, error: str, session_id: str = None):
    """Send error message to client."""
    try:
        await websocket.send_json({
            "type": "error",
            "session_id": session_id,
            "error": error,
            "timestamp": datetime.now().timestamp()
        })
    except Exception as e:
        print(f"Failed to send error message: {e}")
