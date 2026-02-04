# Specifications - Spec-Driven Development

## Overview

This folder contains specifications that serve as **contracts** for feature implementation. Following spec-driven development ensures clear requirements, better design decisions, and fewer implementation surprises.

## Philosophy

> **"Write the contract before the code"**

Specifications define:
- **WHAT** will be built (requirements, API contracts, data models)
- **WHY** it's needed (purpose, user stories, benefits)
- **HOW** it will be tested (acceptance criteria, test scenarios)

Code is the implementation that fulfills the contract.

## Folder Structure

```
specs/
├── README.md              # This file - complete guide
├── QUICKSTART.md          # Quick reference (5-minute spec)
├── TEMPLATE.md            # Template for new specifications
├── TESTING-CHECKLIST.md   # Testing requirements checklist
├── features/              # Feature specifications
│   └── [feature-name].md
├── apis/                  # API endpoint specifications
│   └── [service-name]-api.md
└── components/            # Component specifications
    └── [component-name]-spec.md
```

## Workflow

### 1. Research Phase (Mandatory First Step)

Before creating a spec, **ALWAYS read documentation**:

```bash
# Required reading (use read_file or similar)
- docs/description.md      # App purpose and features
- docs/architecture.md     # Tech stack and patterns
- docs/datamodel.md        # Existing entities and relationships
- docs/frontend.md         # UI/UX patterns (if frontend feature)
- docs/backend.md          # API patterns (if backend feature)
```

Also search the codebase for:
- Similar existing features
- Related code that might be affected
- Patterns to follow

### 2. Specification Creation

Use the workflow: `<spec>`

```
1. Read context (see above)
2. Create spec using TEMPLATE.md
3. Define clear API contracts
4. List acceptance criteria
5. Present to user for review
```

**Spec file naming:**
- Features: `specs/features/[feature-name].md` (e.g., `user-authentication.md`)
- APIs: `specs/apis/[service-name]-api.md` (e.g., `psychiatrist-api.md`)
- Components: `specs/components/[component-name]-spec.md` (e.g., `chat-interface-spec.md`)

### 3. Review & Approval

Specs should be reviewed before implementation:
- Are requirements clear?
- Are API contracts well-defined?
- Are test scenarios comprehensive?
- Are dependencies identified?

Update the spec **Status** field when approved.

### 4. Implementation

Use the workflow: `<develop>`

```
1. Read the approved spec
2. Fetch relevant implementation rules
3. Implement code according to the contract
4. Verify implementation matches spec
```

### 5. Validation

Use the workflow: `<validate>`

```
1. Implement tests defined in the spec
2. Run tests and fix failures
3. Check acceptance criteria
```

### 6. Update Spec (if needed)

During implementation, if requirements change:
- Update the spec first
- Document the decision in "Implementation Notes"
- Continue development with updated contract

## Spec Sections Explained

### Overview
High-level description. Should be understandable by non-technical stakeholders.

### Requirements
Functional (what it does) and non-functional (how well it does it).

### API Contract
**Most critical section.** Defines:
- Input types (parameters, request body)
- Output types (return values, response structure)
- Error conditions
- Side effects

This is the **contract** that code must fulfill.

### Data Model
Changes to database schema, entities, or relationships.

### Component Structure
Concrete list of files to create/modify. Helps estimate scope.

### Dependencies
External libraries, API keys, environment setup needed.

### Testing Strategy
**⚠️ MANDATORY SECTION - Cannot be skipped or incomplete**

This is where you define HOW the feature will be validated. A spec without a comprehensive test plan is incomplete and cannot be approved.

**Must include:**

1. **Unit Tests:** Test individual functions/components
   - Every public function needs tests
   - Edge cases (empty, null, boundary values)
   - Error conditions (invalid input, exceptions)
   - Mock external dependencies
   - **Example:** "Test sanitizeMessage() with XSS attempt → returns escaped string"

2. **Integration Tests:** Test module interactions
   - API endpoints (success + error cases)
   - Service layer with real dependencies
   - Database operations
   - External API integrations
   - **Example:** "POST /api/chat with valid data → 200 OK with response"

3. **E2E Tests:** Test complete user flows
   - Every user story needs an E2E test
   - Happy path (everything works)
   - Error handling (things go wrong, user recovers)
   - Alternative flows (different routes to same goal)
   - **Example:** "User sends message → receives streaming response → message appears in chat"

**Why this is mandatory:**
- Tests verify the implementation fulfills the contract
- Tests become living documentation
- Tests catch regressions during future changes
- Tests force you to think through edge cases during design
- **No tests = feature cannot be validated = spec is incomplete**

**Rule:** Every functional requirement must have corresponding test(s). If you can't test it, the requirement is too vague.

### Acceptance Criteria
Checklist for "done". Every item should be verifiable.

**Must include testing criteria:**
- [ ] All unit tests implemented and passing
- [ ] All integration tests implemented and passing  
- [ ] All E2E tests implemented and passing
- [ ] Test coverage meets goals (e.g., 85%)

Feature is NOT complete until all tests pass.

## Benefits of Spec-Driven Development

1. **Clarity:** Requirements are clear before coding starts
2. **Better Design:** Thinking through the contract surfaces issues early
3. **Testability:** Tests are defined alongside requirements
4. **Documentation:** Specs serve as living documentation
5. **Collaboration:** Non-coders can review and approve specs
6. **Reduced Rework:** Fewer surprises during implementation

## Example: Creating a New Feature

```bash
# 1. Research (read documentation)
# 2. Create spec
specs/features/video-generation-ui.md

# 3. Spec defines:
- User uploads image
- User enters prompt
- System generates video
- User downloads result

# 4. Implement according to spec
# 5. Validate against acceptance criteria
# 6. Update spec if implementation reveals necessary changes
```

## Tips

- **Start Simple:** Don't over-specify. Capture essentials first.
- **Be Concrete:** "The system should be fast" → "Response time < 2 seconds"
- **Think in Contracts:** What are inputs? What are outputs? What are errors?
- **Update Specs:** If implementation changes requirements, update the spec
- **Reference Others:** Link to related specs, docs, and existing code

## Status Workflow

```
Draft → In Review → Approved → Implemented
```

- **Draft:** Initial spec creation, may have gaps
- **In Review:** Ready for review, seeking feedback
- **Approved:** Reviewed and approved, ready for implementation
- **Implemented:** Code fulfills the spec, tests pass

## Integration with Workflows

The spec-driven development integrates with existing workflows:

- `<research>` → Gather context before spec creation
- `<spec>` → Create specification (NEW)
- `<develop>` → Implement according to spec
- `<validate>` → Verify implementation matches spec
- `<document>` → Update project docs
- `<record>` → Log changes in changelog

## Testing Enforcement

Before submitting a spec for approval, use the testing checklist:

📋 **See `specs/TESTING-CHECKLIST.md`** for:
- Pre-approval checklist (verify all items checked)
- Test coverage completeness criteria
- Test plan quality levels
- Common missing tests
- Red flags to avoid
- Self-check questions

**Specs without comprehensive test plans will be rejected.**

## Questions?

Refer to:
- `specs/TESTING-CHECKLIST.md` - Testing requirements (USE THIS!)
- `specs/QUICKSTART.md` - Quick reference guide
- `specs/TEMPLATE.md` - Full specification template
- `specs/features/example-chat-feature.md` - Complete example
- `.cursor/rules/workflows.mdc` - Workflow definitions
- `.cursor/rules/documentation.mdc` - Documentation structure
- `docs/architecture.md` - Project architecture
