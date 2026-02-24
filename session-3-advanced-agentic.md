# Session 3: Advanced Agentic Workflows
**Duration:** 90 min | **Level:** Advanced

**Prerequisites:** Session 1 (Greenfield) & Session 2 (Brownfield)

**Goal:** Scale with agents, custom tools, and multi-agent pipelines

**Theme:** You've built from zero (Session 1) and tamed existing code (Session 2). Now we scale: build custom tools, wrap them as skills, configure specialized agents, and wire it all together. From manual work to automated pipeline.

**Rehearsal projects:** 3 alternatives in `github.com/pasilastbot/ai_training` — Code Review Pipeline, Documentation Generator, or Test Suite Generator.

---

## PART 1: TOOLS

### 1. MCP vs CLI Tools (5 min)
**When to use Model Context Protocol vs command-line tools**

AI agents interact with external systems in two ways:

| Factor | CLI | MCP |
|--------|-----|-----|
| Token efficiency | Better (30%+) | Schema bloat |
| Setup effort | Low | Medium-High |
| Debugging | Easy (stdout) | Harder |
| Type safety | Text-based | JSON schemas |
| Stateful tasks | Harder | Better |
| Security controls | Manual | Built-in |

**The verdict:** CLI frequently outperforms MCP for speed and stability, especially when tools already exist as CLIs.

**The pattern:**
- If a good CLI exists → Use CLI (git, npm, docker, aws)
- If task needs browser/stateful/secure workflows → Consider MCP
- If reimplementing CLI as MCP → Usually counterproductive

---

### 2. MCP Integrations (5 min)
**GitHub, Slack, databases, custom servers**

Common MCP servers and when they make sense:

| Server | Purpose | Key Operations |
|--------|---------|----------------|
| **GitHub** | Code hosting | PRs, issues, repos, actions |
| **Slack** | Communication | Send messages, read channels |
| **Database** | Data access | Query, insert, update |
| **Browser** | Web automation | Navigate, click, screenshot |

MCP connects AI agents to external systems with a standardized protocol. Custom MCP servers can expose internal tools with approval flows and access controls.

---

### 3. Inventing CLI Tools (5 min)
**Need → Script → Test → Register**

When you find yourself repeating a task, automate it:

1. **NEED** — Identify a repetitive task (you do it more than 3 times)
2. **SCRIPT** — Write it in TypeScript/Python/Bash
3. **TEST** — Verify it works with real data
4. **REGISTER** — Add to package.json and document for AI

```bash
# Example: register in package.json
"scripts": {
  "analyze-complexity": "tsx tools/analyze-complexity.ts"
}
```

Once documented in AGENTS.md, AI can use your custom tools automatically.

---

### REHEARSAL: Pick Your Target (10 min)
**Clone the repo, explore the codebase**

```bash
git clone https://github.com/pasilastbot/ai_training
cd ai_training/session-3-agentic/
```

**Pick one of 3 alternatives:**

| Target | What You're Working With | Your Job |
|--------|------------------------|----------|
| **A) Code Review** | Sample PR diffs with security issues and quality problems | Build tools to catch them |
| **B) Doc Generator** | Undocumented Node.js app (~300 lines). Zero docs, zero comments | Build tools to document it |
| **C) Test Generator** | Working app with 0% test coverage | Build tools to test it |

**First task:** Explore the target codebase and understand what you're working with. What patterns do you see? What would you automate?

---

### BUILD: Create Your CLI Tool (10 min)
**Build a custom tool for your pipeline**

Using `prompts/02-cli-tool.md`:

1. Identify a repetitive task in your chosen pipeline
2. Write & test the script from the provided template
3. Verify it works standalone with real data

**Examples by pipeline:**
- Code Review: `check-security.sh` — scans for SQL injection / XSS patterns
- Doc Generator: `analyze-deps.sh` — extracts import/dependency graph
- Test Generator: `coverage-check.sh` — runs tests and reports coverage %

