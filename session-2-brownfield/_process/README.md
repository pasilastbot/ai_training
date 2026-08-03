# Process templates

Portable starter kit for the generic process in [`AGENTS.md`](../AGENTS.md).

Copy these into a new repository, then fill in `project.md` from `templates/project.template.md`.

| Template | Purpose |
|---|---|
| [`project.template.md`](templates/project.template.md) | Project-specific config — paths, commands, tiers, traps |
| [`WORKLIST.template.md`](templates/WORKLIST.template.md) | Live control surface for open work |
| [`REQUIREMENTS.template.md`](templates/REQUIREMENTS.template.md) | One ledger file (single context or minimal profile) |
| [`epic.template.md`](templates/epic.template.md) | User capability record |
| [`spec.template.md`](templates/spec.template.md) | Ephemeral multi-REQ spec (delete when done) |

## Adoption

1. Copy `AGENTS.md`, `prompts.md`, and `_process/` to the repo root.
2. Copy `project.template.md` → `project.md` and fill every section.
3. Pick a **scale profile** in `project.md` (minimal / standard / full) — see `AGENTS.md` §0.
4. Create artifacts from the templates that match your profile.
5. Optionally symlink `CLAUDE.md` → `AGENTS.md`.
