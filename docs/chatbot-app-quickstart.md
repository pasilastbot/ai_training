# Chatbot Application - Implementation Quick Start

**Reference:** See `chatbot-app-design.md` for complete design documentation.

## Implementation Order

### Phase 1: Backend Foundation (Days 1-2)
1. **Setup project structure**
   ```bash
   mkdir -p api/{__init__.py,app.py,config.py}
   mkdir -p api/{websocket_handler.py,session_manager.py}
   mkdir -p api/{gemini_wrapper.py,response_formatter.py,function_handler.py}
   ```

2. **Install dependencies**
   ```bash
   pip install fastapi uvicorn websockets python-dotenv
   ```

3. **Implement core components** (in order):
   - `config.py` - Configuration and environment variables
   - `session_manager.py` - Session storage and management
   - `gemini_wrapper.py` - Integration with gemini_agent.py
   - `response_formatter.py` - Format responses for frontend
   - `function_handler.py` - Handle function call display
   - `websocket_handler.py` - WebSocket endpoint logic
   - `app.py` - Main FastAPI application

### Phase 2: Frontend Foundation (Days 3-4)
1. **Create file structure**
   ```bash
   mkdir -p web/static/{css,js,assets/icons}
   touch web/index.html
   touch web/static/css/chat.css
   touch web/static/js/{main.js,websocket.js,chat.js,renderer.js}
   ```

2. **Implement components** (in order):
   - `index.html` - Main HTML structure
   - `websocket.js` - WebSocket client
   - `chat.js` - Chat UI logic
   - `renderer.js` - Message rendering
   - `main.js` - Application initialization
   - `chat.css` - Styling

### Phase 3: Integration & Testing (Day 5)
1. **Test basic chat flow**
   - Send/receive messages
   - Display conversation history
   - Handle errors

2. **Test function calling**
   - Test image generation (nano_banana_generate)
   - Test search (google_search)
   - Test datetime tool
   - Verify function call display

3. **Test rich content**
   - Image display
   - Code block rendering
   - Markdown formatting

### Phase 4: Polish & Deploy (Day 6)
1. **UI/UX improvements**
   - Loading states
   - Error messages
   - Responsive design

2. **Performance optimization**
   - Response streaming
   - Session cleanup
   - File management

3. **Documentation & deployment**
   - Update README
   - Deployment guide
   - Environment setup

---

## Key Implementation Notes

### Backend: gemini_wrapper.py Integration

**DO:**
```python
# Import functions directly from gemini_agent.py
from gemini_agent import (
    build_cli_tools,
    build_system_prompt,
    execute_cli_function,
    find_function_call_parts,
    make_function_response_part,
    load_api_key
)

# Initialize once
api_key = load_api_key()
client = genai.Client(api_key=api_key)
tools = build_cli_tools()
system_prompt = build_system_prompt()
```

**DON'T:**
```python
# Don't call as subprocess
subprocess.run(["python", "gemini_agent.py", ...])  # WRONG
```

### Frontend: WebSocket Message Handling

**Key Pattern:**
```javascript
// Send message
ws.send(JSON.stringify({
  type: 'user_message',
  session_id: sessionId,
  content: userInput
}));

// Receive and route messages
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  switch(msg.type) {
    case 'assistant_message':
      renderAssistantMessage(msg);
      break;
    case 'function_call':
      showFunctionExecution(msg);
      break;
    case 'media':
      displayMedia(msg);
      break;
  }
};
```

### Session Management Pattern

```python
# In-memory session store (upgrade to Redis later)
sessions = {}

def get_or_create_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = {
            'history': [
                types.Content(role="user", parts=[types.Part(text=system_prompt)]),
                types.Content(role="model", parts=[types.Part(text="Ready!")])
            ],
            'created_at': datetime.now(),
            'last_activity': datetime.now()
        }
    return sessions[session_id]
```

---

## File Templates

### api/app.py (Minimal Starter)

