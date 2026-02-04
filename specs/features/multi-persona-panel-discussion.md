# Multi-Persona Panel Discussion Feature

> **Status:** 📝 Draft - Ready for Review
> **Created:** 2026-02-04
> **Last Updated:** 2026-02-04
> **Author:** AI Agent
> **Depends On:** multi-persona-psychiatrist.md (implemented)
> **Development Approach:** Test-Driven Development (TDD)

## Overview

### Purpose
Enable multiple psychiatric personas to engage in collaborative panel discussions where they comment on and respond to each other's insights while helping the user. This creates a rich, multi-perspective therapy experience where personas can build on, challenge, or complement each other's observations.

### User Story
As a user of the psychiatrist application, I want to start a panel discussion with multiple AI therapists who discuss my situation together, so that I can benefit from multiple therapeutic perspectives simultaneously and see how different approaches interact with each other.

### Scope

**Included:**
- Panel mode with 2-4 selectable personas
- Turn-based discussion where personas respond in sequence
- Personas can reference and comment on each other's previous responses
- User can interject at any time to add context or ask questions
- Discussion summaries and key insights extraction
- Moderator persona to guide the discussion flow
- Configurable panel compositions (e.g., "The Tough Love Panel", "The Mystical & Modern Panel")

**Not Included (Future Enhancements):**
- Real-time simultaneous responses (debating mode)
- User voting on most helpful persona insight
- Persona interruptions or cross-talk
- Audio/voice panel discussions
- Saved panel templates per user
- Panel transcript exports

---

## Requirements

### Functional Requirements

- **FR-1:** Users MUST be able to activate "Panel Mode" from the main interface
- **FR-2:** Users MUST be able to select 2-4 personas to form a discussion panel
- **FR-3:** The system MUST provide pre-configured panel compositions (e.g., "Balanced Panel", "Tough Love Panel")
- **FR-4:** Each persona MUST take turns responding to the user's message in sequence
- **FR-5:** Personas MUST be able to reference previous responses from other panel members in their own responses
- **FR-6:** The system MUST maintain a discussion context including all persona responses for each user message
- **FR-7:** Users MUST be able to send follow-up messages while in panel mode
- **FR-8:** The moderator persona (optional) MUST introduce the panel and summarize key insights
- **FR-9:** Each persona response MUST be clearly labeled with the persona's name
- **FR-10:** Users MUST be able to exit panel mode and return to single-persona chat
- **FR-11:** The system MUST generate a discussion summary after 3-5 exchanges
- **FR-12:** Personas MUST maintain their unique personalities while referencing each other
- **FR-13:** The API MUST support streaming responses for each persona in sequence
- **FR-14:** Users MUST be able to "skip" a persona's turn if they want fewer perspectives

### Non-Functional Requirements

- **Performance:** Each persona's response should generate within 3-5 seconds (per persona, so 10-20s total for a 4-persona panel)
- **Cost Awareness:** Panel mode uses 2-4x the API calls - users should be informed
- **Token Management:** Each persona must be aware of token limits and keep responses concise (2-4 sentences)
- **Maintainability:** Adding new panel configurations should be configuration-only (no code changes)
- **Accessibility:** Panel discussions should work with ASCII fallback if sprites unavailable
- **Responsiveness:** Panel mode UI should adapt to mobile/tablet (stacked layout)
- **Error Handling:** If one persona fails, others should still respond (graceful degradation)

---

## Persona Definitions

### Panel Configurations

#### Configuration 1: The Balanced Panel (Default)
**Members:** Dr. Sigmund 2000, Dr. Ada Sterling, Captain Whiskers
**Description:** Combines retro humor, evidence-based therapy, and whimsical wisdom
**Best For:** General problems, mixed perspectives

#### Configuration 2: The Tough Love Panel
**Members:** Dr. Rex Hardcastle, Dr. Ada Sterling
**Description:** Direct, no-nonsense advice from two practical perspectives
**Best For:** Procrastination, motivation issues, decision paralysis

#### Configuration 3: The Mystical & Modern Panel
**Members:** Dr. Luna Cosmos, Dr. Ada Sterling
**Description:** Spiritual intuition meets clinical psychology
**Best For:** Existential questions, life purpose, spirituality

#### Configuration 4: The Fun Panel
**Members:** Dr. Sigmund 2000, Dr. Pixel, Captain Whiskers
**Description:** Lighthearted therapy with humor and gaming metaphors
**Best For:** Anxiety relief, stress, overthinking

#### Configuration 5: The Expert Panel (Full House)
**Members:** Dr. Sigmund 2000, Dr. Luna Cosmos, Dr. Rex Hardcastle, Dr. Pixel
**Description:** Maximum diversity - all perspectives represented
**Best For:** Complex problems requiring multiple angles

### Moderator Persona (New)

**ID:** `moderator-dr-panel`
**Name:** Dr. Panel (Moderator)
**Role:** Neutral facilitator who introduces the panel and synthesizes insights

**System Prompt:**
```
You are Dr. Panel, a neutral moderator for therapeutic panel discussions.

ROLE:
- Introduce the panel members at the start
- Synthesize key themes and insights after several exchanges
- Ask clarifying questions if the panel seems to miss important context
- Summarize actionable advice at the end

RESPONSE RULES:
1. Keep introductions brief (1-2 sentences per panelist)
2. Summaries should be concise (3-5 bullet points max)
3. Use neutral, professional language
4. Credit insights to specific panelists by name
5. End summaries with an open-ended question to the user

Remember: You facilitate, you don't provide therapy yourself.
```

---

## API Contract

### New Endpoints

#### POST /api/panel/start

Initiate a panel discussion session.

**Request:**
```json
{
  "message": "I'm feeling overwhelmed with work deadlines",
  "panel_config": "balanced",
  "persona_ids": ["dr-sigmund-2000", "dr-ada-sterling", "captain-whiskers"],
  "include_moderator": true,
  "user_history": []
}
```

