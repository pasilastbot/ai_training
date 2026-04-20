# Software Factory Training Rehearsals

This folder is designed for live training. It demonstrates how to move from a
single-agent "factory" call to a spec-driven implementation loop.

Core idea for participants:

"A software factory is a reusable policy wrapper around an agent loop:
goal contract + tool policy + quality gates."

## Training flow (3 rehearsals)

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

---

## Setup for training session

1. Use project Python (recommended):

```bash
uv run python -V
```

2. Verify CLIs:

```bash
codex --version
opencode --version
```

3. If needed, set API keys (CLI auth sessions may already be enough):

```bash
export ANTHROPIC_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here
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
- `backend_runner.py` - backend adapter (`claude`, `codex`, `opencode`)
- `spec.example.json` - editable loop specification
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
