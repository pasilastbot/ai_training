# Session 1: Greenfield Development with AI

**90 min | Beginner | "From Zero to Working App"**

Build a working application from scratch using AI. You'll learn tools, prompting, specs, and TDD — by building something real.

---

## Pick Your Project

Choose ONE of these three projects to build during the session:

### A) Todo CLI (Node.js/TypeScript)
A command-line todo manager with categories and priorities.
- **Feature 1:** Add a todo (with title, category, priority)
- **Feature 2:** List todos with filtering (by category, by status)
- **Folder:** `a-todo-cli/`

### B) Weather Dashboard API (Node.js/TypeScript)
A REST API that fetches, caches, and serves weather data.
- **Feature 1:** GET /weather/:city — returns current weather (from mock data)
- **Feature 2:** GET /forecast/:city — returns 5-day forecast with caching
- **Folder:** `b-weather-api/`

### C) Bookmark Manager API (Node.js/TypeScript)
A REST API for saving, tagging, and searching bookmarks.
- **Feature 1:** POST /bookmarks — create bookmark with URL validation and tags
- **Feature 2:** GET /bookmarks?tag=X — search bookmarks by tag
- **Folder:** `c-bookmark-api/`

---

## Session Flow

| # | Type | Topic | Duration |
|---|------|-------|----------|
| 1 | THEORY | AI Coding Tools Landscape | 5 min |
| 2 | THEORY | Rules & Configuration (.cursor/rules, CLAUDE.md, AGENTS.md) | 5 min |
| 3 | **REHEARSAL** | **Pick your project, clone the repo, set up CLAUDE.md** | **10 min** |
| 4 | THEORY | Effective Prompting: Context Sandwich | 5 min |
| 5 | THEORY | Model Selection | 5 min |
| 6 | **BUILD** | **Write your first Context Sandwich prompt to scaffold** | **10 min** |
| 7 | THEORY | Why Not Vibe Code? Vibe Coding vs SDD | 5 min |
| 8 | THEORY | Greenfield: Spec-Driven Development | 5 min |
| 9 | THEORY | Writing Effective Specifications | 5 min |
| 10 | **BUILD** | **Write the spec for Feature 1** | **10 min** |
| 11 | THEORY | TDD Cycle with AI (Red-Green-Refactor) | 5 min |
| 12 | **BUILD** | **Implement Feature 1 with TDD, then spec + build Feature 2** | **15 min** |
| 13 | WRAP-UP | Review what you built, Q&A | 5 min |

**Total: 90 min** (45 min theory + 45 min hands-on)

---

## Getting Started

1. Clone this repo
2. `cd` into your chosen project folder
3. Run `npm install`
4. Copy `CLAUDE.md.template` to `CLAUDE.md` and fill in the blanks
5. Follow the prompts in `prompts/` in order (01 → 02 → 03 → 04)

Each prompt file contains the exact prompt to use at each BUILD step.
