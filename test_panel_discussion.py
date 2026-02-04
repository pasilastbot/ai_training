"""
Unit and integration tests for multi-persona panel discussion feature.

This test suite follows Test-Driven Development (TDD) methodology.
Each test is written BEFORE the implementation (RED phase).

Run with: pytest test_panel_discussion.py -v
Run with coverage: pytest test_panel_discussion.py -v --cov=psychiatrist_panel --cov-report=html
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime, timedelta


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_panel_config():
    """Sample panel configuration for testing."""
    return {
        "moderator": {
            "id": "moderator-dr-panel",
            "name": "Dr. Panel",
            "role": "moderator",
            "systemPrompt": "You are Dr. Panel, a neutral moderator...",
            "asciiArt": {
                "neutral": "    [M]\n   /   \\\n  | . . |\n   \\ - /\n    '='"
            }
        },
        "panel_configs": {
            "balanced": {
                "id": "balanced",
                "name": "The Balanced Panel",
                "description": "Combines retro humor, evidence-based therapy, and whimsical wisdom",
                "persona_ids": ["dr-sigmund-2000", "dr-ada-sterling", "captain-whiskers"],
                "best_for": "General problems, mixed perspectives",
                "icon": "⚖️",
                "order": 1,
                "default": True
            },
            "tough-love": {
                "id": "tough-love",
                "name": "The Tough Love Panel",
                "description": "Direct, no-nonsense advice",
                "persona_ids": ["dr-rex-hardcastle", "dr-ada-sterling"],
                "best_for": "Procrastination, motivation issues",
                "icon": "💪",
                "order": 2
            }
        }
    }


@pytest.fixture
def panel_config_file(tmp_path, sample_panel_config):
    """Create a temporary panel config file for testing."""
    config_file = tmp_path / "panel_configs.json"
    with open(config_file, 'w') as f:
        json.dump(sample_panel_config, f)
    return config_file


# ============================================================================
# PHASE 1: CONFIGURATION LOADING (TDD Cycle 1)
# ============================================================================

class TestConfigurationLoading:
    """Test panel configuration loading functionality."""
    
    # Test 1.1: Load panel configurations from JSON (RED)
    def test_load_panel_configs(self, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: A valid panel_configs.json file exists
        When: load_panel_configs() is called
        Then: All panel configs and moderator are loaded correctly
        """
        # This will fail because load_panel_configs doesn't exist yet
        from psychiatrist_panel import load_panel_configs
        
        configs = load_panel_configs(str(panel_config_file))
        
        # Assertions
        assert configs is not None
        assert 'panel_configs' in configs
        assert 'moderator' in configs
        assert 'balanced' in configs['panel_configs']
        assert 'tough-love' in configs['panel_configs']
        assert len(configs['panel_configs']) == 2
        
        # Verify moderator
        assert configs['moderator']['id'] == 'moderator-dr-panel'
        assert configs['moderator']['role'] == 'moderator'
    
    # Test 1.2: Get panel config by ID - valid (RED)
    def test_get_panel_config_valid(self, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: Panel configs are loaded
        When: get_panel_config() is called with valid ID 'balanced'
        Then: Returns correct panel configuration
        """
        from psychiatrist_panel import load_panel_configs, get_panel_config
        
        # Load configs first
        load_panel_configs(str(panel_config_file))
        
        # Get specific config
        config = get_panel_config('balanced')
        
        # Assertions
        assert config is not None
        assert config['id'] == 'balanced'
        assert config['name'] == 'The Balanced Panel'
        assert len(config['persona_ids']) == 3
        assert 'dr-sigmund-2000' in config['persona_ids']
        assert 'dr-ada-sterling' in config['persona_ids']
        assert 'captain-whiskers' in config['persona_ids']
    
    # Test 1.3: Get panel config by ID - invalid (RED)
    def test_get_panel_config_invalid(self, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: Panel configs are loaded
        When: get_panel_config() is called with invalid ID 'nonexistent'
        Then: Returns None or raises appropriate error
        """
        from psychiatrist_panel import load_panel_configs, get_panel_config
        
        # Load configs first
        load_panel_configs(str(panel_config_file))
        
        # Get invalid config
        config = get_panel_config('nonexistent')
        
        # Assertion
        assert config is None
    
    # Test 1.4: Load moderator persona (RED)
    def test_load_moderator_persona(self, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: Panel configs are loaded with moderator
        When: get_moderator_persona() is called
        Then: Returns moderator configuration
        """
        from psychiatrist_panel import load_panel_configs, get_moderator_persona
        
        # Load configs first
        load_panel_configs(str(panel_config_file))
        
        # Get moderator
        moderator = get_moderator_persona()
        
        # Assertions
        assert moderator is not None
        assert moderator['id'] == 'moderator-dr-panel'
        assert moderator['name'] == 'Dr. Panel'
        assert moderator['role'] == 'moderator'
        assert 'systemPrompt' in moderator
        assert 'asciiArt' in moderator


# ============================================================================
# PHASE 2: SESSION MANAGEMENT (TDD Cycle 2)
# ============================================================================

class TestSessionManagement:
    """Test panel session creation and management."""
    
    # Test 2.1: Create new panel session (RED)
    def test_create_panel_session(self, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: Panel configs are loaded
        When: create_panel_session() is called with 'balanced' config
        Then: Returns a new PanelSession with unique session_id and exchange_count=0
        """
        from psychiatrist_panel import load_panel_configs, create_panel_session
        
        # Load configs
        load_panel_configs(str(panel_config_file))
        
        # Create session
        session = create_panel_session('balanced', include_moderator=True)
        
        # Assertions
        assert session is not None
        assert session.session_id is not None
        assert len(session.session_id) > 0
        assert session.panel_config_id == 'balanced'
        assert len(session.persona_ids) == 3  # balanced has 3 personas
        assert 'dr-sigmund-2000' in session.persona_ids
        assert 'dr-ada-sterling' in session.persona_ids
        assert 'captain-whiskers' in session.persona_ids
        assert session.has_moderator is True
        assert session.exchange_count == 0
        assert len(session.discussion_history) == 0
    
    # Test 2.2: Session ID is unique (RED)
    def test_session_id_uniqueness(self, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: Panel configs are loaded
        When: Two sessions are created
        Then: Each session has a unique session_id
        """
        from psychiatrist_panel import load_panel_configs, create_panel_session
        
        # Load configs
        load_panel_configs(str(panel_config_file))
        
        # Create two sessions
        session1 = create_panel_session('balanced')
        session2 = create_panel_session('balanced')
        
        # Assertions
        assert session1.session_id != session2.session_id
    
    # Test 2.3: Store and retrieve active session (RED)
    def test_store_and_retrieve_session(self, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: A panel session is created
        When: Session is stored and then retrieved by ID
        Then: Retrieved session matches the original
        """
        from psychiatrist_panel import (
            load_panel_configs, 
            create_panel_session,
            store_session,
            get_session
        )
        
        # Load configs and create session
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        # Store session
        store_session(session)
        
        # Retrieve session
        retrieved = get_session(session.session_id)
        
        # Assertions
        assert retrieved is not None
        assert retrieved.session_id == session.session_id
        assert retrieved.panel_config_id == session.panel_config_id
        assert retrieved.persona_ids == session.persona_ids
    
    # Test 2.4: Get session - invalid ID (RED)
    def test_get_session_invalid(self):
        """
        RED PHASE: Write failing test first.
        
        Given: No session with ID 'invalid-id' exists
        When: get_session() is called with 'invalid-id'
        Then: Returns None
        """
        from psychiatrist_panel import get_session
        
        # Try to get non-existent session
        session = get_session('invalid-session-id-12345')
        
        # Assertion
        assert session is None
    
    # Test 2.5: Session creation without moderator (RED)
    def test_create_panel_session_no_moderator(self, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: Panel configs are loaded
        When: create_panel_session() is called with include_moderator=False
        Then: Session is created with has_moderator=False
        """
        from psychiatrist_panel import load_panel_configs, create_panel_session
        
        # Load configs
        load_panel_configs(str(panel_config_file))
        
        # Create session without moderator
        session = create_panel_session('balanced', include_moderator=False)
        
        # Assertions
        assert session is not None
        assert session.has_moderator is False
    
    # Test 2.6: Session with invalid panel config (RED)
    def test_create_session_invalid_config(self, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: Panel configs are loaded
        When: create_panel_session() is called with invalid config ID
        Then: Raises ValueError
        """
        from psychiatrist_panel import load_panel_configs, create_panel_session
        
        # Load configs
        load_panel_configs(str(panel_config_file))
        
        # Try to create session with invalid config
        with pytest.raises(ValueError, match="Panel config not found"):
            create_panel_session('nonexistent-config')


# ============================================================================
# PHASE 3: DISCUSSION CONTEXT BUILDING (TDD Cycle 3)
# ============================================================================

@pytest.fixture
def mock_persona_config():
    """Mock persona configuration for testing."""
    return {
        "id": "dr-sigmund-2000",
        "name": "Dr. Sigmund 2000",
        "systemPrompt": "You are Dr. Sigmund 2000, a retro therapist..."
    }


class TestDiscussionContext:
    """Test discussion context building for personas."""
    
    # Test 3.1: Build context for first persona (no previous responses) (RED)
    def test_build_context_first_persona(self, panel_config_file, mock_persona_config):
        """
        RED PHASE: Write failing test first.
        
        Given: A new panel session with no previous responses
        When: build_discussion_context() is called for the first persona
        Then: Context includes system prompt, user message, and no previous responses
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            build_discussion_context
        )
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        user_message = "I am feeling stressed about work"
        
        # Build context for first persona
        context = build_discussion_context(
            session=session,
            persona_id='dr-sigmund-2000',
            persona_config=mock_persona_config,
            user_message=user_message
        )
        
        # Assertions
        assert context is not None
        assert mock_persona_config['systemPrompt'] in context
        assert user_message in context
        assert 'previous' in context.lower() or 'none' in context.lower()
    
    # Test 3.2: Build context for second persona (with one previous response) (RED)
    def test_build_context_second_persona(self, panel_config_file, mock_persona_config):
        """
        RED PHASE: Write failing test first.
        
        Given: A session with one previous persona response
        When: build_discussion_context() is called for the second persona
        Then: Context includes the previous persona's response
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            build_discussion_context,
            PanelResponse
        )
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        user_message = "I am feeling stressed"
        
        # Add a previous response to session history
        previous_response = PanelResponse(
            persona_id='dr-sigmund-2000',
            persona_name='Dr. Sigmund 2000',
            response='Ah yes, the classic stress buffer overflow!',
            mood='thinking',
            references=[],
            ascii_art='...'
        )
        
        # Add to discussion history
        if not session.discussion_history:
            session.discussion_history.append({
                'user_message': user_message,
                'responses': []
            })
        session.discussion_history[0]['responses'].append(previous_response)
        
        # Build context for second persona
        context = build_discussion_context(
            session=session,
            persona_id='dr-ada-sterling',
            persona_config=mock_persona_config,
            user_message=user_message
        )
        
        # Assertions
        assert 'Dr. Sigmund 2000' in context
        assert 'stress buffer overflow' in context
        assert 'build on' in context.lower() or 'reference' in context.lower()
    
    # Test 3.3: Build context with multiple previous responses (RED)
    def test_build_context_multiple_previous_responses(self, panel_config_file, mock_persona_config):
        """
        RED PHASE: Write failing test first.
        
        Given: A session with multiple previous persona responses
        When: build_discussion_context() is called for the third persona
        Then: Context includes all previous responses in order
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            build_discussion_context,
            PanelResponse
        )
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        user_message = "I am overwhelmed"
        
        # Add multiple previous responses
        responses = [
            PanelResponse(
                persona_id='dr-sigmund-2000',
                persona_name='Dr. Sigmund 2000',
                response='Classic overload situation!',
                mood='thinking',
                references=[],
                ascii_art='...'
            ),
            PanelResponse(
                persona_id='dr-ada-sterling',
                persona_name='Dr. Ada Sterling',
                response='Building on that, this appears to be catastrophizing.',
                mood='neutral',
                references=['dr-sigmund-2000'],
                ascii_art='...'
            )
        ]
        
        session.discussion_history.append({
            'user_message': user_message,
            'responses': responses
        })
        
        # Build context for third persona
        context = build_discussion_context(
            session=session,
            persona_id='captain-whiskers',
            persona_config=mock_persona_config,
            user_message=user_message
        )
        
        # Assertions
        assert 'Dr. Sigmund 2000' in context
        assert 'Dr. Ada Sterling' in context
        assert 'Classic overload' in context
        assert 'catastrophizing' in context
    
    # Test 3.4: Context includes persona reference instructions (RED)
    def test_context_includes_reference_instructions(self, panel_config_file, mock_persona_config):
        """
        RED PHASE: Write failing test first.
        
        Given: A session with previous responses
        When: build_discussion_context() is called
        Then: Context includes instructions to reference other panelists
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            build_discussion_context,
            PanelResponse
        )
        
        # Setup with previous response
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        previous_response = PanelResponse(
            persona_id='dr-sigmund-2000',
            persona_name='Dr. Sigmund 2000',
            response='Test response',
            mood='neutral',
            references=[],
            ascii_art='...'
        )
        
        session.discussion_history.append({
            'user_message': 'Test',
            'responses': [previous_response]
        })
        
        # Build context
        context = build_discussion_context(
            session=session,
            persona_id='dr-ada-sterling',
            persona_config=mock_persona_config,
            user_message='Follow-up message'
        )
        
        # Assertions - check for reference instructions
        assert 'reference' in context.lower() or 'build on' in context.lower() or 'comment' in context.lower()
    
    # Test 3.5: Empty user message raises error (RED)
    def test_empty_user_message_error(self, panel_config_file, mock_persona_config):
        """
        RED PHASE: Write failing test first.
        
        Given: A panel session
        When: build_discussion_context() is called with empty user message
        Then: Raises ValueError
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            build_discussion_context
        )
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        # Try with empty message
        with pytest.raises(ValueError, match="User message cannot be empty"):
            build_discussion_context(
                session=session,
                persona_id='dr-sigmund-2000',
                persona_config=mock_persona_config,
                user_message=''
            )
    
    # Test 3.6: Context formatting is consistent (RED)
    def test_context_formatting_consistency(self, panel_config_file, mock_persona_config):
        """
        RED PHASE: Write failing test first.
        
        Given: Multiple calls to build_discussion_context
        When: Context is built for different scenarios
        Then: Context format is consistent (same structure/sections)
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            build_discussion_context
        )
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        # Build context twice
        context1 = build_discussion_context(
            session=session,
            persona_id='dr-sigmund-2000',
            persona_config=mock_persona_config,
            user_message='First message'
        )
        
        context2 = build_discussion_context(
            session=session,
            persona_id='dr-sigmund-2000',
            persona_config=mock_persona_config,
            user_message='Second message'
        )
        
        # Both should have system prompt section
        assert mock_persona_config['systemPrompt'] in context1
        assert mock_persona_config['systemPrompt'] in context2
        
        # Both should have user message section
        assert 'First message' in context1
        assert 'Second message' in context2
    
    # Test 3.7: Previous responses are ordered correctly (RED)
    def test_previous_responses_ordering(self, panel_config_file, mock_persona_config):
        """
        RED PHASE: Write failing test first.
        
        Given: Multiple previous responses in session
        When: build_discussion_context() is called
        Then: Previous responses appear in correct order (chronological)
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            build_discussion_context,
            PanelResponse
        )
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        # Add responses in specific order
        responses = [
            PanelResponse('persona1', 'Persona 1', 'First response', 'neutral', [], '...'),
            PanelResponse('persona2', 'Persona 2', 'Second response', 'neutral', [], '...'),
            PanelResponse('persona3', 'Persona 3', 'Third response', 'neutral', [], '...')
        ]
        
        session.discussion_history.append({
            'user_message': 'Test',
            'responses': responses
        })
        
        # Build context
        context = build_discussion_context(
            session=session,
            persona_id='persona4',
            persona_config=mock_persona_config,
            user_message='Test'
        )
        
        # Check ordering - first should appear before second before third
        idx_first = context.index('First response')
        idx_second = context.index('Second response')
        idx_third = context.index('Third response')
        
        assert idx_first < idx_second < idx_third
    
    # Test 3.8: Context limits previous responses to save tokens (RED)
    def test_context_limits_previous_responses(self, panel_config_file, mock_persona_config):
        """
        RED PHASE: Write failing test first.
        
        Given: A session with many previous exchanges (>5)
        When: build_discussion_context() is called
        Then: Only recent exchanges are included (e.g., last 3-5)
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            build_discussion_context,
            PanelResponse
        )
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        # Add many exchanges (more than limit)
        for i in range(8):
            session.discussion_history.append({
                'user_message': f'Message {i}',
                'responses': [
                    PanelResponse(
                        'persona1',
                        'Persona 1',
                        f'Response {i}',
                        'neutral',
                        [],
                        '...'
                    )
                ]
            })
        
        # Build context
        context = build_discussion_context(
            session=session,
            persona_id='persona1',
            persona_config=mock_persona_config,
            user_message='Final message'
        )
        
        # Should NOT include very old exchanges (e.g., 0 and 1)
        assert 'Response 0' not in context
        assert 'Response 1' not in context
        
        # Should include recent exchanges (e.g., 6 and 7)
        assert 'Response 6' in context or 'Response 7' in context


