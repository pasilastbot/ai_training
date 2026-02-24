# AGENTS.md — Project Agent Configuration

> This file configures AI agent behavior across three domains:
> **Documentation**, **Spec-Driven Development**, and **Skills & Tools**.
> Each section is independent but they reference each other where needed.

---

# PART 1: Documentation Plan

The documentation plan defines a **3-tiered documentation structure** with
explicit cross-references between tiers. AI agents use this structure to
navigate from high-level architecture down to specific implementations and back.

## Tier Structure

```
┌─────────────────────────────────────────────────────────┐
│  TIER 1 — Architecture & High-Level                     │
│  Purpose, tech stack, system boundaries, data model     │
│  Location: docs/                                        │
│  Navigation: Tier 1 → Tier 2 (via subsystem references) │
├─────────────────────────────────────────────────────────┤
│  TIER 2 — Subsystems                                    │
│  Domain-specific subsystems, interfaces, data flow      │
│  Location: docs/subsystems/<name>/                      │
│  Navigation: ↑ Tier 1 | ↓ Tier 3 | → Other subsystems  │
├─────────────────────────────────────────────────────────┤
│  TIER 3 — Modules & Code-Level                          │
│  Implementation patterns, business rules, inline docs   │
│  Location: docs/subsystems/<name>/modules/              │
│  Navigation: ↑ Tier 2 | → Source code (@file refs)      │
└─────────────────────────────────────────────────────────┘
```

Each tier **must** reference related documents in other tiers, enabling
navigation in both directions (drill-down and bubble-up).

---

## Content Plan (content-plan.md)

The content plan is the **index of all project documentation**. It tracks what
exists, what's missing, and in what order docs should be generated. AI agents
read this first to understand the documentation landscape.

### Template

```markdown
# Documentation Content Plan

## Overview
[1-2 sentence project description. What does this system do?]

## Documentation Index

| # | Module / Area | Tier | Status | Path | Priority | Last Updated |
|---|---------------|------|--------|------|----------|--------------|
| 1 | Architecture Overview | T1 | Done | docs/architecture.md | Critical | 2025-01-15 |
| 2 | Data Model | T1 | Done | docs/datamodel.md | Critical | 2025-01-15 |
| 3 | Auth Subsystem | T2 | Done | docs/subsystems/auth/ | Critical | 2025-01-20 |
| 4 | Auth — Session Module | T3 | In Progress | docs/subsystems/auth/modules/session.md | High | — |
| 5 | Payments Subsystem | T2 | Not Started | docs/subsystems/payments/ | High | — |
| 6 | Notifications Subsystem | T2 | Not Started | docs/subsystems/notifications/ | Medium | — |

## Status Legend
- **Done** — Written, reviewed, up-to-date with current code
- **In Progress** — Draft exists, may be incomplete or outdated
- **Not Started** — Needs to be written
- **Outdated** — Exists but doesn't match current code

## Generation Order
Generate documentation in dependency order:
1. **Tier 1 first** — Architecture, data model, development guide (everything depends on these)
2. **Core Tier 2 next** — Subsystems that other subsystems depend on (auth, database, shared libraries)
3. **Feature Tier 2** — Business logic subsystems (ordered by developer priority)
4. **Tier 3 last** — Module docs within each subsystem (ordered by complexity)

## What Each Document Must Include
- Purpose and scope
- Key files and entry points (with `@file` references to source code)
- Data flow (how data moves through the module)
- Dependencies on other modules (with links to their Tier 2/3 docs)
- Cross-tier references ("See also" links up and down the tiers)
- Known issues, tech debt, or gotchas
```

---

## Tier 1: Architecture & High-Level Documentation

_Location:_ `docs/`
_Navigation:_ Tier 1 → Tier 2 (subsystem references) | → content-plan.md

Tier 1 provides the system-wide view. Every document here covers the **entire
system**, not individual subsystems.

### Required Documents

| # | Document | Path | Covers |
|---|----------|------|--------|
| 1 | Project Description | `docs/description.md` | Purpose, target users, key features, business domain |
| 2 | System Architecture | `docs/architecture.md` | Tech stack, folder structure, component map, deployment |
| 3 | Data Model | `docs/datamodel.md` | Core entities, schema overview, relationships |
| 4 | Development Guide | `docs/development.md` | Setup, commands, code standards, testing, local dev |
| 5 | API Reference | `docs/api-reference.md` | REST endpoints, auth, request/response formats |

