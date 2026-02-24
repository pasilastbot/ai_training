# AI-Native Engineering Mastery - Session Plan v4

## Design Principles
- **Session 1** = Greenfield only (Beginner) — build something new from zero
- **Session 2** = Brownfield only (Intermediate) — work with existing codebases
- **Session 3** = Advanced Agentic Workflows — scale with agents, tools, multi-agent
- **The rehearsal IS the session** — introduced at the start, built upon after each theory block
- Pattern: Theory → Apply to YOUR project → Theory → Apply to YOUR project → ...
- Session 1 has **3 alternative rehearsal projects** in `github.com/pasilastbot/ai_training`
- Session 2 uses a **real open-source game**: [Suroi](https://github.com/HasangerGames/suroi) (~114k LOC TypeScript, battle royale io-game, runs in browser)
- Session 3 has **3 alternative rehearsal pipelines** in `github.com/pasilastbot/ai_training`

---

## SESSION 1: Greenfield Development with AI
**90 min | Beginner | "From Zero to Working App"**

### Session Flow

| # | Type | Topic | Duration | Slide |
|---|------|-------|----------|-------|
| 1 | TITLE | Session 1: Greenfield Development with AI | — | `03-s1-title.png` |
| 2 | THEORY | AI Coding Tools Landscape | 5 min | `04-s1-tools-landscape.png` |
| 3 | THEORY | Rules & Configuration (.cursor/rules, CLAUDE.md, AGENTS.md) | 5 min | `05-s1-rules-config.png` |
| 4 | REHEARSAL | **Pick your project, clone the repo, set up CLAUDE.md** | 10 min | `06-s1-rehearsal-intro.png` |
| 5 | THEORY | Effective Prompting: Context Sandwich | 5 min | `07-s1-context-sandwich.png` |
| 6 | THEORY | Model Selection | 5 min | `08-s1-model-selection.png` |
| 7 | BUILD | **Write your first Context Sandwich prompt to scaffold the project** | 10 min | `09-s1-build-scaffold.png` |
| 8 | THEORY | Greenfield: Spec-Driven Development (Spec → Code → Tests) | 5 min | `11-s1-greenfield-sdd.png` |
| 9 | THEORY | Writing Effective Specifications (templates, Given/When/Then) | 5 min | `12-s1-specifications.png` |
| 10 | BUILD | **Write the spec for Feature 1 of your project** | 10 min | `13-s1-build-spec.png` |
| 11 | THEORY | TDD Cycle with AI (Red → Green → Refactor) | 5 min | `14-s1-tdd-cycle.png` |
| 12 | BUILD | **Implement Feature 1 with TDD, then spec + build Feature 2** | 15 min | `15-s1-build-tdd.png` |
| 13 | WRAP-UP | Review what you built, Q&A | 5 min | `16-s1-wrap-up.png` |

### Rehearsal Alternatives

#### A) Todo CLI (Node.js/TypeScript)
**Folder:** `session-1-greenfield/a-todo-cli/`
A command-line todo manager with categories and priorities.

| After theory... | Students do... | Repo provides... |
|-----------------|---------------|-----------------|
| Tools + Rules | Clone repo, create `CLAUDE.md` with project rules | Empty project with `package.json`, `.cursor/rules` template |
| Prompting + Models | Prompt AI to scaffold: folder structure, types, CLI framework | Prompt template: scaffold prompt with Context Sandwich |
| SDD + Specs | Write spec for "Add Todo" with Given/When/Then | Spec template + example spec for reference |
| TDD | Implement "Add Todo" with TDD, then spec + build "List Todos with filters" | Test runner pre-configured, TDD prompt template |

**Features to build:**
1. Add a todo (with title, category, priority)
2. List todos with filtering (by category, by status)

---

#### B) Weather Dashboard API (Node.js/TypeScript)
**Folder:** `session-1-greenfield/b-weather-api/`
A REST API that fetches, caches, and serves weather data.

| After theory... | Students do... | Repo provides... |
|-----------------|---------------|-----------------|
| Tools + Rules | Clone repo, create `CLAUDE.md` with API design rules | Empty project with `package.json`, Express starter |
| Prompting + Models | Prompt AI to scaffold: routes, services, types | Prompt template: API scaffold prompt |
| SDD + Specs | Write spec for "Get Current Weather" endpoint | Spec template + example OpenAPI-style spec |
| TDD | Implement "Get Current Weather" with TDD, then spec + build "Get Forecast" | Mock weather data included, test setup ready |

**Features to build:**
1. GET /weather/:city — returns current weather (from mock data)
2. GET /forecast/:city — returns 5-day forecast with caching

---

#### C) Bookmark Manager API (Node.js/TypeScript)
**Folder:** `session-1-greenfield/c-bookmark-api/`
A REST API for saving, tagging, and searching bookmarks.

| After theory... | Students do... | Repo provides... |
|-----------------|---------------|-----------------|
| Tools + Rules | Clone repo, create `CLAUDE.md` with data model rules | Empty project with `package.json`, in-memory DB setup |
| Prompting + Models | Prompt AI to scaffold: routes, models, validation | Prompt template: CRUD scaffold prompt |
| SDD + Specs | Write spec for "Create Bookmark" with validation rules | Spec template + Given/When/Then examples |
| TDD | Implement "Create Bookmark" with TDD, then spec + build "Search by tag" | Test framework ready, sample data fixtures |

**Features to build:**
1. POST /bookmarks — create bookmark with URL validation and tags
2. GET /bookmarks?tag=X — search bookmarks by tag

---

## SESSION 2: Brownfield Development with AI
**90 min | Intermediate | "Taming Existing Codebases"**

### Session Flow

| # | Type | Topic | Duration | Slide |
|---|------|-------|----------|-------|
| 1 | TITLE | Session 2: Brownfield Development with AI | — | `17-s2-title.png` |
| | | **— PART 1: OVERVIEW —** | | |
| 2 | THEORY | Greenfield vs Brownfield — 80% is brownfield | 5 min | `18-s2-green-vs-brown.png` |
| 3 | THEORY | Vibe Coding vs Grounded SDD *(moved from S1)* | 5 min | `10-s1-vibe-vs-sdd.png` |
| 4 | THEORY | ModernPath 4-Step Process (Document → Spec → Develop → Audit) | 5 min | `23-s2-4step-process.png` |
| | | **— PART 2: DOCUMENTATION —** | | |
| 5 | REHEARSAL | **Clone Suroi, run `bun dev`, explore the codebase — 114k lines, no architecture docs** | 10 min | `19-s2-rehearsal-intro.png` |
| 6 | THEORY | Brownfield: 3-Tiered Documentation (High-level → Subsystem → Module) | 5 min | `20-s2-brownfield-docs.png` |
| 7 | THEORY | Documentation Plan (content-plan.md — map what exists, index for AI) | 5 min | `21-s2-documentation-plan.png` |
| 8 | BUILD | **Document Suroi: create content-plan.md + document your subsystem** | 10 min | `22-s2-build-document.png` |
| 9 | THEORY | AI-Friendly Architecture *(side bite while AI documents)* | 5 min | `24-s2-architecture.png` |
| 10 | BUILD | **Test & improve docs — ask AI questions about the codebase, iterate** | 5 min | *(verbal, no slide)* |
| | | **— PART 3: SPEC-DRIVEN CHANGE —** | | |
| 11 | BUILD | **Prompt a change to the game, generate specs using SDD** | 10 min | `26-s2-build-spec.png` |
| 12 | THEORY | Code Review with AI (Critique loops, PR review prompts) | 5 min | `27-s2-code-review.png` |
| 13 | BUILD | **Code review the change against the spec** | 10 min | `29-s2-build-fix.png` |
| 14 | WRAP-UP | What you documented & improved, Q&A | 5 min | `30-s2-wrap-up.png` |
| | | **— BACKUP SLIDES —** | | |
| — | BACKUP | The Fix Workflow | — | `28-s2-fix-workflow.png` |
| — | BACKUP | Quality Checkpoints | — | `25-s2-checkpoints.png` |

### Rehearsal Project: Suroi (surviv.io clone)

**Repo:** `https://github.com/HasangerGames/suroi`
**What it is:** A 2D battle royale io-game (surviv.io clone), ~114k lines of TypeScript. Runs in browser at `localhost:3000`.
**Why it's perfect for brownfield:** Real production codebase, 100% TypeScript, monorepo with `client/`, `server/`, `common/` workspaces, PixiJS rendering, WebSocket networking, Vite bundling — but no architecture documentation.

**Setup:** `bun install && bun dev` → open `http://127.0.0.1:3000`
**Live demo:** https://suroi.io (show before cloning so students understand the game)

#### What makes it a great brownfield exercise

- **~114k lines of TypeScript** — large enough that you NEED AI to navigate
- **Zero architecture docs** — README covers setup, not how the code works
- **Rich domain complexity** — game loop, entity system, physics, networking, map generation, inventory, weapons, obstacles
- **Clear monorepo structure** — `client/` (rendering, input), `server/` (game simulation, networking), `common/` (shared types, definitions)
- **Runs in browser** — students can play the game, change code, see results instantly
- **Real open issues** — actual bugs and feature requests to pick from

#### Subsystem options for documentation focus

Students can pick ONE subsystem to deep-document during the session:

| Subsystem | Location | What to document |
|-----------|----------|-----------------|
| **Game loop & entities** | `server/src/game.ts`, `server/src/objects/` | How the game tick works, entity lifecycle, collision |
| **Weapons & inventory** | `common/src/definitions/`, `server/src/inventory/` | Weapon definitions, damage calc, ammo system |
| **Networking** | `server/src/server.ts`, `client/src/game.ts` | Client-server protocol, state sync, WebSocket messages |
| **Map generation** | `server/src/map.ts`, `common/src/definitions/obstacles.ts` | How maps are generated, obstacle placement, terrain |
| **Rendering** | `client/src/rendering/` | PixiJS scene graph, camera, particle effects |

#### Progressive rehearsal steps

| After theory... | Students do... |
|-----------------|---------------|
| PART 1: Overview (Green vs Brown, Vibe vs SDD, 4-Step) | Clone Suroi, run `bun dev`, open in browser, explore the code — no docs to guide you |
| PART 2: Documentation (3-Tiered Docs, Doc Plan) | Create `content-plan.md` for Suroi, deep-document your chosen subsystem using 3-tiered approach |
| PART 2: Architecture (side bite while AI documents) | Discuss Suroi's architecture: modularity, contracts, coupling. Test & improve docs by asking AI questions about the codebase |
| PART 3: Spec-Driven Change | Prompt a change to the game, generate grounded specs with acceptance criteria using SDD |
| PART 3: Code Review & Audit | Review the change against the spec, run AI code review on the diff, verify in browser |

#### Prompt files (in `session-2-brownfield/prompts/`)

| File | Purpose |
|------|---------|
| `01-explore.md` | Explore Suroi codebase with AI: understand the monorepo, find entry points, map the game loop |
| `02-document.md` | Create content-plan.md + 3-tiered docs for your chosen subsystem |
| `03-spec-changes.md` | Analyze architecture patterns, identify improvement, write a change spec |
| `04-implement.md` | Implement the change, verify in browser, run AI code review |

---

## SESSION 3: Advanced Agentic Workflows
**90 min | Advanced | "Scale with Agents & Tools"**

### Session Flow

| # | Type | Topic | Duration | Slide |
|---|------|-------|----------|-------|
| 1 | TITLE | Session 3: Advanced Agentic Workflows | — | `31-s3-title.png` |
| | | **— PART 1: TOOLS —** | | |
| 2 | THEORY | MCP vs CLI Tools (trade-offs, when to use which) | 5 min | `37-s3-mcp-vs-cli.png` |
| 3 | THEORY | MCP Integrations (GitHub, Slack, databases, custom servers) | 5 min | `38-s3-mcp-integrations.png` |
| 4 | THEORY | Inventing CLI Tools (Need → Script → Test → Register) | 5 min | `39-s3-inventing-cli.png` |
| 5 | REHEARSAL | **Pick your target, clone the repo, explore the codebase** | 10 min | `35-s3-rehearsal-intro.png` |
| 6 | BUILD | **Build a custom CLI tool for your pipeline** | 10 min | `40-s3-build-cli-tool.png` |
| | | **— PART 2: SKILLS —** | | |
| 7 | THEORY | Skills vs Sub-Agents vs Hooks (What / Who / When — overview) | 5 min | `34-s3-skills-agents-hooks.png` |
| 8 | THEORY | Agent Skills (deep dive: web search, file ops, code analysis, APIs) | 5 min | `42-s3-agent-skills.png` |
| 9 | BUILD | **Wrap your CLI tool as a skill — register, document, test** | 10 min | `46-s3-build-skill.png` |
| | | **— PART 3: SUB-AGENTS —** | | |
| 10 | THEORY | Agentic Architecture (Assistant → Tool User → Agent → Multi-Agent) | 5 min | `32-s3-agentic-architecture.png` |
| 11 | THEORY | Specialized Sub-Agents (Spec writer, test generator, code reviewer) | 5 min | `33-s3-sub-agents.png` |
| 12 | BUILD | **Define agent roles in AGENTS.md with hooks & permissions** | 10 min | `36-s3-build-agents.png` |
| | | **— PART 4: HOOKS & SCALING —** | | |
| 13 | THEORY | Hooks & Verification (PostToolUse, Stop hooks — narrow) | 5 min | `41-s3-hooks-verification.png` |
| 14 | THEORY | Scaling Across Teams (Shared agents, centralized docs, metrics) | 5 min | `44-s3-scaling.png` |
| 15 | WRAP-UP | Review your pipeline, discuss team scaling, Q&A | 5 min | `45-s3-wrap-up.png` |
| | | **— BACKUP SLIDES —** | | |
| — | BACKUP | BUILD: Wire Hooks & Run Pipeline | — | `43-s3-build-hooks.png` |

### Rehearsal Alternatives

Each project provides a target scenario + a partially set up agent workspace. Students progressively build tools, wrap them as skills, then configure agents.

#### A) Code Review Pipeline
**Folder:** `session-3-agentic/a-code-review/`
Build a multi-agent pipeline that automatically reviews PRs.

**Target pipeline:** PR Diff Reader → Security Reviewer → Quality Reviewer → Summary Writer

| After theory... | Students do... | Repo provides... |
|-----------------|---------------|-----------------|
| MCP vs CLI + Integrations + Inventing CLI | Clone repo, understand the target pipeline | Sample PR diffs to review, AGENTS.md skeleton |
| (BUILD 1: Tool) | Build a `check-security.sh` CLI tool that scans for common vulnerabilities | Script template, test cases for SQL injection / XSS patterns |
| Skills vs Sub-Agents vs Hooks + Agent Skills | Understand what skills are and how they extend agents | Skill registration examples |
| (BUILD 2: Skill) | Register `check-security.sh` as a skill in CLAUDE.md, document usage, test it | Skill template, registration guide |
| Agentic Arch + Sub-Agents | Learn multi-agent patterns | Agent examples |
| (BUILD 3: Agents) | Define 4 agent roles in AGENTS.md with responsibilities, constraints + hooks | Agent template with blanks to fill, hook config section |

---

#### B) Documentation Generator
**Folder:** `session-3-agentic/b-doc-generator/`
Build an agent workflow that auto-documents undocumented codebases.

**Target pipeline:** Code Scanner → Architecture Mapper → Doc Writer → Quality Checker

| After theory... | Students do... | Repo provides... |
|-----------------|---------------|-----------------|
| MCP vs CLI + Integrations + Inventing CLI | Clone repo, see the undocumented target codebase | Small undocumented Node.js app (~300 lines) |
| (BUILD 1: Tool) | Build an `analyze-deps.sh` CLI tool that extracts import/dependency graph | Script template, expected output format |
| Skills vs Sub-Agents vs Hooks + Agent Skills | Understand skills | Skill examples |
| (BUILD 2: Skill) | Register `analyze-deps.sh` as a skill, document for AI consumption, test it | Skill template |
| Agentic Arch + Sub-Agents | Learn agent pods | — |
| (BUILD 3: Agents) | Define 4 agent roles: scanner, mapper, writer, checker with hooks in AGENTS.md | AGENTS.md skeleton with role descriptions to complete |

---

#### C) Test Suite Generator
**Folder:** `session-3-agentic/c-test-generator/`
Build an agent workflow that generates comprehensive test suites for existing code.

**Target pipeline:** Code Analyzer → Test Strategist → Test Writer → Coverage Reporter

| After theory... | Students do... | Repo provides... |
|-----------------|---------------|-----------------|
| MCP vs CLI + Integrations + Inventing CLI | Clone repo, see the untested target codebase | Small app with 0% test coverage |
| (BUILD 1: Tool) | Build a `coverage-check.sh` CLI tool that runs tests and reports coverage % | Script template, test runner config |
| Skills vs Sub-Agents vs Hooks + Agent Skills | Understand skills | — |
| (BUILD 2: Skill) | Register `coverage-check.sh` as a skill, document for AI, test it | Skill template |
| Agentic Arch + Sub-Agents | Learn multi-agent patterns | — |
| (BUILD 3: Agents) | Define 4 agent roles: analyzer, strategist, writer, reporter with hooks in AGENTS.md | Agent template, hook config section |

---

## Repo Structure: `github.com/pasilastbot/ai_training`

```
ai_training/
├── README.md                          # Repo overview + session picker
│
├── session-1-greenfield/
│   ├── README.md                      # Session 1 overview, pick your project
│   ├── a-todo-cli/
│   │   ├── package.json               # Dependencies pre-configured
│   │   ├── tsconfig.json
│   │   ├── CLAUDE.md.template         # Students copy to CLAUDE.md and fill in
│   │   ├── prompts/
│   │   │   ├── 01-scaffold.md         # Context Sandwich prompt to scaffold
│   │   │   ├── 02-spec.md            # Spec template for Feature 1
│   │   │   ├── 03-tdd.md            # TDD implementation prompt
│   │   │   └── 04-feature2.md        # Spec + build Feature 2
│   │   └── specs/
│   │       └── example-spec.md        # Reference spec (Given/When/Then)
│   ├── b-weather-api/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── CLAUDE.md.template
│   │   ├── prompts/
│   │   │   ├── 01-scaffold.md
│   │   │   ├── 02-spec.md
│   │   │   ├── 03-tdd.md
│   │   │   └── 04-feature2.md
│   │   └── specs/
│   │       └── example-spec.md
│   └── c-bookmark-api/
│       ├── package.json
│       ├── tsconfig.json
│       ├── CLAUDE.md.template
│       ├── prompts/
│       │   ├── 01-scaffold.md
│       │   ├── 02-spec.md
│       │   ├── 03-tdd.md
│       │   └── 04-feature2.md
│       └── specs/
│           └── example-spec.md
│
├── session-2-brownfield/
│   ├── README.md                      # Session 2 overview, Suroi setup instructions
│   ├── prompts/
│   │   ├── 01-explore.md              # Explore Suroi codebase with AI
│   │   ├── 02-document.md             # Create content-plan.md + 3-tiered docs
│   │   ├── 03-spec-changes.md         # Analyze architecture, write change spec
│   │   └── 04-implement.md            # Implement, test in browser, AI code review
│   └── examples/
│       ├── content-plan-example.md    # Example content-plan.md for reference
│       └── change-spec-example.md     # Example change spec for reference
│
├── session-3-agentic/
│   ├── README.md                      # Session 3 overview, pick your project
│   ├── a-code-review/
│   │   ├── target/                    # Sample PR diffs to review
│   │   ├── AGENTS.md.skeleton         # Students complete this
│   │   ├── tools/                     # Script templates
│   │   │   └── check-security.sh.template
│   │   └── prompts/
│   │       ├── 01-explore.md          # Explore the pipeline target
│   │       ├── 02-cli-tool.md         # Build and test CLI tool
│   │       ├── 03-skill.md            # Wrap tool as a skill
│   │       └── 04-agents.md           # Define agents + hooks in AGENTS.md
│   ├── b-doc-generator/
│   │   ├── target/                    # Undocumented Node.js app (~300 lines)
│   │   ├── AGENTS.md.skeleton
│   │   ├── tools/
│   │   └── prompts/
│   │       ├── 01-explore.md
│   │       ├── 02-cli-tool.md
│   │       ├── 03-skill.md
│   │       └── 04-agents.md
│   └── c-test-generator/
│       ├── target/                    # App with 0% test coverage
│       ├── AGENTS.md.skeleton
│       ├── tools/
│       └── prompts/
│           ├── 01-explore.md
│           ├── 02-cli-tool.md
│           ├── 03-skill.md
│           └── 04-agents.md
│
└── solutions/                         # On separate branch: `solutions`
    ├── session-1-greenfield/
    ├── session-2-brownfield/
    └── session-3-agentic/
```

### What each session folder provides

**Session 1 (Greenfield) — each alternative contains:**
- `package.json` with dependencies pre-configured (vitest for testing)
- `CLAUDE.md.template` — students copy to `CLAUDE.md` and fill in project-specific rules
- `prompts/` — step-by-step prompt files matching the BUILD steps in the session
- `specs/` — example spec for reference

**Session 2 (Brownfield) — uses Suroi (`github.com/HasangerGames/suroi`):**
- Students clone Suroi directly (not from ai_training repo)
- `prompts/` — step-by-step prompt files for each BUILD step (in ai_training repo)
- `examples/` — reference content-plan and change spec examples
- No solutions branch needed — students produce unique documentation for their chosen subsystem

**Session 3 (Agentic) — each alternative contains:**
- `target/` — codebase that the agent pipeline will process
- `AGENTS.md.skeleton` — partially filled, students complete during BUILD 3 (agents + hooks)
- `tools/` — script templates for CLI tool creation (BUILD 1)
- `prompts/` — step-by-step prompt files: explore → CLI tool → skill → agents

---

## Complete Slide Deck Order (for PPT generator)

Every slide in presentation order. All filenames are final. All slides are DONE.

### INTRO (3 slides)

| # | Filename | Title |
|---|----------|-------|
| 0 | `00-master-title.png` | AI-Native Engineering Mastery |
| 1 | `01-intro-trainer.png` | Your Trainer: Pasi Vuorio |
| 2 | `02-training-overview.png` | Training Overview: Greenfield → Brownfield → Scale |

### SESSION 1: Greenfield (13 slides)

| # | Filename | Title | Type |
|---|----------|-------|------|
| 3 | `03-s1-title.png` | Session 1: Greenfield Development with AI | TITLE |
| 4 | `04-s1-tools-landscape.png` | 1. AI Coding Tools Landscape | THEORY |
| 5 | `05-s1-rules-config.png` | Rules & Configuration | THEORY |
| 6 | `06-s1-rehearsal-intro.png` | REHEARSAL: Pick Your Project | REHEARSAL |
| 7 | `07-s1-context-sandwich.png` | 2. Effective Prompting: Context Sandwich | THEORY |
| 8 | `08-s1-model-selection.png` | 3. Model Selection | THEORY |
| 9 | `09-s1-build-scaffold.png` | BUILD: Scaffold Your Project | BUILD |
| 10 | `11-s1-greenfield-sdd.png` | Greenfield: Spec-Driven Development | THEORY |
| 11 | `12-s1-specifications.png` | 6. Writing Effective Specifications | THEORY |
| 12 | `13-s1-build-spec.png` | BUILD: Write Your Feature Spec | BUILD |
| 13 | `14-s1-tdd-cycle.png` | 7. TDD Cycle with AI | THEORY |
| 14 | `15-s1-build-tdd.png` | BUILD: Implement with TDD | BUILD |
| 15 | `16-s1-wrap-up.png` | Session 1 Wrap-Up: What You Built | WRAP-UP |

### SESSION 2: Brownfield (14 main + 2 backup = 16 slides)

| # | Filename | Title | Type |
|---|----------|-------|------|
| | | **— PART 1: OVERVIEW —** | |
| 16 | `17-s2-title.png` | Session 2: Brownfield Development with AI | TITLE |
| 17 | `18-s2-green-vs-brown.png` | 1. Greenfield vs Brownfield | THEORY |
| 18 | `10-s1-vibe-vs-sdd.png` | 2. Vibe Coding vs Grounded SDD *(moved from S1)* | THEORY |
| 19 | `23-s2-4step-process.png` | 3. ModernPath 4-Step Process | THEORY |
| | | **— PART 2: DOCUMENTATION —** | |
| 20 | `19-s2-rehearsal-intro.png` | SUROI: Your Brownfield Challenge | REHEARSAL |
| 21 | `20-s2-brownfield-docs.png` | 4. Brownfield: 3-Tiered Documentation | THEORY |
| 22 | `21-s2-documentation-plan.png` | 5. Documentation Plan: content-plan.md | THEORY |
| 23 | `22-s2-build-document.png` | BUILD: Document Suroi | BUILD |
| 24 | `24-s2-architecture.png` | 6. AI-Friendly Architecture (Side Bite) | THEORY |
| | | **— PART 3: SPEC-DRIVEN CHANGE —** | |
| 25 | `26-s2-build-spec.png` | BUILD: Grounded Specs for Your Change | BUILD |
| 26 | `27-s2-code-review.png` | 7. Code Review with AI | THEORY |
| 27 | `29-s2-build-fix.png` | BUILD: Review & Audit Your Change | BUILD |
| 28 | `30-s2-wrap-up.png` | Session 2 Wrap-Up: What You Documented | WRAP-UP |
| | | **— BACKUP SLIDES —** | |
| — | `28-s2-fix-workflow.png` | BACKUP: The Fix Workflow | BACKUP |
| — | `25-s2-checkpoints.png` | BACKUP: Quality Checkpoints | BACKUP |

### SESSION 3: Agentic (15 main + 1 backup = 16 slides)

| # | Filename | Title | Type |
|---|----------|-------|------|
| | | **— PART 1: TOOLS —** | |
| 29 | `31-s3-title.png` | Session 3: Advanced Agentic Workflows | TITLE |
| 30 | `37-s3-mcp-vs-cli.png` | 1. MCP vs CLI Tools | THEORY |
| 31 | `38-s3-mcp-integrations.png` | 2. MCP Integrations | THEORY |
| 32 | `39-s3-inventing-cli.png` | 3. Inventing CLI Tools | THEORY |
| 33 | `35-s3-rehearsal-intro.png` | REHEARSAL: Pick Your Target | REHEARSAL |
| 34 | `40-s3-build-cli-tool.png` | BUILD: Create Your CLI Tool | BUILD |
| | | **— PART 2: SKILLS —** | |
| 35 | `34-s3-skills-agents-hooks.png` | 4. Skills vs Sub-Agents vs Hooks | THEORY |
| 36 | `42-s3-agent-skills.png` | 5. Agent Skills | THEORY |
| 37 | `46-s3-build-skill.png` | BUILD: Wrap Your Tool as a Skill | BUILD |
| | | **— PART 3: SUB-AGENTS —** | |
| 38 | `32-s3-agentic-architecture.png` | 6. Agentic Architecture | THEORY |
| 39 | `33-s3-sub-agents.png` | 7. Specialized Sub-Agents | THEORY |
| 40 | `36-s3-build-agents.png` | BUILD: Define Your Agents | BUILD |
| | | **— PART 4: HOOKS & SCALING —** | |
| 41 | `41-s3-hooks-verification.png` | 8. Hooks & Verification | THEORY |
| 42 | `44-s3-scaling.png` | 9. Scaling Across Teams | THEORY |
| 43 | `45-s3-wrap-up.png` | Session 3 Wrap-Up: What You Automated | WRAP-UP |
| | | **— BACKUP SLIDES —** | |
| — | `43-s3-build-hooks.png` | BACKUP: Wire Hooks & Run Pipeline | BACKUP |

### TOTALS

| Section | Slides |
|---------|--------|
| Intro | 3 |
| Session 1 | 13 |
| Session 2 | 14 (+2 backup) |
| Session 3 | 15 (+1 backup) |
| **Total** | **48** |

### Archived
Old slide files are in `_old_slides/` for reference.
