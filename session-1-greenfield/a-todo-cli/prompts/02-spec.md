# Prompt 02: Write Your Feature Spec

**When to use:** After the SDD + Specifications theory blocks
**Goal:** Write a spec for Feature 1 (Add Todo) using the AGENTS.md spec template

---

## Your Task

Write a spec for the "Add Todo" feature. Save it as `specs/add-todo.md`.

**Use the spec template from `../../AGENTS.md` (Workflow: spec → Spec Template) as your format.**

### Feature Requirements

The `add` command lets users create a new todo item via the CLI.

Behaviors to cover:
- Adding a basic todo with just a title (what defaults apply?)
- Adding a todo with a custom priority (`--priority high`)
- Adding a todo with a category (`--category work`)
- Rejecting an empty title
- Rejecting an invalid priority value

Technical constraints:
- Pure functions for business logic (testable without CLI)
- In-memory storage (no database)
- IDs are sequential integers starting from 1
- Valid priorities: low, medium, high

---

## The "Can AI Test This?" Check

Before moving on, verify each AC you wrote:
1. Does every AC have a specific expected value or output string?
2. Could you write an `expect()` assertion for each **Then** clause?
3. Are error cases covered with exact error messages?
4. Are defaults explicit (e.g., what's the default priority)?

If any answer is "no" — rewrite the AC until it's testable.

---

## Ask AI to Review Your Spec

```
@specs/add-todo.md
@../../AGENTS.md

Review this spec against the spec template in AGENTS.md:
1. Is every AC testable with a concrete assertion?
2. Are there missing edge cases?
3. Does it follow the Given/When/Then format?
4. Is the test strategy complete?

List any issues found.
```
