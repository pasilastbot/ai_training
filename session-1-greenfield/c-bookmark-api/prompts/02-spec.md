# Prompt 02: Write Your Feature Spec

**When to use:** After the SDD + Specifications theory blocks
**Goal:** Write a spec for Feature 1 (Create Bookmark)

---

## Create `specs/create-bookmark.md`

```markdown
# Feature: Create Bookmark

## Overview
Users can save a bookmark with a URL, title, optional description, and tags.

## User Story
As an API consumer, I want to save bookmarks with tags so I can organize and find them later.

## Acceptance Criteria

### AC1: Create bookmark with valid URL
**Given** the bookmarks list may have existing items
**When** POST /bookmarks with:
  ```json
  { "url": "https://example.com", "title": "Example", "tags": ["reference"] }
  ```
**Then** return 201 with the created bookmark including:
  - id: auto-generated string
  - url: "https://example.com"
  - title: "Example"
  - tags: ["reference"]
  - createdAt: ISO 8601 timestamp

### AC2: Reject invalid URL
**Given** any state
**When** POST /bookmarks with:
  ```json
  { "url": "not-a-url", "title": "Bad" }
  ```
**Then** return 400 with error: "Invalid URL format"

### AC3: Reject missing title
**Given** any state
**When** POST /bookmarks with:
  ```json
  { "url": "https://example.com" }
  ```
**Then** return 400 with error: "Title is required"

### AC4: Reject duplicate URL
**Given** a bookmark with url "https://example.com" already exists
**When** POST /bookmarks with the same URL
**Then** return 409 with error: "Bookmark already exists for this URL"

### AC5: Default empty tags
**Given** any state
**When** POST /bookmarks without tags field
**Then** create the bookmark with tags: []

## Technical Constraints
- URL validation: must start with http:// or https://
- Title: required, max 200 characters
- Tags: optional array of lowercase strings
- IDs: use a simple counter or timestamp-based

## Test Strategy
- Unit tests for validation (AC2, AC3)
- Unit tests for service logic (AC1, AC4, AC5)
- Edge case: very long URL, special characters in title
```

---

## Validate each AC

For every **Then** clause, write the assertion in your head:
- AC1: `expect(response.status).toBe(201)` and `expect(body.url).toBe("https://example.com")`
- AC2: `expect(response.status).toBe(400)` and `expect(body.error).toBe("Invalid URL format")`

If you can't write the assertion, the AC needs more detail.
