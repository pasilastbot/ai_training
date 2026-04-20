# Session 1: Greenfield with AI
**Duration:** 90 min | **Level:** Beginner

**Goal:** From zero to working app with specs, TDD, and AI as a real collaborator

**Theme:** This session establishes your proto capability. You'll learn to leverage AI tools to build working applications using spec-driven development. The workflow: **Rules → Skills → Scaffold → Spec → TDD → Ship**.

**Materials:** `session-1-greenfield/` prompts (01-scaffold.md through 04-feature2.md)

---

## Session Flow

| # | Type | Topic | Duration |
|---|------|-------|----------|
| 1 | THEORY | AI Coding Tools & Project Rules | 5 min |
| 2 | THEORY | Skills — Making Capabilities Discoverable | 10 min |
| 3 | THEORY | Effective Prompting & Model Selection | 10 min |
| 4 | THEORY | Spec-Driven Development & Acceptance Criteria | 10 min |
| 5 | **BUILD** | TDD with AI + Two End-to-End Builds | 35 min |

**Total: 70 min + 20 min buffer for Q&A**

---

## PART 1: TOOLS & CONFIGURATION

### 1. AI Coding Tools Landscape (5 min)
**Choose the right tool for the task**

| Tool | Strengths | Best For |
|------|-----------|----------|
| **Cursor** | Multi-model, fast iteration, Composer 2 | Fast iteration, multi-file edits |
| **GitHub Copilot** | Enterprise compatible, VS Code integration | Enterprise environments |
| **Claude Code** | Best agentic tool, full reasoning | Architecture, complex implementation |
| **Codex CLI** | Terminal-native, GPT-5.4 powered | Hard problems, automation |

### Rules & Configuration
**Your codebase constitution**

```
project-root/
├── .cursor/
│   └── rules/           # Cursor-specific rules
│       ├── main.mdc     # Always-applied rules
│       └── testing.mdc  # Applied when working on tests
├── CLAUDE.md            # Claude Code instructions
└── AGENTS.md            # Cross-tool neutral format
```

What rules should define:
- Processes (spec-driven, TDD, review)
- Index to tools, docs, and skills
- Coding styles and conventions
- Testing instructions and frameworks
- Guardrails — what NOT to do

---

### 2. Skills — Making Capabilities Discoverable (10 min)
**If it's not documented, the AI doesn't know it exists**

A skill is a documented capability the AI can discover and invoke. Without documentation, your scripts, APIs, and tools are invisible to the assistant.

```markdown
## skill: run-tests
description: Run the test suite
trigger: "test", "verify", "check"
command: npm test
output: test results + coverage

## skill: lint
description: Check code style
command: npx eslint src/
```

### The Hierarchy

| Concept | What It Is | When Introduced |
|---------|------------|-----------------|
| **Skills** | What the AI can do | Session 1 |
| **Sub-Agents** | Who does specialized work | Session 2 |
| **Hooks** | When to verify | Session 3-4 |

**Key insight:** Skills bridge the gap between "the AI could do this" and "the AI knows how to do this."

---

## PART 2: PROMPTING & MODELS

### 3. Effective Prompting (10 min)
**Context sandwich, @ injection, constraints**

#### The Context Sandwich

```
TOP BREAD (Context):
@src/auth/login.ts
@docs/architecture.md

FILLING (Request):
"Refactor the login function to use the new OAuth2 flow 
documented in architecture.md"

BOTTOM BREAD (Constraints):
"Keep existing error handling. 
Add unit tests for the new flow."
```

#### @ Context Injection

| Symbol | What It Does | Example |
|--------|--------------|---------|
| `@file` | Include specific file | `@src/utils/auth.ts` |
| `@folder` | Include folder contents | `@src/components/` |
| `@codebase` | Semantic search | `@codebase how does caching work?` |
| `@docs` | Include documentation | `@docs/api-spec.md` |
| `@web` | Search the internet | `@web Next.js 14 server actions` |

**Pro Tip:** Over-specify context. Token cost is cheap; debugging AI hallucinations is expensive.

#### Model Selection

