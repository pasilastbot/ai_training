# Prompt 01: Scaffold Your Project

**When to use:** After the Context Sandwich + Model Selection theory blocks
**Goal:** Use a Context Sandwich prompt to get AI to scaffold your project structure

---

## Your Context Sandwich Prompt

Copy-paste this into Cursor or Claude Code, then customize the parts in `[brackets]`:

```
@CLAUDE.md
@package.json
@tsconfig.json

Create the initial project structure for a command-line todo manager.

The CLI should support these commands:
- `add <title>` — add a new todo
- `list` — list all todos
- `done <id>` — mark a todo as completed

Set up the following folder structure:
- src/index.ts — CLI entry point (parse arguments, route to commands)
- src/types.ts — TypeScript interfaces for Todo, Category, Priority
- src/commands/ — one file per command (add.ts, list.ts, done.ts)
- src/storage.ts — in-memory storage (array of todos)

Requirements:
- Follow the coding standards in CLAUDE.md
- Use TypeScript strict mode
- Define interfaces before implementing functions
- Do NOT implement the full logic yet — just create the files with type signatures and placeholder functions that throw "not implemented"
```

---

## What to look for

After AI generates the scaffold:
1. Does it follow your CLAUDE.md rules?
2. Are the types well-defined?
3. Is the folder structure clean and logical?
4. Did it use `any` anywhere? (It shouldn't!)

If something doesn't match your rules, iterate:
```
The types in src/types.ts are missing the Priority enum.
Add: priority should be 'low' | 'medium' | 'high' with default 'medium'.
Also add a Category type as a string.
```
