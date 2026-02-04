# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI training and agent system for developers. Multi-platform AI integration (Gemini, Ollama, OpenAI, Replicate) with CLI tools, interactive agents, and a RAG pipeline using ChromaDB.

## Setup & Dependencies

```bash
# Node.js dependencies
npm install

# Python dependencies
pip install -r requirements.txt
# or: python3 -m pip install google-genai html2text rich ollama chromadb requests
```

API keys go in `.env.local` (copy from `.env.example`). Required keys: `GOOGLE_AI_STUDIO_KEY`/`GEMINI_API_KEY`, `REPLICATE_API_TOKEN`, `OPENAI_API_KEY`.

## Running Tools

All CLI tools run via npm scripts using `tsx` (TypeScript) or `python3`:

```bash
# TypeScript tools (all use tsx)
npm run gemini -- --prompt "..."
npm run nano-banana -- -p "description" -o output.png
npm run google-search -- -q "query"
npm run qwen3-tts -- -t "text" --mode voice
npm run play-audio -- file.wav
npm run generate-video -- -p "description"
npm run datetime -- --format iso
npm run html-to-md -- --url https://example.com
npm run download-file -- --url https://example.com/file
npm run optimize-image -- input.png
npm run openai-image -- --prompt "description"

# Python tools (RAG pipeline)
npm run data-indexing -- --url https://example.com
npm run semantic-search -- "query"

# Python agents (run directly)
python3 gemini_agent.py --chat           # Interactive Gemini agent
python3 gemini_agent.py "question"       # Single query
python3 ollama_agent.py --chat           # Interactive Ollama agent
```

## RAG Pipeline

Requires ChromaDB running in client-server mode:

```bash
chroma run --path ./chroma
```

1. **Index content**: `npm run data-indexing -- --url <url>` or `--file <path>`
2. **Query**: `npm run semantic-search -- "question"` or `python3 rag_query.py`

For Ollama RAG: requires `mxbai-embed-large` embedding model and a chat model (e.g., `gemma3:4b`).

## Architecture

### Two language stacks

- **TypeScript** (`tools/`): CLI tools executed via `tsx`. Each tool is a standalone CLI using `commander` or `yargs`. Tools handle image generation, search, video generation, TTS, file operations.
- **Python** (root): AI agents (`gemini_agent.py`, `ollama_agent.py`), RAG pipeline (`index_site*.py`, `rag_query*.py`), content indexing, and the `tools/data-indexing.py` / `tools/semantic-search.py` scripts.

### Key patterns

- All TypeScript tools load env vars from `.env.local` via `dotenv`
- Gemini API uses `@google/genai` SDK (newer) — not the legacy `@google/generative-ai`
- `gemini_agent.py` supports tools (Google Search, Code Execution, URL Context), MCP, and plan mode
- ChromaDB is used for vector storage; Gemini embeddings (`text-embedding-004`) for indexing and search
- TypeScript strict mode is enabled (`tsconfig.json`)

### Documentation

- `/docs/todo.md` — task tracking
- `/docs/ai_changelog.md` — log of AI-made changes
- `/docs/learnings.md` — technical learnings

## Development Rules (from Cursor rules)

- **Never create a new project** — always work within existing structure
- **Verify external APIs** — use web search to confirm API docs/versions, don't rely solely on training data
- **Prefer latest stable library versions**
- **Search before modifying** — understand impact of changes before editing existing code
- **Simplicity** — prefer the simplest, most direct solution
- **Claude-specific**: implement only what is explicitly asked, no extras

Read @.cursor/rules/workflows