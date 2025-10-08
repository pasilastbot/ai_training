# Gemini Chatbot Application

A real-time web-based chatbot powered by Google Gemini API with full integration of all CLI tools from `gemini_agent.py`.

## Features

- 💬 **Real-time Chat**: WebSocket-based instant messaging
- 🔧 **Function Calling**: Seamlessly executes 15+ CLI tools
- 🔍 **Web Search**: Google Search with grounding
- 🎨 **Image Generation**: Multiple models (Gemini, OpenAI, etc.)
- 🎬 **Video Generation**: Create videos from prompts
- 📊 **Semantic Search**: Query indexed content from ChromaDB
- 🌐 **Web Scraping**: Convert HTML to Markdown
- ⏰ **Utilities**: Date/time, file downloads, and more

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Node.js 18+ (for CLI tools)
- Gemini API key

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for CLI tools)
npm install
```

### 3. Set API Key

```bash
# macOS/Linux
export GOOGLE_AI_STUDIO_KEY=your_api_key_here

# Windows
set GOOGLE_AI_STUDIO_KEY=your_api_key_here

# PowerShell
$env:GOOGLE_AI_STUDIO_KEY="your_api_key_here"
```

### 4. Run the Application

**Option A: Use the startup script**
```bash
./start_chatbot.sh
```

**Option B: Run directly**
```bash
python3 api/app.py
```

### 5. Open in Browser

Navigate to: **http://localhost:8000**

## Architecture

### Backend (FastAPI + Python)

```
api/
├── app.py                  # Main FastAPI application
├── config.py               # Configuration settings
├── session_manager.py      # Chat session management
├── gemini_wrapper.py       # Gemini agent integration
├── websocket_handler.py    # WebSocket message handling
├── response_formatter.py   # Response formatting (future)
└── function_handler.py     # Function call handling (future)
```

**Key Components:**
- **FastAPI**: Web server with WebSocket support
- **Session Manager**: Maintains conversation history per session
- **Gemini Wrapper**: Integrates `gemini_agent.py` with async support
- **WebSocket Handler**: Routes messages between client and agent

### Frontend (Vanilla JavaScript)

```
web/
├── index.html              # Main chat interface
└── static/
    ├── css/
    │   └── chat.css        # Responsive chat styling
    └── js/
        ├── main.js         # App initialization
        ├── websocket.js    # WebSocket client
        ├── chat.js         # Chat UI logic
        └── renderer.js     # Message rendering
```

**Features:**
- Responsive design (mobile-friendly)
- Real-time message streaming
- Function call visualization
- Auto-scrolling chat
- Connection status indicator

## Usage Examples

### Basic Chat
```
You: What's the weather in Tokyo?
AI: [Executes google_search function]
AI: The current weather in Tokyo is...
```

### Image Generation
```
You: Generate an image of a futuristic city
AI: [Executes nano_banana_generate function]
AI: Here's the generated image: public/images/city-123.png
```

### Semantic Search
```
You: Search my indexed documents for "machine learning"
AI: [Executes semantic_search function]
AI: Found 5 relevant results...
```

## Configuration

Edit `api/config.py` or set environment variables:

```bash
# Server settings
API_HOST=0.0.0.0
API_PORT=8000

# Session settings
SESSION_TIMEOUT=1800          # 30 minutes
MAX_MESSAGE_LENGTH=10000

# Gemini settings
GEMINI_MODEL=gemini-2.5-flash

# ChromaDB settings (for semantic search)
CHROMA_HOST=localhost
CHROMA_PORT=8000
```

## API Endpoints

### WebSocket
- `WS /ws/chat` - Real-time chat communication

### HTTP REST
- `GET /` - Serve chat interface
- `GET /api/health` - Health check
- `POST /api/sessions/new` - Create new session
- `GET /api/sessions/{id}/history` - Get conversation history
- `DELETE /api/sessions/{id}` - Delete session

## Message Protocol

### Client → Server

**New Session:**
```json
{
  "type": "new_session",
  "timestamp": 1633024800000
}
```

**User Message:**
```json
{
  "type": "user_message",
  "session_id": "uuid",
  "content": "Your message here",
  "timestamp": 1633024800000
}
```

**Clear History:**
```json
{
  "type": "clear_history",
  "session_id": "uuid"
}
```

### Server → Client

**Session Created:**
```json
{
  "type": "session_created",
  "session_id": "uuid",
  "timestamp": 1633024800000
}
```

**Assistant Message:**
```json
{
  "type": "assistant_message",
  "session_id": "uuid",
  "content": "AI response text",
  "complete": false,
  "timestamp": 1633024805000
}
```

**Function Call:**
```json
{
  "type": "function_call",
  "session_id": "uuid",
  "function_name": "google_search",
  "function_args": {"query": "weather"},
  "status": "executing",
  "timestamp": 1633024802000
}
```

**Function Result:**
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

## Available Tools

The chatbot has access to all tools defined in `gemini_agent.py`:

1. **html_to_md** - Scrape and convert HTML to Markdown
2. **google_search** - Web search with grounding
3. **nano_banana_generate** - Image generation (Gemini 2.5 Flash)
4. **nano_banana_edit** - Image editing
5. **gemini_image_generate** - Image generation (Gemini/Imagen)
6. **gemini_image_edit** - Image editing (Gemini)
7. **openai_image_generate** - Image generation (OpenAI)
8. **openai_image_edit** - Image editing (OpenAI)
9. **generate_video** - Video generation (Replicate models)
10. **datetime** - Get current date/time
11. **data_indexing** - Index content to ChromaDB
12. **semantic_search** - Search ChromaDB collections
13. **download_file** - Download files from URLs
14. **image_optimizer** - Optimize and edit images
15. **remove_background_advanced** - Advanced background removal

## Troubleshooting

### Connection Error
- Ensure the server is running on port 8000
- Check firewall settings
- Verify WebSocket support in browser

### API Key Error
- Verify `GOOGLE_AI_STUDIO_KEY` or `GOOGLE_API_KEY` is set
- Check key is valid in Google AI Studio

### Function Execution Fails
- Ensure npm dependencies are installed (`npm install`)
- Check specific tool requirements (e.g., ChromaDB for semantic search)
- Review function output in browser console

### ChromaDB Not Found
If using semantic search or data indexing:
```bash
# Terminal 1: Start ChromaDB
chroma run --path ./chroma

# Terminal 2: Start chatbot
./start_chatbot.sh
```

## Development

### Running in Development Mode
```bash
# Enable debug mode
export DEBUG=true

# Server will auto-reload on code changes
python3 api/app.py
```

### Adding New Functions
1. Add function declaration to `gemini_agent.py`
2. Implement execution in `execute_cli_function()`
3. Function will automatically be available in chatbot

## Production Deployment

### Using Uvicorn
```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN npm install

EXPOSE 8000

CMD ["python3", "api/app.py"]
```

## License

See main repository LICENSE file.

## Support

For issues or questions, refer to:
- Main README.md
- docs/chatbot-app-design.md (comprehensive design document)
- CLAUDE.md (development guide)
