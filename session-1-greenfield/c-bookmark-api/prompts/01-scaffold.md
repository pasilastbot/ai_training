# Prompt 01: Scaffold Your Project

**When to use:** After the Context Sandwich + Model Selection theory blocks
**Goal:** Use a Context Sandwich prompt to scaffold the bookmark API

---

## Your Context Sandwich Prompt

```
@CLAUDE.md
@package.json
@tsconfig.json

Create the initial project structure for a bookmark manager API.

The API should have these endpoints:
- POST /bookmarks — create a new bookmark
- GET /bookmarks — list all bookmarks (with optional tag filter)
- GET /bookmarks/:id — get a single bookmark
- DELETE /bookmarks/:id — delete a bookmark

Set up the following folder structure:
- src/index.ts — Express server setup, mount routes
- src/types.ts — TypeScript interfaces (Bookmark, CreateBookmarkInput, Tag)
- src/routes/bookmarks.ts — route handlers
- src/services/bookmark-service.ts — business logic (CRUD operations)
- src/services/validation.ts — URL and input validation
- src/storage.ts — in-memory storage (array of bookmarks)

Requirements:
- Follow the coding standards in CLAUDE.md
- Define all TypeScript interfaces in types.ts first
- Create placeholder functions that throw "not implemented"
- A Bookmark should have: id, url, title, description (optional), tags (string array), createdAt
- Express server listens on PORT env var or 3000
```

---

## What to look for

After AI generates:
1. Is the Bookmark interface complete with all fields?
2. Is URL validation mentioned in validation.ts?
3. Are route handlers separated from business logic?
4. Does `npm run lint` pass (no TypeScript errors)?
