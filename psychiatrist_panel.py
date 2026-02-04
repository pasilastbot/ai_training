"""
Multi-Persona Panel Discussion Module

This module handles panel discussion functionality where multiple psychiatric
personas collaborate to provide diverse therapeutic perspectives.

Developed using Test-Driven Development (TDD) methodology.
"""

import json
import logging
import uuid
import os
import re
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, List, Any, Iterator

# Setup logging
logger = logging.getLogger(__name__)

# Try to import Gemini client
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Gemini client not available. Install google-genai package.")


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class PanelResponse:
    """Represents a response from a single persona in a panel discussion."""
    persona_id: str
    persona_name: str
    response: str
    mood: str
    references: List[str]  # IDs of personas referenced
    ascii_art: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class PanelSession:
    """Represents an active panel discussion session."""
    session_id: str
    panel_config_id: str
    persona_ids: List[str]
    has_moderator: bool
    exchange_count: int = 0
    discussion_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ============================================================================
# GLOBAL STATE
# ============================================================================

_panel_configs: Dict[str, Any] = {}
_moderator: Optional[Dict[str, Any]] = None
_config_loaded: bool = False
_loaded_config_path: Optional[str] = None
_active_sessions: Dict[str, PanelSession] = {}  # session_id -> PanelSession


# ============================================================================
# CONFIGURATION LOADING
# ============================================================================

def load_panel_configs(config_path: str) -> Dict[str, Any]:
    """
    Load panel configurations from JSON file.
    
    Args:
        config_path: Path to panel_configs.json file
        
    Returns:
        Dictionary containing 'panel_configs' and 'moderator'
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
        ValueError: If config file is missing required fields
    """
    global _panel_configs, _moderator, _config_loaded, _loaded_config_path
    
    logger.info(f"Loading panel configurations from {config_path}")

    # Fast path: return cached config if already loaded from same path
    if _config_loaded and _loaded_config_path == config_path:
        return {"panel_configs": _panel_configs, "moderator": _moderator}
    
    # Validate file exists
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Panel config file not found: {config_path}")
    
    # Read and parse JSON
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in panel config file: {e}")
        raise
    
    # Validate required fields
    if 'panel_configs' not in data:
        raise ValueError("Config file missing 'panel_configs' field")
    
    # Store in global state
    _panel_configs = data.get('panel_configs', {})
    _moderator = data.get('moderator')
    _config_loaded = True
    _loaded_config_path = config_path
    
    logger.info(f"Loaded {len(_panel_configs)} panel configurations")
    
    return data


