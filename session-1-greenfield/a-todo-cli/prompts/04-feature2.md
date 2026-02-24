# Prompt 04: Spec + Build Feature 2

**When to use:** After completing Feature 1 with TDD
**Goal:** Repeat the full cycle — spec → test → implement — for "List Todos with Filters"

---

## Step 1: Write the Spec

Create `specs/list-todos.md`:

```
@specs/add-todo.md (use as format reference)
@src/types.ts

Write a spec for "List Todos" with these acceptance criteria:

AC1: List all todos
- Given 3 todos exist
- When the user runs `list`
- Then all 3 todos are displayed with id, title, status, priority

AC2: Filter by category
- Given todos exist in categories "work" and "personal"
- When the user runs `list --category work`
- Then only "work" todos are shown

AC3: Filter by status
- Given completed and incomplete todos exist
- When the user runs `list --done`
- Then only completed todos are shown

AC4: Empty list
- Given no todos exist
- When the user runs `list`
- Then output: "No todos yet. Add one with: add <title>"

Include error case: invalid category filter.
Use the same spec format as add-todo.md.
```

---

## Step 2: TDD Implementation

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
