# Example: Chat Feature Specification

> **Status:** Example (for demonstration purposes)
> **Created:** 2026-02-04
> **Last Updated:** 2026-02-04
> **Author:** AI Agent

## Overview

### Purpose
Add a conversational chat interface to interact with the Gemini agent, allowing users to have multi-turn conversations with context preservation.

### User Story
As a **developer**, I want to **have a persistent chat interface** so that **I can interact with the AI agent across multiple messages without losing conversation context**.

### Scope
**Included:**
- Web-based chat UI
- Message history persistence (session-based)
- Streaming responses
- Code syntax highlighting in responses

**Not Included:**
- Multi-user support (single-user only)
- Authentication
- Long-term storage (no database)

---

## Requirements

### Functional Requirements
- **FR-1:** User can send messages and receive AI responses
- **FR-2:** Chat history is preserved during the session
- **FR-3:** Responses are streamed token-by-token for better UX
- **FR-4:** Code blocks in responses have syntax highlighting
- **FR-5:** User can clear the chat history
- **FR-6:** System messages (errors, warnings) are visually distinct

### Non-Functional Requirements
- **Performance:** First token response time < 2 seconds
- **Security:** Input sanitization to prevent XSS attacks
- **Accessibility:** Keyboard navigation support (Enter to send, Shift+Enter for newline)
- **Responsive:** Works on desktop and tablet (mobile optional)

---

## API Contract

### Backend Endpoint

```
POST /api/chat
```

**Request:**
```typescript
{
  message: string;          // User's message
  chatHistory?: Array<{     // Optional previous messages
    role: 'user' | 'model';
    parts: string[];
  }>;
  stream?: boolean;         // Enable streaming (default: true)
}
```

**Response (non-streaming):**
```typescript
{
  response: string;
  status: 'success' | 'error';
  error?: string;
}
```

**Response (streaming):**
```
Content-Type: text/event-stream

data: {"token": "Hello", "done": false}
data: {"token": " there", "done": false}
data: {"token": "!", "done": true}
```

### Frontend Function Signature
```typescript
async function sendChatMessage(
  message: string,
  history: ChatMessage[],
  onToken?: (token: string) => void
): Promise<ChatResponse>
```

---

## Data Model

### New Entities
```typescript
interface ChatMessage {
  id: string;              // Unique message ID
  role: 'user' | 'model' | 'system';
  content: string;
  timestamp: Date;
}

interface ChatSession {
  id: string;              // Session ID
  messages: ChatMessage[];
  createdAt: Date;
  lastActivity: Date;
}
```

### Modified Entities
None (this is a greenfield feature).

### Relationships
- ChatSession (1) → ChatMessage (many)

---

## Component Structure

### Files to Create
| File Path | Purpose | Dependencies |
|-----------|---------|--------------|
| `public/chat/index.html` | Chat UI page | None |
| `public/chat/chat.js` | Frontend chat logic | Fetch API, EventSource |
| `public/chat/styles.css` | Chat styling | None |
| `chat_api.py` | Flask backend for chat | `flask`, `google-genai` |

### Files to Modify
None (standalone feature).

### Folder Structure
```
public/
└── chat/
    ├── index.html
    ├── chat.js
    └── styles.css

chat_api.py (root level)
```

---

## Dependencies

### External Libraries
| Package | Version | Purpose |
|---------|---------|---------|
| `google-genai` | Latest | Gemini API client (Python) |
| `flask` | ^3.0.0 | Web server |
| `flask-cors` | ^4.0.0 | CORS handling |
| `highlight.js` | CDN | Syntax highlighting (frontend) |

### API Keys / Environment Variables
- `GEMINI_API_KEY` or `GOOGLE_AI_STUDIO_KEY`: Required for Gemini API

### System Requirements
- Python 3.9+
- Modern browser with EventSource support

---

## Testing Strategy

> **Comprehensive test plan covering all requirements**

### Test Coverage Goals
- **Target Coverage:** 85% line coverage, 80% branch coverage
- **Critical Paths:** Message sanitization and API communication (100% coverage)
- **Excluded:** Third-party library internals (Gemini SDK, EventSource polyfills)

### Unit Tests (REQUIRED)

#### Test Cases by Function/Component

**Function: `sanitizeMessage(message: string): string`**
- **Test 1: XSS Prevention - Script tags**
  - **Given:** Message contains `<script>alert('xss')</script>`
  - **When:** `sanitizeMessage()` is called
  - **Then:** Returns escaped version: `&lt;script&gt;alert('xss')&lt;/script&gt;`
  - **Assertions:** No executable script tags in output

