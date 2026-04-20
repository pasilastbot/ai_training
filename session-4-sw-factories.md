# Session 4: Software Factories + Retro
**Duration:** 90 min | **Level:** Advanced

**Prerequisites:** Sessions 1-3 completed. Basic Python familiarity recommended.

**Goal:** Move from individual agent usage to repeatable software factory workflows and close the course with a structured retro.

**Theme:** Session 3 focused on building agent capability. Session 4 focuses on operationalizing that capability: factory anatomy, role-based policies, spec-driven delivery loops, and explicit learnings capture from sessions 1-3.

**Materials:** `session-4-agentic/claude-factory-rehearsal/` — 3 rehearsals with working scripts for `claude`, `codex`, and `opencode` backends.

**Core insight:**
> "A software factory is a reusable policy wrapper around an agent loop: goal contract + tool policy + quality gates."

---

## Session Flow

| # | Type | Topic | Duration |
|---|------|-------|----------|
| 1 | THEORY | What Is a Software Factory? | 10 min |
| 2 | THEORY | Factory Anatomy (Inputs → Pipeline → Gates → Outputs) | 10 min |
| 3 | **REHEARSAL 1** | **Minimal Factory** — single call, multiple backends | **10 min** |
| 4 | THEORY | Factory Roles & Policies | 5 min |
| 5 | **REHEARSAL 2** | **Role-Based Factories + Session Resume** | **15 min** |
| 6 | THEORY | Spec-Driven Delivery Loops | 5 min |
| 7 | **REHEARSAL 3** | **Spec Loop Factory** — implement/test/review cycle | **15 min** |
| 8 | DISCUSSION | Retro and Learnings (Sessions 1-3) | 15 min |
| 9 | WRAP-UP | Key takeaways + next steps | 5 min |

**Total: 90 min** (30 min theory + 40 min rehearsal + 20 min retro/wrap-up)

---

## PART 1: SOFTWARE FACTORY FOUNDATIONS

### 1. What Is a Software Factory? (10 min)
**From one-off prompts to repeatable delivery**

A software factory is a repeatable pipeline where AI agents and humans collaborate through defined stages, guardrails, and artifacts.

Factory outcomes:
- consistent quality across teams
- faster cycle time with less ad-hoc work
- auditable decisions and traces
- easier onboarding through standard flows

---

### 2. Anatomy of a Modern AI Software Factory (10 min)
**Inputs -> Pipeline -> Gates -> Outputs -> Learnings**

```
Intake (request/spec)
  -> Planning agent
  -> Build agent
  -> Test/review agent
  -> Verification gates (hooks, policies)
  -> Release artifact
  -> Retro + learnings
```

| Layer | Responsibility | Typical Artifact |
|------|----------------|------------------|
| Intake | Define goal and constraints | Spec, acceptance criteria |
| Execution | Implement through agents/tools | Code, tests, docs |
| Control | Enforce safety and quality | Hook logs, approvals, checks |
| Feedback | Capture outcomes and improvements | Retro notes, playbook updates |

---

## PART 2: REHEARSALS

### Rehearsal 1 — Minimal Factory (10 min)
**Goal:** Show the smallest possible factory shape.

A factory accepts a task, a backend executes it, output comes back as one result.

**Script:** `01_minimal_factory.py`

```bash
cd session-4-agentic/claude-factory-rehearsal/

# Run with different backends
uv run python 01_minimal_factory.py --backend claude "Summarize this project"
uv run python 01_minimal_factory.py --backend codex "Summarize this project"
uv run python 01_minimal_factory.py --backend opencode "Summarize this project"
```

**Discussion points:**
- What's the difference between calling an LLM vs calling a factory?
- How does the backend choice affect the result?
- Where would you add quality gates?

---

### 3. Factory Roles & Policies (5 min)
**Same backend, different policy → different behavior**

Factories are policies, not just prompts. A role defines:
- what the agent is allowed to do
- what output format is expected
- what constraints apply

Common factory roles:
- **Analyzer:** read-only, produces findings
- **Planner:** produces step-by-step plans
- **Fixer:** makes targeted changes to resolve issues
- **Reviewer:** evaluates work against criteria

---

### Rehearsal 2 — Role-Based Factories + Session Resume (15 min)
**Goal:** Show that factories are policies, and sessions can persist.

**Scripts:** `02_factory_catalog.py`, `03_resumable_factory.py`

```bash
# Different roles, same backend
uv run python 02_factory_catalog.py analyzer --backend codex "Find likely risk areas"
uv run python 02_factory_catalog.py planner --backend claude "Create implementation plan"
uv run python 02_factory_catalog.py fixer --backend opencode "Fix the auth bug"

# Session resume (factory memory)
uv run python 03_resumable_factory.py start --backend opencode "Inspect auth flow"
uv run python 03_resumable_factory.py resume --backend opencode "Continue and propose fixes"
```

**Discussion points:**
- How does role policy change agent behavior?
- When would you use session resume vs fresh start?
- What state should persist between factory calls?

---

### 4. Spec-Driven Delivery Loops (5 min)
**Automation loop for real software work**

