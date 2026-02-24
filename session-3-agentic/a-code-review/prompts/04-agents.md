# Prompt 04: Define Your Agents with Hooks

**When to use:** PART 3 — BUILD step (after Agentic Architecture + Sub-Agents theory)
**Goal:** Complete AGENTS.md with agent roles, permissions, and hooks

---

## Step 1: Complete the agent definitions

```
@AGENTS.md.skeleton
@target/

Complete the AGENTS.md file. For each of the 4 agents, define:

### PR Diff Reader
- **Role:** Parse and summarize the PR diff (1-2 sentences)
- **Process:** Numbered steps for what this agent does
- **Output Format:** Already provided in skeleton

### Security Reviewer
- **Role:** Already provided. Add constraints.
- **Skills:** check-security (your custom skill from Prompt 03)
- **Can:** Read files, run security scan
- **Cannot:** Modify files, approve PRs
- **Output Format:** Already provided

### Quality Reviewer
- **Role:** Check code quality, patterns, TypeScript best practices
- **Process:** Steps matching what Security Reviewer does, but for quality
- **Output Format:** Define this (use same severity table as Security Reviewer)
- **Cannot:** Overlap with Security Reviewer (no security checks)

### Summary Writer
- **Role:** Synthesize all findings into a final verdict
- **Process:** Already provided
- **Output Format:** Already provided

Key rule: Each agent has ONE job. No overlap.
```

---

## Step 2: Add hooks

Add a Hooks section to AGENTS.md:

```
Add these hooks to AGENTS.md:

## Hooks

### PostToolUse Hook
After each agent produces output, validate the format:
- Check for required section headers
- Verify severity levels are valid (Critical/Major/Minor)
- Verify Summary Writer includes verdict (APPROVE / REQUEST CHANGES / BLOCK)

### Stop Hook
Before marking pipeline complete, verify:
1. All 4 agents produced output
2. Security Reviewer used the check-security skill
3. Summary Writer includes a final verdict
4. If any Critical findings exist, verdict must be REQUEST CHANGES or BLOCK
```

---

## Step 3: Verify your AGENTS.md

Read through the completed AGENTS.md and check:

- [ ] Each agent has a clear, non-overlapping role
- [ ] Security Reviewer references the check-security skill
- [ ] Constraints prevent agents from stepping on each other
- [ ] Hooks validate output format and completeness
- [ ] Summary Writer verdict logic accounts for severity levels
