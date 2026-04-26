# Session 4: Software Factories + Retro
**Duration:** 2–3 hours | **Level:** Advanced

**Prerequisites:** Sessions 1-3 completed. Basic Python familiarity recommended.

**Goal:** Move from individual agent usage to repeatable AI software factory workflows and close the course with a structured retro.

**Theme:** Session 3 focused on building agent capability — planning, tools, memory, and delegation. Session 4 focuses on operationalizing that capability at team scale: why factories exist, how they're architected, real-world examples, role-based policies, spec-driven delivery loops, common failure modes, and explicit learnings capture from sessions 1-3.

**Materials:** `session-4-agentic/claude-factory-rehearsal/` — 3 rehearsals with working scripts for `claude`, `codex`, and `opencode` backends. No API keys required — works with CLI subscriptions.

**Documentation:** `session-4-agentic/AGENTS.md` — Factory framework configuration and reference.

**Core insight:**
> "Without factories, autonomous agents are just doing expensive vibe coding at scale. A software factory is a reusable policy wrapper around an agent loop: goal contract + tool policy + quality gates."

---

## Session Flow

| # | Type | Topic | Duration |
|---|------|-------|----------|
| 1 | — | Title & Objectives | — |
| 2 | THEORY | From Agents to Factories | 10 min |
| 3 | THEORY | What Is an AI Software Factory? | 10 min |
| 4 | THEORY | Factory Architecture (7 Layers) | 10 min |
| 5 | THEORY | AI Factories in the Wild | 10 min |
| 6 | **REHEARSAL 1** | **Minimal Factory** — single call, multiple backends | **15 min** |
| 7 | THEORY | Factory Roles & Policies | 10 min |
| 8 | **REHEARSAL 2** | **Role-Based Factories + Session Resume** | **15 min** |
| 9 | THEORY | Spec-Driven Delivery Loops | 10 min |
| 10 | **REHEARSAL 3** | **Spec Loop Factory** — implement/test/review cycle | **15 min** |
| 11 | THEORY | What Can Go Wrong | 10 min |
| 12 | DISCUSSION | Retro Framework (Sessions 1-3) | 15 min |
| 13 | THEORY | The Journey: Sessions 1-4 | 5 min |
| 14 | WRAP-UP | Session 4 Summary | 5 min |

**Total: ~2.5 hours** (65 min theory + 45 min rehearsal + 30 min retro/wrap-up)

---

## PART 1: WHY FACTORIES?

### 1. From Agents to Factories (10 min)
**The bridge from Session 3 to Session 4**

Session 3 gave you agents that can plan, use tools, remember, and delegate. But autonomous agents without structure create a new problem: **vibe coding at scale**.

The progression through this training:

```
Session 1: Vibe Coding         → Fast prototypes, unpredictable quality
Session 2: Discipline (SDD)    → Specs, TDD, auditable process
Session 3: Agents              → Autonomous tool-using loops
Session 4: Factories           → Agents + discipline at team scale
```

Without factories, you get:
- Agents that produce inconsistent output across runs
- No audit trail for decisions
- Prompt drift as team members customize independently
- Expensive compute with no quality guarantees

**Key insight:** Factories apply the same discipline Session 2 taught for human workflows — but to autonomous agent pipelines.

---

### 2. What Is an AI Software Factory? (10 min)
**Orchestrated pipelines where AI agents handle the SDLC**

> An AI software factory is an orchestrated pipeline where AI agents autonomously handle most of the software development lifecycle — coding, testing, debugging, code review, documentation — while humans provide strategic direction, architecture decisions, and final validation.

This is distinct from:
- **AI-assisted development** (Sessions 1-2): Human drives, AI helps
- **Autonomous agents** (Session 3): Single agent with tools
- **AI software factories** (Session 4): Multiple agents in a governed pipeline

Factory outcomes:
- Consistent quality across teams and runs
- Faster cycle time with less ad-hoc work
- Auditable decisions and traces
- Easier onboarding through standard flows
- Scalable: same factory pattern serves multiple projects

**The human role shifts:** from writing code to directing architecture, defining acceptance criteria, and validating outputs. Humans are factory operators, not assembly-line workers.

