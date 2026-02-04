# Backend Documentation

## Overview

The backend consists of Python scripts that serve as AI agents, RAG pipeline components, and a demo Flask API. All backend code is in Python 3.9+ and uses async patterns where appropriate.

---

## API Endpoints

### Dr. Sigmund 2000 API (`psychiatrist_api.py`)

**Base URL:** `http://localhost:5001`

#### GET /
Serves the main HTML page for the psychiatrist game.

**Response:** HTML (`public/psychiatrist/index.html`)

---

#### POST /api/chat
Send a message to the AI psychiatrist and receive a response.

**Request Body:**
```json
{
  "message": "User's message text",
  "history": [
    {"role": "user", "content": "Previous user message"},
    {"role": "assistant", "content": "Previous bot response"}
  ],
  "persona_id": "dr-sigmund-2000",
  "consult": true
}
```

**Response (Success - 200):**
```json
{
  "response": "Dr. Sigmund's therapeutic response...",
  "mood": "thinking",
  "ascii_art": "…",
  "consult": {
    "enabled": true,
    "consulted_persona_id": "dr-ada-sterling",
    "consulted_persona_name": "Dr. Ada Sterling",
    "transcript": [
      { "from_persona_name": "Dr. Rex Hardcastle", "to_persona_name": "Dr. Ada Sterling", "text": "…" },
      { "from_persona_name": "Dr. Ada Sterling", "to_persona_name": "Dr. Rex Hardcastle", "text": "…" }
    ]
  }
}
```

**Response (Error - 400/500):**
```json
{
  "error": "Error description",
  "response": "Fallback error message in character",
  "mood": "concerned",
  "ascii_art": "..."
}
```

**Mood Values:** `thinking`, `amused`, `concerned`, `shocked`, `neutral`

---

#### POST /api/reset
Reset the conversation and start a new session.

**Request Body:** Empty

**Response (200):**
```json
{
  "response": "Session reset message...",
  "mood": "neutral",
  "ascii_art": "..."
}
```

---

#### GET /api/panel/configs
List available pre-configured panel compositions.

**Response (200):**
```json
{
  "configs": [
    {
      "id": "balanced",
      "name": "The Balanced Panel",
      "description": "…",
      "persona_ids": ["dr-sigmund-2000", "dr-ada-sterling", "captain-whiskers"],
      "best_for": "…",
      "default": true
    }
  ]
}
```

---

#### POST /api/panel/start
Start a new panel discussion session.

**Request Body:**
```json
{
  "message": "I'm feeling overwhelmed…",
  "panel_config": "balanced",
  "persona_ids": ["dr-sigmund-2000", "dr-ada-sterling"],
  "include_moderator": true
}
```

**Response (200):** Returns `session_id`, optional `moderator_intro`, `panel_responses`, and `panel_state`.

**Streaming (SSE):** Add `"stream": true` to the request body to receive persona responses as they are generated (events: `session`, `moderator_intro`, `panel_response`, `panel_state`, `done`).

---

#### POST /api/panel/continue
Continue an existing panel session.

**Request Body:**
```json
{
  "session_id": "panel-abc123",
  "message": "Follow-up message…",
  "skip_personas": []
}
```

**Response (200):** Returns `panel_responses` and updated `panel_state` (includes `should_summarize`).

**Streaming (SSE):** Add `"stream": true` to stream `panel_response` events sequentially, followed by `panel_state` and `done`.

---

#### POST /api/panel/summarize
Generate a moderator summary for the current session.

**Request Body:**
```json
{ "session_id": "panel-abc123" }
```

**Response (200):** Returns `moderator_summary` with `key_insights` and `credited_personas`.

---

#### POST /api/panel/end
End a panel session and remove it from memory.

**Request Body:**
```json
{ "session_id": "panel-abc123", "return_to_persona_id": "dr-ada-sterling" }
```