**Response:**
```json
{
  "session_id": "panel-12345",
  "moderator_intro": {
    "persona": "moderator-dr-panel",
    "response": "Welcome! Today's panel includes Dr. Sigmund 2000, Dr. Ada Sterling, and Captain Whiskers. Let's hear from each of them.",
    "mood": "neutral"
  },
  "panel_responses": [
    {
      "persona_id": "dr-sigmund-2000",
      "persona_name": "Dr. Sigmund 2000",
      "response": "Ah yes, the dreaded 'deadline anxiety buffer overflow' - classic case! Your psyche is defragmenting under pressure...",
      "mood": "thinking",
      "references": [],
      "ascii_art": "..."
    },
    {
      "persona_id": "dr-ada-sterling",
      "persona_name": "Dr. Ada Sterling",
      "response": "I'd add to Dr. Sigmund's observation that this sounds like a cognitive distortion - catastrophizing. Let's break down the actual tasks...",
      "mood": "neutral",
      "references": ["dr-sigmund-2000"],
      "ascii_art": "..."
    },
    {
      "persona_id": "captain-whiskers",
      "persona_name": "Captain Whiskers, PhD",
      "response": "Purr-fectly stated, Dr. Ada. As a cat, I recommend breaking tasks into smaller 'naps' - I mean, chunks. What if you approached one deadline at a time?",
      "mood": "amused",
      "references": ["dr-ada-sterling"],
      "ascii_art": "..."
    }
  ],
  "panel_state": {
    "active": true,
    "exchange_count": 1,
    "total_personas": 3,
    "has_moderator": true
  }
}
```

---

#### POST /api/panel/continue

Continue an existing panel discussion with a new user message.

**Request:**
```json
{
  "session_id": "panel-12345",
  "message": "That's helpful, but I also have personal commitments",
  "skip_personas": []
}
```

**Response:**
```json
{
  "session_id": "panel-12345",
  "panel_responses": [
    {
      "persona_id": "dr-sigmund-2000",
      "persona_name": "Dr. Sigmund 2000",
      "response": "Ah-ha! The old work-life balance subroutine! This is classic disk space allocation conflict...",
      "mood": "amused",
      "references": [],
      "ascii_art": "..."
    },
    {
      "persona_id": "dr-ada-sterling",
      "persona_name": "Dr. Ada Sterling",
      "response": "Building on what Dr. Sigmund mentioned about balance - let's identify your priorities. Studies show that...",
      "mood": "thinking",
      "references": ["dr-sigmund-2000"],
      "ascii_art": "..."
    },
    {
      "persona_id": "captain-whiskers",
      "persona_name": "Captain Whiskers, PhD",
      "response": "Both excellent points. As Dr. Ada suggested, meow-st importantly, you need boundaries. Even cats know when to ignore the red dot...",
      "mood": "concerned",
      "references": ["dr-ada-sterling"],
      "ascii_art": "..."
    }
  ],
  "panel_state": {
    "active": true,
    "exchange_count": 2,
    "total_personas": 3,
    "has_moderator": true,
    "should_summarize": false
  }
}
```

---

#### POST /api/panel/summarize

Request a summary of the discussion so far.

**Request:**
```json
{
  "session_id": "panel-12345"
}
```

**Response:**
```json
{
  "moderator_summary": {
    "persona": "moderator-dr-panel",
    "response": "Let me synthesize what the panel has discussed:\n\n• **Time Management**: Dr. Sigmund and Dr. Ada both emphasized breaking tasks into manageable chunks\n• **Priorities**: Dr. Ada highlighted the importance of identifying what truly matters\n• **Boundaries**: Captain Whiskers reminded us that saying 'no' is essential\n\nWhat specific deadline is causing you the most stress right now?",
    "mood": "neutral",
    "key_insights": [
      "Break tasks into smaller chunks",
      "Identify true priorities",
      "Set boundaries and learn to say no"
    ],
    "credited_personas": ["dr-sigmund-2000", "dr-ada-sterling", "captain-whiskers"]
  }
}
```

---

#### POST /api/panel/end

End the panel discussion and return to single-persona mode.

**Request:**
```json
{
  "session_id": "panel-12345",
  "return_to_persona_id": "dr-ada-sterling"
}
```

**Response:**
```json
{
  "success": true,
  "final_summary": {
    "total_exchanges": 3,
    "insights_count": 5,
    "farewell_message": "Thank you for participating in this panel discussion. The panel members hope their diverse perspectives were helpful!"
  },
  "active_persona": "dr-ada-sterling"
}
```

---

#### GET /api/panel/configs

Get available panel configurations.

**Response:**
```json
{
  "configs": [
    {
      "id": "balanced",
      "name": "The Balanced Panel",
      "description": "Combines retro humor, evidence-based therapy, and whimsical wisdom",
      "persona_ids": ["dr-sigmund-2000", "dr-ada-sterling", "captain-whiskers"],
      "best_for": "General problems, mixed perspectives",
      "default": true
    },
    {
      "id": "tough-love",
      "name": "The Tough Love Panel",
      "description": "Direct, no-nonsense advice from two practical perspectives",
      "persona_ids": ["dr-rex-hardcastle", "dr-ada-sterling"],
      "best_for": "Procrastination, motivation issues"
    }
    // ... more configs
  ]
}
```

---

## Data Model

### New Configuration Structure

**File:** `config/panel_configs.json`

