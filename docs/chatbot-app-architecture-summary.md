# Chatbot Application - Architecture Summary

A quick visual reference for the chatbot architecture.

## System Overview

```
┌───────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                               │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    FRONTEND (HTML + JS)                      │  │
│  │                                                               │  │
│  │  Components:                                                  │  │
│  │  • Chat UI (index.html)                                      │  │
│  │  • WebSocket Client (websocket.js)                           │  │
│  │  • Message Renderer (renderer.js)                            │  │
│  │  • Chat Logic (chat.js)                                      │  │
│  │  • Styles (chat.css)                                         │  │
│  └─────────────────────────────────────────────────────────────┘  │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                         │ WebSocket: ws://localhost:8000/ws/chat
                         │ HTTP: http://localhost:8000/api/*
                         │
┌────────────────────────▼──────────────────────────────────────────┐
│                    PYTHON API SERVER                               │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                  FastAPI Application                         │  │
│  │                                                               │  │
│  │  api/app.py                   - Main application             │  │
│  │  api/websocket_handler.py     - WebSocket endpoint           │  │
│  │  api/session_manager.py       - Session & history            │  │
│  │  api/gemini_wrapper.py        - Gemini integration           │  │
│  │  api/response_formatter.py    - Response formatting          │  │
│  │  api/function_handler.py      - Function call display        │  │
│  │  api/config.py                - Configuration                │  │
│  └─────────────────────────────────────────────────────────────┘  │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                         │ Python imports & function calls
                         │
┌────────────────────────▼──────────────────────────────────────────┐
│                      gemini_agent.py                               │
│                                                                     │
│  • Gemini API client (google.genai)                               │
│  • 15 CLI tool function declarations                               │
│  • Function execution handlers                                     │
│  • System prompt builder                                           │
│  • Conversation history management                                 │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                         │ API calls & tool execution
                         │
┌────────────────────────▼──────────────────────────────────────────┐
│                    EXTERNAL SERVICES                               │
│                                                                     │
│  • Google Gemini API (AI responses)                               │
│  • ChromaDB (semantic search)                                      │
│  • File System (generated images/videos)                          │
└─────────────────────────────────────────────────────────────────────┘
```

## Communication Flow

### 1. User Sends Message

```
User types "Create an image of a futuristic car"
    ↓
Frontend (chat.js) captures input
    ↓
WebSocket client sends JSON:
{
  "type": "user_message",
  "session_id": "abc-123",
  "content": "Create an image of a futuristic car"
}
    ↓
Backend (websocket_handler.py) receives message
```

### 2. Backend Processing

```
websocket_handler.py
    ↓ retrieves session
session_manager.py
    ↓ gets conversation history
gemini_wrapper.py
    ↓ imports from gemini_agent.py
    ↓ calls Gemini API with tools
gemini_agent.py
    ↓ returns response with function_call
```

### 3. Function Execution

```
gemini_wrapper.py detects function call
    ↓
Sends notification to frontend:
{
  "type": "function_call",
  "function_name": "nano_banana_generate",
  "function_args": {"prompt": "futuristic car"}
}
    ↓
Frontend displays: "🔧 Generating image..."
    ↓
execute_cli_function("nano_banana_generate", {...})
    ↓
CLI tool runs: npm run nano-banana -- -p "futuristic car"
    ↓
Returns result: {"ok": true, "stdout": "File saved to: public/images/car-1234.png"}
```

### 4. AI Response with Result

```
gemini_wrapper.py adds function result to history
    ↓
Calls Gemini API again with result
    ↓
Gemini responds with natural language + file reference
    ↓
response_formatter.py formats response
    ↓
Sends to frontend:
{
  "type": "assistant_message",
  "content": "I've created the image for you!",
  "complete": true
}
{
  "type": "media",
  "media_type": "image",
  "url": "http://localhost:8000/public/images/car-1234.png"
}
    ↓
Frontend displays message + image
```

## File Structure

```
ai_training/
├── gemini_agent.py              # Core AI engine (existing)
│
├── api/                          # NEW: Backend API
│   ├── __init__.py
│   ├── app.py                    # FastAPI application
│   ├── config.py                 # Configuration
│   ├── websocket_handler.py      # WebSocket endpoint
│   ├── session_manager.py        # Session management
│   ├── gemini_wrapper.py         # Gemini integration
│   ├── response_formatter.py     # Response formatting
│   └── function_handler.py       # Function call handling
│
├── web/                          # NEW: Frontend
│   ├── index.html                # Main chat interface
│   └── static/
│       ├── css/
│       │   └── chat.css          # Styling
│       ├── js/
│       │   ├── main.js           # App initialization
│       │   ├── websocket.js      # WebSocket client
│       │   ├── chat.js           # Chat UI logic
│       │   └── renderer.js       # Message rendering
│       └── assets/
│           └── icons/            # UI icons
│
├── public/                       # Generated content (existing)
│   ├── images/                   # AI-generated images
│   └── videos/                   # AI-generated videos
│
└── docs/                         # Documentation
    ├── chatbot-app-design.md              # Full design doc
    ├── chatbot-app-quickstart.md          # Implementation guide
    └── chatbot-app-architecture-summary.md # This file
```

## Key Integration Points

### 1. Importing gemini_agent.py Functions

```python
# In api/gemini_wrapper.py
from gemini_agent import (
    build_cli_tools,              # Get all CLI tool definitions
    build_system_prompt,          # Get enhanced system prompt
    execute_cli_function,         # Execute function (html_to_md, etc.)
    find_function_call_parts,     # Parse function calls from response
    make_function_response_part,  # Create function response for API
    load_api_key                  # Load API key from .env
)
```

### 2. Building Conversation Context

