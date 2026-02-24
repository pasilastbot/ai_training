# Prompt 04: Code Review the Change Against the Spec

**When to use:** PART 3 — After Code Review with AI theory block
**Goal:** Review your implementation against the spec, verify in browser, audit quality

---

## Step 1: Verify in browser

After the code changes from Prompt 03:

1. Make sure `bun dev` is running
2. Open http://127.0.0.1:3000
3. Play the game and test your change

```
I've made the changes from the spec. Help me verify them:

1. What should I look for in the browser to confirm each acceptance criterion is met?
2. What should I check in the browser console?
3. What edge cases should I test manually?
```

---

## Step 2: Code review against the spec

Run a spec-grounded review — does the code match what we specified?

```
@specs/[your-change].md
@[files you modified]

Review my code changes against the spec.

For each acceptance criterion:
- Is it fully implemented? (YES / PARTIAL / NO)
- If PARTIAL or NO, what's missing?

Then do a quality review:
- Does the code follow existing patterns in the codebase?
- Are TypeScript types correct?
- Is error handling present where needed?
- Any performance concerns?
- Any safety issues that could affect other subsystems?

For each issue found, rate severity (Critical / Major / Minor) and suggest a fix.
```

---

## Step 3: Fix review findings (if time permits)

If the review found issues:

```
Fix these review findings:
[paste the issues]

After each fix, verify:
1. The fix doesn't break existing behavior
2. The change still works in the browser
3. The fix aligns with the spec
```

---

## Wrap-Up Reflection

After reviewing:
- How did documentation (`content-plan.md`, subsystem docs) help you navigate the codebase?
- Did writing the spec before coding prevent mistakes?
- What's the difference between "vibe coding" this change vs. grounding it with SDD?
- What did the AI code review catch that you might have missed?
