# «Spec title — kebab-slug matches filename»

**Epic:** [EPIC-«CTX»-NNN-«slug»](../EPIC-«CTX»-NNN-«slug».md) · **Status:** OPEN · **Opened:** «YYYY-MM-DD»
**Contexts:** «CTX, …» · **WORKLIST:** «row id»

One paragraph: what the user gets when this spec ships — their outcome, not the implementation.

---

## Problem

What is wrong or missing today? One or two sentences a non-developer would recognize.

## Research & reuse

What already exists that this spec builds on — grep results, not guesses. Scope from `project.md` § Search scope.

| Found | Location | Reuse / rule out |
|---|---|---|
| | | |

## Architecture decisions

Only decisions that are expensive to reverse. Each names the alternative that lost and why.

| Decision | Chosen | Alternatives rejected |
|---|---|---|
| | | |

## REQ checklist

Every row must end at `VERIFIED` with a test citation before this spec closes. Link epic SCN ids.

| REQ | Title | Status | SCN | Done |
|---|---|---|---|---|
| REQ-«CTX»-NNN | | GAP | SCN-«CTX»-NNN | [ ] |

## Test plan

Per layer (`AGENTS.md` §6) — name files before writing tests.

| Layer | What it guards | File(s) |
|---|---|---|
| Pure logic | | |
| Application / API | | |
| UI | | |
| Artifact | | |
| Integration / E2E | | |
| External provider | | |

## Implementation order

Thin vertical slices — one gateable unit per row.

| # | Slice | REQ(s) | Done | Notes |
|---|---|---|---|---|
| 1 | | | [ ] | |
| 2 | | | [ ] | |

## Open questions

Ambiguity → entry in open questions doc (`project.md` § Paths), linked here as `OQ-NNN`. Do not guess.

| ID | Question | Blocks |
|---|---|---|
| OQ-«NNN» | | |

---

## Close checklist

Tick before deleting this file (`AGENTS.md` §4):

- [ ] Every REQ in the checklist is `VERIFIED` with test citation in the ledger
- [ ] Epic SCN → REQ links updated
- [ ] Gate green: «GATE_COMMAND» from `project.md`
- [ ] Browser pass + screenshots in path from `project.md` § Paths
- [ ] WORKLIST row closed · PROGRESS updated if appropriate
- [ ] **Delete this spec file** — ledger + epic are the permanent record
