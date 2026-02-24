# Prompt 04: Spec + Build Feature 2

**When to use:** After completing Feature 1 with TDD
**Goal:** Repeat the full cycle — spec → test → implement — for "Search Bookmarks by Tag"

---

## Step 1: Write the Spec Yourself

Write a spec for the "Search Bookmarks by Tag" feature. Save it as `specs/search-bookmarks.md`.

**Use the same format as your Feature 1 spec (which follows the AGENTS.md template).**

### Feature Requirements

The GET /bookmarks endpoint lists all bookmarks, optionally filtered by tag.

Behaviors to cover:
- Listing all bookmarks (what response format? include count?)
- Filtering by tag query parameter
- No matching tags (what to return?)
- Case-insensitive tag matching

Technical constraints:
- Response format: `{ data: Bookmark[], count: number }`
- No pagination required for v1

---

## Step 2: Ask AI to Review Your Spec

```
@specs/search-bookmarks.md
@specs/create-bookmark.md

Review this spec for completeness:
1. Is every AC testable with a concrete assertion?
2. Are there missing edge cases?
3. Does the response format include count?
4. Does it follow the same format as create-bookmark.md?

List any issues found.
```

Fix any issues the AI identifies before proceeding.

---

## Step 3: TDD — RED for AC1 (List all)

```
@specs/search-bookmarks.md
@src/types.ts
@src/services/bookmark-service.ts
@src/storage.ts

Looking at AC1 (List all bookmarks), write a failing test.

Requirements:
- Add tests to src/services/bookmark-service.test.ts (same file as Feature 1)
- Test listBookmarks() returns all bookmarks with correct count
- Do NOT implement yet

Run the test to confirm it fails.
```

**Verify:** `npm test` — the new test should FAIL.

---

## Step 4: GREEN for AC1

```
The listBookmarks test is failing.

Implement listBookmarks(tag?: string) in src/services/bookmark-service.ts.

Requirements:
- Return all bookmarks from storage
- Keep it simple — just make the test pass

Run tests to confirm they pass.
```

**Verify:** `npm test` — all tests pass (create + list).

---

## Step 5: RED/GREEN for remaining ACs

```
@specs/search-bookmarks.md
@src/services/bookmark-service.test.ts
@src/services/bookmark-service.ts

Add tests for the remaining ACs from your spec one at a time:
- Tag filter returns only matching bookmarks
- Empty result when no tags match
- Case-insensitive tag matching

For each: write the test, run it, then implement to make it pass.
All existing tests must still pass after each step.
```

---

## Wrap-Up

After both features:
- Start server: `npm run dev`
- Create a bookmark: `curl -X POST http://localhost:3000/bookmarks -H "Content-Type: application/json" -d '{"url":"https://github.com","title":"GitHub","tags":["dev"]}'`
- Search by tag: `curl http://localhost:3000/bookmarks?tag=dev`
- Run full test suite: `npm test`
