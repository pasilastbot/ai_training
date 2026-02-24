# Prompt 03: Wrap Your Tool as a Skill

**When to use:** PART 2 — BUILD step (after Skills vs Sub-Agents vs Hooks + Agent Skills theory)
**Goal:** Register check-security.sh as an AI-discoverable skill

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

### check-security
**Command:** `bash tools/check-security.sh <directory>`
**Purpose:** Scan code for common security vulnerabilities (SQL injection, hardcoded secrets, missing validation, dangerous eval)
**Input:** Path to directory or file to scan
**Output:** JSON array of findings, each with type, file, line, match
**Exit codes:** 0 = no critical findings, 1 = critical findings found
**When to use:** Before approving any code review, after code changes

### Example usage
```bash
# Scan a directory
bash tools/check-security.sh target/

# Scan a specific file
bash tools/check-security.sh target/sample-diff-1.patch
```
```

---

## Step 2: Add usage examples for AI

Good skill documentation includes examples that show AI exactly how to use the tool:

```
Add 2-3 usage examples to the check-security skill registration.
Show:
1. Basic scan of a directory
2. How to interpret the JSON output
3. What to do when findings are critical vs minor
```

---

## Step 3: Test it — ask AI to use your skill

Now verify AI can discover and use your skill:

```
@AGENTS.md.skeleton

I need to review the code in target/ for security issues.
Use the available skills to scan for vulnerabilities.
Report what you find.
```

**Check:** Did AI find and use `check-security.sh`? Did it interpret the output correctly?

If AI didn't use the skill, improve the documentation — the registration might be unclear.

---

## What you should have after this step

- [ ] Skill registered in AGENTS.md with command, purpose, output format
- [ ] Usage examples included
- [ ] AI successfully discovered and used the skill
- [ ] Output was correctly interpreted by AI