- **Test 2: XSS Prevention - Event handlers**
  - **Given:** Message contains `<img src=x onerror="alert('xss')">`
  - **When:** `sanitizeMessage()` is called
  - **Then:** Event handlers are stripped or escaped
  
- **Test 3: Valid HTML preserved**
  - **Given:** Message contains `<strong>bold text</strong>`
  - **When:** `sanitizeMessage()` is called (if we allow formatting)
  - **Then:** Safe HTML is preserved

- **Test 4: Edge case - Empty input**
  - **Given:** Empty string `""`
  - **When:** `sanitizeMessage()` is called
  - **Then:** Returns empty string without error

**Function: `formatChatHistory(messages: ChatMessage[]): GeminiFormat`**
- **Test 1: Single message conversion**
  - **Given:** `[{ role: 'user', content: 'Hello', timestamp: ... }]`
  - **When:** `formatChatHistory()` is called
  - **Then:** Returns `[{ role: 'user', parts: ['Hello'] }]`

- **Test 2: Multi-turn conversation**
  - **Given:** Array with user and model messages
  - **When:** `formatChatHistory()` is called
  - **Then:** Alternating user/model format, preserves order

- **Test 3: Edge case - Empty history**
  - **Given:** Empty array `[]`
  - **When:** `formatChatHistory()` is called
  - **Then:** Returns empty array without error

- **Test 4: System messages filtered**
  - **Given:** Array includes system messages
  - **When:** `formatChatHistory()` is called
  - **Then:** System messages excluded (only user/model sent to API)

**Function: `handleStreamToken(token: string, messageId: string)`**
- **Test 1: Token appends to existing message**
  - **Given:** Partial message exists in state
  - **When:** New token arrives
  - **Then:** Token appended to existing content

- **Test 2: First token creates message**
  - **Given:** No message with messageId exists
  - **When:** First token arrives
  - **Then:** New message created with token

**Minimum 15 unit tests total covering:**
- Input sanitization (4 tests)
- Data formatting (4 tests)
- Stream handling (2 tests)
- Error handling (3 tests)
- Utility functions (2 tests)

### Integration Tests (REQUIRED)

#### Test Cases by Integration Point

**Integration: Flask Backend + Gemini API**
- **Test 1: Successful chat completion**
  - **Setup:** Mock Gemini API to return "Hello there"
  - **Steps:**
    1. POST to `/api/chat` with `{ message: "Hi", stream: false }`
    2. Verify Gemini API called with correct parameters
    3. Check response structure
  - **Expected:** `{ response: "Hello there", status: "success" }`
  - **Assertions:** Status 200, valid JSON, no error field

- **Test 2: Chat with history context**
  - **Setup:** Mock Gemini API
  - **Steps:**
    1. POST with message and chatHistory array
    2. Verify Gemini receives formatted history
    3. Check response
  - **Expected:** Response incorporates context
  - **Assertions:** History formatted correctly in API call

- **Test 3: Streaming response**
  - **Setup:** Mock Gemini streaming API
  - **Steps:**
    1. POST with `{ stream: true }`
    2. Verify SSE connection established
    3. Receive tokens as SSE events
    4. Verify final "done" event
  - **Expected:** Tokens streamed progressively
  - **Assertions:** Content-Type: text/event-stream, valid event format

- **Test 4: Error handling - Gemini API failure**
  - **Setup:** Mock Gemini API to throw error
  - **Steps:**
    1. POST to `/api/chat`
    2. Catch exception
  - **Expected:** `{ status: "error", error: "API unavailable" }`
  - **Assertions:** Status 500, error message present

- **Test 5: Error handling - Invalid input**
  - **Setup:** None
  - **Steps:**
    1. POST with missing message field
  - **Expected:** `{ status: "error", error: "Message required" }`
  - **Assertions:** Status 400, validation error

- **Test 6: Error handling - Empty message**
  - **Setup:** None
  - **Steps:**
    1. POST with `{ message: "" }`
  - **Expected:** `{ status: "error", error: "Message cannot be empty" }`
  - **Assertions:** Status 400, validation error

**Integration: Frontend + Backend API**
- **Test 7: Full round-trip**
  - **Setup:** Real Flask server, mock Gemini
  - **Steps:**
    1. Call `sendChatMessage()` from frontend
    2. Verify network request
    3. Receive response
  - **Expected:** Response displayed in UI
  - **Assertions:** No CORS errors, data parsed correctly

**Minimum 7 integration tests** covering API endpoints and service integration.

