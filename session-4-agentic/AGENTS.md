# AGENTS.md — Software Factory Framework

> This file defines the structure and concepts for building Software Factories.
> A **factory** is a reusable policy wrapper around an agent loop:
> **goal contract + tool policy + quality gates**.

---

## Core Concepts

### What Is a Software Factory?

A software factory is NOT just calling an AI agent. It's a **repeatable, policy-driven automation pattern** with:

| Component | Purpose |
|-----------|---------|
| **Goal Contract** | What the factory is trying to achieve |
| **Tool Policy** | Which tools are allowed and in what mode |
| **Quality Gates** | Checks that must pass before completion |
| **Session State** | Ability to resume and continue work |

### Factory vs Agent

| Aspect | Agent | Factory |
|--------|-------|---------|
| Scope | Single task | Repeatable workflow |
| Policy | Ad-hoc | Defined upfront |
| Quality | Trust output | Verify with checks |
| State | Ephemeral | Resumable sessions |

---

## Rehearsal Structure

All rehearsals are in `claude-factory-rehearsal/`:

```
session-4-agentic/
├── AGENTS.md                         # This file
├── README.md                         # Session overview
└── claude-factory-rehearsal/
    ├── 01_minimal_factory.py         # Rehearsal 1: Basic factory
    ├── 02_factory_catalog.py         # Rehearsal 2: Role-based policies
    ├── 03_resumable_factory.py       # Rehearsal 2: Session continuity
    ├── 04_spec_loop_factory.py       # Rehearsal 3: Spec-driven loop
    ├── backend_runner.py             # Multi-backend adapter
    ├── spec.example.json             # Example spec for loop factory
    ├── requirements.txt              # Dependencies
    ├── run_demo.sh                   # Quick test script
    └── README.md                     # Rehearsal instructions
```

---

## Rehearsal 1: Minimal Factory

**Goal:** Show the smallest possible factory shape.

**Key Learning:** A factory accepts a task, runs it through a backend, and returns a result.

```bash
# Run with any backend
uv run python 01_minimal_factory.py --backend claude "Summarize this project"
uv run python 01_minimal_factory.py --backend codex "List files"
uv run python 01_minimal_factory.py --backend opencode "Explain the architecture"
```

**Factory Components:**
- `FactorySpec`: name, prompt_template, allowed_tools, max_turns, permission_mode
- `Factory.run(task)`: formats prompt, runs backend, returns result

---

## Rehearsal 2: Role-Based Policies + Session Resume

**Goal:** Show that factories are policies, not just prompts.

### Part A: Factory Catalog (02_factory_catalog.py)

Same backend + different role policy = different behavior.

| Factory | Role | Tools | Mode |
|---------|------|-------|------|
| `analyzer` | Inspect and explain only | Read, Glob, Grep, WebSearch, WebFetch | Read-only |
| `fixer` | Make minimal safe edits | Read, Glob, Grep, Edit, Bash | Accept edits |
| `planner` | Produce implementation plans | Read, Glob, Grep | Plan-only |

```bash
uv run python 02_factory_catalog.py analyzer --backend claude "Find risks"
uv run python 02_factory_catalog.py planner --backend codex "Create plan"
uv run python 02_factory_catalog.py fixer --backend opencode "Fix issues"
```

### Part B: Resumable Factory (03_resumable_factory.py)

Sessions can continue across calls (factory memory).

```bash
# Start a new session
uv run python 03_resumable_factory.py start --backend claude "Remember: magic number is 42"

# Resume the session
uv run python 03_resumable_factory.py resume --backend claude "What was the magic number?"
```

**Session Files:** `.factory-session-id-{backend}` stores session IDs.

---

## Rehearsal 3: Spec-Driven Delivery Loop

**Goal:** Show automation loop used in real software work.

```bash
uv run python 04_spec_loop_factory.py --backend codex --spec spec.example.json
```