---

## PART 2: SKILLS

### 4. Skills vs Sub-Agents vs Hooks (5 min)
**What / Who / When — the three mechanisms**

Three complementary mechanisms for agentic workflows:

| Mechanism | Role | Analogy |
|-----------|------|---------|
| **SKILLS** = WHAT | Capabilities — add abilities like search, APIs, custom tools | Superpowers |
| **SUB-AGENTS** = WHO | Specialists — delegate to focused experts | Team members |
| **HOOKS** = WHEN | Control — verify before/after actions | Quality gates |

Skills are the foundation: they give agents abilities. Sub-agents organize those abilities into roles. Hooks verify the results.

---

### 5. Agent Skills (5 min)
**Web search, file operations, code analysis, external APIs**

Skills are pluggable capabilities that extend what an AI agent can do. A skill wraps a tool so AI can discover and use it.

| Category | Examples | Use Cases |
|----------|----------|-----------|
| **Web Search** | Google, docs search | Research, API lookups |
| **File Operations** | Read, write, search | Code navigation |
| **Code Analysis** | AST parsing, deps | Understanding codebases |
| **External APIs** | GitHub, Slack, Jira | Integrations |
| **Custom Tools** | Your scripts | Domain-specific ops |

**The key insight:** The CLI tool you just built is useful — but AI can't find it on its own. A skill makes your tool discoverable and usable by AI. It's the bridge between "I wrote a script" and "AI uses my script."

---

### BUILD: Wrap Your Tool as a Skill (10 min)
**Register, document, test**

Using `prompts/03-skill.md`:

1. **Register** the tool in CLAUDE.md / AGENTS.md
   - Document the command, parameters, and expected output
2. **Add usage examples**
   - Show AI how and when to invoke your skill
3. **Test it** — ask AI to use your new skill
   - Verify it discovers and runs the tool correctly

**Example registration in AGENTS.md:**
```markdown
## Custom Skills

### check-security
**Command:** `bash tools/check-security.sh <file-or-dir>`
**Purpose:** Scan code for common security vulnerabilities
**Output:** JSON list of findings with severity and line numbers
**When to use:** Before approving any code review
```

---

## PART 3: SUB-AGENTS

### 6. Agentic Architecture (5 min)
**Assistant → Tool User → Agent → Multi-Agent**

AI coding tools exist on an autonomy spectrum:

| Level | What It Does | Best For | Risk |
|-------|-------------|----------|------|
| **Assistant** | Answers questions | Learning, exploration | None |
| **Tool User** | Executes commands you request | Precise edits | Low |
| **Agent** | Plans & executes multi-step | Well-scoped features | Medium |
| **Multi-Agent** | Coordinates specialists | Large refactors, audits | High |

**Rule of thumb:** Start at Tool User level. Graduate to Agent for tasks with clear boundaries. Use Multi-Agent only for well-defined, reversible operations.

---

### 7. Specialized Sub-Agents (5 min)
**Spec writer, test generator, code reviewer**

Instead of one general-purpose agent, create a "pod" of specialists:

```
┌─────────────────────────────────────────────────────┐
│                  DEVELOPMENT POD                     │
├────────────────┬────────────────┬────────────────────┤
│  Spec Writer   │ Test Generator │   Code Reviewer    │
│                │                │                    │
│ Creates specs  │ Writes tests   │ Checks quality,    │
│ from           │ from specs     │ security, patterns │
│ requirements   │                │                    │
└────────────────┴────────────────┴────────────────────┘
```

Each agent has:
- A **role** — what it does (and what it does NOT do)
- **Constraints** — what files it can touch, what tools it can use
- **Permissions** — what requires approval
- **Hooks** — verification after actions

AGENTS.md defines who does what.

---

### BUILD: Define Your Agents (10 min)
**AGENTS.md with roles, permissions, and hooks**