| Model | Reasoning | Speed | Best For |
|-------|-----------|-------|----------|
| **Claude Opus 4** | Best | Slow | Architecture, complex reasoning |
| **Claude Sonnet 4** | Great | Fast | Daily coding, balanced cost |
| **GPT-5.4** | Best | Medium | Hard tasks, reasoning |
| **Composer 2** | Great | Fastest | Fast iteration, multi-file edits |

**Rule:** Sonnet for daily work → Opus/GPT-5 for deep reasoning → Composer 2 for speed

---

## PART 3: SPEC-DRIVEN DEVELOPMENT

### 4. Spec-Driven Development (10 min)
**The spec IS the prompt**

```
Vibe coding = "make it work, hope for the best" — dangerous in production
Spec-driven = "define what right looks like, then build to that standard"
```

#### User Acceptance Criteria

Each feature needs testable acceptance criteria:

```markdown
Feature: Add Todo Item

AC1: Adding a valid item
- User submits "Buy groceries"
- List contains 1 item, status "pending"
- Success message displayed

AC2: Empty input rejected
- User submits empty string
- Error "Title required" returned
- List remains unchanged

AC3: Duplicate detection
- Submitting same title twice is rejected
- Original item remains unchanged
```

#### The "Can AI Test This?" Check

Before finalizing a spec, verify:
- Is every AC measurable? (numbers, states, not feelings)
- Are edge cases explicit? (empty, null, errors)
- Are side effects listed? (logs, DB writes)
- Is happy path AND error path defined?
- Can each AC become a test case directly?

---

## PART 4: BUILD — TDD WITH AI

### 5. TDD with AI (35 min)
**Red → Green → Refactor**

```
┌─────────┐         ┌─────────┐         ┌─────────┐
│   RED   │────────▶│  GREEN  │────────▶│REFACTOR │
│         │         │         │         │         │
│ Write   │         │ Write   │         │ Improve │
│ failing │         │ minimum │         │ code    │
│ test    │         │ code    │         │ quality │
└─────────┘         └─────────┘         └─────────┘
     ▲                                       │
     └───────────────────────────────────────┘
```

**TDD + AI = confidence.** The test proves the AI wrote what you asked for, not what it hallucinated.

---

### Rehearsal: Clone & Start (10 min)

```bash
git clone https://github.com/pasilastbot/ai_training
cd session-1-greenfield/
```

Use `prompts/01-scaffold.md`:
1. Provide context (CLAUDE.md, package.json, conventions)
2. Request scaffold (folder structure, types, framework)
3. Constraints (follow rules in CLAUDE.md)

---

### Build: Scaffold Your Project (10 min)

Use `prompts/01-scaffold.md` to write your first Context Sandwich prompt:

1. **Provide context** — Your CLAUDE.md, package.json, project conventions
2. **Request** — Scaffold the project: folder structure, types, CLI/API framework
3. **Constraints** — Follow the project rules you defined

**AI generates:** folder structure, TypeScript types, CLI/API framework

---

### Build: Write Your Feature Spec (10 min)

Use `prompts/02-spec.md`:

1. Write acceptance criteria for Feature 1
2. Include happy path, error cases, edge cases
3. Run the "Can AI Test This?" check on each AC

---

### Build: Implement with TDD (15 min)

#### Feature 1 with TDD (`prompts/03-tdd.md`)
1. Write tests first from your ACs
2. AI generates implementation
3. Run tests → all green
4. Refactor together

#### Feature 2 (`prompts/04-feature2.md`)
1. Write spec independently
2. Drive the full TDD cycle
3. Review output against ACs
4. Ship with confidence

---

## Key Takeaways

1. **Configure your AI** with AGENTS.md/CLAUDE.md — processes, links, guardrails
2. **Document skills** — if the AI can't find it, it can't use it
3. **Context Sandwich** — always ground prompts with evidence + request + constraints
4. **Match model to task** — Opus for thinking, Sonnet for coding, Composer 2 for speed
5. **Spec first** — acceptance criteria that AI can turn directly into test cases
6. **TDD with AI** — Red → Green → Refactor gives you confidence, not hope

**Your workflow:** Rules → Skills → Scaffold → Spec → TDD → Ship

---

## Preparation for Session 2

Before the next session:
1. Create an AGENTS.md for your own project
2. Practice the Context Sandwich on 3 real tasks
3. Build one feature using the full TDD cycle
4. Think about: what's different when working on existing codebases?