```json
{
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
      "default": true
    },
    "tough-love": {
      "id": "tough-love",
      "name": "The Tough Love Panel",
      "description": "Direct, no-nonsense advice from two practical perspectives",
      "persona_ids": ["dr-rex-hardcastle", "dr-ada-sterling"],
      "best_for": "Procrastination, motivation issues",
      "icon": "💪",
      "order": 2
    },
    "mystical-modern": {
      "id": "mystical-modern",
      "name": "The Mystical & Modern Panel",
      "description": "Spiritual intuition meets clinical psychology",
      "persona_ids": ["dr-luna-cosmos", "dr-ada-sterling"],
      "best_for": "Existential questions, life purpose",
      "icon": "🔮",
      "order": 3
    },
    "fun": {
      "id": "fun",
      "name": "The Fun Panel",
      "description": "Lighthearted therapy with humor and gaming metaphors",
      "persona_ids": ["dr-sigmund-2000", "dr-pixel", "captain-whiskers"],
      "best_for": "Anxiety relief, stress reduction",
      "icon": "🎮",
      "order": 4
    },
    "expert": {
      "id": "expert",
      "name": "The Expert Panel",
      "description": "Maximum diversity - all perspectives represented",
      "persona_ids": ["dr-sigmund-2000", "dr-luna-cosmos", "dr-rex-hardcastle", "dr-pixel"],
      "best_for": "Complex problems requiring multiple angles",
      "icon": "👥",
      "order": 5
    }
  }
}
```

### TypeScript Interfaces (Frontend)

```typescript
interface PanelConfig {
  id: string;
  name: string;
  description: string;
  persona_ids: string[];
  best_for: string;
  icon: string;
  order: number;
  default?: boolean;
}

interface PanelResponse {
  persona_id: string;
  persona_name: string;
  response: string;
  mood: MoodType;
  references: string[]; // IDs of personas referenced
  ascii_art: string;
  timestamp?: string;
}

interface PanelSession {
  session_id: string;
  panel_config_id: string;
  persona_ids: string[];
  has_moderator: boolean;
  exchange_count: number;
  created_at: string;
  last_updated: string;
}

interface PanelState {
  active: boolean;
  exchange_count: number;
  total_personas: number;
  has_moderator: boolean;
  should_summarize: boolean; // After 3-5 exchanges
}

interface DiscussionContext {
  user_message: string;
  previous_responses: PanelResponse[];
  exchange_number: number;
}
```

### Python Classes (Backend)

```python
from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class PanelResponse:
    persona_id: str
    persona_name: str
    response: str
    mood: str
    references: List[str]
    ascii_art: str
    timestamp: str

@dataclass
class PanelSession:
    session_id: str
    panel_config_id: str
    persona_ids: List[str]
    has_moderator: bool
    exchange_count: int
    discussion_history: List[Dict]
    created_at: str
    last_updated: str

class PanelDiscussionManager:
    """Manages multi-persona panel discussions"""
    
    def __init__(self, personas_config: dict, panel_config: dict):
        self.personas = personas_config
        self.panel_configs = panel_config
        self.active_sessions: Dict[str, PanelSession] = {}
    
    def create_session(self, panel_config_id: str, user_message: str, 
                       include_moderator: bool = True) -> PanelSession:
        """Create a new panel discussion session"""
        pass
    
    def generate_panel_responses(self, session_id: str, 
                                 user_message: str) -> List[PanelResponse]:
        """Generate responses from all panelists in sequence"""
        pass
    
    def build_discussion_context(self, session: PanelSession, 
                                 current_persona_id: str) -> str:
        """Build context including previous panel responses for current persona"""
        pass
    
    def should_generate_summary(self, session: PanelSession) -> bool:
        """Determine if it's time for a moderator summary"""
        pass
    
    def generate_summary(self, session: PanelSession) -> PanelResponse:
        """Generate moderator summary of key insights"""
        pass
```

---

## Component Structure

### Files to Create

| File Path | Purpose | Dependencies |
|-----------|---------|--------------|
| `config/panel_configs.json` | Panel configuration data | personas.json |
| `psychiatrist_panel.py` | Panel discussion logic (new module) | psychiatrist_api.py |
| `public/psychiatrist/panel-mode.css` | Panel mode styling | index.html |
| `public/psychiatrist/panel-mode.js` | Panel mode client logic | sprite-engine.js |
| `tests/test_panel_discussion.py` | TDD test suite for panel mode | pytest |

### Files to Modify

| File Path | Changes | Reason |
|-----------|---------|--------|
| `psychiatrist_api.py` | Add panel endpoints, import panel module | API support |
| `public/psychiatrist/index.html` | Add panel mode UI button, panel display area | Frontend support |
| `config/personas.json` | Add moderator persona | Moderator support |

---

## Dependencies

### External Libraries
| Package | Version | Purpose |
|---------|---------|---------|
| None | - | No new dependencies required |

### API Keys / Environment Variables
- Existing `GOOGLE_AI_STUDIO_KEY` / `GEMINI_API_KEY` used for all panel members
- **Note:** Panel mode will consume 2-4x API quota per user message

### System Requirements
- Sufficient token budget for multiple sequential API calls per user message
- Backend capable of handling 2-4 sequential LLM requests (10-20s total latency)

---

## UI Design

### Panel Selection Screen

```
┌─────────────────────────────────────────────────────────────┐
│              🎭 START PANEL DISCUSSION                      │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │ ⚖️  Balanced Panel  │  │ 💪  Tough Love      │          │
│  │ 3 personas          │  │ 2 personas          │          │
│  │ Best for: General   │  │ Best for: Motivation│          │
│  │ [Dr.Sigmund, Ada,   │  │ [Rex, Ada]          │          │
│  │  Whiskers]          │  │                     │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │ 🔮  Mystical &      │  │ 🎮  Fun Panel       │          │
│  │     Modern          │  │ 3 personas          │          │
│  │ 2 personas          │  │ Best for: Stress    │          │
│  │ Best for: Existential│  │ [Sigmund, Pixel,    │          │
│  │ [Luna, Ada]         │  │  Whiskers]          │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
│  ☑️ Include Moderator (Dr. Panel)                          │
│                                                             │
│  [ START PANEL ] [ CUSTOM PANEL ] [ BACK ]                 │
└─────────────────────────────────────────────────────────────┘
```

