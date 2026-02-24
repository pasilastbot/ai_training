# Prompt 04: Define Your Agents with Hooks

**When to use:** PART 3 — BUILD step (after Agentic Architecture + Sub-Agents theory)
**Goal:** Complete AGENTS.md with agent roles, permissions, and hooks

---

## Step 1: Complete the agent definitions

```
@AGENTS.md.skeleton
@target/

Complete the AGENTS.md file. For each of the 4 agents, define:

### Code Scanner
- **Role:** Already provided. Inventories files, exports, imports.
- **Skills:** analyze-deps (your custom skill from Prompt 03)
- **Can:** Read files, run dependency analysis
- **Cannot:** Write files, modify code
- **Process:** Already provided
- **Output Format:** Already provided (inventory table)

### Architecture Mapper
- **Role:** Identify layers, data flow, entry points
- **Process:** Complete the 5 steps
- **Output Format:** Define this — include a text-based architecture diagram
- **Cannot:** Write documentation (that's Doc Writer's job)

### Doc Writer
- **Role:** Create 3-tiered documentation
- **Process:** Complete the 4 steps
- **Output Format:** Define this — specify the 3 tiers (README, module docs, inline comments)
- **Cannot:** Analyze code (that's Code Scanner/Architecture Mapper)

### Quality Checker
- **Role:** Already provided. Validates completeness and accuracy.
- **Checklist:** Already provided
- **Output Format:** Already provided (quality report)
- **Cannot:** Fix documentation (only reports issues)

Key principle: Code Scanner inventories, Architecture Mapper analyzes,
Doc Writer creates, Quality Checker validates. No overlap.
```

---

## Step 2: Add hooks

Add a Hooks section to AGENTS.md:

```
Add these hooks to AGENTS.md:

## Hooks

### PostToolUse Hook
After Doc Writer produces documentation, validate:
- README.md has required sections (Overview, Architecture, Getting Started)
- Each module file has corresponding documentation
- No placeholder text remains ("TODO", "TBD", "fill in later")
- @file references point to real files

### Stop Hook
Before marking pipeline complete, verify:
1. All 4 agents produced output
2. Code Scanner used the analyze-deps skill
3. All files in target/ have corresponding documentation
4. Quality Checker report shows no Critical issues
5. Maximum 2 retry cycles before accepting current docs
```

---

## Step 3: Verify your AGENTS.md

Read through the completed AGENTS.md and check:

- [ ] Each agent has a clear, non-overlapping role
- [ ] Code Scanner references the analyze-deps skill
- [ ] Constraints prevent agents from stepping on each other
- [ ] Hooks validate documentation completeness
- [ ] Quality Checker has a concrete validation checklist