**Notes:**
- Panel logic lives in `psychiatrist_panel.py` and uses `config/panel_configs.json`.
- Sessions are stored in-memory with TTL-based cleanup (see `SESSION_TTL_SECONDS`).

## AI Agents

### Gemini Agent (`gemini_agent.py`)

A full-featured command-line AI agent with tool calling capabilities.

**Usage:**
```bash
# Interactive chat mode
python gemini_agent.py --chat

# Single query
python gemini_agent.py "Your question here"

# With MCP support
python gemini_agent.py --chat --mcp

# Plan mode (generates JSON plan)
python gemini_agent.py --plan "Task description"
```

**Command-line Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `prompt` | Single query (positional) | - |
| `--model` | Gemini model to use | gemini-2.5-flash |
| `--chat` | Interactive chat mode | false |
| `--mcp` | Enable MCP servers | false |
| `--plan` | Generate JSON execution plan | - |

**Available Tools:**
The agent has access to all CLI tools defined in `.cursor/rules/command_line_tools.mdc`. Key tools include:
- `google_search` - Web search with grounding
- `html_to_md` - Web scraping
- `nano_banana_generate/edit` - Image generation/editing
- `openai_image_generate/edit` - OpenAI image tools
- `gemini_image_generate/edit` - Gemini/Imagen tools
- `generate_video` - Video generation
- `qwen3_tts` - Text-to-speech
- `play_audio` - Audio playback
- `data_indexing` - RAG indexing
- `semantic_search` - RAG query
- `datetime` - Date/time utilities
- `download_file` - File downloads
- `image_optimizer` - Image processing

**System Prompt Features:**
- Current date/time awareness
- Multi-step workflow planning
- Automatic tool selection
- Result interpretation and summarization

---

### Ollama Agent (`ollama_agent.py`)

A local LLM agent that runs without cloud API keys.

**Usage:**
```bash
# Interactive chat
python ollama_agent.py --chat

# Single query
python ollama_agent.py "Your question"

# Specify model
python ollama_agent.py --model glm4:9b "Tell me a joke"

# Disable tools
python ollama_agent.py --no-tools "Simple question"
```

**Command-line Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `prompt` | Single query (positional) | - |
| `--model` | Ollama model | glm-4.7-flash |
| `--chat` | Interactive chat mode | false |
| `--no-tools` | Disable CLI tools | false |

**Prerequisites:**
- Ollama installed and running
- Required models pulled: `ollama pull glm-4.7-flash`

---

## RAG Pipeline

### Indexing Scripts

#### `index_site.py` (Ollama Embeddings)
Indexes web content using Ollama for embeddings.

```bash
python index_site.py "https://example.com" [-o output.json]
```

**Process:**
1. Fetch URL content
2. Convert HTML to Markdown
3. Use Gemini to extract structured chapters
4. Generate embeddings with `mxbai-embed-large`
5. Store in ChromaDB collection `docs`

---

#### `index_site_gemini.py` (Gemini Embeddings)
Indexes web content using Gemini for embeddings.

**Process:**
1. Fetch URL content
2. Convert HTML to Markdown
3. Use Gemini to extract structured chapters
4. Generate embeddings with `text-embedding-004`
5. Store in ChromaDB collection `gemini-docs`

---

#### `tools/data-indexing.py` (CLI Tool)
The unified data indexing tool accessible via npm script.

