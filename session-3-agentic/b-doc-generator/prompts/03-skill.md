# Prompt 03: Wrap Your Tool as a Skill

**When to use:** PART 2 — BUILD step (after Skills vs Sub-Agents vs Hooks + Agent Skills theory)
**Goal:** Register analyze-deps.sh as an AI-discoverable skill

---

## Why this matters

Your CLI tool works — but AI can't find it on its own. A **skill** bridges the gap: it makes your tool discoverable and usable by AI agents. Without registration, AI doesn't know your tool exists.

---

## Step 1: Register the skill

Add this section to your AGENTS.md.skeleton (or create a new CLAUDE.md):

```
@AGENTS.md.skeleton

Add a "Custom Skills" section with this skill registration:

## Custom Skills

### analyze-deps
**Command:** `bash tools/analyze-deps.sh <directory>`
**Purpose:** Extract import/dependency graph from a codebase, showing which files depend on which
**Input:** Path to directory to analyze
**Output:** Text-based dependency tree showing entry points, import chains, and leaf nodes
**Exit codes:** 0 = success, 1 = no files found
**When to use:** Before writing architecture documentation, to understand how files relate

### Example usage
```bash
# Analyze the target app
bash tools/analyze-deps.sh target/

# Output shows:
# src/index.ts
#   → src/routes/tasks.ts
#     → src/db.ts
```
```

---

## Step 2: Add usage examples for AI

```
Add 2-3 usage examples to the analyze-deps skill registration.
Show:
1. Basic dependency scan
2. How to read the output (entry points vs leaf nodes)
3. How this feeds into documentation generation
```

---

## Step 3: Test it — ask AI to use your skill

```
@AGENTS.md.skeleton

I need to understand how the files in target/ relate to each other.
Use the available skills to map the dependencies.
Which file is the entry point? Which files are utilities?
```

**Check:** Did AI find and use `analyze-deps.sh`? Did it correctly identify entry points and dependencies?

---

## What you should have after this step

- [ ] Skill registered in AGENTS.md with command, purpose, output format
- [ ] Usage examples included
- [ ] AI successfully discovered and used the skill
- [ ] Dependency graph correctly interpreted by AI
