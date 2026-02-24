# Prompt 03: Implement Feature 1 with TDD

**When to use:** After the TDD Cycle theory block
**Goal:** Implement "Add Todo" using Red-Green-Refactor

---

## Step 1: RED — Write Failing Test

Copy-paste this prompt:

```
@specs/add-todo.md
@src/types.ts

Looking at AC1 (Add basic todo), write a failing test.

Requirements:
- Use Vitest
- Test file: src/commands/add.test.ts
- Test the business logic function, NOT the CLI parsing
- The function should accept a title and options, and return the created todo
- Import from src/commands/add.ts (which has placeholder code)
- Test ONLY AC1 for now

Run the test to confirm it fails.
```

**Verify:** Run `npm test` — it should FAIL (red). This is correct!

---

## Step 2: GREEN — Write Minimum Code

```
The test in src/commands/add.test.ts is failing.

Implement the minimum code in src/commands/add.ts to make the AC1 test pass.

Requirements:
- Implement only what's needed for AC1
- Use the Todo interface from src/types.ts
- Store todos in src/storage.ts
- Do not over-engineer — just make the test pass

Run the test to confirm it passes.
```

**Verify:** Run `npm test` — it should PASS (green).

---

## Step 3: Add more ACs

Now repeat the cycle for AC2 and AC4:

```
@specs/add-todo.md
@src/commands/add.test.ts
@src/commands/add.ts

Add tests for AC2 (priority flag) and AC4 (empty title rejection).
Then update the implementation to make all tests pass.

Follow the same Red-Green pattern:
1. Write the test
2. Run it — confirm it fails
3. Implement the minimum code
4. Run it — confirm all tests pass
```

---

## Step 4: Refactor

Once tests pass, refactor:

```
All tests pass. Now refactor the add command code:
1. Extract validation into a separate function
2. Add proper TypeScript return types
3. Keep all tests passing

Do not add new features — only improve code quality.
```

**Key rule:** Run tests after EVERY change. If they break, undo and try again.
