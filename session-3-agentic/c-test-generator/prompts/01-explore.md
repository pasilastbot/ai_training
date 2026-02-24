# Prompt 01: Explore the Pipeline Target

**When to use:** PART 1 — REHEARSAL step
**Goal:** Understand the untested target codebase

---

## Step 1: Explore the target code

```
@target/

Analyze this codebase:

1. How many files and functions are there?
2. Which functions are the most complex?
3. Which have the most edge cases?
4. Are there any external dependencies that would need mocking?
5. What's the current test coverage? (hint: 0%)
```

---

## Step 2: Think about automation

Before building anything, consider:

- Which functions should be tested first (highest risk)?
- What types of tests would catch the most bugs?
- What could you script to track coverage progress?

```
If you had to write a test suite for this code,
what would you test first and why?
What repetitive tasks could be automated?
```

---

## What you should know after this step

- [ ] You know what files and functions exist
- [ ] You've identified the most complex / risky functions
- [ ] You know these are pure functions (no mocking needed)
- [ ] You have an idea of what to automate first
