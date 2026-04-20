# Session 4: Software Factories + Retro

**90 min | Advanced | "From Agents to Systems"**

Move from individual agent usage to repeatable software factory workflows. Build factories with role-based policies, session resume, and spec-driven delivery loops.

---

## Prerequisites

- Python 3.10+
- `uv` package manager (recommended)
- API keys for backends you want to use:
  - `ANTHROPIC_API_KEY` for Claude
  - `OPENAI_API_KEY` for Codex/OpenCode

## Quick Start

```bash
cd claude-factory-rehearsal/

# Verify setup
uv run python -V

# Run a minimal factory
uv run python 01_minimal_factory.py --backend claude "Summarize this project"
```

---

## Session Flow

| # | Type | Topic | Duration |
|---|------|-------|----------|
| 1 | Theory | What Is a Software Factory? | 10 min |
| 2 | Theory | Factory Anatomy | 10 min |
| 3 | **Rehearsal 1** | Minimal Factory | 10 min |
| 4 | Theory | Factory Roles & Policies | 5 min |
| 5 | **Rehearsal 2** | Role-Based + Session Resume | 15 min |
| 6 | Theory | Spec-Driven Delivery Loops | 5 min |
| 7 | **Rehearsal 3** | Spec Loop Factory | 15 min |
| 8 | Discussion | Retro (Sessions 1-3) | 15 min |
| 9 | Wrap-up | Key takeaways | 5 min |

**Total: 90 min**

---

## Rehearsals

All rehearsal scripts are in `claude-factory-rehearsal/`:

### Rehearsal 1: Minimal Factory
```bash
uv run python 01_minimal_factory.py --backend claude "Summarize this project"
```

### Rehearsal 2: Role-Based + Resume
```bash
uv run python 02_factory_catalog.py analyzer --backend codex "Find risks"
uv run python 03_resumable_factory.py start --backend opencode "Inspect auth"
uv run python 03_resumable_factory.py resume --backend opencode "Propose fixes"
```

### Rehearsal 3: Spec-Driven Loop
```bash
uv run python 04_spec_loop_factory.py --backend codex --spec spec.example.json
```

---

## Key Files

| File | Purpose |
|------|---------|
| `claude-factory-rehearsal/` | Main rehearsal scripts |
| `claude-factory-rehearsal/spec.example.json` | Editable spec for loop factory |
| `claude-factory-rehearsal/backend_runner.py` | Backend adapter |

---

## Core Insight

> "A software factory is a reusable policy wrapper around an agent loop: goal contract + tool policy + quality gates."
