# Prompt 03: Implement Feature 1 with TDD

**When to use:** After the TDD Cycle theory block
**Goal:** Implement "Create Bookmark" using Red-Green-Refactor

---

## Step 1: RED — Write Failing Tests

```
@specs/create-bookmark.md
@src/types.ts
@src/services/bookmark-service.ts
@src/services/validation.ts

Write failing tests for AC1 (valid bookmark) and AC2 (invalid URL).

Requirements:
- Use Vitest
- Test file: src/services/bookmark-service.test.ts
- Test the service function: createBookmark(input) → Bookmark | Error
- Also write validation tests in: src/services/validation.test.ts
- Test validateUrl("https://example.com") returns true
- Test validateUrl("not-a-url") returns false

Run tests to confirm they fail.
```

---

## Step 2: GREEN — Implement

```
Tests are failing. Implement the minimum code to pass:

1. In src/services/validation.ts — implement validateUrl()
2. In src/services/bookmark-service.ts — implement createBookmark()

Requirements:
- validateUrl checks for http:// or https:// prefix
- createBookmark validates input, creates bookmark, stores it
- Use src/storage.ts for the bookmarks array
- Return the created bookmark with auto-generated id and createdAt

Run tests to confirm they pass.
```

---

## Step 3: Add AC3 + AC4

```
@specs/create-bookmark.md
@src/services/bookmark-service.test.ts

Add tests for:
- AC3: missing title returns error
- AC4: duplicate URL returns error

Then update the implementation to pass all tests.
Run all tests to verify nothing broke.
```

---

## Step 4: Refactor

```
All tests pass. Refactor:
1. Extract all error messages into constants
2. Add proper TypeScript return types (use a Result type or throw typed errors)
3. Normalize tags to lowercase in createBookmark

Keep all tests passing.
```
