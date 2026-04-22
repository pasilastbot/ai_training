---
name: coding-preferences
description: >-
  Persists and loads the user's personal coding preferences from a SQLite
  database in this skill folder. Use when the user asks to remember a coding
  preference, recall saved style or workflow rules, list what was stored, or
  apply their saved conventions before implementing or reviewing code.
---

## Command

`npm run coding-preferences -- <subcommand> [options]`

Database file: `.agents/skills/coding-preferences/preferences.db` (created on first use; `*.db` is gitignored).

## Workflow for agents

1. **Before writing or reviewing code** — run `list` (or `search` with a relevant term) and apply matching preferences.
2. **When the user states a durable rule** ("always use X", "never Y", "my commit style is Z") — confirm they want it saved, then `set` with a clear dot-separated `key` and optional `--category`.
3. **When the user asks "what did I save about …?"** — `search` or `get`.

## Subcommands

| Subcommand | Purpose |
|------------|---------|
| `set KEY` | Create or replace; use `-v`/`--value` or `--stdin` for body |
| `get KEY` | Print one entry; add `--json` for structured output |
| `list` | All keys; `-c` / `--category` to filter |
| `delete KEY` | Remove an entry |
| `search TERM` | Substring match on key and value |

## Options (set)

| Flag | Description |
|------|-------------|
| `-c`, `--category` | Optional group: `style`, `git`, `tests`, `typescript`, etc. |
| `-v`, `--value` | Preference text (single argument; use quotes for spaces) |
| `--stdin` | Read multiline body from stdin |

## Requirements

- Python 3 (stdlib only)
- No API keys

## Examples

```bash
# Save a one-line preference
npm run coding-preferences -- set typescript.style -c style -v "Prefer explicit return types on exported functions."

# Multiline body
printf '%s\n' "Use conventional commits." "Scope optional for tooling-only changes." | npm run coding-preferences -- set git.commit --stdin -c git

# List everything
npm run coding-preferences -- list

# List by category
npm run coding-preferences -- list -c git

# Fetch one (human-readable)
npm run coding-preferences -- get typescript.style

# Search
npm run coding-preferences -- search "commit"

# Remove
npm run coding-preferences -- delete typescript.style
```

## Key naming

Use stable, lowercase, dot-separated keys, e.g. `typescript.style`, `react.hooks`, `testing.framework`, `review.checklist`.