### Optional Documents (add as project grows)

| # | Document | Path | Covers |
|---|----------|------|--------|
| 6 | Security | `docs/security.md` | Auth flow, authorization, data protection |
| 7 | Deployment | `docs/deployment.md` | Environments, CI/CD, infrastructure |
| 8 | Integration Guide | `docs/integration.md` | External services, third-party APIs |
| 9 | Features & Use Cases | `docs/features.md` | Feature inventory, use case documentation |
| 10 | Terminology | `docs/terminology.md` | Domain-specific terms and definitions |

### Tier 1 Document Template

```markdown
# [Document Title]

<!-- @tier: 1 -->
<!-- @see-also: docs/subsystems/[relevant]/ -->

## Overview
[What this document covers and why it matters]

## [Main Content]
[Architecture diagrams, data model, API overview, etc.]

## Subsystem References
Navigate to Tier 2 for subsystem details:
- [Subsystem A](docs/subsystems/subsystem-a/) — [1-line description]
- [Subsystem B](docs/subsystems/subsystem-b/) — [1-line description]

## Related Documents
- **Tier 1:** [links to other Tier 1 docs]
- **Tier 2:** [links to relevant subsystem docs]
```

---

## Tier 2: Subsystem Documentation

_Location:_ `docs/subsystems/<subsystem-name>/`
_Navigation:_ ↑ Tier 1 (architecture) | ↓ Tier 3 (modules) | → Other subsystems

Each major subsystem gets its own folder with a README and supporting docs.
Tier 2 documents describe **how a subsystem works** — its boundaries,
interfaces, data flow, and dependencies on other subsystems.

### Folder Structure Per Subsystem

```
docs/subsystems/<subsystem-name>/
├── README.md              # Subsystem overview (required)
├── patterns.md            # Reusable patterns within this subsystem
├── modules/               # Tier 3: module-level docs
│   ├── <module-a>.md
│   └── <module-b>.md
└── [additional docs as needed]
```

### Subsystem README Template

```markdown
# [Subsystem Name]

<!-- @tier: 2 -->
<!-- @parent: docs/architecture.md -->
<!-- @modules: docs/subsystems/[name]/modules/ -->
<!-- @source: src/[subsystem-path]/ -->

## Purpose
[What this subsystem does — 1-2 sentences]

## Key Files & Entry Points
| File | Purpose |
|------|---------|
| `src/[path]/index.ts` | Main entry point |
| `src/[path]/routes.ts` | Route definitions |
| `src/[path]/service.ts` | Business logic |

## Architecture
[How this subsystem is structured internally]

## Data Flow
```
Input → [Step 1] → [Step 2] → [Step 3] → Output
```
[Describe how data moves through the subsystem]

## Interfaces & Contracts
[Public APIs, exported functions, event contracts]

## Dependencies
- **Depends on:** [List other subsystems this one calls]
  - [Subsystem X](../subsystem-x/) — for authentication
  - [Subsystem Y](../subsystem-y/) — for data access
- **Depended on by:** [List subsystems that call this one]

## Module Index (Tier 3)
For implementation details, see:
- [Module A](modules/module-a.md) — [1-line description]
- [Module B](modules/module-b.md) — [1-line description]

## Related Documents
- **Tier 1:** [docs/architecture.md](../../architecture.md) — System overview
- **Tier 2:** [links to related subsystems]
- **Tier 3:** [links to modules within this subsystem]
- **Patterns:** [patterns.md](patterns.md) — Reusable patterns
```

### Subsystem Patterns Template (patterns.md)

```markdown
# [Subsystem Name] — Patterns

<!-- @tier: 2 -->
<!-- @parent: docs/subsystems/[name]/README.md -->

## Pattern: [Pattern Name]
**When to use:** [Trigger condition]
**Implementation:**
[Code example or step-by-step description]
**Example files:** `@file src/[path]/example.ts`

## Pattern: [Pattern Name]
...
```

---

## Tier 3: Module & Code-Level Documentation

_Location:_ `docs/subsystems/<subsystem-name>/modules/`
_Navigation:_ ↑ Tier 2 (subsystem README) | → Source code (@file references)

Tier 3 documents describe **specific modules or components** within a subsystem.
They are the bridge between documentation and source code.

### Module Document Template