# ============================================================================
# PHASE 4: RESPONSE GENERATION (TDD Cycle 4)
# ============================================================================

@pytest.fixture
def mock_gemini_response():
    """Mock successful Gemini API response."""
    mock_response = Mock()
    mock_response.text = json.dumps({
        "response": "This is a thoughtful therapeutic response from the persona.",
        "mood": "thinking"
    })
    return mock_response


@pytest.fixture
def mock_personas_config():
    """Mock full personas configuration for testing."""
    return {
        "dr-sigmund-2000": {
            "id": "dr-sigmund-2000",
            "name": "Dr. Sigmund 2000",
            "systemPrompt": "You are Dr. Sigmund 2000..."
        },
        "dr-ada-sterling": {
            "id": "dr-ada-sterling",
            "name": "Dr. Ada Sterling",
            "systemPrompt": "You are Dr. Ada Sterling..."
        },
        "captain-whiskers": {
            "id": "captain-whiskers",
            "name": "Captain Whiskers, PhD",
            "systemPrompt": "You are Captain Whiskers..."
        }
    }


class TestResponseGeneration:
    """Test panel response generation."""
    
    # Test 4.1: Generate response for single persona (RED)
    @patch('psychiatrist_panel.get_gemini_client')
    def test_generate_persona_response(self, mock_get_client, panel_config_file, mock_gemini_response):
        """
        RED PHASE: Write failing test first.
        
        Given: A persona context and user message
        When: generate_persona_response() is called
        Then: Returns a PanelResponse with response text and mood
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            generate_persona_response
        )
        
        # Mock Gemini client
        mock_client = Mock()
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_gemini_response
        mock_client.models = Mock()
        mock_client.models.generate_content = mock_model.generate_content
        mock_get_client.return_value = mock_client
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        persona_config = {
            "id": "dr-sigmund-2000",
            "name": "Dr. Sigmund 2000",
            "systemPrompt": "You are Dr. Sigmund 2000..."
        }
        
        # Generate response
        response = generate_persona_response(
            session=session,
            persona_id='dr-sigmund-2000',
            persona_config=persona_config,
            user_message='I am stressed'
        )
        
        # Assertions
        assert response is not None
        assert response.persona_id == 'dr-sigmund-2000'
        assert response.persona_name == 'Dr. Sigmund 2000'
        assert len(response.response) > 0
        assert response.mood in ['thinking', 'amused', 'concerned', 'shocked', 'neutral']
        assert isinstance(response.references, list)
        assert response.ascii_art is not None
    
    # Test 4.2: Generate responses for full panel (RED)
    @patch('psychiatrist_panel.get_gemini_client')
    def test_generate_panel_responses(self, mock_get_client, panel_config_file, 
                                     mock_gemini_response, mock_personas_config):
        """
        RED PHASE: Write failing test first.
        
        Given: A panel session with 3 personas
        When: generate_panel_responses() is called
        Then: Returns list of 3 responses in correct order
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            generate_panel_responses
        )
        
        # Mock Gemini client
        mock_client = Mock()
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_gemini_response
        mock_client.models = Mock()
        mock_client.models.generate_content = mock_model.generate_content
        mock_get_client.return_value = mock_client
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        # Generate all panel responses
        responses = generate_panel_responses(
            session=session,
            personas_config=mock_personas_config,
            user_message='I need help'
        )
        
        # Assertions
        assert len(responses) == 3  # balanced panel has 3 personas
        assert responses[0].persona_id == 'dr-sigmund-2000'
        assert responses[1].persona_id == 'dr-ada-sterling'
        assert responses[2].persona_id == 'captain-whiskers'
        
        # Each response should be valid
        for response in responses:
            assert len(response.response) > 0
            assert response.mood in ['thinking', 'amused', 'concerned', 'shocked', 'neutral']
    
    # Test 4.3: Detect references in responses (RED)
    def test_detect_persona_references(self):
        """
        RED PHASE: Write failing test first.
        
        Given: Response text that mentions other personas
        When: detect_persona_references() is called
        Then: Returns list of persona IDs that were referenced
        """
        from psychiatrist_panel import detect_persona_references
        
        # Response that references other personas
        response_text = (
            "Building on what Dr. Ada Sterling said about cognitive distortions, "
            "I agree with Dr. Sigmund's observation about buffer overflow. "
            "Captain Whiskers makes a good point too."
        )
        
        available_personas = {
            'dr-sigmund-2000': {
                'id': 'dr-sigmund-2000',
                'name': 'Dr. Sigmund 2000'
            },
            'dr-ada-sterling': {
                'id': 'dr-ada-sterling',
                'name': 'Dr. Ada Sterling'
            },
            'captain-whiskers': {
                'id': 'captain-whiskers',
                'name': 'Captain Whiskers, PhD'
            }
        }
        
        # Detect references
        references = detect_persona_references(response_text, available_personas)
        
        # Assertions
        assert 'dr-ada-sterling' in references
        assert 'dr-sigmund-2000' in references
        assert 'captain-whiskers' in references
    
    # Test 4.4: Handle API errors gracefully (RED)
    @patch('psychiatrist_panel.get_gemini_client')
    def test_generate_response_api_error(self, mock_get_client, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: Gemini API throws an exception
        When: generate_persona_response() is called
        Then: Returns a PanelResponse with error fallback message
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            generate_persona_response
        )
        
        # Mock Gemini client to raise exception
        mock_client = Mock()
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception('API Error')
        mock_client.models = Mock()
        mock_client.models.generate_content = mock_model.generate_content
        mock_get_client.return_value = mock_client
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        persona_config = {
            "id": "dr-sigmund-2000",
            "name": "Dr. Sigmund 2000",
            "systemPrompt": "Test"
        }
        
        # Generate response (should handle error)
        response = generate_persona_response(
            session=session,
            persona_id='dr-sigmund-2000',
            persona_config=persona_config,
            user_message='Test message'
        )
        
        # Assertions
        assert response is not None
        assert '[Error' in response.response or 'experiencing technical' in response.response.lower()
        assert response.mood == 'shocked' or response.mood == 'concerned'
    
    # Test 4.5: Response structure validation (RED)
    @patch('psychiatrist_panel.get_gemini_client')
    def test_response_structure_validation(self, mock_get_client, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: Gemini returns malformed JSON
        When: generate_persona_response() is called
        Then: Handles gracefully and returns valid response structure
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            generate_persona_response
        )
        
        # Mock malformed response
        mock_response = Mock()
        mock_response.text = "This is not valid JSON at all!"
        
        mock_client = Mock()
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_client.models = Mock()
        mock_client.models.generate_content = mock_model.generate_content
        mock_get_client.return_value = mock_client
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        persona_config = {
            "id": "test-persona",
            "name": "Test Persona",
            "systemPrompt": "Test"
        }
        
        # Generate response
        response = generate_persona_response(
            session=session,
            persona_id='test-persona',
            persona_config=persona_config,
            user_message='Test'
        )
        
        # Should still return valid structure
        assert response is not None
        assert hasattr(response, 'persona_id')
        assert hasattr(response, 'response')
        assert hasattr(response, 'mood')
    
    # Test 4.6: Empty response handling (RED)
    @patch('psychiatrist_panel.get_gemini_client')
    def test_empty_response_handling(self, mock_get_client, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: Gemini returns empty or minimal response
        When: generate_persona_response() is called
        Then: Returns a valid fallback response
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            generate_persona_response
        )
        
        # Mock empty response
        mock_response = Mock()
        mock_response.text = json.dumps({"response": "", "mood": "neutral"})
        
        mock_client = Mock()
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_client.models = Mock()
        mock_client.models.generate_content = mock_model.generate_content
        mock_get_client.return_value = mock_client
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        persona_config = {
            "id": "test-persona",
            "name": "Test Persona",
            "systemPrompt": "Test"
        }
        
        # Generate response
        response = generate_persona_response(
            session=session,
            persona_id='test-persona',
            persona_config=persona_config,
            user_message='Test'
        )
        
        # Should have a fallback message
        assert len(response.response) > 0
        assert response.response != ""
    
    # Test 4.7: Sequential response generation updates session (RED)
    @patch('psychiatrist_panel.get_gemini_client')
    def test_sequential_generation_updates_session(self, mock_get_client, panel_config_file, 
                                                   mock_gemini_response, mock_personas_config):
        """
        RED PHASE: Write failing test first.
        
        Given: A panel generates responses sequentially
        When: Each response is generated
        Then: Session discussion_history is updated with each response
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            generate_panel_responses
        )
        
        # Mock Gemini
        mock_client = Mock()
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_gemini_response
        mock_client.models = Mock()
        mock_client.models.generate_content = mock_model.generate_content
        mock_get_client.return_value = mock_client
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        initial_history_length = len(session.discussion_history)
        
        # Generate responses
        responses = generate_panel_responses(
            session=session,
            personas_config=mock_personas_config,
            user_message='Help me'
        )
        
        # Session should be updated
        assert len(session.discussion_history) > initial_history_length
        assert session.exchange_count == 1
    
    # Test 4.8: Response includes ASCII art from persona config (RED)
    @patch('psychiatrist_panel.get_gemini_client')
    def test_response_includes_ascii_art(self, mock_get_client, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: A persona with ASCII art configured
        When: generate_persona_response() is called
        Then: Response includes appropriate ASCII art based on mood
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            generate_persona_response
        )
        
        # Mock response with specific mood
        mock_response = Mock()
        mock_response.text = json.dumps({
            "response": "I'm thinking about this...",
            "mood": "thinking"
        })
        
        mock_client = Mock()
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_client.models = Mock()
        mock_client.models.generate_content = mock_model.generate_content
        mock_get_client.return_value = mock_client
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        persona_config = {
            "id": "test-persona",
            "name": "Test Persona",
            "systemPrompt": "Test",
            "asciiArt": {
                "thinking": "  (?_?)\n thinking...",
                "neutral": "  (._.)  "
            }
        }
        
        # Generate response
        response = generate_persona_response(
            session=session,
            persona_id='test-persona',
            persona_config=persona_config,
            user_message='Test'
        )
        
        # Should include ASCII art for 'thinking' mood
        assert '(?_?)' in response.ascii_art or 'thinking' in response.ascii_art.lower()
    
    # Test 4.9: Skip personas functionality (RED)
    @patch('psychiatrist_panel.get_gemini_client')
    def test_skip_personas_in_generation(self, mock_get_client, panel_config_file, 
                                        mock_gemini_response, mock_personas_config):
        """
        RED PHASE: Write failing test first.
        
        Given: A panel with 3 personas and skip list with 1 persona
        When: generate_panel_responses() is called with skip_personas
        Then: Only 2 responses are generated
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            generate_panel_responses
        )
        
        # Mock Gemini
        mock_client = Mock()
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_gemini_response
        mock_client.models = Mock()
        mock_client.models.generate_content = mock_model.generate_content
        mock_get_client.return_value = mock_client
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        # Generate with skip list
        responses = generate_panel_responses(
            session=session,
            personas_config=mock_personas_config,
            user_message='Help',
            skip_personas=['captain-whiskers']
        )
        
        # Assertions
        assert len(responses) == 2  # Only 2 responses (skipped captain-whiskers)
        assert not any(r.persona_id == 'captain-whiskers' for r in responses)
        assert any(r.persona_id == 'dr-sigmund-2000' for r in responses)
        assert any(r.persona_id == 'dr-ada-sterling' for r in responses)


