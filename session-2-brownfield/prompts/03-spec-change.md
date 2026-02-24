# Prompt 03: Prompt a Change & Generate Specs Using SDD

**When to use:** PART 3 — First BUILD step
**Goal:** Pick a visible change to the game and write a grounded spec using Spec-Driven Development

---

## Step 1: Pick a change to the game

Choose something **visible** — you want to see the result in the browser. Pick ONE:

**Option A — Gameplay tweak:**
Change a weapon's stats, adjust player speed, modify loot drop rates, change the safe zone timing

**Option B — Visual change:**
Adjust colors, modify particle effects, change obstacle appearance, add screen shake on hit

**Option C — Small feature:**
Add a kill counter display, show damage numbers, add a minimap marker, change the death screen

**Option D — From GitHub issues:**
Browse https://github.com/HasangerGames/suroi/issues for a small, well-defined issue

---

## Step 2: Generate grounded specs using SDD

Use the 4-Step Process (Document → Spec → Develop → Audit):

```
@docs/[your-subsystem].md
@[relevant source files]

I want to make this change: [describe your chosen change]

Following Spec-Driven Development, write a change specification:

# Change Spec: [Name]

## Current Behavior
[What the code does now — reference the documentation we created]

## Proposed Change
[What it should do after the change]

## Acceptance Criteria
[Given/When/Then for each behavior change]

## Files to Modify
[List of files and what changes in each — be specific]

## Risk Assessment
[What could break? What subsystems could be affected?]

## Verification
[How to verify in the browser — what should I see/do to confirm it works?]

Ground the spec in our documentation:
- Reference the docs we created in Step 2
- Use the actual file paths and function names from the codebase
- Consider the architecture patterns we documented
```

---

## Step 3: Implement the spec

```
@[your change spec]
@[files to modify from the spec]

Implement this change following the spec exactly.

Requirements:
- Modify only the files listed in the spec
- Follow existing code patterns in this project
- Do not change any interfaces that other subsystems depend on
- After each file change, explain what you changed and why
```

---

## The "Is This Spec Ready?" Checklist

Before implementation:
- [ ] Every AC has Given/When/Then format
- [ ] Files to modify are listed with specific changes
- [ ] Risk assessment identifies what could break
- [ ] Verification describes what to look for in the browser
- [ ] The change is small enough to complete in 10 minutes
- [ ] The spec references our documentation (grounded, not vibe)
