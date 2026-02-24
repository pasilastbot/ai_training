# Feature: Delete Bookmark

> This is a reference example. Use this format for your own specs.

## Overview
Users can delete a bookmark by its ID.

## Acceptance Criteria

### AC1: Delete existing bookmark
**Given** a bookmark with id "abc123" exists
**When** DELETE /bookmarks/abc123
**Then** return 204 (no content)
**And** the bookmark is removed from storage

### AC2: Delete non-existent bookmark
**Given** no bookmark with id "xyz999" exists
**When** DELETE /bookmarks/xyz999
**Then** return 404 with error: "Bookmark not found"

### AC3: Verify deletion
**Given** a bookmark was deleted
**When** GET /bookmarks/:id is called with the deleted ID
**Then** return 404

## Technical Constraints
- Hard delete (no soft delete)
- Return 204 on success (no response body)

## Test Strategy
- Unit test: delete from storage array
- Verify list endpoint no longer returns deleted bookmark