### E2E Tests (REQUIRED)

#### Test Scenarios by User Journey

**Scenario 1: First message (Happy Path)**
- **Objective:** User can send their first message and receive a response
- **Preconditions:** Chat page loaded, empty chat history
- **Steps:**
  1. Navigate to `/public/chat/index.html`
  2. Verify input field is visible and enabled
  3. Type "Hello, how are you?" into input field
  4. Press Enter key (or click Send button)
  5. Wait for message to appear in chat with "user" styling
  6. Wait for streaming response to begin (max 3 seconds)
  7. Wait for response to complete (done indicator)
  8. Verify response message appears with "model" styling
- **Expected Result:** 
  - User message appears immediately
  - Model response streams in token-by-token
  - Complete response is coherent
- **Success Criteria:** 
  - Both messages visible in chat
  - Distinct styling for user vs model
  - Input field cleared after send

**Scenario 2: Multi-turn conversation (Context preservation)**
- **Objective:** Verify conversation context is maintained
- **Preconditions:** Chat page loaded
- **Steps:**
  1. Send message: "What is Python?"
  2. Wait for response (should explain Python)
  3. Send follow-up: "Can you show me an example?"
  4. Wait for response
  5. Verify response references previous context (e.g., Python code example)
- **Expected Result:** 
  - Second response is relevant to first question
  - Model doesn't ask "What topic?" (context preserved)
- **Success Criteria:** 
  - Chat history maintained in UI
  - API receives history in request
  - Response demonstrates context awareness

**Scenario 3: Clear chat history**
- **Objective:** User can reset the conversation
- **Preconditions:** Chat has 3+ messages
- **Steps:**
  1. Click "Clear Chat" button
  2. Verify confirmation dialog appears (if implemented)
  3. Confirm clear action
  4. Verify all messages removed from UI
  5. Send new message
  6. Verify response doesn't reference previous context
- **Expected Result:** 
  - Chat UI is empty
  - New conversation starts fresh
- **Success Criteria:** 
  - All messages cleared
  - History not sent to API

**Scenario 4: Error handling - Network failure**
- **Objective:** Graceful handling of API errors
- **Preconditions:** Simulate network failure (disable API or block endpoint)
- **Steps:**
  1. Send message
  2. Wait for error message to appear
  3. Verify error is user-friendly (not stack trace)
  4. Restore network
  5. Retry sending message
  6. Verify recovery works
- **Expected Result:** 
  - Clear error message displayed
  - User can retry after error
  - No broken UI state
- **Success Criteria:** 
  - Error message shown with "error" styling
  - Retry button available OR input still enabled
  - Successful recovery after network restored

**Scenario 5: Code block rendering**
- **Objective:** Code in responses is properly formatted
- **Preconditions:** Chat loaded
- **Steps:**
  1. Send: "Show me a Python function"
  2. Wait for response with code block
  3. Verify code has syntax highlighting
  4. Verify code is in monospace font
  5. Verify copy button present (if implemented)
- **Expected Result:** 
  - Code is visually distinct from text
  - Syntax highlighting applied
- **Success Criteria:** 
  - highlight.js library loaded
  - Code blocks have `.hljs` class
  - Proper language detected

**Scenario 6: Keyboard shortcuts**
- **Objective:** Verify accessibility features
- **Preconditions:** Chat loaded
- **Steps:**
  1. Type message
  2. Press Enter to send (not clicking button)
  3. Press Shift+Enter to add newline (if supported)
  4. Tab through interface to verify keyboard navigation
- **Expected Result:** 
  - Enter sends message
  - Shift+Enter adds newline
  - All interactive elements keyboard-accessible
- **Success Criteria:** 
  - No mouse required for basic operations
  - Focus indicators visible

**Scenario 7: Long message handling**
- **Objective:** System handles very long inputs/outputs
- **Preconditions:** Chat loaded
- **Steps:**
  1. Paste 5000-character message
  2. Attempt to send
  3. Verify either: truncation warning, or successful send
  4. If sent, verify response handles long context
- **Expected Result:** 
  - No browser freeze or crash
  - Clear feedback if message too long
- **Success Criteria:** 
  - Graceful handling of edge case
  - User informed of limits

**Minimum 7 E2E tests** covering all user stories and error scenarios.

### Test Data & Fixtures

**Mock API Responses:**
```python
# tests/fixtures/mock_responses.py
MOCK_CHAT_RESPONSE = {
    "candidates": [{
        "content": {
            "parts": [{"text": "Hello! I'm here to help."}]
        }
    }]
}

MOCK_ERROR_RESPONSE = {
    "error": {"message": "Rate limit exceeded"}
}
```