### Panel Discussion Display

```
┌─────────────────────────────────────────────────────────────┐
│ 🎭 PANEL MODE: The Balanced Panel      [End Panel] [Summary]│
├─────────────────────────────────────────────────────────────┤
│ [Moderator] Dr. Panel:                                      │
│ "Welcome! Today we have Dr. Sigmund 2000, Dr. Ada Sterling, │
│  and Captain Whiskers ready to discuss your situation."     │
├─────────────────────────────────────────────────────────────┤
│ [YOU]:                                                      │
│ "I'm feeling overwhelmed with work deadlines"              │
├─────────────────────────────────────────────────────────────┤
│ [Sprite] [Dr. Sigmund 2000] - Thinking:                    │
│ "Ah yes, the dreaded 'deadline anxiety buffer overflow' -  │
│  classic case! Your psyche is defragmenting under pressure. │
│  Have you tried rebooting your morning routine?"            │
├─────────────────────────────────────────────────────────────┤
│ [Sprite] [Dr. Ada Sterling] - Neutral:                     │
│ "Adding to Dr. Sigmund's observation - this sounds like    │
│  catastrophizing. Let's identify the actual deadline dates. │
│  What's realistically due this week?"                       │
├─────────────────────────────────────────────────────────────┤
│ [Sprite] [Captain Whiskers, PhD] - Amused:                 │
│ "Purr-fectly stated, Dr. Ada. Break tasks into smaller     │
│  chunks - even cats tackle mice one at a time! Which       │
│  deadline is truly urgent?"                                 │
├─────────────────────────────────────────────────────────────┤
│ [💬 Reply to panel...]                  [Send]             │
└─────────────────────────────────────────────────────────────┘
```

---

## Testing Strategy (TDD Approach)

### TDD Process Overview

For this feature, we will follow strict TDD methodology:

1. **RED:** Write failing test for each requirement
2. **GREEN:** Write minimal code to make test pass
3. **REFACTOR:** Improve code while keeping tests green
4. **REPEAT:** For each functional requirement and edge case

### Unit Tests (Backend - Python/pytest)

#### Phase 1: Configuration Loading (TDD Cycle 1)

**Test 1.1: Load panel configurations from JSON**
- **RED:** Write test that calls `load_panel_configs()` before implementation exists
  ```python
  def test_load_panel_configs():
      configs = load_panel_configs('config/panel_configs.json')
      assert 'balanced' in configs['panel_configs']
      assert len(configs['panel_configs']) == 5
  ```
- **GREEN:** Implement minimal `load_panel_configs()` function
- **REFACTOR:** Extract JSON loading logic, add error handling

**Test 1.2: Get panel config by ID - valid**
- **RED:** Write test before implementation
  ```python
  def test_get_panel_config_valid():
      config = get_panel_config('balanced')
      assert config['name'] == 'The Balanced Panel'
      assert len(config['persona_ids']) == 3
  ```
- **GREEN:** Implement `get_panel_config()`
- **REFACTOR:** Add caching mechanism

**Test 1.3: Get panel config by ID - invalid**
- **RED:** Test for invalid ID
  ```python
  def test_get_panel_config_invalid():
      config = get_panel_config('nonexistent')
      assert config is None  # or raises PanelNotFoundError
  ```
- **GREEN:** Add validation in `get_panel_config()`
- **REFACTOR:** Consistent error handling

**Test 1.4: Load moderator persona**
- **RED:** Test moderator loading
  ```python
  def test_load_moderator_persona():
      moderator = get_moderator_persona()
      assert moderator['id'] == 'moderator-dr-panel'
      assert moderator['role'] == 'moderator'
  ```
- **GREEN:** Implement `get_moderator_persona()`
- **REFACTOR:** Merge with persona loading logic

---

#### Phase 2: Session Management (TDD Cycle 2)

**Test 2.1: Create new panel session**
- **RED:**
  ```python
  def test_create_panel_session():
      session = create_panel_session('balanced', include_moderator=True)
      assert session.session_id is not None
      assert len(session.persona_ids) == 3
      assert session.exchange_count == 0
  ```
- **GREEN:** Implement `create_panel_session()`
- **REFACTOR:** Use dataclass for session

**Test 2.2: Session ID is unique**
- **RED:**
  ```python
  def test_session_id_uniqueness():
      session1 = create_panel_session('balanced')
      session2 = create_panel_session('balanced')
      assert session1.session_id != session2.session_id
  ```
- **GREEN:** Add UUID generation
- **REFACTOR:** Extract ID generation function

**Test 2.3: Store and retrieve active session**
- **RED:**
  ```python
  def test_store_and_retrieve_session():
      session = create_panel_session('balanced')
      store_session(session)
      retrieved = get_session(session.session_id)
      assert retrieved.session_id == session.session_id
  ```
- **GREEN:** Implement in-memory session storage
- **REFACTOR:** Consider persistence layer

**Test 2.4: Get session - invalid ID**
- **RED:**
  ```python
  def test_get_session_invalid():
      session = get_session('invalid-id')
      assert session is None
  ```
- **GREEN:** Add validation
- **REFACTOR:** Consistent error handling

---

#### Phase 3: Discussion Context Building (TDD Cycle 3)

**Test 3.1: Build context for first persona (no previous responses)**
- **RED:**
  ```python
  def test_build_context_first_persona():
      session = create_panel_session('balanced')
      context = build_discussion_context(session, 'dr-sigmund-2000', 'I am stressed')
      assert 'You are Dr. Sigmund 2000' in context
      assert 'The user said: I am stressed' in context
      assert 'Previous panel responses: None' in context
  ```
- **GREEN:** Implement `build_discussion_context()`
- **REFACTOR:** Use templates for context formatting

