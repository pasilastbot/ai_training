# Prompt 03: Prompt a Change & Generate Specs Using SDD

**When to use:** PART 3 — First BUILD step
**Goal:** Pick a visible change to the game and write a grounded spec using the AGENTS.md spec template

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

## Step 2: Write the spec yourself

Write a change spec using the spec template from AGENTS.md. Save it as `specs/[your-change].md`.

**Use the spec template from `AGENTS.md` (PART 2 → Workflow: spec → Spec Template) as your format.**

Your spec must include:
- **Current Behavior:** What the code does now — reference the docs you created in Prompt 02
- **Proposed Change:** What it should do after
- **Acceptance Criteria:** Given/When/Then for each behavior change
- **Files to Modify:** Specific files and what changes in each
- **Risk Assessment:** What could break? What subsystems could be affected?
- **Testing Strategy:** How to verify (browser verification for a game)

Ground the spec in your documentation:
- Reference the docs you created in Prompt 02
- Use actual file paths and function names from the codebase
- Consider the architecture patterns you documented

---

## Step 3: Ask AI to review your spec

```
@AGENTS.md
@specs/[your-change].md
@docs/subsystems/[your-subsystem]/README.md

Review this spec against the spec template in AGENTS.md:
1. Is every AC testable with a concrete assertion?
2. Are the files to modify correct and complete?
3. Does the risk assessment identify what could break?
4. Is the spec grounded in our documentation (not invented)?
5. Is the change small enough to complete in 10 minutes?

Check the Spec Readiness Checklist from AGENTS.md.
List any issues found.
```

Fix any issues before proceeding.

---

## Step 4: Implement the spec

```
@specs/[your-change].md
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

Before implementation, check against the AGENTS.md Spec Readiness Checklist:
- [ ] Every AC has Given/When/Then format
- [ ] Files to modify are listed with specific changes
- [ ] Risk assessment identifies what could break
- [ ] Testing strategy describes how to verify
- [ ] The change is small enough to complete in 10 minutes
- [ ] The spec references our documentation (grounded, not vibe)
