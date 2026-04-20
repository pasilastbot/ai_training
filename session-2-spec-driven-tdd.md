# Session 2: Brownfield AI Development
**Duration:** 90 min | **Level:** Intermediate

**Prerequisites:** Session 1 (Greenfield with AI)

**Goal:** Production-grade development — understand before you change, grounded specs, sub-agents

**Theme:** 80% of enterprise work is brownfield (existing systems). This session teaches the discipline needed: **Document → Spec → Develop → Audit**. Vibe coding a change to a 100k+ line codebase is dangerous.

**Materials:** `session-2-brownfield/` prompts, Suroi codebase (114k LOC TypeScript battle royale)

---

## Session Flow

| # | Type | Topic | Duration |
|---|------|-------|----------|
| 1 | THEORY | Greenfield vs Brownfield | 10 min |
| 2 | THEORY | The 4-Step Process (AGENTS.md) | 5 min |
| 3 | THEORY | 3-Tiered Documentation & Navigation | 25 min |
| 4 | THEORY | Grounded Spec-Driven Development | 15 min |
| 5 | THEORY | Review, Audit & Fix Workflows | 15 min |

**Total: 70 min theory + 20 min rehearsals embedded**

---

## PART 1: GREENFIELD VS BROWNFIELD

### 1. The Strategic Shift (10 min)
**In greenfield you define — in brownfield you must discover first**

| Aspect | Greenfield | Brownfield |
|--------|------------|------------|
| **Context** | You define it | You must discover it |
| **Architecture** | Design for AI | Adapt AI to existing patterns |
| **Risk** | Low (fresh start) | High (breaking changes) |
| **AI Strength** | Generation | Understanding first, then changes |
| **Documentation** | Write as you build | Must create retroactively |

**Key insight:** Vibe coding a change to a 114k-line codebase is dangerous. You MUST understand before you change.

### Vibe Coding vs Spec-Driven

| Aspect | Vibe Coding | Spec-Driven (AGENTS.md) |
|--------|-------------|-------------------------|
| Speed | Fast start | Slower start, faster finish |
| Planning | Minimal | Thorough (4-step process) |
| Documentation | None/minimal | 3-tiered, navigable |
| Maintainability | Low | High (grounded specs) |
| Best for | Prototypes | Production, brownfield |

---

## PART 2: THE 4-STEP PROCESS

### 2. Document → Spec → Develop → Audit (5 min)
**Defined as workflows in AGENTS.md**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  DOCUMENT   │───▶│    SPEC     │───▶│   DEVELOP   │───▶│    AUDIT    │
│             │    │             │    │             │    │             │
│ Scan vs     │    │ Create      │    │ TDD: Red →  │    │ 6-pass      │
│ plan, gen   │    │ grounded    │    │ Green →     │    │ review,     │
│ 3-tier docs │    │ spec + ACs  │    │ Refactor    │    │ final gate  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │                   │                  │                  │
     ▼                   ▼                  ▼                  ▼
  research +          spec              tdd +             review +
  document           workflow          develop           audit + fix
```

This loop repeats for every change. Documentation builds up over time, making each cycle faster.

---

## PART 3: 3-TIERED DOCUMENTATION

### 3. Documentation Structure & Navigation (25 min)
**Each tier references the others — navigation up, down, and sideways**

#### The Three Tiers

| Tier | Location | Content | Navigation |
|------|----------|---------|------------|
| **T1 Architecture** | `docs/` | Purpose, tech stack, data model | → Tier 2 via subsystem refs |
| **T2 Subsystems** | `docs/subsystems/<name>/` | Interfaces, data flow, patterns | ↑ T1 ↓ T3 → other subsystems |
| **T3 Modules** | `docs/subsystems/<name>/modules/` | Implementation, @file refs | ↑ T2 → source code |

#### content-plan.md
**The index AI reads first**

```markdown
# Documentation Index — Example

| # | Module / Area | Tier | Status | Path | Priority |
|---|---------------|------|--------|------|----------|
| 1 | Architecture Overview | T1 | Done | docs/architecture.md | Critical |
| 2 | Data Model | T1 | Not Started | docs/datamodel.md | Critical |
| 3 | Auth Subsystem | T2 | In Progress | docs/subsystems/auth/ | High |
| 4 | Auth — Session Module | T3 | Not Started | docs/subsystems/auth/modules/session.md | Medium |

Generation order: Tier 1 first → Core T2 → Feature T2 → T3 last
```

#### Navigation Strategies

| Strategy | Flow | Use When |
|----------|------|----------|
| **Top-Down** | T1 → T2 → T3 → Code | Understanding structure, planning |
| **Feature-Wise** | content-plan → spec → subsystems → modules | Implementing features |
| **Package-Wise** | common → server → client | Debugging data flow |

---

### Sub-Agent Definitions
**One agent per workflow step — each follows its AGENTS.md workflow**

#### Documentation Agent
```markdown
Role: Runs the 'document' workflow

Process:
1. Read content-plan.md
2. Scan filesystem vs plan
3. Generate/update 3-tiered docs
4. Update content-plan.md

Can: Read all source, write docs/ only
Cannot: Edit source code or tests
Output: Scan report + updated docs
```

#### Spec Agent
```markdown
Role: Runs the 'spec' workflow

