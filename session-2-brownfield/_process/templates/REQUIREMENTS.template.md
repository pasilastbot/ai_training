# «CTX» — «Context name» — requirement ledger

**Context:** «models, domain area» · **App / service:** «path»
**Epics:** «links to epic records, or —»
**Created:** «YYYY-MM-DD»

> Status vocabulary and rules: `AGENTS.md` §4.

## Status vocabulary

| Status | Meaning |
|---|---|
| `VERIFIED` | A named test asserts this — row cites file + test name |
| `IMPLEMENTED` | Code does this; no test asserts this specific behaviour |
| `QUESTION` | Behaviour exists; correctness unresolved — link `OQ-NNN` in open questions doc |
| `GAP` | Behaviour that should exist and does not |

**Totals:** «N» VERIFIED · «N» IMPLEMENTED · «N» QUESTION · «N» GAP

---

## Dashboard

| ID | Title | Status | Code | Tests |
|---|---|---|---|---|
| REQ-«CTX»-001 | «Short title» | GAP | | |
| REQ-«CTX»-002 | «Short title» | IMPLEMENTED | `file.ts:42` | |

Test citations name the file and the `it(...)` / test name, checkable in seconds.

---

## Detail blocks

Use for non-obvious acceptance criteria. One block per REQ when the dashboard row is not enough.

### REQ-«CTX»-001 — «Title»

**Status:** GAP · **Epic:** EPIC-«CTX»-NNN · **SCN:** SCN-«CTX»-NNN

**Given** … **When** … **Then** …

**Code:** `file.ts:line` · **Tests:** `file.test.ts` "should …"

---

## Gaps and questions index

| ID | Title | Status | Notes |
|---|---|---|---|
| | | | |
