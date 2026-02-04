# Testing Checklist for Specifications

> Use this checklist to verify your spec has comprehensive test coverage before approval.

## Pre-Approval Checklist

Before a spec can be approved, verify ALL items are checked:

### Documentation Review ✓
- [ ] Read `docs/description.md` (app purpose)
- [ ] Read `docs/architecture.md` (tech stack, testing frameworks)
- [ ] Read `docs/datamodel.md` (data structures)
- [ ] Read relevant `docs/frontend.md` or `docs/backend.md`
- [ ] Searched codebase for similar features/patterns

### Test Coverage Completeness ✓

#### Unit Tests
- [ ] **Every public function** has at least one unit test
- [ ] **Every functional requirement** maps to specific unit test(s)
- [ ] **Happy path** tested for each function
- [ ] **Edge cases** tested (empty input, null, boundary values)
- [ ] **Error conditions** tested (invalid input, exceptions)
- [ ] **External dependencies** mocked (APIs, databases, file system)
- [ ] Test assertions are **specific** (not just "it works")
- [ ] **Minimum 3-5 unit tests per component/module**

Example:
```markdown
✅ GOOD: Test sanitizeMessage() with "<script>alert('xss')</script>" → returns escaped string
❌ BAD: Test sanitization function
```

#### Integration Tests
- [ ] **Every API endpoint** has success case test
- [ ] **Every API endpoint** has error case test(s)
- [ ] **Service layer** tested with real dependencies
- [ ] **Database operations** tested (if applicable)
- [ ] **External API integrations** tested (with mocks)
- [ ] Request/response **validation** tested
- [ ] **Authentication/authorization** tested (if applicable)
- [ ] **Minimum 2-3 integration tests per integration point**

Example:
```markdown
✅ GOOD: POST /api/chat with valid message → 200 OK with response structure
✅ GOOD: POST /api/chat with missing message → 400 Bad Request with error
❌ BAD: Test the API
```

#### E2E Tests
- [ ] **Every user story** has at least one E2E test
- [ ] **Happy path** (main flow) fully tested
- [ ] **Error handling** flows tested (user sees error, can recover)
- [ ] **Alternative paths** tested (different routes to same goal)
- [ ] **Multi-step processes** tested end-to-end
- [ ] **UI state** verified at each step (for frontend)
- [ ] Tests include **specific user actions** (click, type, wait)
- [ ] Tests include **specific expected outcomes** (message appears, redirect happens)
- [ ] **Minimum 2-3 E2E scenarios per feature**

Example:
```markdown
✅ GOOD: 
Scenario: User sends first message
Steps: 1) Load page, 2) Type "Hello", 3) Press Enter, 4) Wait for response
Expected: User message appears, model response streams in, both visible in chat

❌ BAD: Test that user can chat
```

### Test Plan Quality ✓
- [ ] Tests are **concrete** (not vague "test it works")
- [ ] Tests specify **Given/When/Then** or equivalent
- [ ] Tests include **expected assertions**
- [ ] Test data/fixtures are **defined**
- [ ] Test coverage **percentage goal** specified (e.g., 85%)
- [ ] **Mock data** defined for external dependencies
- [ ] **Performance criteria** included (if applicable)
- [ ] **Security tests** included (if handling sensitive data)

### Acceptance Criteria ✓
- [ ] Includes "All unit tests implemented"
- [ ] Includes "All unit tests pass (100%)"
- [ ] Includes "All integration tests implemented"
- [ ] Includes "All integration tests pass (100%)"
- [ ] Includes "All E2E tests implemented"
- [ ] Includes "All E2E tests pass"
- [ ] Includes "Test coverage meets goals"
- [ ] Every functional requirement has acceptance criterion

### Common Missing Tests
Check that these are NOT missing:

- [ ] **Empty input** tests (what if user sends empty string?)
- [ ] **Null/undefined** tests (what if parameter is null?)
- [ ] **Long input** tests (what if 10,000 characters?)
- [ ] **Special characters** tests (emoji, unicode, SQL chars)
- [ ] **Network failure** tests (what if API is down?)
- [ ] **Timeout** tests (what if response takes 30 seconds?)
- [ ] **Concurrent operation** tests (if applicable)
- [ ] **Race condition** tests (if async operations)

