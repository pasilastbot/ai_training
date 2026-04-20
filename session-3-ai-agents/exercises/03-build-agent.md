# Exercise 3: Build the Agent

**Duration:** 15 min | **Type:** Team Build

---

## Goal

Combine your tool (Exercise 1) and memory skill (Exercise 2) into a working agent with UI, guardrails, and subagents.

---

## Prerequisites

- Tool from Exercise 1
- RAG memory skill from Exercise 2
- `gemini_agent.py` as the base

---

## Agent Architecture

Your agent has six layers:

| Layer | What it does |
|-------|-------------|
| **UI Layer** | Chat interface, shows agent thinking + tool calls |
| **Agent Loop** | Observe → Plan → Act → Evaluate → Store |
| **Tool Registry** | Your tools from Exercise 1 + built-ins |
| **RAG Memory** | Your skill from Exercise 2 |
| **Subagents** | Specialists for review, test, doc generation |
| **Guardrails** | Blocked patterns, approval gates, safety limits |

---

## Step 1: Plan Your Agent (5 min team discussion)

Before building, answer these questions:

### Use Case
What real workflow will your agent automate?
- PR review pipeline?
- Deploy checklist?
- Incident triage?
- Onboarding automation?

### Tools
- Which CLI tools will it use?
- Which tool from Exercise 1?
- What APIs to integrate?

### Memory
- What will you embed? (decisions, errors, patterns?)
- What triggers retrieval?
- What stays ephemeral?

### Guardrails
- What patterns should be blocked? (`rm -rf`, `drop table`, etc.)
- What requires human approval?
- What are the stop conditions?

### Subagents
- Which tasks to delegate?
- `review-agent` for code review?
- `test-agent` for test generation?
- `doc-agent` for documentation?

---

## Step 2: Build Checklist

Work through these in order:

### 2.1 Start from gemini_agent.py

```bash
cd session-3-ai-agents/
python gemini_agent.py --chat
```

Verify it works before modifying.

### 2.2 Integrate Your Tool (Exercise 1)

Add your tool to the agent:

1. Add function declaration in `build_cli_function_declarations()`
2. Add execution handler in `execute_cli_function()`
3. Test: ask the agent to use your tool

### 2.3 Integrate RAG Memory (Exercise 2)

Add your memory skill:

1. Import your memory functions
2. Add to the tool registry (as a callable tool)
3. Test: store something, then ask a question that should retrieve it

### 2.4 Add Guardrails

Protect against dangerous operations:

```python
BLOCKED_PATTERNS = [
    "rm -rf",
    "drop table", 
    "delete from",
    "format",
    "--force",
]

def is_blocked(args):
    args_str = json.dumps(args).lower()
    return any(p in args_str for p in BLOCKED_PATTERNS)
```

Add to each tool handler:
```python
if is_blocked(args):
    return {"ok": False, "error": "Blocked: potentially destructive"}
```

### 2.5 Add Subagent Delegation (Optional)

If time permits, add subagent definitions:

```python
SUBAGENTS = {
    "review-agent": "You are a code review specialist. Focus on security, performance, and maintainability.",
    "test-agent": "You are a test generation specialist. Write comprehensive unit and integration tests.",
    "doc-agent": "You are a documentation specialist. Write clear, concise documentation.",
}
```

---

## Step 3: Test Your Agent

Run through these scenarios:

1. **Basic chat** — Does the agent respond?
2. **Tool use** — Ask it to use your custom tool
3. **Memory** — Store something, then ask about it
4. **Guardrail** — Try a blocked operation (should refuse)
5. **End-to-end** — Run your planned use case

```bash
python gemini_agent.py --chat

> Use my-tool to check something
> Remember: always validate inputs
> What should I remember about validation?
> Delete all files (should be blocked)
```

---

## Checkpoint

After 15 minutes, each team should have:

- [ ] Working agent (chat mode)
- [ ] Custom tool integrated (from Ex 1)
- [ ] RAG memory integrated (from Ex 2)
- [ ] At least one guardrail active
- [ ] Tested at least 3 scenarios

---

## Demo (Optional)

If time permits, each team demos:
1. Their use case
2. Their custom tool in action
3. Memory storing + retrieval
4. A blocked operation being refused

---

## Output

**Working agent per team** with:
- Tools from Exercise 1
- RAG memory from Exercise 2
- Guardrails
- (Optional) Subagent delegation