---

### 3. Factory Architecture — 7 Layers (10 min)
**The full stack of an AI software factory**

```
┌─────────────────────────────────────┐
│  7. Integration Layer               │  CI/CD, repos, issue trackers
├─────────────────────────────────────┤
│  6. Observability Layer             │  Logs, traces, cost tracking
├─────────────────────────────────────┤
│  5. Validation & Guardrails         │  Tests, hooks, approval gates
├─────────────────────────────────────┤
│  4. Memory & Context Layer          │  RAG, session state, learnings
├─────────────────────────────────────┤
│  3. Tools & Execution Layer         │  CLI, MCP, APIs, sandboxes
├─────────────────────────────────────┤
│  2. Agent Layer                     │  Planner, Builder, Reviewer...
├─────────────────────────────────────┤
│  1. Orchestration Layer             │  Spec intake, routing, loops
└─────────────────────────────────────┘
```

| Layer | Responsibility | Maps to Training |
|-------|---------------|------------------|
| 1. Orchestration | Spec intake, agent routing, loop control | S4: Spec-driven loops |
| 2. Agent | Role-based agents (planner, builder, reviewer) | S3: Agent loop, S4: Factory roles |
| 3. Tools & Execution | CLI commands, MCP servers, sandboxed execution | S3: MCP vs CLI |
| 4. Memory & Context | RAG retrieval, session persistence, learnings DB | S3: Memory + RAG |
| 5. Validation | Pre/post hooks, test gates, approval workflows | S2: TDD, S4: Quality gates |
| 6. Observability | Structured logs, cost tracking, decision traces | S4: Anti-patterns |
| 7. Integration | Git, CI/CD, issue trackers, deployment | S2: Audit step |

**Key point:** Sessions 1-3 built layers 2-5. Session 4 adds the orchestration, observability, and integration layers that turn agents into a factory.

---

### 4. AI Factories in the Wild (10 min)
**Real-world examples and productivity data**

#### Industry Examples

| Company | What They Built | Key Insight |
|---------|----------------|-------------|
| **Stripe** | "Minions" — agents triggered from Slack that produce PRs | Integration-first: meet devs where they work |
| **StrongDM** | AI handles all coding; humans only do roadmaps and architecture | Human role = direction + validation |
| **Cursor** | Automations — background agents for coding tasks | IDE-native factory pattern |
| **Factory.ai** | Dedicated AI software factory platform ($1.5B valuation) | Factory-as-a-service is a market category |

#### Productivity Numbers

- 30-70% productivity gains reported across early adopters
- 8-20× speedup on migration and boilerplate tasks
- AI-generated code approaching 50% of total output at some companies
- Biggest gains on well-specified, repetitive work — exactly what factories excel at

#### What This Means for Teams

The factory pattern isn't theoretical — it's being deployed at scale by companies building real products. The question isn't whether to adopt it, but how to do it safely and incrementally.

---

## PART 2: REHEARSALS

### Rehearsal 1 — Minimal Factory (15 min)
**Goal:** Show the smallest possible factory shape.

A factory accepts a task, a backend executes it, output comes back as one result. This is the "hello world" of factories — one agent, one call, structured input/output.

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

### 5. Factory Roles & Policies (10 min)
**Same backend, different policy → different behavior**

Factories are policies, not just prompts. A role defines:
- what the agent is allowed to do (tool permissions)
- what output format is expected (structured contracts)
- what constraints apply (safety boundaries)

Common factory roles:

| Role | Permissions | Output | Constraints |
|------|------------|--------|-------------|
| **Analyzer** | Read-only | Findings report | No modifications |
| **Planner** | Read-only | Step-by-step plan | No execution |
| **Fixer** | Read + write targeted files | Minimal diff | Scoped changes only |
| **Reviewer** | Read-only | Pass/fail + rationale | Against defined criteria |

**Key insight:** The same LLM backend behaves completely differently under different role policies. This is the core factory lever — you control agent behavior through policy, not prompt engineering.

---

### Rehearsal 2 — Role-Based Factories + Session Resume (15 min)
**Goal:** Show that factories are policies, and sessions can persist.