**Test 3.2: Build context for second persona (with one previous response)**
- **RED:**
  ```python
  def test_build_context_second_persona():
      session = create_panel_session('balanced')
      previous_response = PanelResponse(
          persona_id='dr-sigmund-2000',
          response='Classic case!',
          # ... other fields
      )
      session.discussion_history.append({'responses': [previous_response]})
      
      context = build_discussion_context(session, 'dr-ada-sterling', 'I am stressed')
      assert 'Dr. Sigmund 2000 said: Classic case!' in context
      assert 'You can build on, challenge, or complement their insight' in context
  ```
- **GREEN:** Add previous response formatting
- **REFACTOR:** Extract response formatting function

**Test 3.3: Build context with multiple previous responses**
- **RED:**
  ```python
  def test_build_context_third_persona():
      # Setup with 2 previous responses
      context = build_discussion_context(session, 'captain-whiskers', 'I am stressed')
      assert 'Dr. Sigmund 2000 said:' in context
      assert 'Dr. Ada Sterling said:' in context
  ```
- **GREEN:** Loop through all previous responses
- **REFACTOR:** Limit to last N responses to save tokens

**Test 3.4: Context includes persona reference instructions**
- **RED:**
  ```python
  def test_context_includes_reference_instructions():
      # After building context for non-first persona
      context = build_discussion_context(session, 'dr-ada-sterling', 'I am stressed')
      assert 'Reference other panelists by name when building on their ideas' in context
  ```
- **GREEN:** Add instruction template
- **REFACTOR:** Make instructions configurable

---

#### Phase 4: Response Generation (TDD Cycle 4)

**Test 4.1: Generate response for single persona**
- **RED:**
  ```python
  def test_generate_persona_response():
      response = generate_persona_response(
          persona_id='dr-sigmund-2000',
          context='...',
          user_message='I am stressed'
      )
      assert response.persona_id == 'dr-sigmund-2000'
      assert len(response.response) > 0
      assert response.mood in ['thinking', 'amused', 'concerned', 'shocked', 'neutral']
  ```
- **GREEN:** Implement `generate_persona_response()` with Gemini API call
- **REFACTOR:** Extract API call logic

**Test 4.2: Generate responses for full panel**
- **RED:**
  ```python
  def test_generate_panel_responses():
      session = create_panel_session('balanced')
      responses = generate_panel_responses(session, 'I am stressed')
      assert len(responses) == 3  # balanced panel has 3 personas
      assert responses[0].persona_id == 'dr-sigmund-2000'
      assert responses[1].persona_id == 'dr-ada-sterling'
      assert responses[2].persona_id == 'captain-whiskers'
  ```
- **GREEN:** Implement sequential response generation
- **REFACTOR:** Make order configurable

**Test 4.3: Detect references in responses**
- **RED:**
  ```python
  def test_detect_references():
      response_text = "Building on Dr. Ada's point about catastrophizing..."
      references = detect_persona_references(response_text, available_persona_ids)
      assert 'dr-ada-sterling' in references
  ```
- **GREEN:** Implement name-to-ID matching
- **REFACTOR:** Use regex for robust detection

**Test 4.4: Handle API errors gracefully**
- **RED:**
  ```python
  def test_generate_response_api_error(mocker):
      mocker.patch('gemini_api.generate', side_effect=Exception('API Error'))
      response = generate_persona_response('dr-sigmund-2000', '...', 'Test')
      assert response.response.startswith('[Error')  # Fallback message
      assert response.mood == 'shocked'
  ```
- **GREEN:** Add try-except in generation
- **REFACTOR:** Add logging and error reporting

---

#### Phase 5: Moderator Functionality (TDD Cycle 5)

**Test 5.1: Generate moderator introduction**
- **RED:**
  ```python
  def test_generate_moderator_intro():
      session = create_panel_session('balanced', include_moderator=True)
      intro = generate_moderator_intro(session)
      assert intro.persona_id == 'moderator-dr-panel'
      assert 'Dr. Sigmund 2000' in intro.response
      assert 'Dr. Ada Sterling' in intro.response
      assert 'Captain Whiskers' in intro.response
  ```
- **GREEN:** Implement `generate_moderator_intro()`
- **REFACTOR:** Use template for consistency

**Test 5.2: Determine when to summarize**
- **RED:**
  ```python
  def test_should_summarize():
      session = create_panel_session('balanced')
      session.exchange_count = 2
      assert not should_generate_summary(session)
      
      session.exchange_count = 3
      assert should_generate_summary(session)
  ```
- **GREEN:** Implement threshold check (3-5 exchanges)
- **REFACTOR:** Make threshold configurable

**Test 5.3: Generate discussion summary**
- **RED:**
  ```python
  def test_generate_summary():
      session = create_panel_session('balanced')
      # Add sample discussion history
      summary = generate_panel_summary(session)
      assert summary.persona_id == 'moderator-dr-panel'
      assert 'key insights' in summary.response.lower() or 'summarize' in summary.response.lower()
      assert len(summary.references) > 0  # Credits other personas
  ```
- **GREEN:** Implement summary generation with context
- **REFACTOR:** Extract key insight detection

**Test 5.4: Summary credits correct personas**
- **RED:**
  ```python
  def test_summary_credits_personas():
      # Setup session with known responses from specific personas
      summary = generate_panel_summary(session)
      assert 'dr-sigmund-2000' in summary.references
      assert 'dr-ada-sterling' in summary.references
  ```
- **GREEN:** Parse summary for persona mentions
- **REFACTOR:** Use structured output if possible

---

#### Phase 6: Edge Cases (TDD Cycle 6)

**Test 6.1: Panel with minimum personas (2)**
- **RED:**
  ```python
  def test_panel_minimum_personas():
      session = create_panel_session('tough-love')  # 2 personas
      responses = generate_panel_responses(session, 'Help me')
      assert len(responses) == 2
  ```
