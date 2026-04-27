# Software Factory Training Rehearsals

This folder is designed for live training. It demonstrates how to move from a
single-agent "factory" call to a spec-driven implementation loop.

Core idea for participants:

"A software factory is a reusable policy wrapper around an agent loop:
goal contract + tool policy + quality gates."

## Training flow (4 rehearsals)

### Rehearsal 1 - Minimal Factory

**Goal:** show the smallest possible factory shape.

Script:

- `01_minimal_factory.py`

What to teach:

- a factory accepts a task
- a backend executes it (`claude`, `codex`, `opencode`)
- output comes back as one final result

Run:

```bash
uv run python 01_minimal_factory.py --backend claude "Summarize this project"
uv run python 01_minimal_factory.py --backend codex "Summarize this project"
uv run python 01_minimal_factory.py --backend opencode "Summarize this project"
```

### Rehearsal 2 - Behavior by Factory Role + Session Resume

**Goal:** show that factories are policies, not just prompts.

Scripts:

- `02_factory_catalog.py` (analyzer / fixer / planner)
- `03_resumable_factory.py` (start/resume)

What to teach:

- same backend, different role policy => different behavior
- sessions can continue across calls (factory memory)

Run:

```bash
uv run python 02_factory_catalog.py analyzer --backend codex "Find likely risk areas"
uv run python 02_factory_catalog.py planner --backend claude "Create implementation plan"

uv run python 03_resumable_factory.py start --backend opencode "Inspect auth flow"
uv run python 03_resumable_factory.py resume --backend opencode "Continue and propose fixes"
```

### Rehearsal 3 - Spec-Driven Delivery Loop

**Goal:** show automation loop used in real software work.

Script:

- `04_spec_loop_factory.py`

Spec:

- `spec.example.json`

What to teach:

- factory reads a delivery spec
- runs loop: implement -> checks -> review
- repeats until approved or max iterations reached

Run:

```bash
uv run python 04_spec_loop_factory.py --backend codex --spec spec.example.json
```

### Rehearsal 4 - Agent Factory (All Concepts Combined)

**Goal:** show end-to-end agent creation that combines roles, resume, and loops.

Script:

- `05_agent_factory.py`

Spec example:

- `spec.agent-example.json`

What to teach:

- factory takes a simple idea and generates a detailed spec
- multiple roles work together (spec_generator, implementer, validator, reviewer, fixer)
- implementation loops until all validation checks pass
- **E2E tests verify the agent actually works** (API, UI, CLI all tested)
- sessions can be resumed if interrupted
- produces complete, **tested** agents matching session-3-ai-agents structure

E2E Tests run automatically:
1. `api_health_check` - API starts and responds to /health
2. `api_endpoint_test` - At least one endpoint responds
3. `ui_serves_html` - UI serves HTML on root path
4. `cli_help` - CLI responds to --help

Run:

```bash
# Full workflow: generate spec and implement
uv run python 05_agent_factory.py start --backend claude "weather forecast agent"

# Generate spec only (for review before implementation)
uv run python 05_agent_factory.py spec --backend claude "recipe finder agent"

# Implement from an existing spec
uv run python 05_agent_factory.py implement --backend codex --spec spec.agent-example.json

# Resume an interrupted session
uv run python 05_agent_factory.py resume --backend claude "continue implementing"
```

---

## Setup for training session

**No API keys required** — uses CLI subscriptions.

1. Verify Python:

```bash
uv run python -V  # or python3 -V
```

2. Verify CLIs (at least one required):

```bash
claude --version   # Claude Code
codex --version    # OpenAI Codex
opencode --version # OpenCode
```

3. Install Python SDK:

```bash
pip install claude-agent-sdk
```

4. Run all checks + sample runs:

```bash
./run_demo.sh
```

---

## Files in this training pack

- `01_minimal_factory.py` - single factory call
- `02_factory_catalog.py` - role-based factory policies
- `03_resumable_factory.py` - session continuation
- `04_spec_loop_factory.py` - implement/test/review loop
- `05_agent_factory.py` - complete agent creation factory (combines all concepts)
- `backend_runner.py` - backend adapter (`claude`, `codex`, `opencode`)
- `spec.example.json` - editable loop specification
- `spec.agent-example.json` - example agent specification for agent factory
- `run_demo.sh` - quick environment and demo runner

---

## Spec format for rehearsal 3

`04_spec_loop_factory.py` expects JSON with:

- `goal`: target outcome
- `max_iterations`: maximum loop rounds
- `checks`: deterministic local commands
- optional:
  - `implement_instructions`
  - `review_instructions`
  - `allowed_tools`
  - `permission_mode`
  - `agent_max_turns`
  - `model`

`checks[].command` can use `{python}` placeholder, which resolves to:

- `uv run python` when available
- otherwise `python3`

---

## Spec format for rehearsal 4 (Agent Factory)

`05_agent_factory.py` can generate specs automatically from an idea, or accept a JSON spec file:

```json
{
  "name": "agent-name",
  "description": "What the agent does",
  "capabilities": ["list of capabilities"],
  "tools": [
    {"name": "tool_name", "description": "...", "parameters": [...]}
  ],
  "skills": [
    {"name": "skill-name", "description": "...", "tools": [...]}
  ],
  "subagents": [
    {"name": "subagent_name", "purpose": "..."}
  ],
  "memory_schemas": [
    {"name": "schema_name", "fields": [...]}
  ],
  "api_endpoints": [
    {"method": "GET", "path": "/endpoint", "description": "..."}
  ],
  "ui_views": [
    {"name": "view_name", "description": "..."}
  ],
  "environment_variables": [
    {"name": "VAR_NAME", "required": true, "description": "..."}
  ]
}
```

The factory creates agents that match the structure defined in `session-3-ai-agents/agents/AGENTS.md`:

- Main agent CLI (`{agent_name}.py`)
- UI folder with Flask app (`ui/app.py`)
- API folder with FastAPI (`api/main.py`)
- Tools folder with CLI scripts (`tools/*.py`)
- Skills folder with markdown files (`skills/*.md`)
- Subagents folder (`subagents/*.py`)
- Memory folder with schemas and data (`memory/`)
