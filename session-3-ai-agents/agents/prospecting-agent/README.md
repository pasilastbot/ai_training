# Prospecting Agent

A B2B prospect research and enrichment agent using Gemini's integrated tools (Google Search, URL Context, Maps).

## Features

- **ICP Management**: Define and refine your Ideal Customer Profile
- **Prospect Search**: Find companies matching your criteria using grounded search
- **Prospect Enrichment**: Deep research on specific companies
- **Memory**: Persistent storage for preferences and session state
- **REST API**: FastAPI-based API for integration
- **Web UI**: Flask-based dashboard

## Quick Start

### 1. Install Dependencies

```bash
cd session-3-ai-agents/agents/prospecting-agent
pip install -r requirements.txt
```

### 2. Set API Key

```bash
export GEMINI_API_KEY=your_api_key
# Or create .env.local with:
# GEMINI_API_KEY=your_api_key
```

### 3. Run the Agent

#### CLI Mode (Interactive)

```bash
python prospecting_agent.py --chat
```

#### CLI Mode (Single Query)

```bash
python prospecting_agent.py "Find AI startups in San Francisco Series A"
```

#### With Custom ICP

```bash
python prospecting_agent.py --icp memory/data/sample_icp.json "Find matching companies"
```

### 4. Run the API

```bash
uvicorn api.main:app --reload --port 8001
```

API docs: http://localhost:8001/docs

### 5. Run the Web UI

```bash
python ui/app.py
```

Open: http://localhost:5001

## Structure

```
prospecting-agent/
├── prospecting_agent.py    # Main CLI agent
├── requirements.txt        # Dependencies
├── README.md              # This file
├── ui/
│   ├── app.py             # Flask web UI
│   └── templates/         # HTML templates
├── api/
│   └── main.py            # FastAPI REST API
├── tools/
│   ├── store_prospect.py  # Database storage
│   ├── retrieve_prospects.py # Database queries
│   └── memory_tool.py     # Memory CLI
├── skills/
│   ├── prospect-storage.md   # Storage skill
│   ├── icp-management.md     # ICP skill
│   └── delegation.md         # Delegation skill
├── subagents/
│   ├── prospect_search.py    # Search subagent
│   └── prospect_enrich.py    # Enrichment subagent
└── memory/
    ├── memory.py             # ChromaDB memory store
    ├── icp_schema.json       # ICP schema
    ├── prospect_schema.json  # Prospect schema
    └── data/                 # Local storage
        └── sample_icp.json   # Sample ICP
```

## Usage Examples

### Define Your ICP

```bash
# Via CLI
python tools/memory_tool.py icp update --key target_industries --value '["SaaS", "Fintech"]'
python tools/memory_tool.py icp update --key geography --value '["US", "UK"]'

# Or load from file
python tools/memory_tool.py icp set --file memory/data/sample_icp.json
```

### Search for Prospects

```bash
# Via subagent directly
python subagents/prospect_search.py --query "AI companies in healthcare" --pretty

# With ICP
python subagents/prospect_search.py --icp-file memory/data/sample_icp.json --pretty

# Via main agent
python prospecting_agent.py "Find Series B SaaS companies in the US"
```

### Enrich a Prospect

```bash
# Via subagent directly
python subagents/prospect_enrich.py --company "Acme Corp" --website "https://acme.com" --pretty

# Via main agent
python prospecting_agent.py "Tell me more about Stripe"
```

### Manage Prospects

```bash
# Store a prospect
python tools/store_prospect.py --company "Acme Corp" --industry "SaaS" --score 85

# List prospects
python tools/retrieve_prospects.py --all --pretty

# Filter by status
python tools/retrieve_prospects.py --status enriched --min-score 70 --pretty

# Get statistics
python tools/retrieve_prospects.py --stats
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| GET | /icp | Get current ICP |
| POST | /icp | Update ICP |
| POST | /search | Search prospects |
| POST | /enrich | Enrich prospect |
| GET | /prospects | List prospects |
| GET | /prospects/{id} | Get prospect |
| POST | /prospects | Store prospect(s) |
| GET | /stats | Get statistics |

## Gemini Tools Used

The agent leverages Gemini's integrated tools:

- **Google Search**: Real-time web search with grounding
- **URL Context**: Analyze specific company websites
- **Google Maps**: Location-based queries (optional)

These tools are combined with function calling for a powerful research workflow.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Gemini API key |
| `DATABASE_URL` | No | PostgreSQL URL (defaults to SQLite) |
| `CHROMA_HOST` | No | ChromaDB host (default: localhost) |
| `CHROMA_PORT` | No | ChromaDB port (default: 8000) |