# ============================================================================
# PHASE 5: MODERATOR FUNCTIONALITY (TDD Cycle 5)
# ============================================================================

class TestModeratorFunctionality:
    """Test moderator introduction and summary generation."""
    
    # Test 5.1: Generate moderator introduction (RED)
    @patch('psychiatrist_panel.get_gemini_client')
    def test_generate_moderator_intro(self, mock_get_client, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: A panel session with 3 personas
        When: generate_moderator_intro() is called
        Then: Returns introduction mentioning all panelists by name
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            generate_moderator_intro,
            get_moderator_persona
        )
        
        # Mock Gemini for moderator
        mock_response = Mock()
        mock_response.text = "Welcome! Today's panel includes Dr. Sigmund 2000, Dr. Ada Sterling, and Captain Whiskers."
        
        mock_client = Mock()
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_client.models = Mock()
        mock_client.models.generate_content = mock_model.generate_content
        mock_get_client.return_value = mock_client
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced', include_moderator=True)
        
        # Generate intro
        intro = generate_moderator_intro(session)
        
        # Assertions
        assert intro is not None
        assert intro.persona_id == 'moderator-dr-panel'
        assert intro.persona_name == 'Dr. Panel'
        assert 'Dr. Sigmund 2000' in intro.response or 'panel' in intro.response.lower()
        assert intro.mood == 'neutral'
    
    # Test 5.2: Determine when to summarize (RED)
    def test_should_generate_summary(self, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: A panel session with various exchange counts
        When: should_generate_summary() is called
        Then: Returns True when exchange_count >= threshold (e.g., 3)
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            should_generate_summary
        )
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        # Test different exchange counts
        session.exchange_count = 0
        assert not should_generate_summary(session)
        
        session.exchange_count = 1
        assert not should_generate_summary(session)
        
        session.exchange_count = 2
        assert not should_generate_summary(session)
        
        session.exchange_count = 3
        assert should_generate_summary(session)
        
        session.exchange_count = 5
        assert should_generate_summary(session)
    
    # Test 5.3: Generate discussion summary (RED)
    @patch('psychiatrist_panel.get_gemini_client')
    def test_generate_panel_summary(self, mock_get_client, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: A session with multiple exchanges
        When: generate_panel_summary() is called
        Then: Returns summary with key insights
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            generate_panel_summary,
            PanelResponse
        )
        
        # Mock Gemini for summary
        mock_response = Mock()
        mock_response.text = json.dumps({
            "summary": "The panel discussed stress management. Key insights: 1) Break tasks into chunks, 2) Set boundaries",
            "key_insights": [
                "Break tasks into manageable chunks",
                "Set healthy boundaries"
            ]
        })
        
        mock_client = Mock()
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_client.models = Mock()
        mock_client.models.generate_content = mock_model.generate_content
        mock_get_client.return_value = mock_client
        
        # Setup with discussion history
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        # Add sample discussion
        session.discussion_history.append({
            'user_message': 'I am stressed',
            'responses': [
                PanelResponse('dr-sigmund-2000', 'Dr. Sigmund 2000', 
                             'Break tasks into chunks', 'thinking', [], '...'),
                PanelResponse('dr-ada-sterling', 'Dr. Ada Sterling',
                             'Set boundaries', 'neutral', [], '...')
            ]
        })
        session.exchange_count = 3
        
        # Generate summary
        summary = generate_panel_summary(session)
        
        # Assertions
        assert summary is not None
        assert summary.persona_id == 'moderator-dr-panel'
        assert 'key insights' in summary.response.lower() or 'summary' in summary.response.lower()
        assert len(summary.response) > 0
    
    # Test 5.4: Summary credits correct personas (RED)
    @patch('psychiatrist_panel.get_gemini_client')
    def test_summary_credits_personas(self, mock_get_client, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: A discussion with known persona responses
        When: generate_panel_summary() is called
        Then: Summary references field includes credited persona IDs
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            generate_panel_summary,
            PanelResponse
        )
        
        # Mock summary that mentions personas
        mock_response = Mock()
        mock_response.text = json.dumps({
            "summary": "Dr. Sigmund 2000 and Dr. Ada Sterling both emphasized task management.",
            "key_insights": ["Task management is key"]
        })
        
        mock_client = Mock()
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_client.models = Mock()
        mock_client.models.generate_content = mock_model.generate_content
        mock_get_client.return_value = mock_client
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        
        session.discussion_history.append({
            'user_message': 'Help',
            'responses': [
                PanelResponse('dr-sigmund-2000', 'Dr. Sigmund 2000', 
                             'Test', 'thinking', [], '...'),
                PanelResponse('dr-ada-sterling', 'Dr. Ada Sterling',
                             'Test', 'neutral', [], '...')
            ]
        })
        session.exchange_count = 3
        
        # Generate summary
        summary = generate_panel_summary(session)
        
        # Check references
        assert 'dr-sigmund-2000' in summary.references or 'dr-ada-sterling' in summary.references
    
    # Test 5.5: Summary threshold is configurable (RED)
    def test_summary_threshold_configurable(self, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: Different summary threshold values
        When: should_generate_summary() is called with custom threshold
        Then: Returns True/False based on custom threshold
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            should_generate_summary
        )
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        session.exchange_count = 4
        
        # Test with default threshold (3)
        assert should_generate_summary(session) is True
        
        # Test with custom threshold
        assert should_generate_summary(session, threshold=5) is False
        assert should_generate_summary(session, threshold=4) is True
        assert should_generate_summary(session, threshold=3) is True
    
    # Test 5.6: Moderator handles empty discussion history (RED)
    @patch('psychiatrist_panel.get_gemini_client')
    def test_moderator_empty_history(self, mock_get_client, panel_config_file):
        """
        RED PHASE: Write failing test first.
        
        Given: A session with no discussion history
        When: generate_panel_summary() is called
        Then: Returns appropriate message or raises informative error
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            generate_panel_summary
        )
        
        # Setup
        load_panel_configs(str(panel_config_file))
        session = create_panel_session('balanced')
        # No discussion history added
        
        # Try to generate summary
        with pytest.raises(ValueError, match="No discussion history|Cannot generate summary"):
            generate_panel_summary(session)


# ============================================================================
# PHASE 7: EDGE CASES (TDD Cycle 7)
# ============================================================================

class TestEdgeCases:
    """Test edge cases and lifecycle management."""

    def test_custom_panel_min_two_personas(self):
        """
        Given: Exactly 2 persona IDs
        When: create_custom_panel_session() is called
        Then: Session is created successfully
        """
        from psychiatrist_panel import create_custom_panel_session

        session = create_custom_panel_session(
            persona_ids=["dr-sigmund-2000", "dr-ada-sterling"],
            include_moderator=False,
            personas_config={
                "dr-sigmund-2000": {"id": "dr-sigmund-2000"},
                "dr-ada-sterling": {"id": "dr-ada-sterling"},
            },
        )
        assert session is not None
        assert len(session.persona_ids) == 2

    def test_custom_panel_max_four_personas(self):
        """
        Given: Exactly 4 persona IDs
        When: create_custom_panel_session() is called
        Then: Session is created successfully
        """
        from psychiatrist_panel import create_custom_panel_session

        session = create_custom_panel_session(
            persona_ids=["dr-sigmund-2000", "dr-luna-cosmos", "dr-rex-hardcastle", "dr-pixel"],
            include_moderator=True,
            personas_config={
                "dr-sigmund-2000": {"id": "dr-sigmund-2000"},
                "dr-luna-cosmos": {"id": "dr-luna-cosmos"},
                "dr-rex-hardcastle": {"id": "dr-rex-hardcastle"},
                "dr-pixel": {"id": "dr-pixel"},
            },
        )
        assert session is not None
        assert len(session.persona_ids) == 4

    def test_custom_panel_too_few_personas_raises(self):
        from psychiatrist_panel import create_custom_panel_session

        with pytest.raises(ValueError, match="2-4"):
            create_custom_panel_session(persona_ids=["dr-sigmund-2000"])

    def test_custom_panel_too_many_personas_raises(self):
        from psychiatrist_panel import create_custom_panel_session

        with pytest.raises(ValueError, match="2-4"):
            create_custom_panel_session(
                persona_ids=["a", "b", "c", "d", "e"]
            )

    def test_custom_panel_unknown_persona_raises_when_personas_config_provided(self):
        from psychiatrist_panel import create_custom_panel_session

        with pytest.raises(ValueError, match="Unknown persona"):
            create_custom_panel_session(
                persona_ids=["dr-sigmund-2000", "unknown-persona"],
                personas_config={"dr-sigmund-2000": {"id": "dr-sigmund-2000"}},
            )

    def test_get_session_returns_none_when_expired(self, panel_config_file):
        """
        Given: A stored session with last_updated far in the past
        When: get_session() is called with short ttl_seconds
        Then: Returns None and the session is removed
        """
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            store_session,
            get_session,
        )

        load_panel_configs(str(panel_config_file))
        session = create_panel_session("balanced")
        store_session(session)

        # Make session look old
        past = datetime.utcnow() - timedelta(seconds=10)
        session.last_updated = past.isoformat()

        retrieved = get_session(session.session_id, now=datetime.utcnow(), ttl_seconds=1)
        assert retrieved is None

    def test_cleanup_expired_sessions_removes_only_expired(self, panel_config_file):
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            store_session,
            cleanup_expired_sessions,
            get_session,
        )

        load_panel_configs(str(panel_config_file))
        s1 = create_panel_session("balanced")
        s2 = create_panel_session("balanced")
        store_session(s1)
        store_session(s2)

        now = datetime.utcnow()
        s1.last_updated = (now - timedelta(seconds=10)).isoformat()
        s2.last_updated = now.isoformat()

        removed = cleanup_expired_sessions(now=now, ttl_seconds=1)
        assert removed == 1

        assert get_session(s1.session_id, now=now, ttl_seconds=1) is None
        assert get_session(s2.session_id, now=now, ttl_seconds=1) is not None

    def test_delete_session_removes_session(self, panel_config_file):
        from psychiatrist_panel import (
            load_panel_configs,
            create_panel_session,
            store_session,
            delete_session,
            get_session,
        )

        load_panel_configs(str(panel_config_file))
        session = create_panel_session("balanced")
        store_session(session)

        deleted = delete_session(session.session_id)
        assert deleted is not None
        assert deleted.session_id == session.session_id
        assert get_session(session.session_id) is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