**Test Messages:**
```javascript
// tests/fixtures/test_messages.js
const validMessages = [
  "Hello",
  "What is AI?",
  "Can you help me with Python?"
];

const maliciousMessages = [
  "<script>alert('xss')</script>",
  "<img src=x onerror='alert()'>",
  "'; DROP TABLE users; --"
];
```

### Performance Tests
- **Response Time:** First token within 2 seconds
- **Streaming:** No visible lag between tokens
- **Load:** Handle 10 concurrent users (if multi-user added later)

### Security Tests
- **XSS Prevention:** All malicious messages in `maliciousMessages` sanitized
- **CORS:** Only allowed origins can access API
- **Input Validation:** Reject messages > 10,000 characters

---

## Acceptance Criteria

> **Feature is NOT complete until ALL criteria are met**

### Functional Criteria
- [ ] **AC-1:** User can type and send messages via UI (keyboard and button)
- [ ] **AC-2:** AI responses appear in the chat interface with streaming
- [ ] **AC-3:** Chat history is preserved during the session
- [ ] **AC-4:** Code blocks in responses have syntax highlighting
- [ ] **AC-5:** Responses stream token-by-token (visible progressive rendering)
- [ ] **AC-6:** User can clear chat history with a button
- [ ] **AC-7:** System errors are displayed in a distinct style with recovery option
- [ ] **AC-8:** Input is sanitized to prevent XSS attacks

### Testing Criteria (MANDATORY)
- [ ] **All 15+ unit tests implemented** (sanitization, formatting, streaming, errors)
- [ ] **All unit tests pass** (100% passing, 0 failures)
- [ ] **All 7+ integration tests implemented** (API endpoints, Gemini integration)
- [ ] **All integration tests pass** (100% passing, mocked external APIs)
- [ ] **All 7+ E2E tests implemented** (user flows, error handling, accessibility)
- [ ] **All E2E tests pass** (automated or manually verified)
- [ ] **Test coverage ≥85%** (verified with coverage report)
- [ ] **Edge cases tested** (empty input, long messages, special characters)
- [ ] **Error conditions tested** (network failures, API errors, invalid input)
- [ ] **Security tests pass** (XSS attempts blocked, CORS configured)

### Quality Criteria
- [ ] **Code review completed** (peer reviewed or AI reviewed)
- [ ] **No linter errors** (Python: flake8/black, JavaScript: ESLint)
- [ ] **No console errors** in browser (checked in dev tools)
- [ ] **Accessibility validated** (keyboard navigation works, ARIA labels)
- [ ] **Performance acceptable** (first token < 2s, no UI freezing)
- [ ] **Documentation updated** (README, API docs, inline comments)
- [ ] **CORS configured** (only allowed origins)

### Deployment Criteria
- [ ] **Dependencies documented** (requirements.txt, package.json if needed)
- [ ] **Environment variables documented** (GEMINI_API_KEY in .env.example)
- [ ] **Deployment instructions** (how to run Flask server, serve static files)
- [ ] **Health check endpoint** (optional: `/api/health` for monitoring)

---

## Implementation Notes

### Design Decisions
- **Decision:** Use EventSource for streaming instead of WebSockets
  - **Rationale:** Simpler implementation, unidirectional flow sufficient for this use case
  - **Trade-off:** WebSockets would allow server-initiated messages, but we don't need that

- **Decision:** Session-based storage (no database)
  - **Rationale:** Simplicity for MVP, most users only need single-session conversations
  - **Trade-off:** History lost on page refresh, but acceptable for this use case

### Known Limitations
- Chat history is lost on page refresh (no persistence)
- Single-user only (no authentication or user management)
- No conversation branching or editing of previous messages

### Future Enhancements
- Add localStorage to persist chat across page reloads
- Export chat history as Markdown
- Add voice input/output
- Support image attachments
- Multi-user support with authentication

---

## References

- Related specs: None (first chat implementation)
- Documentation: 
  - `docs/architecture.md` - Tech stack
  - `docs/backend.md` - API patterns
  - `docs/frontend.md` - UI/UX guidelines
- External docs: 
  - [Gemini API Streaming](https://ai.google.dev/gemini-api/docs/text-generation?lang=python#generate-a-text-stream)
  - [EventSource API](https://developer.mozilla.org/en-US/docs/Web/API/EventSource)
- Related code:
  - `gemini_agent.py` - Existing Gemini integration
  - `psychiatrist_api.py` - Flask API example
