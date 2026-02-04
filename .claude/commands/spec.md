# Spec-Driven Development

Create a feature specification before writing any code. The spec serves as a binding contract between planning and implementation.

## Input

Feature name or description: $ARGUMENTS

## Instructions

Follow these steps in order. Do NOT skip any mandatory steps.

### Step 1: Read Context (MANDATORY)

Read ALL of these documentation files to understand the project:

- `docs/description.md` — app purpose and features
- `docs/architecture.md` — tech stack, patterns, testing
- `docs/datamodel.md` — entities, relationships, schemas
- `docs/frontend.md` — UI/UX patterns (if feature has frontend)
- `docs/backend.md` — API patterns, services (if feature has backend)

Then search the codebase for code related to the feature being specified. Look for:
- Similar existing features or patterns
- Related modules that will be affected
- Existing types, interfaces, or schemas to reuse

If the feature involves external APIs or libraries, search the web to confirm current documentation and versions.

### Step 2: Create the Specification

Create a new file at `specs/features/<feature-name>.md` using the template from `specs/TEMPLATE.md`.

The spec MUST include all of these sections:

**Header:**
- Status: Draft
- Created date: today
- Author: AI Agent

**Overview:**
- Purpose — what does this feature do and why
- User Story — "As a [user], I want [action] so that [benefit]"
- Scope — what is included and explicitly NOT included

**Requirements:**
- Functional requirements (FR-1, FR-2, etc.) — specific, testable
- Non-functional requirements — performance, security, scalability

**API Contract:**
- Endpoints with method, path, request/response types
- Function signatures with parameter and return types
- Error conditions and error response formats

**Data Model:**
- New entities with TypeScript interfaces
- Modified entities with field changes
- Relationships between entities

**Component Structure:**
- Files to create (path, purpose, dependencies)
- Files to modify (path, changes, reason)
- Folder structure diagram

**Dependencies:**
- External libraries with versions
- API keys / environment variables needed
- System requirements

**Testing Strategy (MANDATORY — must be comprehensive):**

This is the most critical section. Follow the quality standards in `specs/TESTING-CHECKLIST.md`.

- **Unit Tests:** For every public function, write Given/When/Then test cases. Include happy path, edge cases (empty, null, boundary), and error conditions. Mock external dependencies. Minimum 3-5 tests per component.
- **Integration Tests:** For every API endpoint, write success and error test cases with request/response examples. Test service layer interactions. Minimum 2-3 tests per integration point.
- **E2E Tests:** For every user story, write a complete step-by-step scenario. Include happy path, error recovery, and alternative flows. Minimum 2-3 scenarios per feature.
- **Test Coverage Goals:** Specify target percentage (e.g., 85% line coverage)
- **Test Data:** Define mock data, fixtures, and test databases needed

**Acceptance Criteria:**
- Functional criteria — checkable conditions for each requirement
- Testing criteria (MANDATORY):
  - All unit tests implemented and passing
  - All integration tests implemented and passing
  - All E2E tests implemented and passing
  - Test coverage meets goals
- Quality criteria — linting, documentation, performance
- Deployment criteria — dependencies, env vars, migrations

### Step 3: Validate the Test Plan (MANDATORY)

Before presenting the spec, verify:

1. EVERY functional requirement (FR-*) maps to at least one unit test
2. EVERY user story maps to at least one E2E test scenario
3. Error conditions and edge cases are covered
4. Tests are specific and actionable (not vague like "test that it works")
5. Test data and fixtures are defined

If ANY of these checks fail, the spec is NOT ready. Go back and fix it.

### Step 4: Present for Review

Present the completed spec to the user. Highlight:
- Key design decisions and trade-offs
- Areas where user input is needed
- The testing strategy summary
- Any open questions or assumptions made

Wait for user feedback and iterate until the spec is approved.

### Step 5: After Approval

Once the user approves the spec:
1. Update the spec Status from "Draft" to "Approved"
2. The spec is now the contract for implementation
3. Implementation should follow the `develop` workflow using this spec
