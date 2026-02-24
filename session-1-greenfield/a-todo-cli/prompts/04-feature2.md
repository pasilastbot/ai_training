# Prompt 04: Spec + Build Feature 2

**When to use:** After completing Feature 1 with TDD
**Goal:** Repeat the full cycle — spec → test → implement — for "List Todos with Filters"

---

## Step 1: Write the Spec Yourself

Write a spec for the "List Todos" feature. Save it as `specs/list-todos.md`.

**Use the same format as your Feature 1 spec (which follows the AGENTS.md template).**

### Feature Requirements

The `list` command shows all todos, optionally filtered.

Behaviors to cover:
- Listing all todos (displays id, title, status, priority)
- Filtering by category (`--category work`)
- Filtering by completion status (`--done`)
- Empty list (no todos exist — what message?)
- Invalid category filter (no matches)

---

## Step 2: Ask AI to Review Your Spec

```
@specs/list-todos.md
@specs/add-todo.md

Review this spec for completeness:
1. Is every AC testable with a concrete assertion?
2. Are there missing edge cases?
3. Does it follow the same format as add-todo.md?

List any issues found.
```

Fix any issues before proceeding.

---

## Step 3: TDD Implementation

```
@specs/list-todos.md
@src/types.ts
@src/storage.ts

Implement "List Todos" using TDD:

1. Write failing tests for AC1 and AC4 in src/commands/list.test.ts
2. Implement minimum code in src/commands/list.ts to pass them
3. Add test for AC2 (category filter), implement
4. Add test for AC3 (status filter), implement
5. Run all tests (including add tests) to verify nothing broke

Follow the Red-Green-Refactor pattern from Feature 1.
```

---

## Wrap-Up

After both features are implemented, reflect:
- How many tests do you have?
- Did the spec help AI produce correct code on the first try?
- What would have been different without the spec?
