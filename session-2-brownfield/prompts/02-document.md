# Prompt 02: Document the Codebase

**When to use:** PART 2 — After the 3-Tiered Documentation + Documentation Plan theory blocks
**Goal:** Create a content-plan.md and document your chosen subsystem, then test & improve

---

## Step 1: Create content-plan.md

Create `content-plan.md` in the Suroi project root:

```
@codebase

Create a Documentation Content Plan (content-plan.md) for this project.

The plan should:
1. List all major subsystems that need documentation
2. Mark their documentation status (none exist yet, so all are "Not Started")
3. Prioritize them by importance for a new developer
4. Specify what each doc should cover

Use this format:

# Documentation Content Plan

## Overview
[Brief project description]

## Documentation Index
| # | Module | Status | Path | Priority |
|---|--------|--------|------|----------|
| 1 | Architecture Overview | Not Started | docs/architecture.md | Critical |
| 2 | ... | ... | ... | ... |

## Generation Instructions
[Order to generate docs in, what to include]
```

---

## Step 2: Document your subsystem (3-Tiered Approach)

Now create documentation for your chosen subsystem using all 3 tiers:

```
@[YOUR SUBSYSTEM KEY FILES]

Create 3-tiered documentation for [YOUR SUBSYSTEM]:

**Tier 1 — High-Level (add to content-plan.md):**
- Purpose of this subsystem
- Key design decisions
- Entry points

**Tier 2 — Module Overview (create docs/[subsystem].md):**
- How the subsystem works step by step
- Data flow diagram (text-based)
- Key interfaces and their relationships
- Dependencies on other subsystems

**Tier 3 — Code-Level:**
- Suggest inline comments for the 3-5 most complex functions
- Document any implicit behavior or assumptions

Make the documentation AI-navigable:
- Use @file references for related code
- Link between tiers
- Include "See also" references
```

---

## Step 3: Test & improve your docs

> This step runs during BUILD step 9 (5 min), after the Architecture theory side bite.

Now test your documentation by asking AI questions that require understanding the code. If AI can't answer using your docs, improve them.

```
@content-plan.md
@docs/[your-subsystem].md

I'm a new developer on this project. Using ONLY the documentation above, answer these:

1. How would I add a new [entity/weapon/message/obstacle/effect] to [your subsystem]?
2. What files would I need to modify?
3. What would I need to be careful about (side effects, dependencies)?

If you can't answer any of these from the docs alone, tell me what's missing.
```

Then fix the gaps:

```
The documentation is missing [what AI identified].
Update docs/[your-subsystem].md to include this information.
```

---

## What you should have after this step

- [ ] `content-plan.md` listing all subsystems
- [ ] `docs/[your-subsystem].md` with Tier 2 documentation
- [ ] Updated `content-plan.md` marking your subsystem as "Done"
- [ ] Documentation tested by asking AI questions — gaps filled
- [ ] Understanding of how the 3-tiered structure helps AI navigate
