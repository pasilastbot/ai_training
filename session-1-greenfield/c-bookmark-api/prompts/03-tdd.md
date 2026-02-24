# Prompt 03: Implement Feature 1 with TDD

**When to use:** After the TDD Cycle theory block
**Goal:** Implement "Create Bookmark" using Red-Green-Refactor

---

## Step 1: RED — Write Failing Tests for Validation

Copy-paste this prompt:

```
@specs/create-bookmark.md
@src/types.ts
@src/services/validation.ts

Looking at AC2 (Reject invalid URL), write failing validation tests.

Requirements:
- Use Vitest
- Test file: src/services/validation.test.ts
- Test validateUrl("https://example.com") returns true
- Test validateUrl("not-a-url") returns false
- Do NOT modify the validation implementation yet

Run the test to confirm it fails.
```

**Verify:** Run `npm test` — it should FAIL (red). This is correct!

---

## Step 2: GREEN — Implement Validation

```
The validation tests are failing.

Implement validateUrl() in src/services/validation.ts to make them pass.

Requirements:
- Check that the URL starts with http:// or https://
- Keep it simple — just make the tests pass

Run tests to confirm they pass.
```

**Verify:** Run `npm test` — it should PASS (green).

---

## Step 3: RED — Write Failing Test for AC1 (Create Bookmark)

```
@specs/create-bookmark.md
@src/types.ts
@src/services/bookmark-service.ts

Looking at AC1 (Create bookmark with valid URL), write a failing test.

Requirements:
- Test file: src/services/bookmark-service.test.ts
- Test createBookmark({ url, title, tags }) returns a Bookmark with correct fields
- Test ONLY AC1 for now
- Do NOT modify the service implementation yet

Run the test to confirm it fails.
```

**Verify:** Run `npm test` — the new test should FAIL.

---

## Step 4: GREEN — Implement AC1

```
The bookmark service test is failing.

Implement createBookmark() in src/services/bookmark-service.ts to make the AC1 test pass.

Requirements:
- Validate input using validateUrl from validation.ts
- Create bookmark with auto-generated id and createdAt
- Store in src/storage.ts
- Return the created bookmark

Run tests to confirm they pass.
```

**Verify:** Run `npm test` — all tests pass.

---

## Step 5: RED/GREEN — Add AC3 (Missing title)

```
@specs/create-bookmark.md
@src/services/bookmark-service.test.ts
@src/services/bookmark-service.ts

Add a test for AC3 (missing title returns error).
Then update the implementation to make it pass.
All existing tests must still pass.
```

**Verify:** Run `npm test` — all tests pass.

---

## Step 6: RED/GREEN — Add AC4 (Duplicate URL)

```
@specs/create-bookmark.md
@src/services/bookmark-service.test.ts
@src/services/bookmark-service.ts

Add a test for AC4 (duplicate URL returns error).
Then update the implementation to make it pass.
All existing tests must still pass.
```

**Verify:** Run `npm test` — all tests pass.

---

## Step 7: Refactor

Once all tests pass, refactor:

```
All tests pass. Refactor:
1. Extract all error messages into constants
2. Add proper TypeScript return types (use a Result type or throw typed errors)
3. Normalize tags to lowercase in createBookmark
4. Ensure AC5 (default empty tags) is handled

Keep all tests passing.
```

**Key rule:** Run tests after EVERY change. If they break, undo and try again.
