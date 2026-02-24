# Prompt 02: Write Your Feature Spec

**When to use:** After the SDD + Specifications theory blocks
**Goal:** Write a spec for Feature 1 (Add Todo) with Given/When/Then acceptance criteria

---

## The Spec Template

Create a file called `specs/add-todo.md` with this content. Fill in the `[brackets]`:

```markdown
# Feature: Add Todo

## Overview
Users can add a new todo item with a title, category, and priority level via the CLI.

## User Story
As a CLI user, I want to add todos with categories and priorities so that I can organize my tasks.

## Acceptance Criteria

### AC1: Add basic todo
**Given** the todo list is empty
**When** the user runs `add "Buy groceries"`
**Then** a todo is created with:
  - title: "Buy groceries"
  - completed: false
  - priority: "medium" (default)
  - id: auto-generated unique number
**And** the CLI outputs: "Added todo #1: Buy groceries"

### AC2: Add todo with priority
**Given** the todo list may have existing items
**When** the user runs `add "Fix bug" --priority high`
**Then** a todo is created with priority "high"
**And** the CLI outputs: "Added todo #[id]: Fix bug [HIGH]"

### AC3: Add todo with category
**Given** the todo list may have existing items
**When** the user runs `add "Write tests" --category work`
**Then** a todo is created with category "work"

### AC4: Reject empty title
**Given** any state
**When** the user runs `add ""`
**Then** no todo is created
**And** the CLI outputs an error: "Title cannot be empty"

### AC5: Reject invalid priority
**Given** any state
**When** the user runs `add "Task" --priority urgent`
**Then** no todo is created
**And** the CLI outputs an error: "Invalid priority. Use: low, medium, high"

## Technical Constraints
- Pure functions for business logic (testable without CLI)
- In-memory storage (no database)
- IDs are sequential integers starting from 1

## Test Strategy
- Unit tests for each AC
- Edge case: very long title (200+ chars)
```

---

## The "Can AI Test This?" Check

Before moving on, verify each AC:
1. Does every AC have specific expected output strings?
2. Could you write an `expect()` assertion for each **Then** clause?
3. Are error cases covered (AC4, AC5)?
4. Are defaults explicit (AC1: priority "medium")?

If any answer is "no" — rewrite the AC until it's testable.