Using `prompts/04-agents.md`:

1. **Define 3-4 specialized sub-agents** with responsibilities
2. **Configure permissions** — what each agent can and cannot do
3. **Add hooks** — verification gates for critical actions

**Example for Code Review Pipeline:**
```markdown
## Agents

### Security Reviewer
**Role:** Analyze code for security vulnerabilities
**Skills:** check-security (your custom skill)
**Can:** Read files, run security scan
**Cannot:** Modify files, approve PRs
**Hook:** PostToolUse — log all findings

### Quality Reviewer
**Role:** Check code quality and patterns
**Can:** Read files, run linter
**Cannot:** Modify files
```

---

## PART 4: HOOKS & SCALING

### 8. Hooks & Verification (5 min)
**PostToolUse, Stop hooks, permission management**

Hooks are quality gates that run automatically:

| Hook | When It Runs | Purpose |
|------|--------------|---------|
| **PreToolUse** | Before any tool | Approve dangerous operations |
| **PostToolUse** | After tool completes | Verify results, log actions |
| **Stop** | Agent completes task | Final review before "done" |

**Key patterns:**
- Require approval for file deletions, env changes, deployments
- Log all tool uses for audit trail
- Run tests before marking any task complete
- Max 3 retry attempts before asking for human help

Hooks prevent agents from going off the rails. They're configured in AGENTS.md alongside agent definitions.

---

### 9. Scaling Across Teams (5 min)
**Shared agents, centralized docs, metrics**

Going from individual AI use to team-wide adoption:

```
Organization Level: Shared AGENTS.md (org-wide standards)
         │
    ┌────┼────┐
    ▼    ▼    ▼
 Team A  B    C Rules (team-specific)
    │    │    │
    ▼    ▼    ▼
 Project Rules (repo-specific)
```

**Track AI effectiveness:**
- Efficiency: time to first PR, AI assist ratio
- Quality: first-pass success rate, test coverage delta
- Team: adoption rate, knowledge sharing

---

### Session 3 Wrap-Up (5 min)
**What You Automated**

**Recap of what you accomplished:**
1. **TOOLS:** Built a custom CLI tool for your pipeline
2. **SKILLS:** Wrapped it as an AI-discoverable skill
3. **AGENTS:** Defined specialized sub-agents with AGENTS.md
4. **HOOKS:** Configured verification gates

**The progression:** Tool → Skill → Agent → Pipeline

**Key takeaway:** From manual work to automated pipeline. Tools give you capabilities. Skills make them discoverable. Agents organize them into workflows. Hooks keep them safe.

---

## BACKUP MATERIALS

### Wire Hooks & Run Pipeline
If time permits, additional exercise:
1. Add PostToolUse hooks for verification
2. Configure Stop verification gates
3. Run full pipeline end-to-end

---

## Rehearsal Prompt Files

All prompt files are in the training repo at `session-3-agentic/[your-choice]/prompts/`:

| File | Purpose | Used in |
|------|---------|---------|
| `01-explore.md` | Explore the pipeline target, understand the codebase | REHEARSAL intro |
| `02-cli-tool.md` | Build and test a CLI tool from the template | BUILD: CLI Tool |
| `03-skill.md` | Register the tool as a skill, document, test with AI | BUILD: Skill |
| `04-agents.md` | Define agents + hooks in AGENTS.md | BUILD: Agents |

---

## Next Steps After Training

### Immediate (This Week)
1. Set up AGENTS.md in your main project
2. Build one custom CLI tool for a repetitive task
3. Register it as a skill

### Short-term (This Month)
1. Define 2-3 specialized sub-agents
2. Add basic hooks for dangerous operations
3. Document your first 5 learnings

### Long-term (This Quarter)
1. Create team-shared configuration repository
2. Roll out to additional teams
3. Build custom agents for your domain
4. Integrate MCP servers for key workflows
