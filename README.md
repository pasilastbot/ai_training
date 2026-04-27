# AI Training for Developers

A hands-on training course on building software with AI. Four 90-minute sessions progressing from greenfield development to automated software factories.

---

## Sessions

| # | Session | Level | Focus |
|---|---------|-------|-------|
| 1 | [Greenfield Development](session-1-greenfield/) | Beginner | Build from scratch — tools, prompting, specs, TDD |
| 2 | [Brownfield Development](session-2-brownfield/) | Intermediate | Navigate existing codebases — document, spec changes, code review |
| 3 | [AI Agents](session-3-ai-agents/) | Advanced | Build AI agents — tools, memory, RAG, skills, subagents |
| 4 | [Software Factories](session-4-agentic/) | Advanced | Automated delivery — role-based policies, spec loops, E2E testing |

---

## Session Summaries

### Session 1: Greenfield Development
Build a working application from scratch using AI. Choose from three projects:
- **Todo CLI** — Command-line todo manager with categories and priorities
- **Weather Dashboard API** — REST API for weather data with caching
- **Bookmark Manager API** — REST API for saving, tagging, and searching bookmarks

Learn: AI tools landscape, rules/configuration, effective prompting, spec-driven development, TDD with AI.

### Session 2: Brownfield Development
Work with **Suroi** (~114k lines of TypeScript), a real open-source battle royale game. Learn to:
- Document unfamiliar codebases with AI (3-tiered documentation)
- Spec changes using SDD (Spec-Driven Development)
- Code review changes against specifications

Learn: ModernPath 4-step process, AI-friendly architecture, documentation plans.

### Session 3: AI Agents
Design, build, and rehearse practical AI agents with tools, memory, and retrieval:
- **Exercise 1:** Invent a CLI tool using AGENTS.md workflow
- **Exercise 2:** Build RAG-backed memory (embed, store, retrieve)
- **Exercise 3:** Combine tools + memory + guardrails into a full agent

Includes pre-built agents: lunch-selection-agent, weather-forecast-agent, prospecting-agent, tes-agent, holiday-planner.

### Session 4: Software Factories
Move from individual agent usage to repeatable software factory workflows:
- **Rehearsal 1:** Minimal factory — single task execution
- **Rehearsal 2:** Role-based policies + session resume
- **Rehearsal 3:** Spec-driven delivery loops (implement → check → review)
- **Rehearsal 4:** Agent Factory — automated agent creation with E2E testing

Learn: Factory anatomy, role policies (analyzer/fixer/planner), spec-driven loops, quality gates.

---

## Setup

### Node.js (Sessions 1–2)

```bash
npm install
```

### Python (Sessions 3–4)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set API key for Gemini
export GEMINI_API_KEY=<your_key>

# For Session 4, install Claude SDK
pip install claude-agent-sdk
```

### CLI Tools (Session 4)

At least one CLI tool with active subscription:
```bash
claude --version   # Claude Code CLI
codex --version    # OpenAI Codex CLI
opencode --version # OpenCode CLI
```

---

## Project Structure

```
README.md                        # This file
AGENTS.md                        # Agent configuration, workflows, documentation templates

session-1-greenfield/            # Session 1: Greenfield projects
├── a-todo-cli/                  # Todo CLI project
├── b-weather-api/               # Weather Dashboard API project
└── c-bookmark-api/              # Bookmark Manager API project

session-2-brownfield/            # Session 2: Brownfield work on Suroi
├── prompts/                     # Step-by-step prompt files
└── docs/                        # Documentation outputs

session-3-ai-agents/             # Session 3: AI Agents
├── agents/                      # Pre-built agent implementations
│   ├── lunch-selection-agent/   # Restaurant discovery + recommendations
│   ├── weather-forecast-agent/  # Weather forecasts + alerts
│   ├── prospecting-agent/       # B2B prospect search
│   ├── tes-agent/               # Finnish collective agreements
│   └── holiday-planner/         # Family holiday planning
├── exercises/                   # Hands-on exercises
├── gemini_agent.py              # Base agent template
└── index_site.py                # RAG indexing script

session-4-agentic/               # Session 4: Software Factories
├── claude-factory-rehearsal/    # Factory rehearsal scripts
│   ├── 01_minimal_factory.py    # Basic factory pattern
│   ├── 02_factory_catalog.py    # Role-based policies
│   ├── 03_resumable_factory.py  # Session resume capability
│   ├── 04_spec_loop_factory.py  # Spec-driven delivery loop
│   ├── 05_agent_factory.py      # Complete agent creation factory
│   ├── backend_runner.py        # Multi-backend adapter
│   └── spec.*.json              # Spec examples
└── AGENTS.md                    # Factory framework documentation

.agents/skills/                  # CLI tool documentation (SKILL.md per tool)
tools/                           # CLI tool implementations
slides/                          # Presentation slides
```

---

## Key Concepts

| Concept | Session | Description |
|---------|---------|-------------|
| Context Sandwich | 1 | Prompt structure: context → task → constraints |
| Spec-Driven Development | 1, 2 | Write specs before code, use AI to implement |
| 3-Tiered Documentation | 2 | High-level → Subsystem → Module docs |
| Agent Loop | 3 | Plan → Execute → Observe → Repeat |
| RAG | 3 | Retrieval-Augmented Generation for memory |
| Software Factory | 4 | Policy wrapper: goal + tools + quality gates |
| Spec Loop | 4 | Implement → Check → Review until approved |

---

## Quick Links

- [Session 1 README](session-1-greenfield/README.md)
- [Session 2 README](session-2-brownfield/README.md)
- [Session 3 README](session-3-ai-agents/README.md)
- [Session 4 README](session-4-agentic/README.md)
- [AGENTS.md](AGENTS.md) — Workflow templates and conventions