```bash
npm run data-indexing -- --url https://example.com
npm run data-indexing -- --file document.pdf
npm run data-indexing -- --url https://example.com --collection my-docs
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `--url` | URL to index | - |
| `--file` | Local file to index | - |
| `--output` | Save processed JSON | - |
| `--collection` | ChromaDB collection | gemini-docs |
| `--model` | Gemini model | gemini-2.5-flash |
| `--embedding-model` | Embedding model | gemini-embedding-001 |
| `--chroma-host` | ChromaDB host | localhost |
| `--chroma-port` | ChromaDB port | 8000 |

---

### Query Scripts

#### `rag_query.py`
Basic RAG query without vector database.

```bash
python rag_query.py "https://example.com" "Your question"
```

**Process:**
1. Fetch and chunk URL content
2. Build context from chunks
3. Query Gemini with context + question

---

#### `rag_query_ollama.py`
RAG query using ChromaDB and Ollama.

```bash
python rag_query_ollama.py "Your question"
```

**Process:**
1. Embed query with `mxbai-embed-large`
2. Search ChromaDB for similar chunks
3. Build context from results
4. Query Ollama with context + question

---

#### `tools/semantic-search.py` (CLI Tool)
The unified semantic search tool.

```bash
npm run semantic-search -- "your query"
npm run semantic-search -- "your query" --collection my-docs
npm run semantic-search -- "your query" --n-results 10 --format json
```

**Options:**
| Option | Description | Default |
|--------|-------------|---------|
| `query` | Search query (positional) | - |
| `--collection` | ChromaDB collection | gemini-docs |
| `--n-results` | Number of results | 5 |
| `--format` | Output format (text/json) | text |
| `--embedding-model` | Embedding model | gemini-embedding-001 |
| `--min-distance` | Min distance threshold | - |
| `--max-distance` | Max distance threshold | - |
| `--where` | JSON metadata filter | - |

---

## Service Architecture

### ChromaDB Integration

ChromaDB runs as a separate service in client-server mode:

```bash
# Start ChromaDB server
chroma run --path ./chroma
```

**Default Configuration:**
- Host: `localhost`
- Port: `8000`
- Data Path: `./chroma`

**Collections:**
| Collection | Purpose | Embedding Model |
|------------|---------|-----------------|
| `gemini-docs` | Gemini-indexed content | text-embedding-004 |
| `docs` | Ollama-indexed content | mxbai-embed-large |

---

### API Key Configuration

All backend scripts load API keys from `.env.local`:

```bash
# Google Gemini
GOOGLE_AI_STUDIO_KEY=your_key
# or
GEMINI_API_KEY=your_key

# OpenAI (for image tools)
OPENAI_API_KEY=your_key

# Replicate (for video/TTS)
REPLICATE_API_TOKEN=your_token
```

**Loading Pattern:**
```python
from dotenv import load_dotenv
load_dotenv('.env.local')

API_KEY = os.getenv('GOOGLE_AI_STUDIO_KEY') or os.getenv('GEMINI_API_KEY')
```

---

## Authentication

Currently, the system uses API key authentication for external services only. There is no user authentication system implemented.

**External Service Authentication:**
- Google Gemini: API key in header (handled by SDK)
- OpenAI: API key in header (handled by SDK)
- Replicate: API token in header (handled by SDK)
- Ollama: No authentication (local service)
- ChromaDB: No authentication (local service)

---

## Error Handling

### Flask API Error Pattern

```python
try:
    # Process request
    response = client.models.generate_content(...)
    return jsonify({
        "response": response_text,
        "mood": mood,
        "ascii_art": ASCII_FACES[mood]
    })
except Exception as e:
    return jsonify({
        "error": str(e),
        "response": f"Error message in character...",
        "mood": "shocked",
        "ascii_art": ASCII_FACES["shocked"]
    }), 500
```

### Agent Error Pattern

```python
def execute_cli_function(name, args):
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return {"ok": proc.returncode == 0, "stdout": proc.stdout, "stderr": proc.stderr}
    except Exception as e:
        return {"ok": False, "error": str(e)}
```

---

## Performance Considerations

### Streaming Responses

The Gemini agent supports streaming for long responses:
```python
# Streaming disabled by default but available
for chunk in response_stream:
    process.stdout.write(chunk.text)
```

### Rate Limiting

External APIs have rate limits:
- Gemini: Varies by tier (free tier has limits)
- OpenAI: Based on account tier
- Replicate: Based on account credits

Consider implementing client-side rate limiting for production use.

### Caching

No caching is currently implemented. Consider adding:
- Response caching for repeated queries
- Embedding caching for frequently accessed content
- ChromaDB query result caching