```python
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")
app.mount("/public", StaticFiles(directory="public"), name="public")

@app.get("/")
async def root():
    with open("web/index.html") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # TODO: Implement chat logic
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### web/static/js/websocket.js (Minimal Starter)

```javascript
class ChatWebSocket {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.handlers = {};
  }

  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('Connected');
      if (this.handlers.onopen) this.handlers.onopen();
    };
    
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (this.handlers.onmessage) this.handlers.onmessage(msg);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (this.handlers.onerror) this.handlers.onerror(error);
    };
    
    this.ws.onclose = () => {
      console.log('Disconnected');
      if (this.handlers.onclose) this.handlers.onclose();
    };
  }

  send(message) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  on(event, handler) {
    this.handlers[event] = handler;
  }
}

export default ChatWebSocket;
```

---

## Testing Checklist

### Backend Tests
- [ ] WebSocket connection established
- [ ] Message sent from client received by server
- [ ] Response sent from server received by client
- [ ] Session created and retrieved correctly
- [ ] Function call detected and executed
- [ ] Function result formatted correctly
- [ ] Multiple function calls handled in sequence
- [ ] Error handling works (invalid message, API error, etc.)
- [ ] Session timeout works

### Frontend Tests
- [ ] UI loads correctly
- [ ] Input field accepts text
- [ ] Send button triggers message send
- [ ] Enter key sends message
- [ ] Message appears in chat after sending
- [ ] Response received and displayed
- [ ] Function call notification displayed
- [ ] Generated images displayed with correct path
- [ ] Code blocks formatted with syntax highlighting
- [ ] Markdown rendered correctly
- [ ] Auto-scroll to latest message works
- [ ] Typing indicator shows during processing
- [ ] Error messages displayed clearly
- [ ] Reconnection works after disconnect

### Integration Tests
- [ ] End-to-end: User message → Gemini response → Display
- [ ] Image generation: Prompt → Generate → Display image
- [ ] Search: Query → google_search → Results displayed
- [ ] Multi-step: Search → Generate image based on results
- [ ] Session persistence across messages
- [ ] Function call loop works (multiple tools in sequence)

---

## Common Pitfalls to Avoid

1. **Don't parse response.text for function calls**
   - Use `find_function_call_parts()` from gemini_agent.py
   - Function calls are in `response.candidates[0].content.parts`

2. **Don't forget system prompt in history**
   - Always start history with system prompt
   - Include model acknowledgment response

3. **Don't call Gemini API directly**
   - Use the imported functions from gemini_agent.py
   - They handle tool configuration correctly

4. **Don't ignore WebSocket close events**
   - Implement reconnection logic
   - Handle network interruptions gracefully

5. **Don't store API keys in frontend**
   - All API calls must go through backend
   - Never expose GOOGLE_AI_STUDIO_KEY to client

6. **Don't forget to sanitize user input**
   - Escape HTML in messages
   - Validate message length
   - Rate limit requests

7. **Don't block on long operations**
   - Use async/await throughout
   - Stream responses when possible

---

## Environment Variables

Create `.env.local` with:

```bash
# Required
GOOGLE_AI_STUDIO_KEY=your_key_here

# Optional (for additional features)
OPENAI_API_KEY=your_key
REPLICATE_API_TOKEN=your_token

# Configuration
API_PORT=8000
SESSION_TIMEOUT=1800
MAX_MESSAGE_LENGTH=10000
RATE_LIMIT=20
```

---

## Running the Application

```bash
# Terminal 1: Start ChromaDB (if using semantic search)
chroma run --path ./chroma

# Terminal 2: Start API server
cd api
python app.py

# Browser: Open http://localhost:8000
```

---

## Next Steps After Implementation

1. **Add authentication**
   - User login/signup
   - Session tied to user ID
   - Personal conversation history

2. **Improve session storage**
   - Move from in-memory to Redis
   - Persist conversations to database
   - Support conversation search

3. **Add features**
   - Voice input (Web Speech API)
   - Export conversations
   - Share conversations
   - Multi-language support

4. **Optimize performance**
   - Response caching
   - Load balancing
   - CDN for static assets
   - Database connection pooling

---

**Ready to implement?** Start with Phase 1, Backend Foundation. See `chatbot-app-design.md` for detailed specifications of each component.