- **GREEN:** Ensure no hardcoded persona count
- **REFACTOR:** Validate minimum personas in config

**Test 6.2: Panel with maximum personas (4)**
- **RED:**
  ```python
  def test_panel_maximum_personas():
      session = create_panel_session('expert')  # 4 personas
      responses = generate_panel_responses(session, 'Help me')
      assert len(responses) == 4
  ```
- **GREEN:** Ensure loops handle any count
- **REFACTOR:** Consider max limit for performance

**Test 6.3: Skip persona functionality**
- **RED:**
  ```python
  def test_skip_persona():
      session = create_panel_session('balanced')
      responses = generate_panel_responses(session, 'Help', skip_personas=['captain-whiskers'])
      assert len(responses) == 2
      assert not any(r.persona_id == 'captain-whiskers' for r in responses)
  ```
- **GREEN:** Filter personas before generation
- **REFACTOR:** Validate skip list

**Test 6.4: Empty user message**
- **RED:**
  ```python
  def test_empty_user_message():
      session = create_panel_session('balanced')
      with pytest.raises(ValueError):
          generate_panel_responses(session, '')
  ```
- **GREEN:** Add input validation
- **REFACTOR:** Consistent validation across endpoints

**Test 6.5: Session expiration**
- **RED:**
  ```python
  def test_session_expiration():
      session = create_panel_session('balanced')
      # Mock time passage
      assert is_session_expired(session, max_age_minutes=30)
  ```
- **GREEN:** Implement timestamp checking
- **REFACTOR:** Add cleanup job

---

### Integration Tests

#### Integration Test 1: Full panel discussion flow (E2E API)

**Setup:**
- Start Flask test server
- Load test configuration

**Test Steps:**
1. POST to `/api/panel/start` with message "I need help"
2. Verify response contains:
   - Moderator intro (if included)
   - 3 panel responses (for balanced panel)
   - Correct personas in order
3. Extract session_id
4. POST to `/api/panel/continue` with follow-up message
5. Verify:
   - Same session_id
   - Responses reference previous responses
6. POST to `/api/panel/summarize`
7. Verify:
   - Moderator summary returned
   - Key insights listed
   - Persona credits present
8. POST to `/api/panel/end`
9. Verify:
   - Success status
   - Final summary

**Expected:** All steps pass, responses are coherent and persona-appropriate

---

#### Integration Test 2: Panel config selection

**Test Steps:**
1. GET `/api/panel/configs`
2. Verify 5 configs returned
3. For each config:
   - POST `/api/panel/start` with that config
   - Verify correct personas respond
   - Verify response count matches config

**Expected:** Each config works correctly with its defined personas

---

#### Integration Test 3: Error recovery in panel

**Test Steps:**
1. Mock Gemini API to fail for second persona
2. POST to `/api/panel/start`
3. Verify:
   - First persona response succeeds
   - Second persona returns error fallback
   - Third persona still responds (if 3-persona panel)
4. Check that session remains active

**Expected:** Graceful degradation, other personas unaffected

---

#### Integration Test 4: Context building across exchanges

**Test Steps:**
1. Start panel with 2 personas
2. Send message "I'm stressed about work"
3. Extract both responses
4. Send follow-up "What if I also have family issues?"
5. Parse second exchange responses for references to first exchange
6. Verify at least one persona mentions "work" or "stress" from first exchange

**Expected:** Personas maintain conversation context

---

### E2E Tests (Frontend + Backend)

#### E2E Scenario 1: User starts panel discussion from single-persona chat

**Steps:**
1. Open application in browser
2. Select "Dr. Sigmund 2000" for single chat
3. Send message "I feel anxious"
4. Receive single response
5. Click "Start Panel Discussion" button
6. Select "The Balanced Panel"
7. Click "Start Panel"
8. Verify:
   - UI switches to panel mode
   - Moderator intro appears (if enabled)
   - Three persona responses appear
   - Each has correct avatar/sprite
   - Responses are in speech bubbles labeled by persona

**Expected:** Smooth transition, all personas respond correctly

---

#### E2E Scenario 2: User navigates through full panel discussion

**Steps:**
1. Start panel discussion (Balanced Panel)
2. Send initial message "I'm overwhelmed"
3. Verify 3 responses appear
4. Send follow-up "I also can't sleep"
5. Verify 3 new responses reference previous context
6. After 3 exchanges, verify "Summary Available" indicator appears
7. Click "Get Summary" button
8. Verify moderator summary displays with bullet points
9. Click "End Panel" button
10. Verify confirmation dialog
11. Confirm
12. Verify return to single-persona mode

**Expected:** Complete flow works, UI updates correctly at each step

---

#### E2E Scenario 3: User tries different panel configurations

**For each of 5 panel configs:**
1. Start new panel with that config
2. Send message "Help me decide on a career change"
3. Verify:
   - Correct number of personas respond (2-4 depending on config)
   - Personas match config definition
   - Responses reflect diverse personalities
4. Send one follow-up
5. End panel

**Expected:** Each config works as defined, personas are distinct

---

#### E2E Scenario 4: Visual and accessibility check

**Steps:**
1. Start panel with "Fun Panel" (3 personas)
2. Verify:
   - Each persona has distinct sprite/avatar (or ASCII fallback)
   - Speech bubbles have different colors per persona
   - Persona names are clearly labeled
   - Scrolling works correctly
   - Mobile view stacks responses vertically
3. Try with sprites disabled (ASCII-only mode)
4. Verify all ASCII art displays correctly

**Expected:** Visual distinction clear, accessible without sprites

---

### Test Coverage Goals

