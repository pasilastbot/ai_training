# Session 3: Advanced Agentic Workflows

**90 min | Advanced | "Scale with Agents & Tools"**

Build a multi-agent pipeline that automates a real development task. You'll build CLI tools, wrap them as skills, define specialized agents, and wire hooks — progressing from Tool → Skill → Agent → Pipeline.

---

## Pick Your Pipeline

Choose ONE of these three projects to build during the session:

### A) Code Review Pipeline
Build a multi-agent pipeline that automatically reviews PRs.
- **Pipeline:** PR Diff Reader -> Security Reviewer -> Quality Reviewer -> Summary Writer
- **Folder:** `a-code-review/`

### B) Documentation Generator
Build an agent workflow that auto-documents undocumented codebases.
- **Pipeline:** Code Scanner -> Architecture Mapper -> Doc Writer -> Quality Checker
- **Folder:** `b-doc-generator/`

### C) Test Suite Generator
Build an agent workflow that generates comprehensive test suites.
- **Pipeline:** Code Analyzer -> Test Strategist -> Test Writer -> Coverage Reporter
- **Folder:** `c-test-generator/`

---

## Session Flow

| # | Type | Topic | Duration |
|---|------|-------|----------|
| | | **— PART 1: TOOLS —** | |
| 1 | THEORY | MCP vs CLI Tools (trade-offs, when to use which) | 5 min |
| 2 | THEORY | MCP Integrations (GitHub, Slack, databases, custom servers) | 5 min |
| 3 | THEORY | Inventing CLI Tools (Need → Script → Test → Register) | 5 min |
| 4 | **REHEARSAL** | **Pick your target, clone the repo, explore the codebase** | **10 min** |
| 5 | **BUILD** | **Build a custom CLI tool for your pipeline** | **10 min** |
| | | **— PART 2: SKILLS —** | |
| 6 | THEORY | Skills vs Sub-Agents vs Hooks (What / Who / When) | 5 min |
| 7 | THEORY | Agent Skills (web search, file ops, code analysis, APIs) | 5 min |
| 8 | **BUILD** | **Wrap your CLI tool as a skill — register, document, test** | **10 min** |
| | | **— PART 3: SUB-AGENTS —** | |
| 9 | THEORY | Agentic Architecture (Assistant → Tool User → Agent → Multi-Agent) | 5 min |
| 10 | THEORY | Specialized Sub-Agents (Spec writer, test generator, reviewer) | 5 min |
| 11 | **BUILD** | **Define agent roles in AGENTS.md with hooks & permissions** | **10 min** |
| | | **— PART 4: HOOKS & SCALING —** | |
| 12 | THEORY | Hooks & Verification (PostToolUse, Stop hooks) | 5 min |
| 13 | THEORY | Scaling Across Teams (Shared agents, centralized docs, metrics) | 5 min |
| 14 | WRAP-UP | Review your pipeline, discuss team scaling, Q&A | 5 min |

**Total: 90 min** (40 min theory + 40 min hands-on + 10 min rehearsal)

---

## Getting Started

1. Clone this repo
2. `cd` into your chosen project folder
3. Read the target files to understand what the pipeline will process
4. Follow the prompts in `prompts/` in order (01 → 04)

## Prompt Files

| File | Purpose | Session Step |
|------|---------|-------------|
| `01-explore.md` | Explore the pipeline target, understand the codebase | REHEARSAL (Part 1) |
| `02-cli-tool.md` | Build and test a CLI tool from the template | BUILD: CLI Tool (Part 1) |
| `03-skill.md` | Register the tool as a skill, document, test with AI | BUILD: Skill (Part 2) |
| `04-agents.md` | Define agents + hooks in AGENTS.md | BUILD: Agents (Part 3) |
