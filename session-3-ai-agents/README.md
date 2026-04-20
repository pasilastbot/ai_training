# Session 3: Develop AI Agents with AI

**90 min | Advanced | "From Sub-Agents to Full Agents"**

Design, build, and rehearse practical AI agents with tools, memory, and retrieval.

---

## Prerequisites

- Python 3.10+
- Gemini API key (`GEMINI_API_KEY` or `GOOGLE_AI_STUDIO_KEY`)
- ChromaDB (for RAG exercises)
- Completed Sessions 1-2

## Setup

```bash
cd session-3-ai-agents/
pip install -r requirements.txt

# Set your API key
export GEMINI_API_KEY=<your_key>

# Start ChromaDB (for Exercises 2-3)
chroma run --path ./chroma-data
```

---

## Session Flow

| # | Type | Topic | Duration |
|---|------|-------|----------|
| 1 | Theory | What Is an AI Agent? | 5 min |
| 2 | Theory | The Agent Loop | 5 min |
| 3 | Theory | Core Agent Capabilities | 5 min |
| 4 | Theory | MCP vs CLI Tools | 10 min |
| 5 | **Exercise 1** | Invent a Tool | 10 min |
| 6 | Theory | Memory Patterns | 5 min |
| 7 | Theory | RAG for Agents | 10 min |
| 8 | **Exercise 2** | RAG-Backed Memory Skill | 10 min |
| 9 | Planning | Plan Your Agent (teams) | 5 min |
| 10 | **Exercise 3** | Build the Agent | 15 min |
| | Wrap-up | Session summary | 5 min |

**Total: ~90 min** (40 min theory + 45 min hands-on + 5 min wrap-up)

---

## Exercises

| File | Focus | Duration |
|------|-------|----------|
| `exercises/01-invent-tool.md` | Use AGENTS.md "invent" workflow to create a CLI tool | 10 min |
| `exercises/02-rag-memory-skill.md` | Build RAG-backed memory (embed + store + retrieve) | 10 min |
| `exercises/03-build-agent.md` | Combine tools + memory + guardrails into full agent | 15 min |

---

## Key Files

| File | Purpose |
|------|---------|
| `gemini_agent.py` | Base agent template — extend this in Exercise 3 |
| `index_site.py` | Index website content to ChromaDB |
| `rag_query.py` | RAG query with Gemini embeddings |

---

## Quick Start

```bash
# Test the agent works
python gemini_agent.py --chat

# Single query
python gemini_agent.py "What time is it in Helsinki?"

# Generate a plan (JSON output)
python gemini_agent.py --plan "Create a REST API for user management"

# Index content for RAG
python index_site.py "https://docs.anthropic.com"

# Query indexed content
python rag_query.py "What is Claude?" --show-sources
```

---

## Exercise Flow

### Exercise 1: Invent a Tool
```
Invent a new tool: [your description]
```
AI implements, tests, and documents the tool.

### Exercise 2: RAG-Backed Memory Skill
```
Create a RAG-backed memory skill: [your description]
```
AI generates embed/store/retrieve logic for persistent memory.

### Exercise 3: Build the Agent
Teams combine:
- Tool from Exercise 1
- Memory from Exercise 2
- Guardrails (blocked patterns)
- Subagents (optional delegation)

Output: Working agent per team.

---

## Key Insight

> AI agents are not "just prompts." They are engineered loops with planning, tools, memory, and verification.
