"""
Session management for chat conversations.
Handles session creation, storage, and cleanup.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, field

from google.genai import types


@dataclass
class SessionContext:
    """Context for a chat session."""

    session_id: str
    history: List[types.Content] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

    def is_expired(self, timeout_seconds: int) -> bool:
        """Check if session has expired."""
        expiry_time = self.last_activity + timedelta(seconds=timeout_seconds)
        return datetime.now() > expiry_time


class SessionManager:
    """Manages chat sessions."""

    def __init__(self, timeout_seconds: int = 1800):
        """
        Initialize session manager.

        Args:
            timeout_seconds: Session timeout in seconds (default 30 minutes)
        """
        self.sessions: Dict[str, SessionContext] = {}
        self.timeout_seconds = timeout_seconds

    def create_session(self, metadata: Optional[Dict] = None) -> SessionContext:
        """
        Create a new chat session.

        Args:
            metadata: Optional metadata for the session

        Returns:
            New SessionContext
        """
        session_id = str(uuid.uuid4())
        session = SessionContext(
            session_id=session_id,
            metadata=metadata or {}
        )
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """
        Retrieve a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            SessionContext if found, None otherwise
        """
        session = self.sessions.get(session_id)
        if session:
            if session.is_expired(self.timeout_seconds):
                self.delete_session(session_id)
                return None
            session.update_activity()
        return session

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired_ids = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(self.timeout_seconds)
        ]
        for sid in expired_ids:
            del self.sessions[sid]
        return len(expired_ids)

    def get_session_count(self) -> int:
        """Get total number of active sessions."""
        return len(self.sessions)
