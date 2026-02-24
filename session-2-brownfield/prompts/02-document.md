# Prompt 02: Document the Codebase

**When to use:** PART 2 — After the 3-Tiered Documentation + Documentation Plan theory blocks
**Goal:** Create a content-plan.md and document your chosen subsystem using the AGENTS.md templates, then test & improve

---

## Step 1: Create content-plan.md

Use the Content Plan template from AGENTS.md to create the project documentation index.

```
@AGENTS.md
@codebase

Create a Documentation Content Plan (content-plan.md) for this project.

Use the Content Plan template from AGENTS.md (PART 1 → Content Plan → Template).
Follow the exact format: Overview, Documentation Index table (with Tier column),
Status Legend, Generation Order, and "What Each Document Must Include" section.

Fill in the Documentation Index by identifying all major subsystems in this codebase.
Mark all as "Not Started" since no docs exist yet.
Prioritize by importance for a new developer joining the project.
```

---

## Step 2: Document your subsystem (3-Tiered Approach)

Use the Tier 2 Subsystem README template from AGENTS.md to document your chosen subsystem.

```
@AGENTS.md
@[YOUR SUBSYSTEM KEY FILES]

Create documentation for [YOUR SUBSYSTEM] using the templates in AGENTS.md:

1. **Tier 2 — Subsystem README** (create docs/subsystems/[subsystem]/README.md):
   Use the "Subsystem README Template" from AGENTS.md (PART 1 → Tier 2).
   Include: Purpose, Key Files, Architecture, Data Flow, Interfaces, Dependencies.

2. **Update content-plan.md:**
   Add Tier 1 entry for this subsystem's high-level description.
   Mark your Tier 2 doc as "Done".

3. **Tier 3 — Code-Level:**
   Suggest inline comments for the 3-5 most complex functions.
   Document any implicit behavior or assumptions.

Make the documentation AI-navigable:
- Use @file references for related code
- Include cross-tier references (link up to Tier 1, down to Tier 3)
- Include "See also" references to related subsystems
```

---

## Step 3: Test & improve your docs

> This step runs during BUILD step 9 (5 min), after the Architecture theory side bite.

Test your documentation by asking AI questions that require understanding the code. If AI can't answer using your docs, improve them.

```
@content-plan.md
@docs/subsystems/[your-subsystem]/README.md

I'm a new developer on this project. Using ONLY the documentation above, answer these:

1. How would I add a new [entity/weapon/message/obstacle/effect] to [your subsystem]?
2. What files would I need to modify?
3. What would I need to be careful about (side effects, dependencies)?

If you can't answer any of these from the docs alone, tell me what's missing.
```

Then fix the gaps:

```
The documentation is missing [what AI identified].
Update docs/subsystems/[your-subsystem]/README.md to include this information.
```

---

## What you should have after this step

- [ ] `content-plan.md` following the AGENTS.md template format
- [ ] `docs/subsystems/[your-subsystem]/README.md` following the Tier 2 template
- [ ] Updated `content-plan.md` marking your subsystem as "Done"
- [ ] Documentation tested by asking AI questions — gaps filled
