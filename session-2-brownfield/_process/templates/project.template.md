# Project — «Project name»

Project-specific configuration for the generic process in [`AGENTS.md`](AGENTS.md).
Copy-paste drivers live in [`prompts.md`](prompts.md).

**Read [`AGENTS.md`](AGENTS.md) first** for the universal process; use this file for names, paths,
commands, tiers, and traps that apply only to this repository.

---

## Identity

| Field | Value |
|---|---|
| **Project** | «Project name» |
| **Product** | «One-line description» |
| **Process alias** | «e.g. CLAUDE.md → AGENTS.md, or —» |
| **Scale profile** | «minimal / standard / full — see AGENTS.md §0» |
| **Product docs** | «README.md» |
| **What the system is** | «docs/…» |
| **What it guarantees** | «ledger path from § Paths» |
| **What it does for users** | «epics path from § Paths, or — if minimal» |

---

## Paths

Map logical names to repo paths. Prompts and `AGENTS.md` refer to these keys, not hardcoded locations.

| Key | Path | Notes |
|---|---|---|
| `process` | `AGENTS.md` | Generic process manual |
| `project_config` | `project.md` | This file |
| `prompts` | `prompts.md` | Session drivers |
| `worklist` | `WORKLIST.md` | Open work |
| `progress` | `PROGRESS.md` | Shipped rollup |
| `ledger` | `«contexts/<CTX>/REQUIREMENTS.md or docs/REQUIREMENTS.md»` | Requirement gate |
| `ledger_index` | `«contexts/README.md or —»` | Coverage summary |
| `ledger_exemplar` | `«path to one good ledger row example»` | For Prompt 1 |
| `epics` | `«epics/ or —»` | User capabilities |
| `epic_index` | `«epics/README.md or —»` | Epic catalog |
| `epic_spec_dir` | `«epics/EPIC-<CTX>-NNN/specs/ or —»` | Ephemeral specs |
| `epic_spec_template` | `_process/templates/spec.template.md` | Copy source |
| `open_questions` | `«docs/open-questions.md»` | `OQ-NNN` entries |
| `product_docs` | `docs/` | System documentation |
| `product_readme` | `README.md` | Architecture, env, deployment |
| `screenshots` | `«docs/screenshots/<slug>/»` | Browser evidence |
| `agent_memories` | `agent-memories/` | Build gotchas |
| `process_templates` | `_process/templates/` | Starter files |
| `historical_archive` | `«tasks/ or —»` | Read-only legacy specs |

---

## Search scope

What to grep before adding a page, action, component, or constant:

```
«e.g. apps/*, packages/*, or src/**»
```

---

## Commands

| Need | Command |
|---|---|
| Dev | «…» |
| Lint · typecheck · test · build | «…» |
| E2E | «…» |
| Migrate / schema | «…» |

**Gate (workspace root):** `«GATE_COMMAND»`

**CI runs:** «lint, typecheck, test — list what CI actually gates»

**Local gate adds:** «e.g. build — list what CI skips but DoD requires»

---

## Repository map

```
«Directory tree — apps, packages, docs, etc.»
```

---

## Verification tiers

Omit this section for **minimal** or **standard** profiles without tier targets.

| Tier | Contexts / areas | Target VERIFIED | New REQ rule |
|---|---|---|---|
| **T1** | «…» | ≥ «…»% | Ships only as `VERIFIED` |
| **T2** | «…» | ≥ «…»% | Ships only as `VERIFIED` |

Recount command:

```bash
«grep or script for VERIFIED count»
```

---

## Project non-negotiables (extensions)

Rules that extend `AGENTS.md` §1 for this repo only:

1. «…»

---

## Testing (this repo)

Map `AGENTS.md` §6 layers to concrete paths:

| Layer (§6) | Where | Examples |
|---|---|---|
| Pure logic | «…» | «…» |
| Application / API | «…» | «…» |
| UI | «…» | «…» |
| Artifact | «…» | «…» |
| Integration / E2E | «…» | «…» |
| External provider | «…» | «…» |

---

## Code traps (this repo)

- «…»

Boundary check (if applicable):

```bash
«cross-module import grep»
```

---

## Traceability conventions

| Item | Convention |
|---|---|
| Branch | «req-<ctx>-<nnn>-<slug>» |
| Commits | «scope + REQ ids in body» |
| Screenshots | «path from § Paths» |

---

## Integrations and provider checks

| Integration | Reference |
|---|---|
| «…» | «…» |

---

## Active programs

Long-running agent loops (optional):

| Program | State file | Driver |
|---|---|---|
| «…» | «…» | Prompt 10 in `prompts.md` |

---

## Business agents (optional)

Not platform development — separate workflow agents:

| Agent | Location | Status |
|---|---|---|
| «…» | `agents/…/` | «…» |

---

## Prompt placeholders

| Placeholder | Value |
|---|---|
| `«WORKSPACE_ROOT»` | Repository root |
| `«GATE_COMMAND»` | «full gate command» |
| `«SEARCH_SCOPE»` | «from § Search scope» |
| `«LEDGER_EXEMPLAR»` | «from § Paths ledger_exemplar» |
| `«LEDGER_GLOB»` | «e.g. contexts/*/REQUIREMENTS.md» |
| `«OPEN_QUESTIONS»` | «from § Paths open_questions» |
| `«EPIC_SPEC_TEMPLATE»` | `_process/templates/spec.template.md` |
