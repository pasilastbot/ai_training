# Prompt 02: Write Your Feature Spec

**When to use:** After the SDD + Specifications theory blocks
**Goal:** Write a spec for Feature 1 (Create Bookmark) using the AGENTS.md spec template

---

## Your Task

Write a spec for the "Create Bookmark" feature. Save it as `specs/create-bookmark.md`.

**Use the spec template from `../../AGENTS.md` (Workflow: spec → Spec Template) as your format.**

### Feature Requirements

The POST /bookmarks endpoint creates a new bookmark with URL validation and tags.

Behaviors to cover:
- Creating a bookmark with valid URL, title, and tags (what fields in response?)
- Rejecting an invalid URL (what counts as invalid?)
- Rejecting a missing title
- Rejecting a duplicate URL (what if it already exists?)
- Default behavior when tags are not provided

Technical constraints:
- URL validation: must start with http:// or https://
- Title: required, max 200 characters
- Tags: optional array of lowercase strings
- IDs: simple counter or timestamp-based
- POST returns 201 on success
- Error response: `{ error: string }`

---

## The "Can AI Test This?" Check

Before moving on, verify each AC you wrote:
1. Does every AC have specific expected status codes and error messages?
2. Could you write an `expect()` assertion for each **Then** clause?
3. Are error cases covered (invalid URL, missing title, duplicate)?
4. Are defaults explicit (what happens with no tags)?

If any answer is "no" — rewrite the AC until it's testable.

---

## Ask AI to Review Your Spec

```
@specs/create-bookmark.md
@../../AGENTS.md

Review this spec against the spec template in AGENTS.md:
1. Is every AC testable with a concrete assertion?
2. Are there missing edge cases?
3. Are the error messages consistent?
4. Is the test strategy complete?

List any issues found.
```
