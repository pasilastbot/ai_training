# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI training repository containing tools and examples for working with Google Gemini API, local LLMs (Ollama), RAG (Retrieval-Augmented Generation), and various AI-powered CLI tools. The project demonstrates web scraping, semantic search, image/video generation, and AI agent implementations.

## Core Architecture

### Dual Runtime Environment
- **Python 3.10+**: RAG systems, Ollama integration, Gemini agents, data processing
- **Node.js/TypeScript**: CLI tools for image generation, search, datetime, video generation

### Key Systems

#### 1. Gemini Agent (`gemini_agent.py`)
Central agentic system providing:
- Interactive chat mode with tool calling
- 15+ CLI tool integrations (image gen, search, video, etc.)
- Google Search grounding, code execution, URL context
- MCP (Model Context Protocol) stdio tool support
- Plan mode for generating JSON execution plans

**Usage:**
```bash
python3 gemini_agent.py --chat              # Interactive mode
python3 gemini_agent.py "Who won euro 2024?" # Single query
python3 gemini_agent.py --plan "task"       # Generate execution plan
```

#### 2. RAG System (ChromaDB-based)
Three implementations:
- **Gemini-based**: `index_site.py`, `rag_query.py`, `rag_query_final.py`
- **Ollama-based**: `index_site_ollama.py`, `rag_query_ollama.py`
- **Python tools**: `tools/data-indexing.py`, `tools/semantic-search.py`

Workflow:
1. Index websites/documents → ChromaDB with embeddings
2. Query → semantic search → context-augmented LLM response

#### 3. CLI Tools System
TypeScript/Python tools accessible via npm scripts and directly:
- Image generation: `nano-banana`, `imagen`, `recraft`, `flux`
- Search: `google-search` (with grounding)
- Utilities: `datetime`, `download-file`, `html-to-md`
- Data: `data-indexing`, `semantic-search`
- Video: `generate-video`

## Common Commands

### Setup
```bash
# Python dependencies
pip install -r requirements.txt
# or manually:
pip install google-genai html2text rich ollama chromadb requests

# Node.js dependencies
npm install

# Set API key
export GEMINI_API_KEY=<your_key>           # macOS/Linux
set GEMINI_API_KEY=<your_key>              # Windows
$env:GEMINI_API_KEY=<your_key>             # PowerShell
```

### Running ChromaDB (required for RAG)
```bash
chroma run --path ./chroma
```

### RAG Examples

#### Gemini-based RAG
```bash
# Index a website
python3 index_site.py "https://example.com"

# Query indexed content
python3 rag_query.py "https://example.com" "your question"

# Final implementation (advanced)
python3 rag_query_final.py "https://example.com" "your question"
```

#### Ollama-based RAG
```bash
# Pull required models first
ollama pull gemma3:4b          # or gemma3:12b, gemma3:32b
ollama pull mxbai-embed-large

# Index website
python3 index_site_ollama.py "https://example.com"

# Query
python3 rag_query_ollama.py "your question"
```

#### Python CLI RAG tools
```bash
# Index content
npm run data-indexing -- --url https://example.com
npm run data-indexing -- --file document.txt
npm run data-indexing -- --url https://example.com --collection mycollection

# Search indexed content
npm run semantic-search -- "your query"
npm run semantic-search -- "query" --collection mycollection --n-results 10
npm run semantic-search -- --list-collections
```

### CLI Tools

#### Image Generation
```bash
npm run nano-banana -- -p "A futuristic car" -o car.png
npm run nano-banana -- -p "Add flames" -i car.png -o car-flames.png
```

#### Search
```bash
npm run google-search -- -q "latest AI developments"
npm run google-search -- -q "weather today" --format json
```

#### Utilities
```bash
npm run datetime                           # Current datetime
npm run datetime -- --format iso           # ISO 8601
npm run datetime -- --timezone Europe/Helsinki
npm run html-to-md -- <url>                # Convert webpage to markdown
```

#### Data Processing
```bash
npm run data-indexing -- --url https://site.com --output doc.json
npm run semantic-search -- "search query" --format json
```

### Other Scripts
```bash
# HTML parsing
python3 parse_html.py https://website.com

# Guardrails testing
python3 guardrails_test.py https://siili.com "query"

# Weather test
python3 weather_test.py

# ReAct pattern examples
python3 react_ollama.py
python3 react_ollama_real.py
```

## Environment Variables

Required in `.env.local` or environment:

```bash
# Primary API key (required)
GOOGLE_AI_STUDIO_KEY=<your_key>
# or
GOOGLE_API_KEY=<your_key>

# Optional for specific tools
OPENAI_API_KEY=<key>           # For OpenAI-based image tools
REPLICATE_API_TOKEN=<token>     # For Replicate video/image models
```

## Documentation System

The project follows a structured documentation approach defined in `.cursor/rules/documentation.mdc`:

### Core Documentation Files (`/docs`)
- `description.md`: App description, use cases, features
- `architecture.md`: Tech stack, folder structure, testing
- `datamodel.md`: Entities, attributes, relationships
- `frontend.md`: Views, UI/UX patterns, styling
- `backend.md`: API endpoints, authentication, services
- `todo.md`: Task tracking (✅ done, ⏳ in progress, ❌ not started)
- `ai_changelog.md`: Log of AI-made changes
- `learnings.md`: Technical learnings, best practices, solutions
- `chatbot-app-design.md`: Comprehensive chatbot application design

### Documentation Subfolders
- `docs/patterns/`: Software design patterns for implementing features
- `docs/subsystems/`: Subsystem descriptions and component relationships