```markdown
# [Module Name]

<!-- @tier: 3 -->
<!-- @parent: docs/subsystems/[name]/README.md -->
<!-- @source: src/[subsystem]/[module]/ -->

## Purpose
[What this module does — 1 sentence]

## Key Files
| File | Purpose | Complexity |
|------|---------|------------|
| `src/[path]/handler.ts` | Request handling | Medium |
| `src/[path]/validator.ts` | Input validation | Low |
| `src/[path]/transformer.ts` | Data transformation | High |

## Business Rules
- [Rule 1: describe the business logic this module enforces]
- [Rule 2: configuration or settings that affect behavior]

## Data Lineage
[How data flows through this module — map inputs to outputs]
```
API field → validation → transformation → database column
```

## Dependencies
- **Internal:** [Other modules in same subsystem]
- **External:** [Modules in other subsystems, with Tier 2 links]

## Complex Functions
Document functions where behavior isn't obvious from reading the code:

### `functionName(params)` — @file src/[path]/file.ts:42
**Purpose:** [What it does]
**Implicit behavior:** [Side effects, assumptions, gotchas]
**Called by:** [What invokes this function]

## Configuration
| Setting | Effect | Default |
|---------|--------|---------|
| `FEATURE_FLAG_X` | Enables [behavior] | `false` |

## Related Documents
- **Tier 2:** [../README.md](../README.md) — Subsystem overview
- **Tier 1:** [../../architecture.md](../../architecture.md) — System architecture
- **Patterns:** [../patterns.md](../patterns.md) — Subsystem patterns
```

---

## Documentation Navigation

AI agents navigate documentation using **two complementary strategies**.
Always use both together when planning or implementing.

### Strategy 1: Top-Down (Architecture-Level)

Navigate from system overview down to specific code:

```
Tier 1: docs/architecture.md                    → System overview
  ↓
Tier 2: docs/subsystems/<name>/README.md         → Subsystem details
  ↓
Tier 3: docs/subsystems/<name>/modules/<mod>.md  → Module specifics
  ↓
Code:   src/<subsystem>/<module>/                → Source files
```

**Use when:** Understanding structure, planning architectural changes, onboarding.

### Strategy 2: Feature-Wise (Use-Case Driven)

Navigate from a feature/use case to its implementation:

```
content-plan.md                          → Find the feature area
  ↓
specs/features/<feature>.md              → Read the spec (ACs, files)
  ↓
docs/subsystems/<affected>/README.md     → Understand affected subsystems
  ↓
docs/subsystems/<affected>/modules/*.md  → Module implementation details
  ↓
src/                                     → Source code
```

**Use when:** Implementing features, fixing bugs, tracing end-to-end flows.

### Navigation Rules

1. **Start with content-plan.md** — understand what's documented, what's missing
2. **Use both strategies together** — feature context + architecture context
3. **Follow cross-tier references** — every doc links up and down the tiers
4. **Follow @file references** — docs link to specific source files
5. **Update docs when code changes** — documentation is a living artifact
6. **Only work within documented subsystems** — if a subsystem isn't documented, list it but do not explore further

---

# PART 2: Spec-Driven Development

The spec-driven workflow follows a 4-step process:
**Document → Spec → Develop → Audit**

This section defines each workflow independently. They chain together but can
also be used standalone.

## Workflow: research

**Goal:** Understand a task thoroughly before planning.

**Steps:**
1. **Gather Context:**
   - Navigate documentation using **both strategies** (top-down + feature-wise)
   - Start at Tier 1 for high-level context
   - Dive to Tier 2 for affected subsystem details
   - Check Tier 3 for module implementation patterns
   - Search codebase for existing code patterns
   - Search web for external API/library documentation
2. **Identify Scope:**
   - Which subsystems are affected?
   - What business rules apply?
   - What configuration controls the behavior?
   - What cross-subsystem dependencies exist?
3. **Analyze & Plan:**
   - Synthesize information from all documentation tiers
   - Outline what needs to be done
   - Identify missing information
4. **Present Findings:**
   - State the analysis, plan, and referenced documentation
   - Ask clarifying questions if needed

---

## Workflow: document

**Goal:** Scan the filesystem against the documentation plan and update documentation.

**Steps:**
1. **Read Content Plan:**
   - Read `content-plan.md` to understand what exists and what's missing
   - Note the status of each entry (Done, In Progress, Not Started, Outdated)
   - Identify the generation order and priorities
