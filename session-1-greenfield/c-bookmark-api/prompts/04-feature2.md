# Prompt 04: Spec + Build Feature 2

**When to use:** After completing Feature 1 with TDD
**Goal:** Repeat the full cycle for "Search Bookmarks by Tag"

---

## Step 1: Write the Spec

```
@specs/create-bookmark.md (use as format reference)
@src/types.ts

Write a spec for "Search Bookmarks by Tag" with these acceptance criteria:

AC1: List all bookmarks
- Given 3 bookmarks exist
- When GET /bookmarks
- Then return 200 with all 3 bookmarks and count: 3

AC2: Filter by tag
- Given bookmarks tagged "work", "personal", and "work"
- When GET /bookmarks?tag=work
- Then return only the 2 bookmarks tagged "work"

AC3: Tag not found
- Given bookmarks exist but none tagged "travel"
- When GET /bookmarks?tag=travel
- Then return 200 with empty array and count: 0

AC4: Case-insensitive tag search
- Given a bookmark tagged "Work"
- When GET /bookmarks?tag=work (lowercase)
- Then return the bookmark (tags normalized to lowercase)

Include response format: { data: Bookmark[], count: number }
Save as specs/search-bookmarks.md
```

---

## Step 2: TDD Implementation

```
@specs/search-bookmarks.md
@src/types.ts
@src/services/bookmark-service.ts
@src/storage.ts

Implement "Search Bookmarks" using TDD:

1. Write failing tests for AC1 and AC3 in src/services/bookmark-service.test.ts
2. Implement listBookmarks(tag?: string) to pass them
3. Add tests for AC2 (tag filter) and AC4 (case-insensitive)
4. Update implementation
5. Run ALL tests to verify nothing broke

Follow Red-Green-Refactor throughout.
```

---

## Wrap-Up

After both features:
- Start server: `npm run dev`
- Create a bookmark: `curl -X POST http://localhost:3000/bookmarks -H "Content-Type: application/json" -d '{"url":"https://github.com","title":"GitHub","tags":["dev"]}'`
- Search by tag: `curl http://localhost:3000/bookmarks?tag=dev`
- Run full test suite: `npm test`