A spec-driven factory:
1. Reads a delivery specification (goal, checks, constraints)
2. Runs loop: implement → checks → review
3. Repeats until approved or max iterations reached

Spec components:
- `goal`: target outcome
- `checks`: deterministic local commands (tests, lints)
- `max_iterations`: safety limit
- Optional: `implement_instructions`, `review_instructions`, `allowed_tools`

---

### Rehearsal 3 — Spec-Driven Delivery Loop (15 min)
**Goal:** Show the implement/test/review automation loop.

**Script:** `04_spec_loop_factory.py`  
**Spec:** `spec.example.json`

```bash
# Run the spec loop
uv run python 04_spec_loop_factory.py --backend codex --spec spec.example.json

# Edit spec.example.json to customize:
# - goal
# - checks (test commands)
# - max_iterations
```

**Discussion points:**
- How does the loop decide when to stop?
- What happens when checks fail?
- Where does human review fit in?

---

## PART 3: RETRO + WRAP-UP

### 5. Retro and Learnings Session (15 min)
**Close sessions 1-3 with evidence**

Retro prompts:
1. What gave the highest productivity gain?
2. Where did AI create risk or confusion?
3. Which rules/hooks should become default team policy?
4. What should we standardize as a reusable factory component?

Output artifacts:
- top 5 learnings
- top 3 policy changes
- first version of team factory playbook

---

### Session 4 Wrap-Up (5 min)
**From personal AI usage to team delivery system**

By the end of Session 4, participants have:
1. Understood factory anatomy (intake → execution → control → feedback)
2. Run minimal factories with multiple backends
3. Used role-based policies to control agent behavior
4. Built a spec-driven delivery loop
5. Completed a structured retro for sessions 1-3

**Key takeaway:** Durable AI advantage comes from systems, not hero prompts.

---

## Complete Course Summary

### The Journey: Sessions 1-4

| Session | Theme | Key Concept | You Built |
|---------|-------|-------------|-----------|
| **S1: Greenfield** | Proto capability | Rules → Skills → Spec → TDD | Working app with TDD |
| **S2: Brownfield** | Production discipline | Document → Spec → Develop → Audit | Grounded spec + sub-agents |
| **S3: Agents** | Tool-using autonomy | Agent loop + CLI/MCP + RAG | Custom agent with guardrails |
| **S4: Factories** | Team delivery systems | Policy wrappers + spec loops | Repeatable factory pipeline |

### The Progression

```
Session 1: Individual skill (you + AI)
     ↓
Session 2: Structured process (4-step workflow)
     ↓
Session 3: Autonomous agents (planning + tools + memory)
     ↓
Session 4: Team systems (factories + policies + retro)
```

### Core Artifacts Created

| Artifact | Session | Purpose |
|----------|---------|---------|
| AGENTS.md / CLAUDE.md | S1 | Codebase constitution |
| Skills documentation | S1 | Discoverable capabilities |
| content-plan.md | S2 | Documentation index |
| 3-tier docs | S2 | AI-navigable documentation |
| Sub-agent definitions | S2 | Specialized workflow roles |
| gemini_agent.py (extended) | S3 | Custom tool-using agent |
| Guardrails | S3-S4 | Safety constraints |
| Factory scripts | S4 | Repeatable pipelines |
| spec.json | S4 | Automated delivery specs |
| learnings.md | S2-S4 | Team knowledge base |

### The Full Workflow

```
Rules → Skills → Document → Spec → TDD → Agent → Factory → Retro
  S1      S1        S2       S2     S1-2    S3       S4      S4
```

---

## Setup for Rehearsals

```bash
cd session-4-agentic/claude-factory-rehearsal/

# Verify Python
uv run python -V

# Verify CLIs (if using codex/opencode backends)
codex --version
opencode --version

# Set API keys if needed
export ANTHROPIC_API_KEY=your_key_here
export OPENAI_API_KEY=your_key_here

# Run all demos
./run_demo.sh
```

---

## Files in the Rehearsal Pack

| File | Purpose |
|------|---------|
| `01_minimal_factory.py` | Single factory call |
| `02_factory_catalog.py` | Role-based factory policies (analyzer/planner/fixer) |
| `03_resumable_factory.py` | Session continuation (start/resume) |
| `04_spec_loop_factory.py` | Implement/test/review loop |
| `backend_runner.py` | Backend adapter (claude, codex, opencode) |
| `spec.example.json` | Editable spec for rehearsal 3 |
| `run_demo.sh` | Environment check + demo runner |

---

## Next Steps After Training

### Immediate (This Week)
1. Choose one real workflow to convert into a factory pilot.
2. Pick a factory role (analyzer, planner, fixer) and run 2-3 real tasks.
3. Create your first `spec.json` for an automated delivery loop.

### Short-term (This Month)
1. Add org-level guardrails to your spec checks.
2. Standardize handoff formats between factory roles.
3. Measure cycle time, quality defects, and rework.

### Long-term (This Quarter)
1. Scale the factory pattern across multiple teams.
2. Publish a shared factory playbook and starter kit.
3. Continuously improve from retro data and production incidents.
