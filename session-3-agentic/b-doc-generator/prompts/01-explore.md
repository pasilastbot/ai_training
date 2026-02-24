# Prompt 01: Explore the Pipeline Target

**When to use:** PART 1 — REHEARSAL step
**Goal:** Understand the undocumented target codebase

---

## Step 1: Explore the target app

```
@target/

What does this application do?

Tell me:
1. What's the folder structure?
2. What are the main API endpoints?
3. What data models exist?
4. How do the files depend on each other?
5. What documentation exists? (hint: probably none)
```

---

## Step 2: Think about automation

Before building anything, consider:

- What would a new developer need to know first?
- What's the hardest part of this codebase to understand without docs?
- What could you script to make documentation generation faster?

```
If you had to document this app for a new developer,
what order would you document things in? Why?
What repetitive analysis tasks could be automated?
```

---

## What you should know after this step

- [ ] You understand what the target app does
- [ ] You've identified the main files and their relationships
- [ ] You know what documentation is missing
- [ ] You have an idea of what to automate first
