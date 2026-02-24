# Prompt 02: Build Your CLI Tool

**When to use:** PART 1 — BUILD step
**Goal:** Build the analyze-deps.sh dependency analysis script

---

```
@tools/analyze-deps.sh.template

Complete the dependency analysis script:

1. Find all .ts/.js files in the target directory
2. Extract import/require statements from each file
3. Map which file imports from which other file
4. Output a dependency graph showing:
   - Entry points (files that nothing imports)
   - Leaf nodes (files that import nothing)
   - The import chain between them

Output format (text-based graph):
  src/index.ts
    → src/routes/tasks.ts
      → src/db.ts
    → src/routes/users.ts
      → src/db.ts
    → src/middleware/auth.ts

Accept a directory path as argument (default: target/)
```

Test it:
```bash
chmod +x tools/analyze-deps.sh
./tools/analyze-deps.sh target/
```

---

## What you should have after this step

- [ ] A working `analyze-deps.sh` that maps file dependencies
- [ ] Text-based dependency graph output
- [ ] Tool tested against the target app