```python
# Initialize with system prompt
history = [
    types.Content(role="user", parts=[types.Part(text=build_system_prompt())]),
    types.Content(role="model", parts=[types.Part(text="Ready!")]),
]

# Add user message
history.append(types.Content(role="user", parts=[types.Part(text=user_input)]))

# Call Gemini
response = await client.aio.models.generate_content(
    model="gemini-2.5-flash",
    contents=history,
    config=types.GenerateContentConfig(tools=build_cli_tools())
)
```

### 3. Function Call Loop

```python
for attempt in range(3):  # Max 3 function calls per turn
    calls = find_function_call_parts(response)
    if not calls:
        break  # No more function calls
    
    name, args = calls[0]
    
    # Notify frontend
    await websocket.send_json({
        "type": "function_call",
        "function_name": name,
        "function_args": args
    })
    
    # Execute function
    result = execute_cli_function(name, args)
    
    # Add to history
    history.append(types.Content(
        role="tool",
        parts=[make_function_response_part(name, result)]
    ))
    
    # Call Gemini again with result
    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=history,
        config=types.GenerateContentConfig(tools=build_cli_tools())
    )
```

## WebSocket Message Types

### Client → Server

| Type | Purpose | Example |
|------|---------|---------|
| `user_message` | User sends chat message | `{"type": "user_message", "content": "Hello"}` |
| `new_session` | Request new chat session | `{"type": "new_session"}` |
| `clear_history` | Clear current session | `{"type": "clear_history", "session_id": "..."}` |

### Server → Client

| Type | Purpose | Example |
|------|---------|---------|
| `assistant_message` | AI text response | `{"type": "assistant_message", "content": "Hi!"}` |
| `function_call` | Notify function execution | `{"type": "function_call", "function_name": "google_search"}` |
| `function_result` | Function execution result | `{"type": "function_result", "success": true}` |
| `media` | Generated image/video | `{"type": "media", "url": "/public/images/..."}` |
| `error` | Error message | `{"type": "error", "error": "Rate limit exceeded"}` |

## Available CLI Tools

The chatbot can use all 15 CLI tools from `gemini_agent.py`:

| Tool | Purpose | Example Use |
|------|---------|-------------|
| `html_to_md` | Scrape and convert webpage | "Extract content from example.com" |
| `image_optimizer` | Optimize/resize images | "Resize this image to 800x600" |
| `download_file` | Download from URL | "Download this PDF" |
| `openai_image_generate` | Generate image (OpenAI) | "Create image using DALL-E" |
| `openai_image_edit` | Edit image (OpenAI) | "Edit this image with DALL-E" |
| `gemini_image_generate` | Generate image (Gemini/Imagen) | "Generate image using Imagen" |
| `gemini_image_edit` | Edit image (Gemini) | "Edit this image using Gemini" |
| `generate_video` | Generate video | "Create a 5-second video" |
| `remove_background_advanced` | Remove image background | "Remove background from this image" |
| `nano_banana_generate` | Generate image (Gemini 2.5) | "Create an image of a car" |
| `nano_banana_edit` | Edit image (Gemini 2.5) | "Add flames to this car" |
| `google_search` | Search the web | "What's the weather in London?" |
| `datetime` | Get current date/time | "What time is it in Tokyo?" |
| `data_indexing` | Index content to ChromaDB | "Index this website for RAG" |
| `semantic_search` | Search indexed content | "Find information about Python" |

## Session Management

### Session Structure

```python
{
  "session_id": "abc-123",
  "history": [
    # List of types.Content objects
  ],
  "created_at": datetime,
  "last_activity": datetime,
  "metadata": {
    "user_agent": "...",
    "ip": "..."
  }
}
```

### Session Lifecycle

```
User connects → WebSocket opens → Session created/retrieved
    ↓
User sends message → Added to session history
    ↓
AI responds → Added to session history
    ↓
Session inactive 30min → Cleaned up
    ↓
User reconnects → New session created
```

## Security Layers

```
┌─────────────────────────────────────────────────┐
│ Frontend                                         │
│ • Input length validation (max 10,000 chars)   │
│ • XSS prevention (escape HTML)                  │
│ • Rate limiting UI (disable send button)        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ WebSocket Layer                                  │
│ • Message format validation                     │
│ • Reject malformed messages                     │
│ • Connection rate limiting                      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ Backend API                                      │
│ • Input sanitization                            │
│ • Session validation                            │
│ • API key never exposed to client               │
│ • Rate limiting per session (20/min)            │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ File System                                      │
│ • Validate file types                           │
│ • Restrict to specific directories              │
│ • Prevent path traversal                        │
│ • Auto-cleanup old files                        │
└─────────────────────────────────────────────────┘
```

## Deployment Options

### Option 1: Single Server (Simplest)
```
Cloud VM (e.g., AWS EC2)
├── Nginx (reverse proxy)
├── Python API (Uvicorn)
├── Static files (served by Nginx)
└── ChromaDB (local)
```

### Option 2: Docker Container
```
Docker Container
├── Python 3.10 base
├── FastAPI + dependencies
├── Static files
└── Exposed port 8000
```

### Option 3: Serverless (Future)
```
AWS Lambda / Google Cloud Functions
├── API Gateway (WebSocket support)
├── Lambda functions (Python)
├── S3/Cloud Storage (static files)
└── Redis (session storage)
```

---

## Quick Start Commands

```bash
# 1. Start ChromaDB
chroma run --path ./chroma

# 2. Set environment variables
export GOOGLE_AI_STUDIO_KEY=your_key_here

# 3. Start API server
cd api
python app.py

# 4. Open browser
open http://localhost:8000
```

---

**For detailed specifications, see `chatbot-app-design.md`**  
**For implementation guide, see `chatbot-app-quickstart.md`**

