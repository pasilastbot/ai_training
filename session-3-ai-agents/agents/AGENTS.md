# AGENTS.md — Agent Framework Configuration

> This file defines the structure and rules for building AI agents in this folder.
> Every agent must follow this structure to ensure consistency and interoperability.

---

## Agent Structure

Every agent MUST be placed in its own subfolder under `agents/` with the following structure:

```
agents/
└── {agent-name}/
    ├── {agent_name}.py      # Main CLI agent (required)
    ├── ui/                   # Web UI (required)
    │   └── app.py           # Flask-based web interface
    ├── api/                  # REST API (required)
    │   └── main.py          # FastAPI-based API layer
    ├── tools/                # CLI tools (required)
    │   └── *.py             # Python CLI tools callable by the agent
    ├── skills/               # Skill definitions (required)
    │   └── *.md             # Markdown files describing tool usage
    ├── subagents/            # Delegated agents (required)
    │   └── *.py             # Independent CLI agents for subtasks
    ├── memory/               # Local memory/state (required)
    │   ├── memory.py        # Memory access CLI
    │   ├── *_schema.json    # Data schemas
    │   └── data/            # Local storage (ChromaDB, SQLite, etc.)
    └── requirements.txt      # Agent-specific dependencies (optional)
```

---

## Naming Conventions

| Component | Convention | Example |
|-----------|------------|---------|
| Folder | kebab-case | `prospecting-agent/` |
| Main agent file | snake_case | `prospecting_agent.py` |
| Subagent files | snake_case | `prospect_search.py` |
| Tool files | snake_case | `store_prospect.py` |
| Skill files | kebab-case | `prospect-storage.md` |
| Schema files | snake_case | `icp_schema.json` |

---

## Agent Requirements

### 1. Main Agent (`{agent_name}.py`)

The main agent file MUST:
- Be a CLI application (argparse-based)
- Derive patterns from `../gemini_agent.py`
- Support `--chat` mode for interactive use
- Support single-query mode
- Load skills from `skills/` folder
- Access memory via `memory/memory.py`
- Delegate to subagents when appropriate

```python
#!/usr/bin/env python3
"""
{Agent Name} CLI

Usage:
  python {agent_name}.py --chat           # Interactive mode
  python {agent_name}.py "your query"     # Single query
  python {agent_name}.py --help           # Show help
"""
```

### 2. UI Folder (`ui/`)

The UI folder MUST contain:
- `app.py` — Flask-based web interface
- Static assets in `ui/static/` (optional)
- Templates in `ui/templates/` (optional)

```python
# ui/app.py
from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

@app.route('/')
def index():
    # Main dashboard
    pass
```

### 3. API Folder (`api/`)

The API folder MUST contain:
- `main.py` — FastAPI-based REST API
- Pydantic models for request/response schemas

```python
# api/main.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="{Agent Name} API")

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 4. Tools Folder (`tools/`)

Tools are CLI utilities that the agent can invoke. Each tool MUST:
- Be a standalone Python CLI script
- Accept arguments via argparse
- Return structured output (JSON preferred)
- Exit with appropriate codes (0=success, 1=error)

```python
#!/usr/bin/env python3
"""Tool description."""
import argparse
import json
import sys

def main():
    parser = argparse.ArgumentParser(description="Tool description")
    # Add arguments
    args = parser.parse_args()
    
    # Execute tool logic
    result = {"status": "success", "data": ...}
    print(json.dumps(result))
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### 5. Skills Folder (`skills/`)

Skills are Markdown files that describe how tools are used. Format:

```markdown
---
name: skill-name
description: When to use this skill
tools: [tool1, tool2]
---

## Purpose
[What this skill accomplishes]

## When to Use
[Conditions that trigger this skill]

## Tools Required
[List of tools and their roles]

## Example
[Example invocation]
```

### 6. Subagents Folder (`subagents/`)

Subagents are independent agents that handle specific subtasks. Each subagent MUST:
- Be a standalone CLI (same structure as main agent)
- Accept input via stdin or arguments
- Return structured JSON output
- Be invokable by the main agent

### 7. Memory Folder (`memory/`)

The memory folder provides persistent state. It MUST contain:
- `memory.py` — CLI for memory operations
- Schema files defining data structures
- `data/` folder for local storage

---

## Gemini API Integration

Agents use Gemini's integrated tools for grounded responses:

### Built-in Tools

```python
from google import genai
from google.genai import types

# Enable Google Search, URL Context, and Maps grounding
tools = [
    types.Tool(
        google_search=types.GoogleSearch(),
        url_context=types.UrlContext(),
        google_maps=types.GoogleMaps(),
        function_declarations=[...]  # Custom functions
    )
]

config = types.GenerateContentConfig(
    tools=tools,
    include_server_side_tool_invocations=True  # Enable tool combination
)
```

### Tool Combination

Gemini 3 models support combining built-in tools with custom function calling:
- `google_search` — Real-time web search with grounding
- `url_context` — Fetch and analyze specific URLs
- `google_maps` — Location-aware queries and place data
- Custom functions — Your own tool implementations

---

## Agent Registration

Register new agents by creating their folder structure. The framework automatically discovers agents based on folder structure.

### Registered Agents

| Agent | Description | Status |
|-------|-------------|--------|
| `prospecting-agent` | B2B prospect search and enrichment | Active |
| `lunch-selection-agent` | Restaurant discovery, menu extraction, and personalized lunch recommendations | Active |
| `tes-agent` | Finnish collective bargaining agreement (TES) indexing, comparison, and salary calculation | Active |
| `holiday-planner` | Family holiday planning - understands whole family wishes, recommends and compares destinations | Active |

---

## Running Agents

### CLI Mode

```bash
# Interactive chat
python agents/{agent-name}/{agent_name}.py --chat

# Single query
python agents/{agent-name}/{agent_name}.py "your query"
```

### API Mode

```bash
# Start FastAPI server
uvicorn agents.{agent-name}.api.main:app --reload --port 8001
```

### UI Mode

```bash
# Start Flask UI
python agents/{agent-name}/ui/app.py
# Or with flask run
FLASK_APP=agents/{agent-name}/ui/app.py flask run --port 5001
```

---

## Environment Variables

Agents inherit from the parent environment:

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Gemini API key |
| `GOOGLE_AI_STUDIO_KEY` | Alt | Alternative Gemini key |
| `DATABASE_URL` | Optional | PostgreSQL connection string |
| `CHROMA_HOST` | Optional | ChromaDB host (default: localhost) |
| `CHROMA_PORT` | Optional | ChromaDB port (default: 8000) |

---

## Workflow: Create New Agent

To create a new agent:

1. **Create folder structure:**
   ```bash
   mkdir -p agents/{agent-name}/{ui,api,tools,skills,subagents,memory/data}
   ```

2. **Copy templates:**
   - Main agent from `../gemini_agent.py`
   - Adapt for your use case

3. **Define skills:**
   - Create skill files in `skills/`
   - Document tool usage patterns

4. **Implement subagents:**
   - Create specialized agents for subtasks
   - Use Gemini's built-in tools as needed

5. **Add memory schema:**
   - Define data structures in `*_schema.json`
   - Implement memory CLI in `memory/memory.py`

6. **Build API and UI:**
   - Expose agent via FastAPI
   - Create web dashboard with Flask

7. **Register in this file:**
   - Add to "Registered Agents" table
   - Document capabilities