### Workflow System (`.cursor/rules/`)
The project uses defined workflows for agentic behavior:
- `<research>`: Gather context before planning
- `<develop>`: Implement code for features
- `<fix>`: Diagnose and resolve errors (update learnings.md)
- `<validate>`: Implement and run tests
- `<document>`: Update documentation files
- `<design>`: Design frontend features
- `<implement_ai>`: Implement AI/LLM features
- `<record>`: Document completed work (update ai_changelog.md, todo.md)
- `<use_tools>`: Execute project CLI tools
- `<invent>`: Create new CLI tools
- `<commit>`: Git commit changes

**Important workflow rules:**
- Always use latest stable library versions
- Verify external API docs with web search (don't rely on internal knowledge)
- Use `web_search` or `gemini --ground` for up-to-date information
- For Gemini-based features: Always use `@google/genai` library (not older `generativeai`)
- Update `learnings.md` when fixing non-trivial issues
- Update `todo.md` and `ai_changelog.md` when completing tasks

## Important Technical Details

### Gemini API Integration
- **Preferred SDK**: `@google/genai` for TypeScript, `google.genai` for Python
- **Default model**: `gemini-2.5-flash`
- **Function calling**: CLI tools exposed as function declarations to agent
- **Streaming**: Supported for real-time responses

### RAG Implementation
- **Vector DB**: ChromaDB (client-server mode via `chroma run`)
- **Embeddings**:
  - Gemini: Built-in embeddings
  - Ollama: `mxbai-embed-large` model
- **Chunking**: Gemini-based semantic chunking in `data-indexing.py`
- **Collections**: Namespaced storage in ChromaDB

### CLI Tools Architecture
All tools in `gemini_agent.py` are exposed via `build_cli_function_declarations()`:
- `html_to_md`: Scrape and convert HTML to Markdown
- `gemini`: Call Gemini with grounding/prompts
- `nano_banana`: Image generation and editing
- `google_search`: Web search with grounding
- `datetime`: Get formatted datetime
- `data_indexing`: Index URLs/files to ChromaDB
- `semantic_search`: Query ChromaDB collections
- `download_file`: Download files from URLs
- `generate_video`: Video generation
- And more...

Tools execute via subprocess calls to npm scripts or Python scripts.

### Folder Structure
```
.
├── gemini_agent.py          # Main agentic system
├── index_site.py            # Gemini-based site indexing
├── rag_query.py             # Gemini-based RAG queries
├── rag_query_ollama.py      # Ollama-based RAG queries
├── parse_html.py            # HTML parsing utility
├── react_ollama*.py         # ReAct pattern examples
├── guardrails_test*.py      # AI safety/guardrails testing
├── weather_test.py          # Weather API example
├── tools/                   # CLI tools (TS/Python)
│   ├── gemini.ts/.py        # Gemini API wrappers
│   ├── data-indexing.py     # ChromaDB indexing
│   ├── semantic-search.py   # ChromaDB search
│   ├── nano-banana.ts       # Image generation
│   ├── google-search.ts     # Search tool
│   ├── datetime.ts          # Datetime utility
│   └── ...
├── docs/                    # Project documentation
├── .cursor/rules/           # Cursor AI rules (workflows, behavior)
├── chroma/                  # ChromaDB data directory
├── public/                  # Generated images/videos
├── web/                     # Web frontend (chatbot UI)
├── agents/                  # Agent implementations
└── package.json             # Node.js dependencies and scripts
```

## Development Guidelines

### When Working with AI Features
1. **Research first**: Use `<research>` workflow to understand context
2. **Use latest docs**: Prefer `web_search` or grounding over internal knowledge
3. **Gemini SDK**: Always import from `@google/genai` (TypeScript) or `google.genai` (Python)
4. **Test tools**: Run CLI tools directly to verify before integrating
5. **Document learnings**: Add technical insights to `docs/learnings.md`

### When Creating New Tools
1. Implement in `tools/` directory
2. Add npm script to `package.json` if TypeScript
3. Add function declaration to `gemini_agent.py` if integrating with agent
4. Test standalone before integration
5. Document in README.md CLI Tools section

### When Modifying RAG
1. Ensure ChromaDB is running (`chroma run --path ./chroma`)
2. Test with small dataset first
3. Verify embeddings are generated correctly
4. Check collection names for namespace conflicts

### Testing
No formal test framework configured yet. Manual testing:
1. Run individual Python scripts with sample inputs
2. Execute npm scripts with test parameters
3. Verify ChromaDB queries return relevant results
4. Test gemini_agent.py in chat mode

## Common Issues and Solutions

### ChromaDB Connection Errors
Ensure ChromaDB server is running:
```bash
chroma run --path ./chroma
```

### API Key Not Found
Set environment variable before running:
```bash
export GEMINI_API_KEY=<your_key>
```

### Ollama Model Not Found
Pull required models:
```bash
ollama pull gemma3:4b
ollama pull mxbai-embed-large
```

### Import Errors (Python)
Install all dependencies:
```bash
pip install -r requirements.txt
```

### npm Script Failures
Install Node.js dependencies:
```bash
npm install
```

## Chatbot Application

A comprehensive web-based chatbot design exists in `docs/chatbot-app-design.md`:
- Frontend: HTML/CSS/JavaScript with WebSocket communication
- Backend: Python FastAPI with session management
- Integration: Uses `gemini_agent.py` as library (not subprocess)
- Features: Real-time chat, function calling display, image generation, streaming

See the design document for full architecture, API endpoints, and implementation details.