def get_panel_config(panel_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific panel configuration by ID.
    
    Args:
        panel_id: The ID of the panel configuration (e.g., 'balanced')
        
    Returns:
        Panel configuration dict if found, None otherwise
        
    Note:
        Returns None if panel_id not found or configs not loaded yet
    """
    if not _config_loaded:
        logger.warning("Attempted to get panel config before loading configs")
    
    config = _panel_configs.get(panel_id)
    
    if config is None:
        logger.debug(f"Panel config not found: {panel_id}")
    
    return config


def get_moderator_persona() -> Optional[Dict[str, Any]]:
    """
    Get the moderator persona configuration.
    
    Returns:
        Moderator configuration dict if loaded, None otherwise
        
    Note:
        Returns None if moderator not configured or configs not loaded yet
    """
    if not _config_loaded:
        logger.warning("Attempted to get moderator before loading configs")
    
    return _moderator


def list_panel_configs() -> List[str]:
    """
    Get list of available panel configuration IDs.
    
    Returns:
        List of panel config IDs
    """
    return list(_panel_configs.keys())


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

SESSION_TTL_SECONDS = 60 * 30  # 30 minutes


def create_custom_panel_session(
    persona_ids: List[str],
    include_moderator: bool = True,
    panel_config_id: str = "custom",
    personas_config: Optional[Dict[str, Dict[str, Any]]] = None,
) -> PanelSession:
    """
    Create a new panel session with an explicit list of persona IDs.

    This supports user-selected panels (2-4 personas) without requiring a
    preconfigured panel_config in `panel_configs.json`.

    Args:
        persona_ids: List of persona IDs (2-4 items)
        include_moderator: Whether to include moderator in the panel
        panel_config_id: Stored config id label (default: "custom")
        personas_config: Optional mapping of valid persona IDs to configs for
            validation. If provided, persona_ids MUST exist in this mapping.

    Raises:
        ValueError: If persona_ids length is not 2-4, or if unknown persona IDs
            are provided when personas_config is present.
    """
    if not isinstance(persona_ids, list):
        raise ValueError("persona_ids must be a list containing 2-4 personas")

    if len(persona_ids) < 2 or len(persona_ids) > 4:
        raise ValueError("persona_ids must contain 2-4 personas")

    # Normalize and ensure stable ordering
    persona_ids = [str(pid) for pid in persona_ids]

    # Optional validation against available personas
    if personas_config is not None:
        unknown = [pid for pid in persona_ids if pid not in personas_config]
        if unknown:
            raise ValueError(f"Unknown persona IDs: {unknown}")

    session_id = f"panel-{uuid.uuid4().hex[:12]}"

    session = PanelSession(
        session_id=session_id,
        panel_config_id=panel_config_id,
        persona_ids=persona_ids,
        has_moderator=include_moderator,
        exchange_count=0,
        discussion_history=[],
    )

    logger.info(f"Created custom panel session {session_id} ({len(persona_ids)} personas)")
    return session


def create_panel_session(
    panel_config_id: str,
    include_moderator: bool = True
) -> PanelSession:
    """
    Create a new panel discussion session.
    
    Args:
        panel_config_id: ID of the panel configuration to use
        include_moderator: Whether to include moderator in the panel
        
    Returns:
        New PanelSession object
        
    Raises:
        ValueError: If panel_config_id is invalid or configs not loaded
    """
    if not _config_loaded:
        raise ValueError("Panel configs not loaded. Call load_panel_configs() first.")
    
    # Get panel configuration
    panel_config = get_panel_config(panel_config_id)
    if panel_config is None:
        raise ValueError(f"Panel config not found: {panel_config_id}")
    
    # Generate unique session ID
    session_id = f"panel-{uuid.uuid4().hex[:12]}"
    
    # Get persona IDs from config
    persona_ids = panel_config['persona_ids'].copy()
    
    # Create session
    session = PanelSession(
        session_id=session_id,
        panel_config_id=panel_config_id,
        persona_ids=persona_ids,
        has_moderator=include_moderator,
        exchange_count=0,
        discussion_history=[]
    )
    
    logger.info(f"Created panel session {session_id} with config '{panel_config_id}'")
    
    return session


def store_session(session: PanelSession) -> None:
    """
    Store a panel session in active sessions.
    
    Args:
        session: PanelSession to store
    """
    global _active_sessions

    # Update lifecycle timestamp
    session.last_updated = datetime.utcnow().isoformat()

    _active_sessions[session.session_id] = session
    logger.debug(f"Stored session {session.session_id}")


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    """Parse ISO datetime string safely."""
    if not value:
        return None
    try:
        # Stored values are naive UTC timestamps via datetime.utcnow().isoformat()
        return datetime.fromisoformat(value)
    except Exception:
        return None


def is_session_expired(
    session: PanelSession,
    *,
    now: Optional[datetime] = None,
    ttl_seconds: int = SESSION_TTL_SECONDS,
) -> bool:
    """
    Check if a session has expired based on last_updated timestamp.
    """
    now = now or datetime.utcnow()

    last = _parse_iso_datetime(session.last_updated) or _parse_iso_datetime(session.created_at)
    if last is None:
        return False

    return (now - last).total_seconds() > ttl_seconds


def cleanup_expired_sessions(
    *,
    now: Optional[datetime] = None,
    ttl_seconds: int = SESSION_TTL_SECONDS,
) -> int:
    """
    Remove expired sessions from memory.

    Returns:
        Number of sessions removed.
    """
    now = now or datetime.utcnow()

    removed = 0
    for sid, sess in list(_active_sessions.items()):
        if is_session_expired(sess, now=now, ttl_seconds=ttl_seconds):
            _active_sessions.pop(sid, None)
            removed += 1

    if removed:
        logger.info(f"Cleaned up {removed} expired panel sessions")

    return removed


def delete_session(session_id: str) -> Optional[PanelSession]:
    """Remove a session from active sessions and return it."""
    return _active_sessions.pop(session_id, None)


def get_session(
    session_id: str,
    *,
    now: Optional[datetime] = None,
    ttl_seconds: int = SESSION_TTL_SECONDS,
) -> Optional[PanelSession]:
    """
    Retrieve a panel session by ID.
    
    Args:
        session_id: The session ID to retrieve
        
    Returns:
        PanelSession if found, None otherwise
    """
    session = _active_sessions.get(session_id)
    
    if session is None:
        logger.debug(f"Session not found: {session_id}")

    if session is None:
        return None

    # Expiry check
    if is_session_expired(session, now=now, ttl_seconds=ttl_seconds):
        _active_sessions.pop(session_id, None)
        logger.info(f"Session expired and removed: {session_id}")
        return None

    return session


def list_active_sessions() -> List[str]:
    """
    Get list of active session IDs.
    
    Returns:
        List of session IDs
    """
    return list(_active_sessions.keys())


# ============================================================================
# DISCUSSION CONTEXT BUILDING
# ============================================================================

# Configuration
MAX_PREVIOUS_EXCHANGES = 3  # Limit to last N exchanges to save tokens


def build_discussion_context(
    session: PanelSession,
    persona_id: str,
    persona_config: Dict[str, Any],
    user_message: str
) -> str:
    """
    Build discussion context for a persona's response generation.
    
    This creates a comprehensive context string that includes:
    - The persona's system prompt
    - The user's message
    - Previous responses from other panelists (if any)
    - Instructions on how to reference other panelists
    
    Args:
        session: The panel session
        persona_id: ID of the persona generating response
        persona_config: Configuration dict for the persona
        user_message: The user's current message
        
    Returns:
        Formatted context string ready for LLM
        
    Raises:
        ValueError: If user_message is empty
    """
    # Validate user message
    if not user_message or not user_message.strip():
        raise ValueError("User message cannot be empty")
    
    # Start building context with system prompt
    context_parts = []
    
    # 1. System Prompt
    system_prompt = persona_config.get('systemPrompt', '')
    context_parts.append(f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n")
    
    # 2. Panel Discussion Context
    context_parts.append("\nPANEL DISCUSSION CONTEXT:")
    context_parts.append(f"You are participating in a panel discussion with {len(session.persona_ids)} therapeutic personas.")
    context_parts.append("Your goal is to provide your unique perspective while being aware of what others have said.\n")
    
    # 3. User's Message
    context_parts.append(f"\nUSER'S MESSAGE:\n{user_message}\n")
    
    # 4. Previous Responses (if any)
    previous_responses = _get_recent_responses(session)
    
    if previous_responses:
        context_parts.append("\nPREVIOUS PANELIST RESPONSES:")
        context_parts.append("The following panel members have already responded to this message:\n")
        
        for response in previous_responses:
            context_parts.append(
                f"• {response.persona_name} said: \"{response.response}\""
            )
        
        # Add instructions for referencing
        context_parts.append(
            "\nINSTRUCTIONS: You may reference, build upon, challenge, or complement "
            "the insights from other panelists by mentioning them by name. "
            "However, maintain your unique therapeutic perspective and personality."
        )
    else:
        context_parts.append(
            "\nPREVIOUS RESPONSES: None - you are the first panelist to respond."
        )
    
    # Join all parts
    context = "\n".join(context_parts)
    
    logger.debug(f"Built context for {persona_id} ({len(context)} chars)")
    
    return context


def _get_recent_responses(session: PanelSession) -> List[PanelResponse]:
    """
    Get recent responses from the session, limited to MAX_PREVIOUS_EXCHANGES.
    
    Args:
        session: The panel session
        
    Returns:
        List of recent PanelResponse objects
    """
    if not session.discussion_history:
        return []
    
    # Get the most recent exchange
    recent_exchanges = session.discussion_history[-MAX_PREVIOUS_EXCHANGES:]
    
    # Extract all responses from recent exchanges
    all_responses = []
    for exchange in recent_exchanges:
        responses = exchange.get('responses', [])
        all_responses.extend(responses)
    
    return all_responses


# ============================================================================
# RESPONSE GENERATION
# ============================================================================

# Configuration
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash-exp"
DEFAULT_MOOD = "neutral"
VALID_MOODS = ['thinking', 'amused', 'concerned', 'shocked', 'neutral']

# Gemini client cache
_gemini_client = None


def get_gemini_client():
    """
    Get or create Gemini API client.
    
    Returns:
        Gemini client instance
        
    Raises:
        RuntimeError: If Gemini not available or API key not set
    """
    global _gemini_client
    
    if not GEMINI_AVAILABLE:
        raise RuntimeError("Gemini client not available. Install google-genai package.")
    
    if _gemini_client is None:
        api_key = os.getenv('GOOGLE_AI_STUDIO_KEY') or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise RuntimeError("Gemini API key not found in environment variables")
        
        _gemini_client = genai.Client(api_key=api_key)
        logger.info("Initialized Gemini client")
    
    return _gemini_client


def generate_persona_response(
    session: PanelSession,
    persona_id: str,
    persona_config: Dict[str, Any],
    user_message: str
) -> PanelResponse:
    """
    Generate a response from a single persona using Gemini API.
    
    Args:
        session: The panel session
        persona_id: ID of the persona generating response
        persona_config: Configuration dict for the persona
        user_message: The user's message
        
    Returns:
        PanelResponse with generated response
    """
    try:
        # Build context for this persona
        context = build_discussion_context(
            session=session,
            persona_id=persona_id,
            persona_config=persona_config,
            user_message=user_message
        )
        
        # Get Gemini client
        client = get_gemini_client()
        
        # Create prompt for structured output
        prompt = f"""{context}

Please respond in JSON format with the following structure:
{{
  "response": "Your therapeutic response (2-4 sentences)",
  "mood": "thinking | amused | concerned | shocked | neutral"
}}

Respond now:"""
        
        # Generate response
        logger.debug(f"Generating response for {persona_id}")
        response = client.models.generate_content(
            model=DEFAULT_GEMINI_MODEL,
            contents=prompt
        )
        
        # Parse response
        response_text = response.text.strip()
        
        # Try to extract JSON (may be wrapped in markdown)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        try:
            response_data = json.loads(response_text)
            response_content = response_data.get('response', response_text)
            mood = response_data.get('mood', DEFAULT_MOOD)
        except json.JSONDecodeError:
            # Fallback: use entire response as text
            logger.warning(f"Failed to parse JSON response for {persona_id}, using raw text")
            response_content = response_text
            mood = DEFAULT_MOOD
        
        # Validate mood
        if mood not in VALID_MOODS:
            mood = DEFAULT_MOOD
        
        # Handle empty responses
        if not response_content or len(response_content.strip()) == 0:
            response_content = f"I need a moment to process this... {persona_config.get('name', persona_id)}"
        
        # Get ASCII art for this mood
        ascii_art = get_ascii_art_for_persona(persona_config, mood)
        
        # Create response object
        panel_response = PanelResponse(
            persona_id=persona_id,
            persona_name=persona_config.get('name', persona_id),
            response=response_content,
            mood=mood,
            references=[],  # Will be populated by reference detection
            ascii_art=ascii_art
        )
        
        logger.info(f"Generated response from {persona_id} (mood: {mood})")
        
        return panel_response
        
    except Exception as e:
        logger.error(f"Error generating response for {persona_id}: {e}")
        
        # Return error fallback response
        return PanelResponse(
            persona_id=persona_id,
            persona_name=persona_config.get('name', persona_id),
            response=f"[Error: I'm experiencing technical difficulties. {str(e)[:50]}]",
            mood='shocked',
            references=[],
            ascii_art=get_ascii_art_for_persona(persona_config, 'shocked')
        )


def generate_panel_responses(
    session: PanelSession,
    personas_config: Dict[str, Dict[str, Any]],
    user_message: str,
    skip_personas: Optional[List[str]] = None
) -> List[PanelResponse]:
    """
    Generate responses from all personas in the panel sequentially.
    
    Args:
        session: The panel session
        personas_config: Dict mapping persona IDs to their configs
        user_message: The user's message
        skip_personas: Optional list of persona IDs to skip
        
    Returns:
        List of PanelResponse objects in order
    """
    return list(
        iter_panel_responses(
            session=session,
            personas_config=personas_config,
            user_message=user_message,
            skip_personas=skip_personas,
        )
    )


def iter_panel_responses(
    session: PanelSession,
    personas_config: Dict[str, Dict[str, Any]],
    user_message: str,
    skip_personas: Optional[List[str]] = None,
) -> Iterator[PanelResponse]:
    """
    Generate responses from all personas in the panel sequentially, yielding each
    response as soon as it's available.

    This enables API-level streaming (persona-by-persona) while preserving the
    same session history updates as `generate_panel_responses()`.
    """
    skip_personas = skip_personas or []

    # Get personas in order
    personas_to_ask = [pid for pid in session.persona_ids if pid not in skip_personas]

    logger.info(f"Generating responses from {len(personas_to_ask)} personas")

    for persona_id in personas_to_ask:
        persona_config = personas_config.get(persona_id)
        if not persona_config:
            logger.warning(f"Persona config not found for {persona_id}, skipping")
            continue

        response = generate_persona_response(
            session=session,
            persona_id=persona_id,
            persona_config=persona_config,
            user_message=user_message,
        )

        response.references = detect_persona_references(response.response, personas_config)

        # Add to session history (for context building)
        if not session.discussion_history or session.discussion_history[-1].get('user_message') != user_message:
            session.discussion_history.append({'user_message': user_message, 'responses': []})

        session.discussion_history[-1]['responses'].append(response)

        yield response

    # Update exchange count once per user message
    session.exchange_count += 1
    session.last_updated = datetime.utcnow().isoformat()


def detect_persona_references(
    response_text: str,
    personas_config: Dict[str, Dict[str, Any]]
) -> List[str]:
    """
    Detect which personas are referenced in a response.
    
    Args:
        response_text: The response text to analyze
        personas_config: Dict mapping persona IDs to their configs
        
    Returns:
        List of persona IDs that were referenced
    """
    references = []
    response_lower = response_text.lower()
    
    for persona_id, persona_data in personas_config.items():
        persona_name = persona_data.get('name', '')
        if not persona_name:
            continue
        
        # Remove common suffixes like PhD, MD, etc. for matching
        name_clean = re.sub(r',\s*(PhD|MD|PsyD|LCSW).*$', '', persona_name)
        
        # Check if full name (without suffix) appears in response
        if name_clean.lower() in response_lower:
            references.append(persona_id)
            continue
        
        # Check for partial name matches
        name_parts = name_clean.split()
        
        # Try different combinations for flexibility
        # e.g., "Dr. Ada", "Captain Whiskers", "Dr. Sigmund"
        if len(name_parts) >= 2:
            # First two words (e.g., "Dr. Ada", "Captain Whiskers")
            partial_name = ' '.join(name_parts[:2])
            if partial_name.lower() in response_lower:
                references.append(persona_id)
                continue
            
            # Last name only if it's distinct enough (>3 chars)
            last_name = name_parts[-1]
            if len(last_name) > 3 and last_name.lower() in response_lower:
                references.append(persona_id)
                continue
    
    return references


def get_ascii_art_for_persona(
    persona_config: Dict[str, Any],
    mood: str
) -> str:
    """
    Get ASCII art for a persona's specific mood.
    
    Args:
        persona_config: Persona configuration dict
        mood: The mood to get art for
        
    Returns:
        ASCII art string
    """
    ascii_art_dict = persona_config.get('asciiArt', {})
    
    # Try to get specific mood
    ascii_art = ascii_art_dict.get(mood)
    
    # Fallback to neutral
    if not ascii_art:
        ascii_art = ascii_art_dict.get('neutral', '  (._.)  ')
    
    return ascii_art


# ============================================================================
# MODERATOR FUNCTIONALITY
# ============================================================================

# Configuration
DEFAULT_SUMMARY_THRESHOLD = 3  # Generate summary after N exchanges


def should_generate_summary(
    session: PanelSession,
    threshold: int = DEFAULT_SUMMARY_THRESHOLD
) -> bool:
    """
    Determine if it's time to generate a discussion summary.
    
    Args:
        session: The panel session
        threshold: Number of exchanges before summary (default: 3)
        
    Returns:
        True if exchange_count >= threshold
    """
    return session.exchange_count >= threshold


def generate_moderator_intro(session: PanelSession) -> PanelResponse:
    """
    Generate moderator introduction for the panel.
    
    Args:
        session: The panel session
        
    Returns:
        PanelResponse from moderator introducing the panel
    """
    try:
        # Get moderator persona
        moderator = get_moderator_persona()
        if not moderator:
            raise ValueError("Moderator persona not loaded")
        
        # Get persona names for introduction
        persona_names = []
        for persona_id in session.persona_ids:
            # We'd need full personas_config here, so let's build a simple intro
            persona_names.append(persona_id.replace('-', ' ').title())
        
        # Build simple introduction prompt
        names_list = ', '.join(persona_names[:-1]) + f", and {persona_names[-1]}" if len(persona_names) > 1 else persona_names[0]
        
        prompt = f"""You are Dr. Panel, the moderator of this therapeutic panel discussion.

The panel includes: {names_list}

Generate a brief, warm welcome message (1-2 sentences) introducing these panelists to the user.
Keep it professional but friendly."""
        
        # Get Gemini client and generate
        client = get_gemini_client()
        response = client.models.generate_content(
            model=DEFAULT_GEMINI_MODEL,
            contents=prompt
        )
        
        intro_text = response.text.strip()
        
        # Remove any markdown
        intro_text = re.sub(r'```.*?```', '', intro_text, flags=re.DOTALL)
        intro_text = intro_text.strip()
        
        # Create response
        panel_response = PanelResponse(
            persona_id='moderator-dr-panel',
            persona_name=moderator.get('name', 'Dr. Panel'),
            response=intro_text,
            mood='neutral',
            references=[],
            ascii_art=moderator.get('asciiArt', {}).get('neutral', '  [M]  ')
        )
        
        logger.info("Generated moderator introduction")
        
        return panel_response
        
    except Exception as e:
        logger.error(f"Error generating moderator intro: {e}")
        
        # Fallback intro
        return PanelResponse(
            persona_id='moderator-dr-panel',
            persona_name='Dr. Panel',
            response=f"Welcome! Today's panel is ready to discuss your concerns.",
            mood='neutral',
            references=[],
            ascii_art='  [M]  '
        )


def generate_panel_summary(session: PanelSession) -> PanelResponse:
    """
    Generate a summary of the panel discussion so far.
    
    Args:
        session: The panel session with discussion history
        
    Returns:
        PanelResponse from moderator with summary
        
    Raises:
        ValueError: If no discussion history exists
    """
    if not session.discussion_history:
        raise ValueError("No discussion history to summarize. Cannot generate summary for empty session.")
    
    try:
        # Get moderator persona
        moderator = get_moderator_persona()
        if not moderator:
            raise ValueError("Moderator persona not loaded")
        
        # Build context from discussion history
        discussion_context = []
        for exchange in session.discussion_history[-DEFAULT_SUMMARY_THRESHOLD:]:
            user_msg = exchange.get('user_message', '')
            discussion_context.append(f"User: {user_msg}")
            
            for response in exchange.get('responses', []):
                discussion_context.append(
                    f"{response.persona_name}: {response.response}"
                )
        
        context_text = '\n'.join(discussion_context)
        
        # Build summary prompt
        prompt = f"""You are Dr. Panel, the moderator of this therapeutic panel discussion.

Review the following discussion and provide a concise summary:

{context_text}

Please respond in JSON format:
{{
  "summary": "Brief summary of the discussion with key themes (3-5 sentences)",
  "key_insights": ["Insight 1", "Insight 2", "Insight 3"]
}}

Credit specific panelists by name when mentioning their insights."""
        
        # Generate summary
        client = get_gemini_client()
        response = client.models.generate_content(
            model=DEFAULT_GEMINI_MODEL,
            contents=prompt
        )
        
        response_text = response.text.strip()
        
        # Parse JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        try:
            summary_data = json.loads(response_text)
            summary_text = summary_data.get('summary', response_text)
            key_insights = summary_data.get('key_insights', [])
            
            # Append key insights to summary
            if key_insights:
                summary_text += "\n\nKey Insights:\n"
                for i, insight in enumerate(key_insights, 1):
                    summary_text += f"{i}. {insight}\n"
        except json.JSONDecodeError:
            logger.warning("Failed to parse summary JSON, using raw text")
            summary_text = response_text
        
        # Create summary response
        panel_response = PanelResponse(
            persona_id='moderator-dr-panel',
            persona_name=moderator.get('name', 'Dr. Panel'),
            response=summary_text,
            mood='neutral',
            references=[],  # Will be populated by reference detection
            ascii_art=moderator.get('asciiArt', {}).get('neutral', '  [M]  ')
        )
        
        # Detect which personas were referenced in summary
        # Build a simple personas dict for reference detection
        personas_mentioned = {}
        for exchange in session.discussion_history:
            for response in exchange.get('responses', []):
                personas_mentioned[response.persona_id] = {
                    'id': response.persona_id,
                    'name': response.persona_name
                }
        
        panel_response.references = detect_persona_references(
            summary_text,
            personas_mentioned
        )
        
        logger.info(f"Generated panel summary (referenced {len(panel_response.references)} personas)")
        
        return panel_response
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        
        # Fallback summary
        return PanelResponse(
            persona_id='moderator-dr-panel',
            persona_name='Dr. Panel',
            response="The panel has provided diverse perspectives on your situation. Key themes include understanding your feelings and finding practical solutions.",
            mood='neutral',
            references=[],
            ascii_art='  [M]  '
        )
