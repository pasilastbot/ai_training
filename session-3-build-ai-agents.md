# Session 3: Develop AI Agents with AI
**Duration:** 90 min | **Level:** Advanced

**Prerequisites:** Session 1 (Greenfield) and Session 2 (Brownfield, Sub-Agents)

**Goal:** Design, build, and rehearse practical AI agents that use tools, memory, and retrieval.

**Theme:** Sessions 1-2 taught skills, sub-agents, and the spec-driven workflow. Session 3 upgrades sub-agents into full agents: what agents are, how the agent loop works, when to use CLI vs MCP tools, how to build your own tools with the AGENTS.md "invent" workflow, and how RAG-backed memory turns a one-shot assistant into a learning system. The session builds up all the pieces (tools, memory, RAG) before teams combine them into a full agent.

---

## Session Flow

| # | Type | Topic | Duration |
|---|------|-------|----------|
| 1 | THEORY | What Is an AI Agent? | 5 min |
| 2 | THEORY | The Agent Loop | 5 min |
| 3 | THEORY | Core Agent Capabilities | 5 min |
| 4 | THEORY | MCP vs CLI Tools | 10 min |
| 5 | **EXERCISE 1** | Invent a Tool (AGENTS.md workflow) | 10 min |
| 6 | THEORY | Memory Patterns for Agents | 5 min |
| 7 | THEORY | RAG for Agents | 10 min |
| 8 | **EXERCISE 2** | RAG-Backed Memory Skill | 10 min |
| 9 | PLANNING | Plan Your Agent (teams) | 5 min |
| 10 | **EXERCISE 3** | Build the Agent (UI + delegation + subagents) | 15 min |
| | WRAP-UP | Session summary | 5 min |

**Total: ~90 min** (40 min theory + 45 min hands-on + 5 min wrap-up)

---

## PART 1: AGENT FOUNDATIONS

### 1. What Is an AI Agent? (5 min)
**From sub-agents to autonomous agents**

Session 2 introduced **sub-agents** (Doc Agent, Spec Agent, Review Agent) — specialized roles with Can/Cannot boundaries. Now we upgrade to **full agents**:

> An AI agent is an LLM loop that can plan steps, call tools, store useful state, and continue until a goal is complete.

#### Sub-Agent vs Agent

| Aspect | Sub-Agent (S2) | Full Agent (S3) |
|--------|----------------------|------------------------|
| Scope | Single workflow step | End-to-end goal |
| Tools | Read/write files | CLI, APIs, search, code exec |
| Memory | Session context | Persistent across runs |
| Autonomy | Human triggers each step | Plans and executes independently |

---

### 2. The Agent Loop (5 min)
**Observe → Plan → Act → Evaluate → Store**

```
Goal
  → Observe context
  → Plan next step
  → Act with tools
  → Evaluate result
  → Store learnings
  → Continue or stop
```

Each step maps to a concrete component: Observe reads context, Plan chooses the next action, Act executes with tools, Evaluate checks the result, Store saves learnings for future runs.

**Design principle:** Every loop should be auditable. If you cannot explain why the agent took an action, the agent is not production-ready.

---

### 3. Core Agent Capabilities (5 min)
**The four pillars of agent engineering**

| Capability | What It Means |
|------------|---------------|
| **Planning** | Breaks goals into next actions |
| **Tool Use** | Runs commands, APIs, structured operations |
| **Memory** | Remembers context, outcomes, reusable patterns |
| **Delegation** | Hands off subtasks to specialist agents |

**Progression across sessions:**

Skills (S1) → Sub-Agents (S2) → Full Agents (S3) → Factories (S4)

---

## PART 2: TOOLS

### 4. MCP vs CLI Tools (10 min)
**Pick the right interface for each task**

#### CLI Tools

**Pros:**
- 30%+ better token efficiency
- Unix-style composability
- Human-readable debugging
- Mature ecosystem

**Cons:**
- Can hallucinate syntax
- Harder for stateful tasks
- Platform-dependent

#### MCP Tools

**Pros:**
- Type-safe JSON schemas
- Complex integrations
- Human-in-loop approvals
- Growing ecosystem

**Cons:**
- Context bloat
- Operational complexity
- Often worse in benchmarks

**Rule of thumb:** CLI outperforms for existing tools. MCP for specialized/secure workflows.

---

### EXERCISE 1: Invent a Tool (10 min)
**Use the AGENTS.md "invent" workflow**

AGENTS.md contains a pre-built `invent` workflow that instructs the AI to implement, test, and document a new CLI tool from a single prompt.

**The Prompt:**

```
Invent a new tool: [your tool description]
```

The AI handles the rest — it implements the tool, writes tests, and generates documentation.

**Tool ideas:**
- A CLI tool that summarizes git commits since last release
- A tool that checks broken links in markdown files
- A tool that generates a dependency graph for a project
- A tool that monitors API response times

**What to observe:**
- How does the AI decompose the task?
- Does it plan before coding?
- Does it test its own output?