| Area | Target Coverage | TDD Approach |
|------|-----------------|--------------|
| Configuration loading | 95% | Write tests before implementing config parsing |
| Session management | 90% | Test-first for create/retrieve/expire logic |
| Context building | 90% | TDD for each context scenario |
| Response generation | 85% | Test personas individually, then in sequence |
| Moderator functionality | 85% | Test intro/summary separately |
| API endpoints | 90% | Test each endpoint with valid/invalid inputs |
| Edge cases | 80% | Add tests for each edge case before fixing |
| UI rendering | 70% | Manual testing primary, automated where possible |

### Test Data

**Mock Panel Configurations:**
```json
{
  "test-panel-2": {
    "id": "test-panel-2",
    "persona_ids": ["dr-sigmund-2000", "dr-ada-sterling"]
  },
  "test-panel-4": {
    "id": "test-panel-4",
    "persona_ids": ["dr-sigmund-2000", "dr-luna-cosmos", "dr-rex-hardcastle", "dr-pixel"]
  }
}
```

**Test Messages:**
- Simple: "I'm stressed"
- Complex: "I'm stressed about work deadlines, and also my relationship is suffering"
- Follow-up: "What if I just quit everything?"
- Vague: "I don't know, just feeling off"

**Expected Response Patterns:**
- Dr. Sigmund: Should include tech/90s references
- Dr. Luna: Should include cosmic/mystical language
- Dr. Rex: Should be direct and use sports metaphors
- Dr. Pixel: Should use gaming terminology
- Dr. Ada: Should reference CBT concepts
- Captain Whiskers: Should include cat puns

---

## Acceptance Criteria

### Core Functionality
- [ ] **AC-1:** Users can activate panel mode from main interface
- [ ] **AC-2:** All 5 pre-configured panel compositions are available
- [ ] **AC-3:** Users can select 2-4 personas to form a custom panel
- [ ] **AC-4:** Panel sessions are created with unique session IDs
- [ ] **AC-5:** All selected personas respond to each user message in sequence
- [ ] **AC-6:** Personas reference each other's responses when appropriate (detected in at least 50% of non-first responses)

### Moderator
- [ ] **AC-7:** Moderator introduces panel members at session start (when enabled)
- [ ] **AC-8:** Moderator generates summary after 3-5 exchanges
- [ ] **AC-9:** Summary includes key insights and credits specific personas

### Context & Memory
- [ ] **AC-10:** Each persona receives context of previous panel responses
- [ ] **AC-11:** Personas maintain their unique personalities in panel discussions
- [ ] **AC-12:** Discussion context persists across multiple user messages in same session

### API
- [ ] **AC-13:** POST `/api/panel/start` creates session and returns first panel responses
- [ ] **AC-14:** POST `/api/panel/continue` returns subsequent panel responses for same session
- [ ] **AC-15:** POST `/api/panel/summarize` returns moderator summary
- [ ] **AC-16:** POST `/api/panel/end` terminates session cleanly
- [ ] **AC-17:** GET `/api/panel/configs` returns all available configurations

### UI
- [ ] **AC-18:** Panel mode UI clearly distinguishes responses from different personas
- [ ] **AC-19:** Each persona response shows name, avatar/sprite, and mood
- [ ] **AC-20:** "End Panel" button is visible and functional
- [ ] **AC-21:** Summary display is clear and actionable

### Performance
- [ ] **AC-22:** Full panel response (3 personas) completes within 20 seconds
- [ ] **AC-23:** Session storage doesn't leak memory (sessions expire after 30 minutes)

### Error Handling
- [ ] **AC-24:** If one persona fails, others still respond
- [ ] **AC-25:** Invalid session IDs return appropriate error message
- [ ] **AC-26:** Invalid panel config IDs fall back to default panel

### Testing
- [ ] **AC-27:** All unit tests pass (50+ tests expected)
- [ ] **AC-28:** All integration tests pass (4 scenarios)
- [ ] **AC-29:** All E2E scenarios pass (4 scenarios)
- [ ] **AC-30:** Test coverage meets targets (85%+ for core logic)

---

## TDD Implementation Sequence

### Phase 1: Configuration & Data Model (TDD)
**Estimated Tests:** 8 unit tests

