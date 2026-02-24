# Prompt 01: Explore the Pipeline Target

**When to use:** PART 1 — REHEARSAL step
**Goal:** Understand the sample PR diffs and what you'll automate

---

## Step 1: Examine the sample diffs

```
@target/sample-diff-1.patch
@target/sample-diff-2.patch

Read these two PR diffs. For each one, tell me:

1. What files are being changed?
2. What's the purpose of the change?
3. Do you spot any issues (security, quality, style)?
4. How severe are the issues?
```

---

## Step 2: Think about automation

Before building anything, consider:

- What patterns would you check for in EVERY code review?
- What's tedious to check manually but easy to script?
- What would catch the most critical issues first?

```
Based on these diffs, what are the top 5 things a code review
pipeline should check for? Rank by severity.
```

---

## What you should know after this step

- [ ] You've read both sample diffs
- [ ] You can identify security issues (SQL injection, hardcoded secrets)
- [ ] You can identify quality issues (error handling, patterns)
- [ ] You have an idea of what to automate first
