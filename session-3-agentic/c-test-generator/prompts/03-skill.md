# Prompt 03: Wrap Your Tool as a Skill

**When to use:** PART 2 — BUILD step (after Skills vs Sub-Agents vs Hooks + Agent Skills theory)
**Goal:** Register coverage-check.sh as an AI-discoverable skill

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

### coverage-check
**Command:** `bash tools/coverage-check.sh [threshold]`
**Purpose:** Run tests and report code coverage percentage, comparing against a threshold
**Input:** Coverage threshold percentage (default: 80)
**Output:** Coverage percentage per file, list of files below threshold
**Exit codes:** 0 = coverage meets threshold, 1 = coverage below threshold
**When to use:** After writing tests, to verify coverage targets are met

### Example usage
```bash
# Check with default 80% threshold
bash tools/coverage-check.sh

# Check with custom threshold
bash tools/coverage-check.sh 90
```
```

---

## Step 2: Add usage examples for AI

```
Add 2-3 usage examples to the coverage-check skill registration.
Show:
1. Basic coverage check with default threshold
2. How to read the output (which files pass/fail)
3. What to do when coverage is below threshold (write more tests)
```

---

## Step 3: Test it — ask AI to use your skill

```
@AGENTS.md.skeleton

I need to check the test coverage for the code in target/.
Use the available skills to run the coverage check.
Tell me what the current coverage is and what needs tests.
```

**Check:** Did AI find and use `coverage-check.sh`? Did it correctly interpret the 0% result?

---

## What you should have after this step

- [ ] Skill registered in AGENTS.md with command, purpose, output format
- [ ] Usage examples included
- [ ] AI successfully discovered and used the skill
- [ ] Coverage result correctly interpreted (should show 0% — no tests yet!)
