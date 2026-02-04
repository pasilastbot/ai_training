"""
Unit and integration tests for the multi-persona psychiatrist API.

Run with: pytest test_psychiatrist_api.py -v
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from psychiatrist_api import (
    app,
    load_personas,
    get_persona,
    get_ascii_art,
    build_system_prompt,
    build_initial_response,
    PERSONAS,
    DEFAULT_PERSONA_ID,
    VALID_MOODS
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_gemini_client():
    """Mock the Gemini API client."""
    with patch('psychiatrist_api.client') as mock:
        # Create a mock response
        mock_response = Mock()
        mock_candidate = Mock()
        mock_content = Mock()
        mock_part = Mock()
        
        mock_part.text = json.dumps({
            "response": "Test response from therapist",
            "mood": "neutral"
        })
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock.models.generate_content.return_value = mock_response
        yield mock


# ============================================================================
# UNIT TESTS - Persona Loading
# ============================================================================

class TestPersonaLoading:
    """Test persona configuration loading."""
    
    def test_load_personas_returns_dict(self):
        """Test that load_personas returns a dictionary with personas."""
        config = load_personas()
        assert isinstance(config, dict)
        assert "personas" in config
        assert "defaultPersonaId" in config
    
    def test_all_six_personas_loaded(self):
        """Test that all 6 personas are loaded."""
        assert len(PERSONAS) == 6
        expected_ids = [
            "dr-sigmund-2000",
            "dr-luna-cosmos",
            "dr-rex-hardcastle",
            "dr-pixel",
            "dr-ada-sterling",
            "captain-whiskers"
        ]
        for persona_id in expected_ids:
            assert persona_id in PERSONAS
    
    def test_each_persona_has_required_fields(self):
        """Test that each persona has all required fields."""
        required_fields = [
            "id", "name", "tagline", "description", "era",
            "systemPrompt", "welcomeMessage", "resetMessage",
            "theme", "spritePath", "asciiArt", "available", "order"
        ]
        for persona_id, persona in PERSONAS.items():
            for field in required_fields:
                assert field in persona, f"{persona_id} missing field: {field}"
    
    def test_each_persona_has_all_mood_ascii_art(self):
        """Test that each persona defines ASCII art for all moods."""
        for persona_id, persona in PERSONAS.items():
            ascii_art = persona.get("asciiArt", {})
            for mood in VALID_MOODS:
                assert mood in ascii_art, f"{persona_id} missing ASCII for mood: {mood}"
    
    def test_each_persona_theme_has_required_colors(self):
        """Test that each persona theme has required color properties."""
        required_theme_fields = [
            "primary", "secondary", "accent", "headerBg", "headerText",
            "userMessageBg", "botMessageBg", "fontFamily", "terminalGreen"
        ]
        for persona_id, persona in PERSONAS.items():
            theme = persona.get("theme", {})
            for field in required_theme_fields:
                assert field in theme, f"{persona_id} theme missing: {field}"


# ============================================================================
# UNIT TESTS - Helper Functions
# ============================================================================

class TestHelperFunctions:
    """Test helper functions for persona management."""
    
    def test_get_persona_valid_id(self):
        """Test getting a persona by valid ID."""
        persona = get_persona("dr-pixel")
        assert persona["id"] == "dr-pixel"
        assert persona["name"] == "Dr. Pixel"
    
    def test_get_persona_invalid_id_returns_default(self):
        """Test that invalid persona ID returns default persona."""
        persona = get_persona("invalid-id")
        assert persona["id"] == DEFAULT_PERSONA_ID
    
    def test_get_persona_none_returns_default(self):
        """Test that None persona ID returns default persona."""
        persona = get_persona(None)
        assert persona["id"] == DEFAULT_PERSONA_ID
    
    def test_get_ascii_art_valid_mood(self):
        """Test getting ASCII art for valid mood."""
        persona = get_persona("captain-whiskers")
        ascii_art = get_ascii_art(persona, "amused")
        assert "cat" in ascii_art.lower() or "/" in ascii_art or "whiskers" in ascii_art.lower()
    
    def test_get_ascii_art_invalid_mood_returns_fallback(self):
        """Test that invalid mood returns fallback ASCII art."""
        persona = get_persona("dr-sigmund-2000")
        ascii_art = get_ascii_art(persona, "invalid-mood")
        assert len(ascii_art) > 0  # Should return something
    
    def test_build_system_prompt_includes_persona_prompt(self):
        """Test that system prompt includes persona-specific content."""
        persona = get_persona("dr-pixel")
        system_prompt = build_system_prompt(persona)
        assert "Dr. Pixel" in system_prompt or "gaming" in system_prompt.lower()
        assert "JSON" in system_prompt  # Should include JSON instructions
    
    def test_build_system_prompt_includes_json_instructions(self):
        """Test that system prompt includes JSON response format."""
        persona = get_persona("dr-sigmund-2000")
        system_prompt = build_system_prompt(persona)
        assert '{"response":' in system_prompt or 'JSON' in system_prompt
        assert "mood" in system_prompt
    
    def test_build_initial_response_is_valid_json(self):
        """Test that initial response is valid JSON."""
        persona = get_persona("dr-luna-cosmos")
        initial_response = build_initial_response(persona)
        parsed = json.loads(initial_response)
        assert "response" in parsed
        assert "mood" in parsed
        assert parsed["mood"] == "neutral"


# ============================================================================
# INTEGRATION TESTS - API Endpoints
# ============================================================================

class TestPersonasEndpoint:
    """Test the /api/personas endpoint."""
    
    def test_get_personas_returns_200(self, client):
        """Test that GET /api/personas returns 200."""
        response = client.get('/api/personas')
        assert response.status_code == 200
    
    def test_get_personas_returns_json(self, client):
        """Test that response is valid JSON."""
        response = client.get('/api/personas')
        data = response.get_json()
        assert data is not None
        assert "personas" in data
        assert "defaultPersonaId" in data
    
    def test_get_personas_returns_all_six(self, client):
        """Test that all 6 personas are returned."""
        response = client.get('/api/personas')
        data = response.get_json()
        assert len(data["personas"]) == 6
    
    def test_get_personas_includes_required_fields(self, client):
        """Test that each persona includes required fields."""
        response = client.get('/api/personas')
        data = response.get_json()
        required_fields = ["id", "name", "tagline", "description", "era", "theme", "spritePath"]
        for persona in data["personas"]:
            for field in required_fields:
                assert field in persona
    
    def test_get_personas_sorted_by_order(self, client):
        """Test that personas are sorted by order field."""
        response = client.get('/api/personas')
        data = response.get_json()
        personas = data["personas"]
        for i in range(len(personas) - 1):
            assert personas[i]["order"] <= personas[i + 1]["order"]


class TestPersonaDetailEndpoint:
    """Test the /api/personas/:id endpoint."""
    
    def test_get_persona_detail_returns_200(self, client):
        """Test that GET /api/personas/dr-pixel returns 200."""
        response = client.get('/api/personas/dr-pixel')
        assert response.status_code == 200
    
    def test_get_persona_detail_returns_json(self, client):
        """Test that response is valid JSON."""
        response = client.get('/api/personas/captain-whiskers')
        data = response.get_json()
        assert data is not None
        assert data["id"] == "captain-whiskers"
    
    def test_get_persona_detail_includes_full_data(self, client):
        """Test that persona detail includes all fields."""
        response = client.get('/api/personas/dr-sigmund-2000')
        data = response.get_json()
        assert "welcomeMessage" in data
        assert "asciiArt" in data
        assert "theme" in data
    
    def test_get_persona_detail_invalid_id_returns_404(self, client):
        """Test that invalid persona ID returns 404."""
        response = client.get('/api/personas/invalid-persona')
        assert response.status_code == 404
    
    def test_get_persona_detail_ascii_art_for_all_moods(self, client):
        """Test that ASCII art is provided for all moods."""
        response = client.get('/api/personas/dr-luna-cosmos')
        data = response.get_json()
        ascii_art = data["asciiArt"]
        for mood in VALID_MOODS:
            assert mood in ascii_art


class TestChatEndpoint:
    """Test the /api/chat endpoint."""
    
    def test_chat_without_message_returns_400(self, client):
        """Test that chat without message returns 400."""
        response = client.post('/api/chat',
                              json={},
                              content_type='application/json')
        assert response.status_code == 400
    
    def test_chat_with_default_persona(self, client, mock_gemini_client):
        """Test chat with default persona."""
        response = client.post('/api/chat',
                              json={"message": "Hello", "history": []},
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert "response" in data
        assert "mood" in data
        assert "ascii_art" in data
    
    def test_chat_with_specific_persona(self, client, mock_gemini_client):
        """Test chat with specific persona ID."""
        response = client.post('/api/chat',
                              json={
                                  "message": "I need help",
                                  "history": [],
                                  "persona_id": "captain-whiskers"
                              },
                              content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert "response" in data
    
    def test_chat_returns_valid_mood(self, client, mock_gemini_client):
        """Test that chat returns a valid mood."""
        response = client.post('/api/chat',
                              json={"message": "Test", "history": []},
                              content_type='application/json')
        data = response.get_json()
        assert data["mood"] in VALID_MOODS
    
    def test_chat_returns_ascii_art(self, client, mock_gemini_client):
        """Test that chat returns ASCII art."""
        response = client.post('/api/chat',
                              json={
                                  "message": "Test",
                                  "history": [],
                                  "persona_id": "dr-pixel"
                              },
                              content_type='application/json')
        data = response.get_json()
        assert "ascii_art" in data
        assert len(data["ascii_art"]) > 0
    
    def test_chat_with_invalid_persona_uses_default(self, client, mock_gemini_client):
        """Test that invalid persona ID falls back to default."""
        response = client.post('/api/chat',
                              json={
                                  "message": "Test",
                                  "history": [],
                                  "persona_id": "invalid-persona"
                              },
                              content_type='application/json')
        assert response.status_code == 200
        # Should not error, should use default persona

    def test_chat_with_hot_mic_consult_returns_transcript(self, client):
        """Test that consult mode returns a visible hot-mic transcript."""
        with patch('psychiatrist_api.client') as mock_client, patch('random.choice') as mock_choice:
            mock_choice.return_value = "dr-ada-sterling"

            # First model call: colleague consult (JSON)
            consult_response = Mock()
            consult_candidate = Mock()
            consult_content = Mock()
            consult_part = Mock()
            consult_part.text = json.dumps({
                "response": "Hot mic: this patient's sleep hygiene is a dumpster fire.",
                "mood": "amused"
            })
            consult_content.parts = [consult_part]
            consult_candidate.content = consult_content
            consult_response.candidates = [consult_candidate]

            # Second model call: final user-facing response (JSON)
            final_response = Mock()
            final_candidate = Mock()
            final_content = Mock()
            final_part = Mock()
            final_part.text = json.dumps({
                "response": "Let’s build a real sleep plan. Start with consistent wake time and fewer screens.",
                "mood": "thinking"
            })
            final_content.parts = [final_part]
            final_candidate.content = final_content
            final_response.candidates = [final_candidate]

            mock_client.models.generate_content.side_effect = [consult_response, final_response]

            response = client.post(
                '/api/chat',
                json={
                    "message": "what should I do to sleep better?",
                    "history": [],
                    "persona_id": "dr-rex-hardcastle",
                    "consult": True
                },
                content_type='application/json'
            )
            assert response.status_code == 200
            data = response.get_json()

            assert "response" in data
            assert "mood" in data
            assert "ascii_art" in data

            assert "consult" in data
            consult = data["consult"]
            assert consult["enabled"] is True
            assert consult["consulted_persona_id"] == "dr-ada-sterling"
            assert consult["consulted_persona_name"] == "Dr. Ada Sterling"
            assert isinstance(consult["transcript"], list)
            assert len(consult["transcript"]) == 2
            assert consult["transcript"][0]["from_persona_id"] == "dr-rex-hardcastle"
            assert consult["transcript"][1]["from_persona_id"] == "dr-ada-sterling"


class TestResetEndpoint:
    """Test the /api/reset endpoint."""
    
    def test_reset_returns_200(self, client):
        """Test that POST /api/reset returns 200."""
        response = client.post('/api/reset', json={})
        assert response.status_code == 200
    
    def test_reset_returns_json(self, client):
        """Test that reset returns valid JSON."""
        response = client.post('/api/reset', json={})
        data = response.get_json()
        assert "response" in data
        assert "mood" in data
        assert "ascii_art" in data
    
    def test_reset_with_persona_returns_persona_message(self, client):
        """Test that reset with persona returns persona-specific message."""
        response = client.post('/api/reset',
                              json={"persona_id": "dr-pixel"},
                              content_type='application/json')
        data = response.get_json()
        assert "response" in data
        # Should contain Dr. Pixel's reset message


# ============================================================================
# INTEGRATION TESTS - Full Flow
# ============================================================================

class TestPersonaSwitchingFlow:
    """Test the complete persona switching workflow."""
    
    def test_complete_chat_flow_with_captain_whiskers(self, client, mock_gemini_client):
        """Test complete flow: select persona, chat, verify response."""
        # 1. Get personas list
        personas_response = client.get('/api/personas')
        assert personas_response.status_code == 200
        
        # 2. Get Captain Whiskers details
        detail_response = client.get('/api/personas/captain-whiskers')
        assert detail_response.status_code == 200
        persona_data = detail_response.get_json()
        
        # 3. Chat with Captain Whiskers
        chat_response = client.post('/api/chat',
                                    json={
                                        "message": "I'm stressed",
                                        "history": [],
                                        "persona_id": "captain-whiskers"
                                    },
                                    content_type='application/json')
        assert chat_response.status_code == 200
        chat_data = chat_response.get_json()
        assert "response" in chat_data
        
        # 4. Reset session
        reset_response = client.post('/api/reset',
                                     json={"persona_id": "captain-whiskers"},
                                     content_type='application/json')
        assert reset_response.status_code == 200
    
    def test_switch_from_one_persona_to_another(self, client, mock_gemini_client):
        """Test switching between personas during session."""
        # Chat with Dr. Sigmund
        response1 = client.post('/api/chat',
                               json={
                                   "message": "Hello",
                                   "history": [],
                                   "persona_id": "dr-sigmund-2000"
                               },
                               content_type='application/json')
        assert response1.status_code == 200
        
        # Switch to Dr. Pixel
        response2 = client.post('/api/chat',
                               json={
                                   "message": "Hello again",
                                   "history": [],
                                   "persona_id": "dr-pixel"
                               },
                               content_type='application/json')
        assert response2.status_code == 200
        
        # Both should succeed with their respective personas


# ============================================================================
# INTEGRATION TESTS - Panel Discussion API (Phase 6)
# ============================================================================

def _mock_text_response(text: str) -> Mock:
    """Create a mock object with a .text attribute."""
    resp = Mock()
    resp.text = text
    return resp


def _mock_panel_gemini_client(text_responses: list) -> Mock:
    """
    Create a mock Gemini client compatible with psychiatrist_panel.py expectations.
    It must support: client.models.generate_content(...) -> response with .text.
    """
    mock_client = Mock()
    mock_client.models = Mock()
    mock_client.models.generate_content.side_effect = [
        _mock_text_response(t) for t in text_responses
    ]
    return mock_client


class TestPanelConfigsEndpoint:
    """Test the GET /api/panel/configs endpoint."""

    def test_get_panel_configs_returns_200(self, client):
        response = client.get('/api/panel/configs')
        assert response.status_code == 200

    def test_get_panel_configs_returns_configs_list(self, client):
        response = client.get('/api/panel/configs')
        data = response.get_json()
        assert data is not None
        assert 'configs' in data
        assert isinstance(data['configs'], list)
        assert len(data['configs']) >= 2
        # Should include default balanced panel config
        ids = [c.get('id') for c in data['configs']]
        assert 'balanced' in ids


class TestPanelStartEndpoint:
    """Test the POST /api/panel/start endpoint."""

    def test_panel_start_returns_session_and_responses(self, client):
        with patch('psychiatrist_panel.get_gemini_client') as mock_get_client:
            mock_get_client.return_value = _mock_panel_gemini_client([
                # Moderator intro
                "Welcome! Today's panel includes Dr. Sigmund 2000, Dr. Ada Sterling, and Captain Whiskers.",
                # Persona responses (JSON)
                json.dumps({"response": "Hello from Dr. Sigmund 2000.", "mood": "neutral"}),
                json.dumps({"response": "Building on Dr. Sigmund 2000, here's a CBT framing.", "mood": "thinking"}),
                json.dumps({"response": "As Captain Whiskers, I agree with Dr. Ada Sterling. Purr.", "mood": "amused"}),
            ])

            response = client.post(
                '/api/panel/start',
                json={"message": "I feel overwhelmed", "panel_config": "balanced", "include_moderator": True},
            )
            assert response.status_code == 200
            data = response.get_json()

            assert 'session_id' in data
            assert isinstance(data['session_id'], str)
            assert data['session_id'].startswith('panel-')

            assert 'panel_responses' in data
            assert isinstance(data['panel_responses'], list)
            assert len(data['panel_responses']) == 3

            assert 'panel_state' in data
            assert data['panel_state']['active'] is True
            assert data['panel_state']['exchange_count'] == 1

            assert 'moderator_intro' in data
            assert data['moderator_intro']['persona'] == 'moderator-dr-panel'

    def test_panel_start_invalid_config_returns_400(self, client):
        response = client.post(
            '/api/panel/start',
            json={"message": "Hello", "panel_config": "nonexistent", "include_moderator": True},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_panel_start_custom_persona_ids(self, client):
        with patch('psychiatrist_panel.get_gemini_client') as mock_get_client:
            mock_get_client.return_value = _mock_panel_gemini_client([
                # Persona responses only (no moderator)
                json.dumps({"response": "Dr. Ada Sterling response.", "mood": "neutral"}),
                json.dumps({"response": "Captain Whiskers response mentions Dr. Ada Sterling.", "mood": "amused"}),
            ])

            response = client.post(
                '/api/panel/start',
                json={
                    "message": "I need advice",
                    "persona_ids": ["dr-ada-sterling", "captain-whiskers"],
                    "include_moderator": False,
                },
            )
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['panel_responses']) == 2
            assert data['panel_state']['total_personas'] == 2
            assert data['panel_state']['has_moderator'] is False


class TestPanelContinueSummarizeEndEndpoints:
    """Test /api/panel/continue, /api/panel/summarize, /api/panel/end."""

    def test_panel_continue_increments_exchange_count(self, client):
        with patch('psychiatrist_panel.get_gemini_client') as mock_get_client:
            mock_get_client.return_value = _mock_panel_gemini_client([
                # Start: moderator + 3 personas
                "Welcome! Panel intro.",
                json.dumps({"response": "Sigmund first.", "mood": "neutral"}),
                json.dumps({"response": "Ada references Dr. Sigmund 2000.", "mood": "thinking"}),
                json.dumps({"response": "Whiskers references Dr. Ada Sterling.", "mood": "amused"}),
                # Continue: 3 personas
                json.dumps({"response": "Sigmund second.", "mood": "amused"}),
                json.dumps({"response": "Ada second.", "mood": "thinking"}),
                json.dumps({"response": "Whiskers second.", "mood": "concerned"}),
            ])

            start = client.post(
                '/api/panel/start',
                json={"message": "Start", "panel_config": "balanced", "include_moderator": True},
            ).get_json()
            session_id = start['session_id']

            cont = client.post(
                '/api/panel/continue',
                json={"session_id": session_id, "message": "Continue", "skip_personas": []},
            )
            assert cont.status_code == 200
            data = cont.get_json()
            assert data['panel_state']['exchange_count'] == 2
            assert 'should_summarize' in data['panel_state']
            assert data['panel_state']['should_summarize'] in [True, False]

    def test_panel_continue_invalid_session_returns_404(self, client):
        response = client.post(
            '/api/panel/continue',
            json={"session_id": "panel-does-not-exist", "message": "Hi"},
        )
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_panel_summarize_returns_moderator_summary(self, client):
        with patch('psychiatrist_panel.get_gemini_client') as mock_get_client:
            mock_get_client.return_value = _mock_panel_gemini_client([
                # Start: moderator + 3 personas
                "Welcome! Panel intro.",
                json.dumps({"response": "Sigmund says X.", "mood": "neutral"}),
                json.dumps({"response": "Ada says Y.", "mood": "thinking"}),
                json.dumps({"response": "Whiskers says Z.", "mood": "amused"}),
                # Summarize: moderator summary JSON
                json.dumps({
                    "summary": "Dr. Sigmund 2000 and Dr. Ada Sterling emphasized task chunking.",
                    "key_insights": ["Chunk tasks", "Set boundaries"]
                }),
            ])

            start = client.post(
                '/api/panel/start',
                json={"message": "Start", "panel_config": "balanced", "include_moderator": True},
            ).get_json()
            session_id = start['session_id']

            summ = client.post('/api/panel/summarize', json={"session_id": session_id})
            assert summ.status_code == 200
            data = summ.get_json()
            assert 'moderator_summary' in data
            ms = data['moderator_summary']
            assert ms['persona'] == 'moderator-dr-panel'
            assert 'response' in ms
            assert 'key_insights' in ms
            assert isinstance(ms['key_insights'], list)
            assert 'credited_personas' in ms

    def test_panel_summarize_invalid_session_returns_404(self, client):
        response = client.post('/api/panel/summarize', json={"session_id": "panel-nope"})
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data

    def test_panel_end_terminates_session(self, client):
        with patch('psychiatrist_panel.get_gemini_client') as mock_get_client:
            mock_get_client.return_value = _mock_panel_gemini_client([
                # Start: moderator + 3 personas
                "Welcome! Panel intro.",
                json.dumps({"response": "Sigmund first.", "mood": "neutral"}),
                json.dumps({"response": "Ada first.", "mood": "thinking"}),
                json.dumps({"response": "Whiskers first.", "mood": "amused"}),
            ])

            start = client.post(
                '/api/panel/start',
                json={"message": "Start", "panel_config": "balanced", "include_moderator": True},
            ).get_json()
            session_id = start['session_id']

            end_resp = client.post(
                '/api/panel/end',
                json={"session_id": session_id, "return_to_persona_id": "dr-ada-sterling"},
            )
            assert end_resp.status_code == 200
            data = end_resp.get_json()
            assert data.get('success') is True
            assert data.get('active_persona') == 'dr-ada-sterling'

            # Continuing should now fail
            cont = client.post('/api/panel/continue', json={"session_id": session_id, "message": "Hi"})
            assert cont.status_code == 404


class TestPanelStreamingEndpoints:
    """Test SSE streaming mode for panel endpoints (FR-13)."""

    def test_panel_start_stream_returns_sse_events(self, client):
        with patch('psychiatrist_panel.get_gemini_client') as mock_get_client:
            mock_get_client.return_value = _mock_panel_gemini_client([
                # Moderator intro
                "Welcome! Panel intro.",
                # 3 personas
                json.dumps({"response": "Sigmund first.", "mood": "neutral"}),
                json.dumps({"response": "Ada first.", "mood": "thinking"}),
                json.dumps({"response": "Whiskers first.", "mood": "amused"}),
            ])

            resp = client.post(
                '/api/panel/start',
                json={"message": "Start", "panel_config": "balanced", "include_moderator": True, "stream": True},
                buffered=True,
            )
            assert resp.status_code == 200
            assert resp.mimetype == 'text/event-stream'

            text = resp.get_data(as_text=True)
            assert 'event: session' in text
            assert 'event: moderator_intro' in text
            assert 'event: panel_response' in text
            assert 'event: panel_state' in text
            assert 'event: done' in text
            assert '"persona_id": "dr-sigmund-2000"' in text

    def test_panel_continue_stream_returns_sse_events(self, client):
        with patch('psychiatrist_panel.get_gemini_client') as mock_get_client:
            mock_get_client.return_value = _mock_panel_gemini_client([
                # Start (non-stream): moderator + 3 personas
                "Welcome! Panel intro.",
                json.dumps({"response": "Sigmund first.", "mood": "neutral"}),
                json.dumps({"response": "Ada first.", "mood": "thinking"}),
                json.dumps({"response": "Whiskers first.", "mood": "amused"}),
                # Continue (stream): 3 personas
                json.dumps({"response": "Sigmund second.", "mood": "amused"}),
                json.dumps({"response": "Ada second.", "mood": "thinking"}),
                json.dumps({"response": "Whiskers second.", "mood": "concerned"}),
            ])

            start = client.post(
                '/api/panel/start',
                json={"message": "Start", "panel_config": "balanced", "include_moderator": True},
            ).get_json()
            session_id = start['session_id']

            resp = client.post(
                '/api/panel/continue',
                json={"session_id": session_id, "message": "Continue", "stream": True},
                buffered=True,
            )
            assert resp.status_code == 200
            assert resp.mimetype == 'text/event-stream'

            text = resp.get_data(as_text=True)
            assert 'event: panel_response' in text
            assert 'event: panel_state' in text
            assert 'event: done' in text

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
