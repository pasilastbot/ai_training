# Prompt 04: Define Your Agents with Hooks

**When to use:** PART 3 — BUILD step (after Agentic Architecture + Sub-Agents theory)
**Goal:** Complete AGENTS.md with agent roles, permissions, and hooks

---

## Step 1: Complete the agent definitions

```
@AGENTS.md.skeleton
@target/

Complete the AGENTS.md file. For each of the 4 agents, define:

### Code Analyzer
- **Role:** Inventory all testable units with complexity scores
- **Process:** Already provided (5 steps)
- **Output Format:** Already provided (testable units table)
- **Cannot:** Write tests (that's Test Writer's job)

### Test Strategist
- **Role:** Create a prioritized test plan
- **Process:** Already provided (5 steps)
- **Output Format:** Already provided (test plan table)
- **Priority criteria:** Define P0 (critical path), P1 (important), P2 (nice to have)
- **Cannot:** Write tests (only decides WHAT to test)

### Test Writer
- **Role:** Write actual test files following the strategy
- **Skills:** coverage-check (your custom skill from Prompt 03)
- **Process:** Already provided (5 steps)
- **Test Template:** Already provided (Given-When-Then)
- **Cannot:** Decide what to test (follows Test Strategist's plan)

### Coverage Reporter
- **Role:** Run tests and report coverage vs threshold
- **Skills:** coverage-check (the same custom skill)
- **Process:** Already provided (5 steps)
- **Output Format:** Already provided (coverage report)
- **Cannot:** Write tests (only reports coverage)

Key principle: Test Strategist decides WHAT to test,
Test Writer decides HOW. Coverage Reporter measures results.
```

---

## Step 2: Add hooks

Add a Hooks section to AGENTS.md:

```
Add these hooks to AGENTS.md:

## Hooks

### Stop Hook (Coverage Gate)
Before marking test generation complete:
1. Run coverage-check skill with 80% threshold
2. If FAIL: parse which files have low coverage
3. Send uncovered function list back to Test Writer
4. Test Writer adds missing tests
5. Maximum 2 retry cycles before accepting current coverage

### PostToolUse Hook
After Test Writer produces test files:
- Verify test files follow the Given-When-Then template
- Check that each P0 item from Test Strategist has tests
- Verify tests actually run (no syntax errors)
```

---

## Step 3: Verify your AGENTS.md

Read through the completed AGENTS.md and check:

- [ ] Each agent has a clear, non-overlapping role
- [ ] Test Writer and Coverage Reporter reference the coverage-check skill
- [ ] Test Strategist defines P0/P1/P2 priority criteria
- [ ] Hooks enforce the 80% coverage gate
- [ ] Maximum retry cycles prevent infinite loops