**Scripts:** `02_factory_catalog.py`, `03_resumable_factory.py`

```bash
# Analyzer: read-only analysis (produces detailed findings)
uv run python 02_factory_catalog.py analyzer --backend claude \
  "Analyze backend_runner.py. What design patterns does it use?"

# Planner: produces implementation plans (no edits)
uv run python 02_factory_catalog.py planner --backend opencode \
  "Create a 3-step plan to add logging to backend_runner.py"

# Fixer: makes actual code changes
uv run python 02_factory_catalog.py fixer --backend claude \
  "Add basic logging to backend_runner.py"

# Session resume (factory memory persists across calls)
uv run python 03_resumable_factory.py start --backend claude \
  "Remember: the magic number is 42"
uv run python 03_resumable_factory.py resume --backend claude \
  "What was the magic number?"
```

**Factory role policies:**
| Role | Allowed Tools | Permission Mode | Purpose |
|------|--------------|-----------------|---------|
| analyzer | Read, Glob, Grep, WebSearch | Read-only | Inspect and explain |
| planner | Read, Glob, Grep | Plan-only | Produce plans |
| fixer | Read, Glob, Grep, Edit, Bash | Accept edits | Make safe changes |

**Discussion points:**
- How does role policy change agent behavior?
- When would you use session resume vs fresh start?
- What state should persist between factory calls?

---

### 6. Spec-Driven Delivery Loops (10 min)
**Automation loop for real software work**

A spec-driven factory closes the loop between intent and verified output:

```
Spec (goal + checks + constraints)
  → Implement (agent writes code)
  → Test (deterministic checks run)
  → Review (agent evaluates quality)
  → Pass? → Release artifact
  → Fail? → Loop back to implement (up to max_iterations)
```

Spec components:
- `goal`: target outcome in plain language
- `checks`: deterministic local commands (tests, lints, type checks)
- `max_iterations`: safety limit to prevent infinite loops
- Optional: `implement_instructions`, `review_instructions`, `allowed_tools`

**Connection to Session 2:** This is the TDD cycle (Red → Green → Refactor) automated inside a factory. The spec replaces the human deciding "is this done?" with deterministic checks.

---

### Rehearsal 3 — Spec-Driven Delivery Loop (15 min)
**Goal:** Show the implement/test/review automation loop.

**Script:** `04_spec_loop_factory.py`
**Specs:** `spec.example.json` (syntax check), `spec.add-timeout.json` (real code changes)

```bash
# Run the spec loop - syntax validation
uv run python 04_spec_loop_factory.py --backend claude --spec spec.example.json

# Run spec that makes actual code changes
uv run python 04_spec_loop_factory.py --backend claude --spec spec.add-timeout.json
```

**Example spec format:**
```json
{
  "goal": "Add 120-second timeout to subprocess calls",
  "max_iterations": 3,
  "checks": [
    {"name": "syntax", "command": "{python} -m py_compile backend_runner.py"},
    {"name": "timeout-exists", "command": "grep -q 'wait_for' backend_runner.py"}
  ]
}
```

**Discussion points:**
- How does the loop decide when to stop?
- What happens when checks fail?
- Where does human review fit in?

---

## PART 3: FAILURE MODES & RETRO

### 7. What Can Go Wrong (10 min)
**Anti-patterns in AI software factories**

| Anti-Pattern | What Happens | Mitigation |
|-------------|-------------|------------|
| **Slop at Scale** | Factory produces high volumes of low-quality code that passes superficial checks | Meaningful test coverage, human review gates on critical paths |
| **Prompt Drift** | Team members customize prompts independently, factory behavior diverges | Version-controlled role policies, shared factory configs |
| **Bag-of-Agents** | Multiple agents without clear orchestration — they duplicate work or conflict | Explicit handoff contracts, single orchestration layer |
| **3 AM Liability** | Autonomous agents deploy changes overnight, nobody reviews until production breaks | Approval gates before deployment, observability alerts, human-in-loop for risky changes |
| **Missing Observability** | Factory runs but nobody knows what it did, how much it cost, or why it made decisions | Structured logging, cost tracking, decision traces |