Process:
1. Study docs (grounding)
2. Create spec from template
3. Fill ACs, files, risk, tests
4. Run readiness checklist

Can: Read docs + code, write specs/
Cannot: Implement code or run tests
Output: Grounded spec ready for dev
```

#### Review Agent
```markdown
Role: Runs the 'review' + 'audit' workflows

Process:
1. Spec compliance audit
2. Test coverage audit
3. Security + architecture audit
4. Performance audit + verdict

Can: Read everything, write reports
Cannot: Modify implementation code
Output: Review report + PASS/FAIL
```

**Single Responsibility:** The doc agent never writes code. The spec agent never implements.

---

### Rehearsal: Orient to the Codebase (10 min)

Using the example brownfield codebase:

1. **Map** — Trace each row in content-plan.md to matching source directory
2. **Navigate** — Use all 3 strategies: top-down, feature-wise, package-wise
3. **Configure** — Paste a sub-agent definition into AGENTS.md with Can/Cannot boundaries

---

## PART 4: GROUNDED SPEC-DRIVEN DEVELOPMENT

### 4. The Spec Template (15 min)
**Grounded in documentation, not hallucinations**

```markdown
# Feature: [Name]

## Overview
- Status: Draft | Review | Approved
- Affected Subsystems: [list with Tier 2 links]
- Protocol Change: Yes/No

## Problem Statement
[What problem? Why needed?]

## Current Behavior
[Reference Tier 2/3 docs — what exists now]

## Proposed Change
[What it should do after implementation]

## Acceptance Criteria

### AC1: [Descriptive Name]
**Given** [precondition]
**When** [action]
**Then** [expected result]

## Files to Modify
| Package | File | Change |
|---------|------|--------|
| common | src/types/player.ts | Add field |
| server | src/objects/player.ts | Update logic |

## Risk Assessment
- What could break
- Performance impact
- Rollback plan

## Testing Strategy
- Unit tests for: [components]
- Integration tests for: [flows]
- Coverage target: [%]

## Related Documentation (MANDATORY)
- Tier 1: [link]
- Tier 2: [link]
- Tier 3: [link]
```

#### Grounded vs Ungrounded

| Ungrounded Spec | Grounded Spec |
|-----------------|---------------|
| "Add caching to the API" | Context: see docs/subsystems/api/ |
| No context, no doc refs | ACs with Given/When/Then |
| AI invents from imagination | Files: specific paths listed |
| | Risk: affects X serialization |
| | Tests: unit + integration |
| | Docs: links Tier 1, 2, 3 |

---

### Build: Write a Grounded Spec (10 min)

Use `prompts/03-spec-changes.md`:

1. Pick an improvement for a subsystem (reference content-plan.md)
2. Fill the spec template with grounded evidence
3. Run the readiness checklist:
   - Every AC testable?
   - Files listed?
   - Risk assessed?
   - Testing comprehensive?
   - All 3 tiers linked?

---

## PART 5: REVIEW, AUDIT & FIX WORKFLOWS

### 5. Quality Gates (15 min)
**Multi-pass review, final audit gate, systematic fixing**

#### Review: 6 Audit Passes

| Pass | Focus | Question |
|------|-------|----------|
| 1 | Spec Compliance | Every requirement met? |
| 2 | Test Coverage | Spec tests vs actual tests? |
| 3 | Security | Input validation, auth, secrets? |
| 4 | Architecture | Patterns, dependencies, data flow? |
| 5 | Performance | Queries, caching, bundle size? |
| 6 | Verdict | APPROVE \| REQUEST CHANGES \| BLOCK |

#### Audit: Final Gate

1. Completeness check (all ACs met?)
2. Run full review workflow
3. Documentation audit (docs updated?)
4. Final test run (coverage met?)

#### Fix Workflow

```
Gather Context → Hypothesize → Validate → Fix → Document
```

**3-Attempt Rule:** Never loop more than 3 times on the same issue without human input.

#### learnings.md
**Check FIRST when encountering errors**

```markdown
## [Date]: [Brief Issue Description]

### Context
[When/where this occurs]

### Symptom
[What you see]

### Root Cause
[Why it happens]

### Solution
[How to fix]

### Prevention
[How to avoid in future]
```

---

### Build: Review & Audit (10 min)

Use `prompts/04-implement.md`:

1. Run the 6-pass review on your spec change
2. Run the audit gate (PASS / FAIL / REQUIRES ADJUSTMENT)
3. If issues found, run the fix workflow
4. Document in learnings.md

---

## Key Takeaways

1. **Brownfield = understand before you change** — AGENTS.md is your process bible
2. **Document → Spec → Develop → Audit** — 4-step loop defined as named workflows
3. **3-tiered docs with cross-references** — AI navigates up, down, and across tiers
4. **Sub-agents with Can/Cannot** — single responsibility, non-overlapping roles
5. **Ground specs in evidence** — reference real docs, real code, real test plans
6. **6-pass review + audit gate** — fix workflow with 3-attempt rule + learnings.md

---

## Preparation for Session 3

Before the next session:
1. Write a spec for an existing codebase using the grounded template
2. Practice the 3-tiered navigation on a real project
3. Set up sub-agent definitions in your AGENTS.md
4. Think about: what happens when agents need to use external tools?