2. **Scan Filesystem:**
   - Recursively scan all source directories
   - For each file: identify exports, classes, functions, public APIs
   - Map import/export relationships between modules
   - Compare discovered modules against the content plan:
     - **Undocumented:** Source code exists, no corresponding docs
     - **Outdated:** Docs exist but don't match current code structure
     - **Orphaned:** Docs reference files that no longer exist
     - **Complete:** Docs exist and match current code
3. **Generate / Update Documentation:**
   - Follow the tier structure and templates from PART 1
   - **Tier 1 first** — architecture, data model, development guide
   - **Tier 2 next** — subsystem READMEs for each major area
   - **Tier 3 last** — module docs for complex or critical modules
   - Every document must include cross-tier references (up, down, sideways)
   - Use `@file` references to link docs to specific source files
4. **Update Content Plan:**
   - Update `content-plan.md` with new statuses and dates
   - Add newly discovered modules that need documentation
   - Remove entries for deleted source files

**Output:**

```markdown
## Documentation Scan Report
| Area | Tier | Status Before | Status After | Path |
|------|------|---------------|--------------|------|
| [module] | T1/T2/T3 | Not Started | Done | docs/... |

## Summary
- Documented: [X] modules
- Undocumented remaining: [Y] modules
- Outdated: [Z] documents
- Coverage: [X/(X+Y)]% of source modules have documentation
```

---

## Workflow: spec

**Goal:** Create a specification before implementation.

**When Required:** New features, major refactorings, API changes, architectural changes, multi-subsystem changes.
**When Optional:** Bug fixes, minor refactorings, documentation updates, config changes, single-file changes.

**Steps:**
1. **Study Documentation (Grounding):**
   - Read relevant docs from all 3 tiers using both navigation strategies
   - Understand existing patterns, business rules, and data flow
   - Ground the spec in documentation — reference actual files and patterns
2. **Create Spec:** `specs/features/<feature-name>.md`

### Spec Template

```markdown
# Feature: [Name]

## Overview
- **Status:** Draft | Review | Approved | In Progress | Done
- **Created:** [Date]
- **Affected Subsystems:** [List — with links to Tier 2 docs]

## Problem Statement
[What problem does this solve? Why is it needed?]

## Current Behavior
[What the system does now — reference Tier 2/3 docs]

## Proposed Change
[What it should do after implementation]

## Acceptance Criteria

### AC1: [Descriptive name]
**Given** [precondition — system state before]
**When** [action — what the user/system does]
**Then** [expected result — observable outcome]

### AC2: [Descriptive name]
**Given** [precondition]
**When** [action]
**Then** [result]

## Files to Modify

| File | Change Description |
|------|--------------------|
| `src/[path]/file.ts` | [What changes and why] |

## Risk Assessment
- **What could break:** [List affected subsystems]
- **Rollback plan:** [How to undo]
- **Dependencies:** [External services, other teams]

## Testing Strategy (MANDATORY — must be comprehensive)

### Unit Tests
For each function/component, define specific test cases:
| Function | Test Case | Given | When | Then | Mocks |
|----------|-----------|-------|------|------|-------|
| `functionA` | happy path | [setup] | [action] | [result] | [deps] |
| `functionA` | edge case | [setup] | [action] | [result] | [deps] |
| `functionA` | error | [setup] | [action] | [error] | [deps] |

### Integration Tests
API endpoint or service layer tests with real dependencies:
| Scenario | Method | Input | Expected Output | Status Code |
|----------|--------|-------|----------------|-------------|
| [happy path] | POST /api/x | {...} | {...} | 200 |
| [error case] | POST /api/x | {...} | {...} | 400 |

### E2E Tests (if applicable)
User flow scenarios from start to finish:
| User Journey | Steps | Expected Outcome |
|-------------|-------|-----------------|
| [happy path] | 1. ... 2. ... 3. ... | [result] |
| [error flow] | 1. ... 2. ... | [error handled] |

### Coverage Target
- Minimum: [X]% (e.g., 80%)
- Critical paths: 100%

### Test Data
- Fixtures: [describe test data needed]
- Mocks: [list external dependencies to mock]

## Related Documentation (MANDATORY)
- **Tier 1:** [Link to architecture/data model docs]
- **Tier 2:** [Link to subsystem docs]
- **Tier 3:** [Link to module docs]
- **Patterns:** [Link to relevant patterns]
```