**The meta-lesson:** Every productivity tool can become a liability multiplier. Factories need the same operational discipline as any production system.

---

### 8. Retro Framework (15 min)
**Close sessions 1-3 with evidence**

Retro prompts:
1. What gave the highest productivity gain?
2. Where did AI create risk or confusion?
3. Which rules/hooks should become default team policy?
4. What should we standardize as a reusable factory component?

Output artifacts:
- Top 5 learnings
- Top 3 policy changes
- First version of team factory playbook

---

## PART 4: WRAP-UP

### 9. The Journey: Sessions 1-4

| Session | Theme | Key Concept | You Built |
|---------|-------|-------------|-----------|
| **S1: Greenfield** | Proto Capability | Rules → Skills → Spec → TDD | Working prototype with TDD |
| **S2: Brownfield** | Hard Engineering | Document → Spec → Develop → Audit | Grounded spec + sub-agents |
| **S3: Agents** | Agent Engineering | Agent loop + CLI/MCP + RAG + memory | Custom agent with tools + memory |
| **S4: Factories** | Factory & Team Adoption | 7-layer architecture + spec loops + policies | Repeatable factory pipeline |

### The Progression

```
Session 1: Vibe Coding          → Individual skill (you + AI)
     ↓
Session 2: Spec-Driven Dev      → Structured process (4-step workflow)
     ↓
Session 3: Agent Engineering    → Autonomous agents (planning + tools + memory)
     ↓
Session 4: Software Factories   → Team systems (orchestration + policies + retro)
```

---

### 10. Session 4 Summary

By the end of Session 4, participants have:

1. Understood why agents need factory structure (vibe coding at scale problem)
2. Learned the 7-layer factory architecture and how Sessions 1-3 built layers 2-5
3. Seen real-world AI factory deployments and productivity data
4. Run minimal factories with multiple backends
5. Used role-based policies to control agent behavior
6. Built a spec-driven delivery loop
7. Identified common anti-patterns and their mitigations
8. Completed a structured retro for sessions 1-3

**Key takeaway:** Durable AI advantage comes from systems, not hero prompts. Factories turn individual agent capability into repeatable team delivery.

---

## Verified Test Results

All rehearsals tested and working with all 3 backends:

| Rehearsal | Claude | Codex | OpenCode | Real Output |
|-----------|--------|-------|----------|-------------|
| 01_minimal_factory | ✅ | ✅ | ✅ | Simple responses |
| 02_factory_catalog (analyzer) | ✅ | ✅ | ✅ | Code analysis with patterns identified |
| 02_factory_catalog (planner) | ✅ | ✅ | ✅ | Step-by-step implementation plans |
| 02_factory_catalog (fixer) | ✅ | ✅ | ✅ | Actual code modifications |
| 03_resumable_factory | ✅ | ✅ | ✅ | Session state persisted and recalled |
| 04_spec_loop_factory | ✅ | ✅ | ✅ | Implement → check → review loop |

**Example real code changes made during testing:**
- Analyzer: Produced 2000+ word code review with 20 specific improvements
- Fixer: Added logging to `backend_runner.py` (import + logger calls)
- Spec loop: Implemented 120-second subprocess timeout with proper error handling

---

## Setup for Rehearsals

**No API keys required** — all backends work with CLI subscriptions:
- `claude` → Claude Code subscription
- `codex` → Codex CLI subscription
- `opencode` → OpenCode subscription

```bash
cd session-4-agentic/claude-factory-rehearsal/

# Verify Python
uv run python -V

# Verify CLIs are installed and authenticated
claude --version   # Claude Code 2.x
codex --version    # codex-cli 0.x
opencode --version # opencode 1.x

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
| `backend_runner.py` | Backend adapter (claude, codex, opencode) with logging and timeout handling |
| `spec.example.json` | Syntax check spec for rehearsal 3 |
| `spec.add-timeout.json` | Example spec that implements actual code changes |
| `run_demo.sh` | Environment check + demo runner |
| `../AGENTS.md` | Factory framework documentation |

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
