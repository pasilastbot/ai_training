# AI Training for Developers

A hands-on training course on building software with AI. Four 90-minute sessions progressing from greenfield development to RAG pipelines.

---

## Sessions

| # | Session | Level | Focus |
|---|---------|-------|-------|
| 1 | [Greenfield Development](session-1-greenfield/) | Beginner | Build from scratch with AI — tools, prompting, specs, TDD |
| 2 | [Brownfield Development](session-2-brownfield/) | Intermediate | Navigate existing codebases — document, spec changes, code review |
| 3 | [Advanced Agentic Workflows](session-3-agentic/) | Advanced | Multi-agent pipelines — CLI tools, skills, agents, hooks |
| 4 | [RAG & AI Agents](session-4-rag/) | Advanced | RAG pipelines — ChromaDB, Gemini, Ollama, guardrails |

---

## Setup

### Node.js (Sessions 1–3)

```bash
npm install
```

### Python (Session 4)

See [session-4-rag/README.md](session-4-rag/README.md) for Python, Ollama, and ChromaDB setup.

---

## Project Structure

```
AGENTS.md                    # Agent configuration, workflows, documentation templates
session-1-greenfield/        # Session 1: Greenfield projects (todo-cli, weather-api, bookmark-api)
session-2-brownfield/        # Session 2: Brownfield work on Suroi codebase
session-3-agentic/           # Session 3: Agentic workflows and pipelines
session-4-rag/               # Session 4: RAG pipeline scripts (Python)
.agents/skills/              # CLI tool documentation (SKILL.md per tool)
tools/                       # CLI tool implementations
slides/                      # Presentation slides
```
