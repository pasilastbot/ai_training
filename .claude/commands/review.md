# Review — Comprehensive Implementation Review Against Spec

Conduct a thorough review of a feature implementation against its specification, covering spec compliance, security, architecture, performance, and testing.

## Input

$ARGUMENTS

If no arguments provided, ask the user for the feature name (matching a spec in `specs/features/`).

## Instructions

### Step 1: Preparation

1. Identify the specification file at `specs/features/<feature-name>.md`
2. Read the complete specification
3. Find all files created or modified for this feature by searching the codebase for related code, types, components, tests, and API endpoints mentioned in the spec
4. Read all implementation files
5. Find test files (patterns: `*.test.ts`, `*.test.py`, `*.spec.js`, `__tests__/*`, `tests/*`)

### Step 2: Spec Compliance Audit

**a. Requirements Verification:**
- List every functional requirement (FR-1, FR-2, etc.) from the spec
- For each requirement, verify implementation status:
  - ✅ Fully implemented and working
  - ⚠️ Partially implemented or has limitations
  - ❌ Not implemented
- Cite evidence: file names, line numbers, function names

**b. Non-Functional Requirements:**
- Performance: Are targets met? Run benchmarks if tests exist
- Scalability: Review data structures and algorithms
- Maintainability: Check code organization and documentation
- Accessibility: Verify fallbacks, ARIA labels, keyboard navigation (if frontend)

**c. Files Verification:**
- Compare "Files to Create" in spec vs actual files created
- Compare "Files to Modify" in spec vs actual modifications
- Document missing or unexpected files

**d. API Contract Verification:**
- For each endpoint in the spec, verify implementation exists
- Check request/response formats match the contract
- Verify error codes and edge cases are handled

**e. Test Coverage Audit:**
- **Unit Tests:** Compare spec test cases vs implemented tests. List missing tests explicitly.
- **Integration Tests:** Verify all integration scenarios from spec are tested
- **E2E Tests:** Verify all user flows from spec are tested
- Run test suite if possible (`npm test`, `pytest`, etc.) and report results
- Run coverage tool if available and compare to spec's coverage target
- CRITICAL: Identify gaps — tests specified but not written

**f. Acceptance Criteria:**
- For each AC in the spec, mark as met ✅ or unmet ❌
- Provide evidence for each
- Calculate percentage: X/Y acceptance criteria met

### Step 3: Security Audit

**a. Input Validation:**
- Check all user inputs are validated (search for validation patterns)
- Look for SQL injection vulnerabilities (raw queries, string concatenation)
- Look for XSS vulnerabilities (innerHTML, dangerouslySetInnerHTML, eval)
- Check file upload validation if applicable

**b. Authentication & Authorization:**
- Verify auth mechanisms if applicable
- Search for hardcoded credentials (API keys, passwords, tokens in source)
- Review session management
- Check API endpoint authorization

**c. Data Protection:**
- Search for secrets committed to code (API keys, passwords, tokens)
- Verify sensitive data handling (encryption, hashing)
- Review logging — ensure no sensitive data is logged
- Check environment variable usage for secrets

**d. Dependencies:**
- Review package.json / requirements.txt for known vulnerable packages
- Run `npm audit` or equivalent if available

### Step 4: Architecture Audit

**a. Code Organization:**
- Verify separation of concerns (UI, business logic, data access)
- Check for circular dependencies
- Review module boundaries and interfaces
- Identify code smells (God classes, duplicated code, long functions)

**b. Design Patterns:**
- Identify patterns used and verify consistency with `docs/architecture.md`
- Check patterns are applied correctly

**c. Data Flow:**
- Trace data flow through the system
- Verify error propagation and handling
- Check async/await usage (no unhandled promises, callback hell)
- Review state management if frontend

**d. Scalability & Maintainability:**
- Check for N+1 query problems
- Look for potential memory leaks (unclosed connections, event listeners)
- Check for inefficient algorithms
- Verify function length (<50 lines generally)
- Check naming conventions and code clarity

### Step 5: Performance Audit

- Run performance tests if they exist
- Check database query efficiency
- Review API response times from test results or logs
- Look for caching opportunities
- If frontend: check bundle sizes, unnecessary re-renders, lazy loading
- Verify image/asset optimization

### Step 6: Documentation Audit

- Check if `docs/ai_changelog.md` has an entry for this feature
- Check if `docs/todo.md` tasks are marked complete
- Check `docs/learnings.md` for relevant entries
- Verify inline code comments for complex logic
- Check if API documentation is updated (if backend)

### Step 7: Generate Review Report

Create a review report file at `temp/review-<feature-name>.md` with these sections:

```markdown
# Review Report: <Feature Name>
**Date:** <today>
**Spec:** specs/features/<feature-name>.md
**Reviewer:** AI Agent

## Executive Summary
- **Overall Compliance:** X%
- **Production Ready:** Yes / No / Partial
- **Critical Issues:** X
- **Tests Passing:** X/Y

## Spec Compliance
| Requirement | Status | Evidence |
|-------------|--------|----------|
| FR-1: ...   | ✅/⚠️/❌ | file:line |

## Acceptance Criteria
| Criteria | Status | Evidence |
|----------|--------|----------|
| AC-1: ... | ✅/❌  | ...      |
**Result: X/Y criteria met (Z%)**

## Security Findings
| Severity | Finding | Location | Recommendation |
|----------|---------|----------|----------------|
| CRITICAL/HIGH/MEDIUM/LOW | ... | file:line | ... |

## Architecture Findings
- Code organization issues
- Design pattern concerns
- Data flow problems

## Performance Findings
- Bottlenecks identified
- Optimization opportunities

## Test Coverage
- **Spec target:** X%
- **Actual:** Y% (or "not measured")
- **Missing tests:** [list]

## Documentation Status
- [ ] Changelog updated
- [ ] Todo updated
- [ ] Learnings recorded
- [ ] API docs updated

## Recommendations (Prioritized)
1. **CRITICAL:** ...
2. **HIGH:** ...
3. **MEDIUM:** ...
4. **LOW:** ...

## Conclusion
Honest assessment of completeness and production readiness.
```

### Step 8: Present Findings

Display a summary to the user with key metrics:
- Overall compliance percentage
- Critical gaps (list)
- Security issues by severity count
- Missing tests (list)
- Production readiness verdict: Yes / No / Partial

Ask the user if they want to address gaps now or accept the current state.

### Review Principles

- **Be Honest:** Don't inflate percentages. If it's 78%, say 78%.
- **Be Specific:** Cite file paths, line numbers, function names. Provide evidence.
- **Be Constructive:** For each issue found, suggest a concrete fix.
- **Be Thorough:** Check everything the spec requires, not just what's easy to verify.
- **Be Fair:** Acknowledge what was done well, not just gaps.
- **Be Practical:** Distinguish "must fix before production" vs "nice to have later".

### Common Gaps to Watch For

- Tests specified in spec but not written
- Only happy path tested, error cases ignored
- Sprite/asset generation skipped (using fallbacks)
- Separate CSS files specified but styles embedded inline
- Some variants/personas tested but not all
- Responsive design specified but not tested
- Security best practices assumed but not verified
- Performance targets specified but not measured