---

## PART 3: MEMORY + RAG

### Memory Patterns for Agents (5 min)
**Short-term context vs durable memory**

| Memory Type | Scope | Typical Use |
|------------|-------|-------------|
| **Working memory** | Current task/session | Keep immediate plan and observations |
| **Episodic memory** | Past runs | Reuse successful strategies, avoid repeated mistakes |
| **Knowledge memory** | Indexed docs/data | Answer with grounded evidence (RAG) |

**Good baseline:**
- Keep short-term memory lightweight
- Persist only high-value learnings
- Tag memory with source + timestamp to reduce stale context

---

### RAG for Agents (10 min)
**Retrieval as long-term factual memory**

```
Documents → Chunk → Embed → Store (ChromaDB)
Query → Retrieve top-K → Augment prompt → Agent reasons → Grounded answer
```

**What changes when RAG is inside an agent:**
- Retrieval becomes a **tool call** in the plan
- Memory and retrieval **complement** each other
- Answers become **traceable**, not just plausible

| Approach | Characteristics |
|----------|-----------------|
| Plain LLM | May hallucinate, uses training data only |
| RAG Query | Grounded in indexed content |
| Agent + RAG | Decides when to retrieve, combines with tools |

---

### EXERCISE 2: RAG-Backed Memory Skill (10 min)
**Build memory on top of the RAG pipeline**

This exercise ties memory to the RAG pipeline we just covered. Students prompt AI to create a skill that embeds knowledge into a vector store and retrieves it with semantic search.

**The Prompt:**

```
Create a RAG-backed memory skill: [your description]
```

AI generates the complete skill: embed + store to vector DB on trigger, semantic retrieve on recall.

**Skill ideas (all RAG-backed):**

| Skill | What it does |
|-------|-------------|
| `remember-learnings` | Embed lessons learned → retrieve similar past insights when facing new problems |
| `project-context` | Index project docs (stack, conventions) → semantic search for grounded answers |
| `decision-log` | Embed architectural decisions + rationale → query "why did we choose X?" |
| `error-patterns` | Embed bug reports + fixes → auto-retrieve matching solutions for new errors |

**Memory + RAG:** You describe the memory pattern. The AI builds the embed/store/retrieve skill.

---

## PART 4: BUILD THE AGENT

### Plan Your Agent (5 min)
**Work in teams — design an agent for a real workflow**

Now you have all the building blocks: tools (Exercise 1), memory + RAG (Exercise 2), and the agent loop theory. Before building, plan the design.

**Step 1: Pick a Use Case** — Choose a real workflow from your team's daily work. Examples: PR review, deploy pipeline, incident triage, onboarding checklist.

**Step 2: Define Tools** — Which CLI/MCP tools? Which ones from Exercise 1? What new tools are needed? What APIs to integrate?

**Step 3: Design Memory** — RAG-backed memory from Exercise 2. What to embed? What retrieval triggers? What to keep ephemeral?

**Also define:**
- **Guardrails:** blocked patterns, stop conditions, approval gates
- **Subagents:** which tasks to delegate to specialist agents? (e.g., review-agent, test-agent, doc-agent)

---

### EXERCISE 3: Build the Agent (15 min)
**Teams build from `gemini_agent.py` — UI + tools + memory + delegation**

Use your plan from the previous step. The agent architecture has six layers:

| Layer | What it does |
|-------|-------------|
| **UI Layer** | Chat interface, tool output display |
| **Agent Loop** | Observe → Plan → Act → Evaluate |
| **Tool Registry** | Your tools from Exercise 1 + built-ins |
| **RAG Memory** | Your skill from Exercise 2 |
| **Subagents** | Delegate: review, test, doc generation |
| **Guardrails** | Blocked patterns, approval gates |

**Build checklist:**

1. **UI** — Chat UI that shows agent thinking + tool calls
2. **Tools + Memory** — Integrate tools from Exercise 1 + RAG memory from Exercise 2
3. **Safety** — Add guardrails: blocked patterns, approvals
4. **Delegation** — Generate subagents: review-agent, test-agent, etc.

```bash
python gemini_agent.py --chat
```

**Output:** Working agent per team — tools + RAG memory + subagents + guardrails.

---

## Session 3 Summary (5 min)

By the end of Session 3, participants have:

1. Understood agent foundations: the agent loop, planning, and core capabilities
2. Chosen CLI vs MCP with clear tradeoffs (pros/cons)
3. Invented a custom tool using the AGENTS.md workflow
4. Created a RAG-backed memory skill (embed + store + retrieve)
5. Planned and built a full agent as a team (UI + tools + memory + subagents)

**Key takeaway:** AI agents are not "just prompts." They are engineered loops with planning, tools, memory, and verification.

---

## Preparation for Session 4

Before Session 4:
1. Keep one working agent from this session as your baseline
2. Bring one real team workflow that should become a "software factory flow"
3. Capture top lessons from sessions 1-3 for the retro discussion