### Loop Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SPEC-DRIVEN LOOP                         │
├─────────────────────────────────────────────────────────────┤
│  1. IMPLEMENT                                               │
│     ├── Read spec goal and instructions                     │
│     ├── Include previous failure context                    │
│     └── Agent makes changes                                 │
│                                                             │
│  2. CHECK                                                   │
│     ├── Run each check command                              │
│     ├── If any fail → back to IMPLEMENT                     │
│     └── If all pass → proceed to REVIEW                     │
│                                                             │
│  3. REVIEW                                                  │
│     ├── Agent reviews against goal                          │
│     ├── Returns FINAL_STATUS: APPROVED or CHANGES_REQUIRED  │
│     └── If APPROVED → done, else → back to IMPLEMENT        │
└─────────────────────────────────────────────────────────────┘
```

### Spec Format

```json
{
  "name": "factory-loop-demo",
  "goal": "Description of what to achieve",
  "max_iterations": 3,
  "agent_max_turns": 16,
  "permission_mode": "acceptEdits",
  "allowed_tools": ["Read", "Glob", "Grep", "Edit", "Bash"],
  "implement_instructions": "Focus on fixing failing checks",
  "review_instructions": "Confirm if goal is met. Return FINAL_STATUS: APPROVED or CHANGES_REQUIRED",
  "checks": [
    {
      "name": "syntax",
      "command": "{python} -m py_compile file.py",
      "timeout_seconds": 120
    }
  ]
}
```

**Placeholders:**
- `{python}` → resolves to `uv run python` or `python3`

---

## Backend Support

All rehearsals support 3 backends via CLI subscriptions (no API keys needed):

| Backend | CLI | Version Check |
|---------|-----|---------------|
| `claude` | Claude Code | `claude --version` |
| `codex` | Codex CLI | `codex --version` |
| `opencode` | OpenCode | `opencode --version` |

### Backend Runner (backend_runner.py)

The adapter translates factory options to each CLI:

```python
@dataclass
class BackendRunOptions:
    backend: Backend           # 'claude', 'codex', or 'opencode'
    prompt: str                # The task/prompt
    cwd: Path                  # Working directory
    allowed_tools: list[str]   # Tools the agent can use
    permission_mode: str       # 'default', 'plan', 'acceptEdits'
    max_turns: int             # Max agent turns
    resume_session_id: str | None  # For session continuity
    model: str | None          # Optional model override

@dataclass
class BackendRunResult:
    ok: bool                   # Success or failure
    text: str                  # Agent's response
    stop_reason: str           # Why it stopped
    session_id: str | None     # For resuming later
```

### Permission Mode Mapping

| Factory Mode | Claude | Codex | OpenCode |
|--------------|--------|-------|----------|
| `default` | SDK default | `--sandbox read-only` | Default |
| `plan` | plan mode | `--sandbox read-only` | Default |
| `acceptEdits` | accept edits | `--full-auto` | Default |

---

## Running the Full Demo

```bash
cd claude-factory-rehearsal/
./run_demo.sh
```

This runs:
1. Runtime info check
2. Syntax validation
3. Dependency verification
4. Live demo with available backends

---

## Quick Reference

### Minimal Factory
```bash
uv run python 01_minimal_factory.py --backend {claude|codex|opencode} "task"
```

### Factory Catalog
```bash
uv run python 02_factory_catalog.py {analyzer|fixer|planner} --backend {backend} "task"
```

### Resumable Factory
```bash
uv run python 03_resumable_factory.py {start|resume} --backend {backend} "task"
```

### Spec Loop Factory
```bash
uv run python 04_spec_loop_factory.py --backend {backend} --spec spec.json [--max-iterations N]
```

---

## Key Takeaways

1. **Factories are policies:** Same agent, different behavior based on role
2. **Sessions enable continuity:** Resume work across multiple calls
3. **Spec-driven loops automate delivery:** Implement → Check → Review until done
4. **Backend agnostic:** Same factory code works with Claude, Codex, OpenCode
5. **No API keys needed:** Works with CLI subscriptions