1. **RED:** Write test for loading `panel_configs.json` (fails - file doesn't exist)
2. **GREEN:** Create `panel_configs.json` with 1 config
3. **REFACTOR:** Add all 5 configs
4. **RED:** Test `get_panel_config()` with valid ID
5. **GREEN:** Implement config retrieval
6. **REFACTOR:** Add caching
7. **RED:** Test invalid config ID
8. **GREEN:** Add validation
9. **RED:** Test moderator loading
10. **GREEN:** Implement moderator retrieval
11. **REFACTOR:** Consolidate persona loading

**Deliverable:** `config/panel_configs.json`, config loading functions, 8 passing tests

---

### Phase 2: Session Management (TDD)
**Estimated Tests:** 6 unit tests

1. **RED:** Test session creation
2. **GREEN:** Implement `create_panel_session()`
3. **REFACTOR:** Use dataclass
4. **RED:** Test session ID uniqueness
5. **GREEN:** Add UUID generation
6. **RED:** Test session storage/retrieval
7. **GREEN:** Implement in-memory store
8. **REFACTOR:** Consider persistence
9. **RED:** Test invalid session ID
10. **GREEN:** Add validation

**Deliverable:** Session management module, 6 passing tests

---

### Phase 3: Discussion Context Building (TDD)
**Estimated Tests:** 8 unit tests

1. **RED:** Test context for first persona (no previous responses)
2. **GREEN:** Implement basic context builder
3. **REFACTOR:** Use templates
4. **RED:** Test context for second persona (1 previous response)
5. **GREEN:** Add previous response formatting
6. **REFACTOR:** Extract formatting logic
7. **RED:** Test context with multiple previous responses
8. **GREEN:** Loop through responses
9. **REFACTOR:** Limit to last N to save tokens
10. **RED:** Test reference instructions inclusion
11. **GREEN:** Add instruction templates

**Deliverable:** Context building module, 8 passing tests

---

### Phase 4: Response Generation (TDD)
**Estimated Tests:** 10 unit tests

1. **RED:** Test single persona response generation
2. **GREEN:** Implement Gemini API call with context
3. **REFACTOR:** Extract API call logic
4. **RED:** Test full panel response generation
5. **GREEN:** Implement sequential generation
6. **REFACTOR:** Make order configurable
7. **RED:** Test reference detection
8. **GREEN:** Implement name-to-ID matching
9. **REFACTOR:** Use regex
10. **RED:** Test API error handling
11. **GREEN:** Add try-except
12. **REFACTOR:** Add logging

**Deliverable:** Response generation module, 10 passing tests

---

### Phase 5: Moderator Functionality (TDD)
**Estimated Tests:** 6 unit tests

1. **RED:** Test moderator intro generation
2. **GREEN:** Implement intro with persona names
3. **REFACTOR:** Use template
4. **RED:** Test summary trigger logic
5. **GREEN:** Implement exchange count check
6. **REFACTOR:** Make threshold configurable
7. **RED:** Test summary generation
8. **GREEN:** Implement summary with key insights
9. **REFACTOR:** Extract insight detection
10. **RED:** Test persona crediting in summary
11. **GREEN:** Parse summary for mentions

**Deliverable:** Moderator module, 6 passing tests

---

### Phase 6: API Endpoints (TDD)
**Estimated Tests:** 10 integration tests

1. **RED:** Test POST `/api/panel/start` endpoint (fails - endpoint doesn't exist)
2. **GREEN:** Implement endpoint with basic response
3. **REFACTOR:** Connect to session manager
4. **RED:** Test POST `/api/panel/continue`
5. **GREEN:** Implement continuation logic
6. **RED:** Test POST `/api/panel/summarize`
7. **GREEN:** Implement summary endpoint
8. **RED:** Test POST `/api/panel/end`
9. **GREEN:** Implement session termination
10. **RED:** Test GET `/api/panel/configs`
11. **GREEN:** Implement config listing
12. **REFACTOR:** Consistent error handling

**Deliverable:** All API endpoints, 10 passing integration tests

---

### Phase 7: Edge Cases (TDD)
**Estimated Tests:** 8 unit tests

1. **RED:** Test minimum 2-persona panel
2. **GREEN:** Ensure no hardcoded counts
3. **RED:** Test maximum 4-persona panel
4. **GREEN:** Validate loop handles any count
5. **RED:** Test skip persona functionality
6. **GREEN:** Filter personas before generation
7. **RED:** Test empty user message
8. **GREEN:** Add input validation
9. **RED:** Test session expiration
10. **GREEN:** Implement timestamp checking

**Deliverable:** Edge case handling, 8 passing tests

---

### Phase 8: Frontend Integration
**Estimated Tests:** Manual E2E testing

1. Create panel mode UI HTML
2. Add panel selection screen
3. Implement API calls from frontend
4. Add response rendering for multiple personas
5. Test full flow manually
6. Fix UI bugs found during testing

**Deliverable:** Working frontend, 4 passing E2E scenarios

---

### Phase 9: Performance & Polish
1. Load test with 4-persona panels
2. Optimize API call sequencing (parallel if possible)
3. Add loading indicators for each persona
4. Implement session cleanup job
5. Add usage metrics/logging

**Deliverable:** Production-ready feature

---

## TDD Progress Tracking

### Test Count Targets

| Phase | Unit Tests | Integration Tests | E2E Tests | Total |
|-------|------------|-------------------|-----------|-------|
| Phase 1 | 8 | 0 | 0 | 8 |
| Phase 2 | 6 | 0 | 0 | 6 |
| Phase 3 | 8 | 0 | 0 | 8 |
| Phase 4 | 10 | 0 | 0 | 10 |
| Phase 5 | 6 | 0 | 0 | 6 |
| Phase 6 | 0 | 10 | 0 | 10 |
| Phase 7 | 8 | 0 | 0 | 8 |
| Phase 8 | 0 | 0 | 4 | 4 |
| **Total** | **46** | **10** | **4** | **60** |

### TDD Checklist Template (Per Test)

```markdown
## Test: [Test Name]

**Phase:** [RED/GREEN/REFACTOR]
**Status:** [ ] Not Started | [ ] RED (Failing) | [ ] GREEN (Passing) | [ ] REFACTORED

### RED Phase
- [ ] Test written
- [ ] Test runs and fails for correct reason
- [ ] Failure message is clear

### GREEN Phase
- [ ] Minimal implementation written
- [ ] Test now passes
- [ ] No other tests broken

### REFACTOR Phase
- [ ] Code improved (if needed)
- [ ] Test still passes
- [ ] Committed to version control

**Notes:** [Any observations or decisions]
```

---

## Future Enhancements

After TDD implementation and testing:

1. **Async Panel Responses:** Generate all persona responses in parallel instead of sequentially (reduces latency from 20s to ~5s)
2. **Debate Mode:** Personas can disagree and have structured debates
3. **User-Directed Questions:** User can ask a specific panelist to respond
4. **Panel Memory:** Panels remember previous sessions with same user
5. **Persona Voting:** Users vote on most helpful response per exchange
6. **Dynamic Panel Recomposition:** Add/remove panelists mid-session
7. **Panel Analytics:** Track which panels/personas are most effective for which problem types
8. **Export Transcripts:** Download full panel discussion as PDF/markdown

---

## References

- Multi-persona implementation: `specs/features/multi-persona-psychiatrist.md`
- Psychiatrist API: `psychiatrist_api.py`
- Persona config: `config/personas.json`
- TDD workflow: `.cursor/rules/workflows.mdc` (tdd section)
- Architecture: `docs/architecture.md`
- Backend patterns: `docs/backend.md`
