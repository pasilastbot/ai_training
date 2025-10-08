# Chatbot Application Design Document

**Version:** 1.0  
**Date:** October 8, 2025  
**Status:** Design Phase

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Frontend Design](#frontend-design)
4. [Backend API Design](#backend-api-design)
5. [Integration with gemini_agent.py](#integration-with-gemini_agentpy)
6. [Data Flow](#data-flow)
7. [API Endpoints](#api-endpoints)
8. [UI/UX Design](#uiux-design)
9. [Security Considerations](#security-considerations)
10. [Deployment](#deployment)

---

## Overview

### Purpose
A web-based chatbot application that provides an interactive interface for users to interact with Gemini AI, leveraging all the CLI tools available in `gemini_agent.py`.

### Key Features
- **Interactive Chat Interface**: Real-time messaging UI for conversing with the AI
- **Function Calling Support**: Seamless integration with all 15 CLI tools (image generation, web scraping, semantic search, etc.)
- **Session Management**: Maintain conversation history and context
- **Rich Media Support**: Display generated images, formatted text, and search results
- **Streaming Responses**: Real-time response streaming for better UX

### Technology Stack
- **Frontend**: HTML5, Vanilla JavaScript (ES6+), CSS3
- **Backend**: Python 3.10+, Flask/FastAPI
- **AI Engine**: Google Gemini API (via `gemini_agent.py`)
- **Communication**: WebSocket for real-time chat, REST API for session management

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (Client)                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │         HTML + CSS + JavaScript                  │   │
│  │  - Chat UI                                       │   │
│  │  - Message rendering                             │   │
│  │  - WebSocket client                              │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │ WebSocket / HTTP
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Python API Server                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Flask/FastAPI Application                │   │
│  │  - WebSocket handler                             │   │
│  │  - Session manager                               │   │
│  │  - Response formatter                            │   │
│  └────────────────────┬────────────────────────────┘   │
│                       │                                  │
│  ┌────────────────────▼────────────────────────────┐   │
│  │          Gemini Agent Integration                │   │
│  │  - gemini_agent.py wrapper                       │   │
│  │  - Function call handler                         │   │
│  │  - Stream processor                              │   │
│  └────────────────────┬────────────────────────────┘   │
└────────────────────────┼────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   gemini_agent.py                        │
│  - Gemini API client                                     │
│  - 15 CLI tool functions                                 │
│  - System prompt & planning                              │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              External Services                           │
│  - Google Gemini API                                     │
│  - ChromaDB (for semantic search)                        │
│  - File system (for generated images/files)              │
└──────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### 1. Frontend Components
- **ChatContainer**: Main chat interface container
- **MessageList**: Displays conversation history
- **MessageInput**: User input field with send button
- **MessageBubble**: Individual message display (user/assistant)
- **MediaViewer**: Display images, files, and rich content
- **TypingIndicator**: Shows when AI is processing
- **FunctionCallDisplay**: Shows when AI is executing functions

#### 2. Backend Components
- **WebSocketServer**: Handles real-time bidirectional communication
- **SessionManager**: Manages chat sessions and history
- **GeminiAgentWrapper**: Python interface to gemini_agent.py
- **ResponseFormatter**: Formats AI responses for frontend consumption
- **FunctionCallHandler**: Processes and displays function execution
- **FileServer**: Serves generated images and files

---

## Frontend Design

### File Structure
```
web/
├── index.html              # Main chat interface
├── static/
│   ├── css/
│   │   └── chat.css        # Styling for chat interface
│   ├── js/
│   │   ├── main.js         # Application entry point
│   │   ├── websocket.js    # WebSocket client
│   │   ├── chat.js         # Chat UI logic
│   │   └── renderer.js     # Message rendering
│   └── assets/
│       ├── icons/          # UI icons
│       └── images/         # Static images
└── generated/              # AI-generated content
```

### HTML Structure (index.html)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gemini Chatbot</title>
    <link rel="stylesheet" href="/static/css/chat.css">
</head>
<body>
    <div class="chat-container">
        <!-- Header -->
        <div class="chat-header">
            <h1>Gemini AI Assistant</h1>
            <div class="status-indicator" id="status"></div>
        </div>

        <!-- Message List -->
        <div class="message-list" id="messageList">
            <!-- Messages will be dynamically inserted here -->
        </div>

        <!-- Typing Indicator -->
        <div class="typing-indicator" id="typingIndicator" style="display: none;">
            <span></span><span></span><span></span>
        </div>

        <!-- Input Area -->
        <div class="input-area">
            <textarea 
                id="messageInput" 
                placeholder="Type your message..."
                rows="1"
            ></textarea>
            <button id="sendButton">Send</button>
        </div>
    </div>

    <script type="module" src="/static/js/main.js"></script>
</body>
</html>
```

### CSS Design Principles

- **Modern, Clean Interface**: Minimalist design inspired by popular chat apps
- **Responsive Layout**: Mobile-first approach, works on all screen sizes
- **Dark/Light Theme**: Support for user preference
- **Smooth Animations**: Subtle transitions for message appearance
- **Accessibility**: ARIA labels, keyboard navigation, high contrast

### JavaScript Architecture

#### main.js
```javascript
// Application initialization and coordination
- Initialize WebSocket connection
- Set up event listeners
- Handle application state
- Coordinate between modules
```

#### websocket.js
```javascript
// WebSocket client management
- Connect to server
- Handle connection states (connecting, open, closed, error)
- Send messages
- Receive and parse server messages
- Automatic reconnection logic
```

#### chat.js
```javascript
// Chat UI logic
- Add messages to UI
- Handle user input
- Scroll management
- Message timestamps
- Session management
```

#### renderer.js
```javascript
// Message rendering
- Render text messages
- Render function calls (show tool usage)
- Render images and media
- Render code blocks with syntax highlighting
- Parse and format markdown
```

---

## Backend API Design

### File Structure
```
api/
├── app.py                      # Main Flask/FastAPI application
├── websocket_handler.py        # WebSocket endpoint handler
├── session_manager.py          # Chat session management
├── gemini_wrapper.py           # Wrapper for gemini_agent.py
├── response_formatter.py       # Format responses for frontend
├── function_handler.py         # Handle function execution display
└── config.py                   # Configuration settings
```

### Technology Choice: FastAPI

**Rationale:**
- Native WebSocket support
- Async/await for concurrent handling
- Automatic API documentation
- Type hints and validation
- Easy to test and maintain

### Core Components

#### 1. app.py - Main Application
```python
Purpose: Application entry point, route registration, CORS setup
Key responsibilities:
- Initialize FastAPI app
- Configure CORS for frontend
- Register WebSocket and HTTP endpoints
- Set up static file serving
- Initialize session manager
- Load environment variables
```

#### 2. websocket_handler.py - WebSocket Logic
```python
Purpose: Handle real-time chat communication
Key responsibilities:
- Accept WebSocket connections
- Receive user messages
- Stream AI responses back to client
- Handle function call notifications
- Manage connection lifecycle
- Error handling and reconnection
```

#### 3. session_manager.py - Session Management
```python
Purpose: Manage chat sessions and conversation history
Key responsibilities:
- Create new sessions
- Store conversation history (in-memory or Redis)
- Retrieve session context
- Clear old sessions
- Session timeout handling
- Multi-user support
```

#### 4. gemini_wrapper.py - Gemini Agent Integration
```python
Purpose: Python interface to gemini_agent.py
Key responsibilities:
- Initialize gemini_agent components
- Build conversation history
- Call Gemini API via agent
- Handle function calls from agent
- Parse and format responses
- Extract media file paths
```

#### 5. response_formatter.py - Response Formatting
```python
Purpose: Format AI responses for frontend consumption
Key responsibilities:
- Convert responses to JSON format
- Extract text, images, function calls
- Format code blocks
- Handle grounding sources
- Create structured message objects
```

#### 6. function_handler.py - Function Call Display
```python
Purpose: Handle and display function executions
Key responsibilities:
- Detect function calls in response
- Format function call information
- Extract results (success/failure, output)
- Create display-friendly function call messages
- Handle file paths from generation tools
```

---

## Integration with gemini_agent.py

### Integration Strategy

Instead of calling `gemini_agent.py` as a subprocess, we'll import and use its internal functions directly as a Python library.

### Key Integration Points

#### 1. Import Core Functions
```python
from gemini_agent import (
    build_cli_function_declarations,
    build_cli_tools_wrapper,
    build_system_prompt,
    execute_cli_function,
    find_function_call_parts,
    make_function_response_part,
    load_api_key
)
```

#### 2. Initialize Gemini Client
```python
- Load API key using load_api_key()
- Create genai.Client instance
- Build tools using build_cli_tools_wrapper()
- Get system prompt using build_system_prompt()
```

#### 3. Maintain Conversation History
```python
- Store history as List[types.Content]
- Include system prompt at start
- Append user messages
- Append assistant responses
- Handle function calls and responses
```

#### 4. Function Call Loop
```python
For each user message:
1. Add to conversation history
2. Call Gemini API with history + tools
3. Check for function calls in response
4. If function calls exist:
   a. Execute via execute_cli_function()
   b. Notify frontend of function execution
   c. Add function response to history
   d. Call Gemini again with updated history
   e. Repeat until no more function calls
5. Return final response to frontend
```

### Session Context Management

```python
SessionContext:
- session_id: Unique identifier
- history: List[types.Content]
- created_at: Timestamp
- last_activity: Timestamp
- metadata: Dict (user info, preferences, etc.)
```

---

## Data Flow

### User Message Flow

```
User types message
    ↓
Frontend captures input
    ↓
WebSocket sends message to backend
    ↓
Backend receives message
    ↓
Session manager retrieves/creates session
    ↓
Add user message to history
    ↓
Call Gemini API with history + tools
    ↓
Check for function calls
    ↓
[If function calls exist]
    ↓
    Execute function via CLI wrapper
    ↓
    Notify frontend: "Executing [function_name]..."
    ↓
    Add function result to history
    ↓
    Call Gemini API again
    ↓
    [Loop until no more function calls]
    ↓
Format final response
    ↓
Stream response chunks to frontend
    ↓
Frontend renders message
    ↓
Display complete
```

### WebSocket Message Types

#### Client → Server Messages
```json
{
  "type": "user_message",
  "session_id": "uuid",
  "content": "What's the weather in London?",
  "timestamp": 1633024800000
}

{
  "type": "new_session",
  "timestamp": 1633024800000
}

{
  "type": "clear_history",
  "session_id": "uuid"
}
```

#### Server → Client Messages

**Text Response:**
```json
{
  "type": "assistant_message",
  "session_id": "uuid",
  "content": "The weather in London is...",
  "timestamp": 1633024805000,
  "complete": true
}
```

**Function Call Notification:**
```json
{
  "type": "function_call",
  "session_id": "uuid",
  "function_name": "google_search",
  "function_args": {"query": "weather London"},
  "status": "executing",
  "timestamp": 1633024802000
}
```

**Function Call Result:**
```json
{
  "type": "function_result",
  "session_id": "uuid",
  "function_name": "google_search",
  "success": true,
  "output": "...",
  "timestamp": 1633024803000
}
```

**Image Generated:**
```json
{
  "type": "media",
  "session_id": "uuid",
  "media_type": "image",
  "path": "/public/images/generated-1234.png",
  "url": "http://localhost:8000/public/images/generated-1234.png",
  "caption": "Generated image based on prompt",
  "timestamp": 1633024810000
}
```

**Streaming Chunk:**
```json
{
  "type": "assistant_message_chunk",
  "session_id": "uuid",
  "content": "The ",
  "chunk_index": 0,
  "complete": false,
  "timestamp": 1633024805000
}
```

**Error:**
```json
{
  "type": "error",
  "session_id": "uuid",
  "error": "API rate limit exceeded",
  "code": "rate_limit",
  "timestamp": 1633024800000
}
```

---

## API Endpoints

### WebSocket Endpoints

#### `WS /ws/chat`
**Purpose:** Real-time chat communication

**Connection:**
- Client connects to WebSocket
- Server assigns/retrieves session
- Bidirectional message exchange

### HTTP REST Endpoints

#### `GET /api/health`
**Purpose:** Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "gemini_agent_available": true
}
```

#### `POST /api/sessions/new`
**Purpose:** Create a new chat session

**Response:**
```json
{
  "session_id": "uuid",
  "created_at": 1633024800000
}
```

#### `GET /api/sessions/{session_id}/history`
**Purpose:** Retrieve conversation history

**Response:**
```json
{
  "session_id": "uuid",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": 1633024800000
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": 1633024805000
    }
  ]
}
```

#### `DELETE /api/sessions/{session_id}`
**Purpose:** Delete a session and its history

**Response:**
```json
{
  "success": true,
  "session_id": "uuid"
}
```

#### `GET /public/images/{filename}`
**Purpose:** Serve generated images

**Response:** Image file (PNG, JPEG, WebP)

#### `GET /public/videos/{filename}`
**Purpose:** Serve generated videos

**Response:** Video file (MP4, WebM)

---

## UI/UX Design

### Visual Design

#### Color Scheme
- **Primary:** #4285F4 (Google Blue)
- **Secondary:** #34A853 (Success Green)
- **Background Light:** #FFFFFF
- **Background Dark:** #1E1E1E
- **Text Primary:** #202124
- **Text Secondary:** #5F6368
- **Border:** #DADCE0
- **Error:** #EA4335

#### Typography
- **Headers:** Inter, 600 weight
- **Body:** Inter, 400 weight
- **Code:** Fira Code, monospace

### Message Display Patterns

#### User Message
```
┌─────────────────────────────────────────────┐
│                         [User Avatar] User: │
│                What's the weather in London? │
│                          [timestamp: 2:30pm] │
└─────────────────────────────────────────────┘
```

#### Assistant Message
```
┌─────────────────────────────────────────────┐
│ [AI Avatar] Assistant:                      │
│ Let me check the weather for you.           │
│                                              │
│ 🔧 Executing: google_search                 │
│    ↳ Query: "weather London current"        │
│                                              │
│ The current weather in London is...         │
│ [timestamp: 2:30pm]                         │
└─────────────────────────────────────────────┘
```

#### Image Generation Display
```
┌─────────────────────────────────────────────┐
│ [AI Avatar] Assistant:                      │
│ I've generated the image for you:           │
│                                              │
│ 🎨 Generated Image                          │
│ ┌──────────────────────────────────┐       │
│ │                                   │       │
│ │     [Generated Image Preview]     │       │
│ │                                   │       │
│ └──────────────────────────────────┘       │
│ 📁 File: public/images/car-1234.png        │
│ [Download] [View Fullsize]                  │
│ [timestamp: 2:31pm]                         │
└─────────────────────────────────────────────┘
```

### Interaction Patterns

#### Auto-expanding Textarea
- Single-line by default
- Expands as user types
- Max 5 lines before scrolling
- Shift+Enter for new line, Enter to send

#### Loading States
- Typing indicator (3 animated dots)
- Function execution badge (spinner + function name)
- Progress bar for long operations

#### Error Handling
- Inline error messages in chat
- Retry button for failed messages
- Connection status indicator in header

#### Rich Content Support
- Markdown rendering (bold, italic, lists, etc.)
- Syntax highlighted code blocks
- Clickable links
- Embedded images
- Collapsible sections for long outputs

---

## Security Considerations

### Input Validation
- Sanitize user input on backend
- Prevent XSS attacks via message escaping
- Rate limiting per session
- Maximum message length enforcement

### API Key Management
- Never expose API keys to frontend
- Store keys in environment variables
- Use `.env.local` for development
- Secure key rotation procedures

### Session Security
- Secure session ID generation (UUID v4)
- Session timeout (30 minutes inactive)
- No authentication required (public demo)
- Optional: Add user authentication later

### File Security
- Validate file types for generated content
- Restrict file serving to specific directories
- Prevent path traversal attacks
- Auto-cleanup old generated files

### WebSocket Security
- Validate message format
- Reject malformed messages
- Rate limit messages per connection
- Auto-disconnect on suspicious activity

---

## Deployment

### Development Environment

**Requirements:**
- Python 3.10+
- Node.js 18+ (for npm scripts)
- ChromaDB running (for semantic search)
- Environment variables configured

**Run:**
```bash
# Terminal 1: Start ChromaDB (if using semantic search)
chroma run --path ./chroma

# Terminal 2: Start Python API server
cd api
python app.py

# Browser: Open http://localhost:8000
```

### Production Deployment

#### Option 1: Single Server
- Deploy on cloud VM (AWS EC2, Google Compute, etc.)
- Use Nginx as reverse proxy
- Run API with Gunicorn/Uvicorn
- Systemd service for auto-restart

#### Option 2: Container (Docker)
```dockerfile
Dockerfile:
- Python 3.10 base image
- Install dependencies
- Copy application files
- Expose port 8000
- Run with uvicorn
```

#### Option 3: Serverless
- Deploy API to AWS Lambda / Google Cloud Functions
- Use API Gateway for WebSocket support
- Store sessions in Redis/DynamoDB
- Serve static files from CDN

### Environment Variables

```bash
# Required
GOOGLE_AI_STUDIO_KEY=your_api_key_here

# Optional
OPENAI_API_KEY=your_openai_key  # For OpenAI image generation
REPLICATE_API_TOKEN=your_token  # For Replicate video/image models

# Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000
API_PORT=8000
SESSION_TIMEOUT=1800  # 30 minutes in seconds
MAX_MESSAGE_LENGTH=10000
RATE_LIMIT=20  # messages per minute
```

### Monitoring & Logging

**Logging:**
- Request/response logging
- Error tracking
- Function call monitoring
- Performance metrics

**Monitoring:**
- API uptime
- Response times
- Error rates
- WebSocket connection count
- Session count

---

## Future Enhancements

### Phase 2 Features
- User authentication and profiles
- Multiple chat sessions per user
- Conversation search
- Export chat history
- Voice input/output
- Mobile app (React Native)

### Advanced Features
- Multi-language support
- Custom tool creation UI
- Conversation branching
- Share conversations
- Collaborative chats
- Plugin system for custom tools

### Performance Optimizations
- Response caching
- Redis for session storage
- CDN for generated media
- Horizontal scaling
- Load balancing

---

## Appendix

### Glossary
- **Session**: A conversation context with history
- **Function Call**: AI executing a CLI tool
- **Streaming**: Sending response in chunks
- **Grounding**: Search-backed responses

### References
- Gemini API Documentation: https://ai.google.dev/
- FastAPI Documentation: https://fastapi.tiangolo.com/
- WebSocket Protocol: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket

### Change Log
- **2025-10-08**: Initial design document created

---

**Document Status:** ✅ Complete - Ready for Implementation