### Spec Readiness Checklist
- [ ] Every AC has Given/When/Then format
- [ ] Files to modify are listed with specific changes
- [ ] Risk assessment identifies what could break
- [ ] Testing strategy is comprehensive (unit + integration + E2E)
- [ ] Every functional requirement has corresponding test case(s)
- [ ] Every user story has corresponding E2E scenario(s)
- [ ] Error conditions and edge cases are covered in tests
- [ ] Coverage target is defined
- [ ] Related Documentation links all 3 tiers
- [ ] Spec is grounded in existing docs (not invented from scratch)

**Validation:** If the testing strategy is incomplete (missing test cases for requirements, no edge cases, no coverage target), the spec is NOT ready for approval. Complete the testing strategy before proceeding.

---

## Workflow: tdd

**Goal:** Implement a feature using Test-Driven Development — Red → Green → Refactor.

**When to Use:** New features with clear requirements, business logic, API endpoints, utility functions, bug fixes (write test that reproduces bug first).

**Prerequisites:** A spec with comprehensive Testing Strategy section (run `spec` workflow first).

### TDD Principles
- **Red:** Write a failing test first (test what doesn't exist yet)
- **Green:** Write minimal code to make the test pass (simplest implementation)
- **Refactor:** Improve code quality while keeping all tests passing
- **Iterate:** Repeat for each requirement until feature is complete

### Steps

**1. Preparation:**
- Read the specification file (`specs/features/<feature-name>.md`)
- Extract all functional requirements and acceptance criteria
- Review the Testing Strategy section — this is your roadmap
- Prioritize: start with core logic, then edge cases, then integrations
- Set up test infrastructure (test files, fixtures, mocks)
- Verify test framework runs with an empty test

**2. TDD Cycle — for EACH requirement:**

```
Phase 1: RED (Write Failing Test)
├── Pick the next unimplemented requirement from spec
├── Write a test that describes the desired behavior
│   ├── Test name describes the requirement
│   ├── Given: set up test data and mocks
│   ├── When: call the function/method that doesn't exist yet
│   └── Then: define expected outcome
├── Write ONLY the test — NO implementation code
└── Run test → confirm it FAILS for the right reason

Phase 2: GREEN (Make Test Pass)
├── Write the SIMPLEST code that makes the test pass
├── Implement ONLY what's needed for THIS test
├── Do not over-engineer or optimize
├── Run test → confirm it PASSES
└── Run ALL tests → confirm no regressions

Phase 3: REFACTOR (Improve Code)
├── Review implementation for improvements:
│   ├── Remove duplication (DRY)
│   ├── Improve naming
│   ├── Extract reusable functions
│   └── Improve readability
├── Run ALL tests after EACH refactoring
└── CRITICAL: Tests must stay green throughout
```

**3. Edge Cases & Error Conditions:**
After core functionality works, repeat TDD cycle for:
- Invalid inputs (null, empty, wrong type)
- Boundary conditions (min/max values, empty arrays)
- Error scenarios (network failures, database errors)
- Each edge case: RED → GREEN → REFACTOR

**4. Integration Tests (if applicable):**
Once unit tests pass, apply same TDD cycle for integration:
- Test interactions between modules, API endpoints, database
- RED: Write integration test that fails
- GREEN: Wire up components to make it pass
- REFACTOR: Improve integration code

**5. E2E Tests (if applicable):**
Once integration works, apply TDD cycle for user flows:
- RED: Write E2E test for complete user journey
- GREEN: Complete implementation to make flow work
- REFACTOR: Improve UX/code

**6. Continuous Validation:**
- Run full test suite frequently
- Check test coverage against spec's target
- If coverage below target, identify untested paths and write tests

**7. Verify Against Spec:**
- Review every requirement in the spec — does it have tests?
- Review every AC — is it met?
- All tests pass? Coverage target met?

**8. Final Refactoring Pass:**
- Review ALL implementation code for final improvements
- Run full test suite after each change
- All tests must remain green

### Test Template

```typescript
describe('[FunctionName]', () => {
  it('should [expected behavior] when [condition]', () => {
    // Given: [setup — preconditions]
    // When: [action — call the function]
    // Then: [assertion — verify result]
  });

  it('should [handle edge case] when [boundary condition]', () => {
    // Given / When / Then
  });

  it('should [error behavior] when [invalid input]', () => {
    // Given / When / Then
  });
});
```

### TDD Best Practices
- **Baby steps:** Smallest possible test, then smallest code to pass it
- **Test first, always:** Never write implementation before writing the test
- **One test at a time:** Focus on one test before writing the next
- **Refactor fearlessly:** With tests as safety net, refactor aggressively
- **Keep tests fast:** Unit tests should run in milliseconds
- **Meaningful names:** Test names should describe what they verify
- **Test behavior, not implementation:** Test what code does, not how
- **No skipping RED:** Always verify the test actually fails first

### TDD Progress Tracking
Track requirement status: `❌ No test → 🔴 RED → 🟢 GREEN → ✅ Refactored`

---

## Workflow: develop

**Goal:** Implement code following the spec and project patterns.

**Steps:**
1. **Check for Spec:** If complex task, read `specs/features/<name>.md`. If none exists, ask whether to create one first.
2. **Research Patterns:** Navigate Tier 2 and Tier 3 docs for the affected subsystem. Read `patterns.md` for reusable patterns.
3. **Implement:** Follow documented patterns. Match existing code style. Update only files listed in the spec.
4. **TDD:** Use acceptance criteria from spec as test cases. Run `tdd` workflow.
5. **Update Docs:** Update affected Tier 2/3 docs. Mark spec status as "In Progress" → "Done".

---

## Workflow: review

**Goal:** Comprehensive multi-pass review of an implementation against its specification, including security, architecture, performance, and testing audits.

**When to Use:** After feature implementation is complete, before marking as production-ready, or when reviewing changes for correctness.

### Steps

**1. Preparation:**
- Identify the specification file (`specs/features/<feature-name>.md`)
- Read the complete specification
- Identify all files created/modified for this feature
- Read all implementation files
- Locate test files

**2. Spec Compliance Audit:**

a. **Requirements Verification:**
For each functional requirement in the spec:
- ✅ Fully implemented and working
- ⚠️ Partially implemented or has limitations
- ❌ Not implemented
Document evidence (file names, line numbers, test results).

b. **Acceptance Criteria:**
For each AC in spec, mark as met ✅ or unmet ❌.
Calculate: X/Y acceptance criteria met.

c. **Files Verification:**
Compare "Files to Modify" in spec vs actual files changed.
Document any missing or unexpected files.

d. **API Contract Verification (if applicable):**
For each endpoint specified, verify implementation exists.
Check request/response formats match spec.

**3. Test Coverage Audit:**

| Category | Spec Requires | Actually Written | Coverage |
|----------|--------------|-----------------|----------|
| Unit tests | [count] | [count] | [X]% |
| Integration tests | [count] | [count] | [X]% |
| E2E tests | [count] | [count] | [X]% |

- Compare spec's test cases vs implemented tests
- Run test coverage tool, compare to spec's target
- **List missing tests explicitly**
- Identify: tests specified but not written

**4. Security Audit:**

a. **Input Validation:**
- All user inputs validated?
- SQL injection vulnerabilities (raw queries, string concatenation)?
- XSS vulnerabilities (innerHTML, dangerouslySetInnerHTML, eval)?

b. **Authentication & Authorization:**
- Auth mechanisms correct?
- Hardcoded credentials?
- API endpoints properly protected?

c. **Data Protection:**
- Secrets in code (API keys, passwords, tokens)?
- Sensitive data in logs?
- Environment variables used for secrets?

d. **Dependencies:**
- Run security audit (npm audit, pip-audit, etc.)
- Known vulnerabilities in dependencies?

**5. Architecture Audit:**

a. **Code Organization:**
- Separation of concerns (UI, business logic, data access)?
- Circular dependencies?
- Code smells (God classes, duplicated code)?

b. **Design Patterns:**
- Consistent with project architecture (docs/architecture.md)?
- Patterns applied correctly?

c. **Data Flow:**
- Trace data flow end-to-end
- Error propagation correct?
- Proper async/await usage?

d. **Scalability:**
- N+1 query problems?
- Pagination implemented?
- Memory leaks (unclosed connections, event listeners)?
- Algorithmic complexity acceptable?

**6. Performance Audit:**

- Database query efficiency
- API response times
- Caching opportunities
- Bundle sizes (frontend)
- Unnecessary re-renders or watchers
- Asset optimization

### Output Format

```markdown
## Review Report: [Feature Name]

### Executive Summary
- Spec compliance: [X]%
- Test coverage: [X]% (target: [Y]%)
- Security issues: [X] critical, [Y] high, [Z] medium
- Production ready: Yes / No / Partial

### Spec Compliance
| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| FR-1 | [desc] | ✅/⚠️/❌ | [file:line] |

### Security Findings
| # | Severity | File:Line | Issue | Recommendation |
|---|----------|-----------|-------|----------------|

### Architecture Findings
| # | Severity | File:Line | Issue | Recommendation |
|---|----------|-----------|-------|----------------|

### Performance Findings
| # | Severity | File:Line | Issue | Recommendation |
|---|----------|-----------|-------|----------------|

### Missing Tests
[List of tests specified but not written]

### Verdict: APPROVE | REQUEST CHANGES | BLOCK
[1-2 sentence recommendation for what to do next]
```

### Review Principles
- **Be honest:** Don't claim 100% if it's 78%. Identify real gaps.
- **Be specific:** Cite line numbers, file names, test names.
- **Be constructive:** For each issue, suggest a fix.
- **Be thorough:** Check everything the spec requires.
- **Be practical:** Distinguish "must fix before production" vs "nice to have later".

---

## Workflow: fix

**Goal:** Diagnose and resolve errors systematically.

**Steps:**
1. **Gather Context** — check `docs/learnings.md`, affected Tier 2/3 docs, error messages
2. **Hypothesize** — identify 1-2 likely causes
3. **Validate** — add temporary logging, run tests
4. **Fix** — smallest change that resolves the issue
5. **Verify** — all tests pass, no regressions
6. **Document** — record solution in `docs/learnings.md`

Do not loop more than 3 times without asking for help.

---

## Workflow: audit

**Goal:** Post-implementation audit — verify completeness, then run `review` for depth.

**When to Use:** After a feature is "done" — before merging or marking complete.
Unlike `review` (which can run during development), `audit` is the **final gate**.

**Steps:**
1. **Completeness Check:**
   - Read the spec (`specs/features/<feature-name>.md`)
   - Verify every acceptance criterion is met (✅ / ❌)
   - Verify every file listed in spec was created/modified
   - Verify documentation was updated (Tier 2/3 docs, content-plan.md)
   - Verify spec status is updated to "Done"
2. **Run Review:**
   - Execute the `review` workflow (above) for full multi-pass audit
   - This covers: spec compliance, tests, security, architecture, performance
3. **Documentation Audit:**
   - Run `document` workflow in scan-only mode
   - Verify new code has corresponding documentation
   - Verify cross-tier references are intact
4. **Final Test Run:**
   - Run complete test suite
   - Verify coverage meets spec target
   - No skipped or TODO tests
5. **Produce Audit Summary:**

```markdown
## Audit Summary: [Feature Name]

### Completeness
- Acceptance criteria: [X/Y] met
- Files: [all present / missing: ...]
- Docs updated: Yes / No
- Spec status: Done / Not updated

### Review Results
[Link to or embed review report]

### Verdict: PASS | FAIL | REQUIRES ADJUSTMENT
[What must be fixed before this can ship]
```

**Max retries:** If audit fails, fix issues and re-audit. Maximum 3 cycles before escalating to human review.

---

## Request Processing Steps

For every user request:

1. **Read the request** — identify goal, affected subsystems, complexity
2. **Navigate documentation** — use both strategies (top-down + feature-wise), consult all 3 tiers
3. **Determine complexity:**
   - **Complex** (new feature, refactor, multi-file) → run `spec` workflow first
   - **Simple** (bug fix, config, single-file) → proceed to `develop` directly
4. **Present analysis:**
   ```
   Request type: [type]
   Complexity: [Complex | Simple]
   Spec required: [Yes | No]
   Workflow: [spec → develop → tdd | develop → tdd | fix | research]
   Affected subsystems: [list with Tier 2 doc links]
   Documentation refs: [Tier 1, 2, 3 docs consulted]
   ```
5. **Execute workflow** — follow the appropriate workflow steps
6. **Record & audit** — update docs, log changes, audit if spec existed

---

# PART 3: Skills & Tools

Register CLI tools, define sub-agents, and configure verification hooks.
This section makes custom tools **discoverable and usable** by AI agents.

## Custom Skills

Each skill is documented in `.agents/skills/<name>/SKILL.md` following the
[OpenAI Codex skills convention](https://developers.openai.com/codex/skills/).
Each SKILL.md has YAML frontmatter with `name` and `description` (trigger
conditions), followed by command, options, requirements, and examples.

### Skill Inventory

| Skill | Command | Description |
|-------|---------|-------------|
| [gemini](.agents/skills/gemini/SKILL.md) | `npm run gemini` | Text generation, vision, document analysis, grounded search via Gemini API |
| [gemini-image](.agents/skills/gemini-image/SKILL.md) | `node tools/gemini-image-tool.js` | Image generation/editing with Gemini 2.0 or Imagen 3.0 |
| [openai-image](.agents/skills/openai-image/SKILL.md) | `npm run openai-image` | Image generation/editing with GPT-image-1 or DALL-E 3 |
| [image-optimizer](.agents/skills/image-optimizer/SKILL.md) | `npm run optimize-image` | Resize, convert format, adjust quality, AI background removal |
| [remove-background](.agents/skills/remove-background/SKILL.md) | `npm run remove-background-advanced` | Local background removal with Sharp (no API key) |
| [html-to-md](.agents/skills/html-to-md/SKILL.md) | `npm run html-to-md` | Scrape webpage to Markdown |
| [download-file](.agents/skills/download-file/SKILL.md) | `npm run download-file` | Download files with progress tracking |
| [generate-video](.agents/skills/generate-video/SKILL.md) | `npm run generate-video` | AI video generation via Replicate (Kling, MiniMax, etc.) |
| [qwen3-tts](.agents/skills/qwen3-tts/SKILL.md) | `npm run qwen3-tts` | Text-to-speech with voice/clone/design modes |
| [play-audio](.agents/skills/play-audio/SKILL.md) | `npm run play-audio` | Play audio files via system player |
| [sprite-animator](.agents/skills/sprite-animator/SKILL.md) | `npm run sprite-animator` | Generate sprite animation frames for games |
| [github-cli](.agents/skills/github-cli/SKILL.md) | `npm run github` | GitHub PRs, issues, releases, repos, workflows |
| [data-indexing](.agents/skills/data-indexing/SKILL.md) | `npm run data-indexing` | Index documents into ChromaDB for semantic search |
| [semantic-search](.agents/skills/semantic-search/SKILL.md) | `npm run semantic-search` | Vector search over ChromaDB-indexed documents |
| [google-search](.agents/skills/google-search/SKILL.md) | `npm run google-search` | Real-time Google Search via Gemini grounding |
| [datetime](.agents/skills/datetime/SKILL.md) | `npm run datetime` | Current date/time in various formats and timezones |

---

## Sub-Agent Definitions

Define specialized agents with non-overlapping responsibilities.

### Agent Template

```markdown
### [Agent Name]
**Role:** [1 sentence — what this agent does]
**Skills:** [List of registered skills this agent can use]

**Process:**
1. [Step]
2. [Step]
3. [Step]

**Can:** [Permitted actions]
**Cannot:** [Forbidden actions — prevents overlap with other agents]

**Output Format:**
[Define structured output this agent produces]
```

### Principles
- **Single Responsibility:** Each agent has ONE job, no overlap
- **Skills Bridge:** Agents use registered skills (above) to invoke tools
- **Constraints Prevent Drift:** "Cannot" is as important as "Can"
- **Structured Output:** Every agent produces a defined format
- **Chain Results:** Each agent's output feeds the next agent's input

---

## Hooks & Verification

Hooks are quality gates that run at defined points in the pipeline.

| Hook | When | Purpose |
|------|------|---------|
| **PreToolUse** | Before a tool executes | Approve dangerous operations |
| **PostToolUse** | After a tool completes | Validate output format and quality |
| **Stop** | Agent marks task complete | Final verification before "done" |

### Hook Configuration Template

```markdown
## Hooks

### PreToolUse
- Require approval for: [list dangerous operations]
- Block: operations outside the agent's "Can" list

### PostToolUse
- Validate: output matches agent's defined format
- Check: all required sections present
- Log: action for audit trail

### Stop (Completion Gate)
- Verify: [acceptance criteria met / coverage threshold / all agents ran]
- Max retries: [N] cycles before escalating to human
```

---

## Learnings

> Check this section FIRST when encountering errors. Add solutions here
> so the same problem is never debugged twice.

### Entry Template

```markdown
### [Short description]
**Context:** [When/where this occurs]
**Symptom:** [What you see]
**Root cause:** [Why it happens]
**Solution:** [How to fix]
**Prevention:** [How to avoid in future]
```