## Test Plan Quality Levels

### ❌ Unacceptable (Cannot be approved)
```markdown
## Testing Strategy
- Test that it works
- Make sure there are no bugs
```
**Problem:** Vague, not actionable, no specific tests

### ⚠️ Minimal (Needs improvement)
```markdown
## Testing Strategy
- Unit test: Test the main function
- E2E test: Test user flow
```
**Problem:** Not specific enough, missing edge cases and error conditions

### ✅ Acceptable (Can be approved)
```markdown
## Testing Strategy

Unit Tests:
- Test sanitizeMessage() with XSS input → returns escaped
- Test sanitizeMessage() with empty string → returns empty
- Test sanitizeMessage() with null → throws error

Integration Tests:
- POST /api/chat with valid data → 200 OK
- POST /api/chat with invalid data → 400 error

E2E Tests:
- User sends message → receives response → both visible
- User sends message when API down → sees error → can retry
```
**Good:** Specific tests, edge cases, error handling

### 🌟 Excellent (Best practice)
```markdown
## Testing Strategy

Test Coverage Goals: 85% line coverage, 80% branch coverage

Unit Tests (15 tests):
Function: sanitizeMessage(input: string): string
  - Test 1: XSS script tag → returns "&lt;script&gt;..."
  - Test 2: XSS event handler → strips handler
  - Test 3: Valid HTML → preserves (if allowed)
  - Test 4: Empty string → returns "" without error
  - Test 5: Null input → throws TypeError with message
  [10 more tests...]

Integration Tests (7 tests):
API: POST /api/chat
  - Test 1: Valid message + no history → 200 OK with response
  - Test 2: Valid message + history → 200 OK, context used
  - Test 3: Missing message field → 400 with "Message required"
  [4 more tests...]

E2E Tests (7 scenarios):
Scenario 1: First message (Happy Path)
  Steps: 1) Load /chat, 2) Type "Hello", 3) Press Enter, 4) Wait 3s
  Expected: User msg appears immediately, model response streams
  Success: Both messages visible, distinct styling
  
Scenario 2: Error recovery
  Steps: 1) Disconnect network, 2) Send message, 3) See error, 4) Reconnect, 5) Retry
  Expected: Clear error msg, retry succeeds
  [5 more scenarios...]

Test Data: fixtures/test-messages.js, fixtures/mock-responses.py
```
**Excellent:** Comprehensive, specific, includes test data, counts defined

## Red Flags

If you see these, the spec is NOT ready:

❌ **"Test that it works"** → Too vague
❌ **No edge case tests** → Only happy path tested
❌ **No error tests** → What happens when things fail?
❌ **No E2E tests** → User flow not validated
❌ **"Tests TBD"** → Tests must be defined upfront
❌ **Generic tests** → "Test the function" vs specific scenario
❌ **No test counts** → Can't verify completeness

## Quick Self-Check

Ask yourself these questions:

1. **Can I implement these tests without further clarification?** 
   - If no → tests too vague
   
2. **Do I know exactly what inputs to use and outputs to expect?**
   - If no → add Given/When/Then

3. **Have I thought through what happens when things go wrong?**
   - If no → add error condition tests

4. **Can a user actually complete their goal end-to-end?**
   - If unsure → add E2E test

5. **Would these tests catch a regression if I broke something?**
   - If no → tests not comprehensive enough

## Enforcement

**Specs without comprehensive test plans will be rejected.**

The `<spec>` workflow includes a validation step:
```
3. Validate Test Plan (MANDATORY):
   - Ensure EVERY functional requirement has corresponding unit test(s)
   - Ensure EVERY user story has corresponding E2E test scenario(s)
   - Ensure error conditions and edge cases are covered
   - If test plan is incomplete, spec is NOT ready for approval
```

**Implementation cannot begin until test plan is approved.**

## Examples

See `specs/features/example-chat-feature.md` for a fully worked example with:
- 15+ unit tests (covering all functions, edge cases, errors)
- 7+ integration tests (all API endpoints, success + error)
- 7+ E2E scenarios (complete user flows, error handling)

This is the standard to meet.
