# Agent Instructions

Universal operating manual for AI-assisted software development with traceability from user
outcome → requirement → test → code.

**Project-specific details** (paths, commands, tech stack, tiers, integrations) live in
[`project.md`](project.md). Read this file first, then `project.md` for the repository you are in.

If your repo symlinks another filename (e.g. `CLAUDE.md` → `AGENTS.md`), they are the same process.

Starter files for new repos: [`_process/templates/`](_process/templates/).

---

## Quick navigation

| You need to… | Read |
|---|---|
| Paths, commands, tiers, traps | [`project.md`](project.md) |
| Scale profile (minimal / standard / full) | §0 |
| Universal rules | §1 — non-negotiables |
| How work is specified | §4 — requirement gate |
| Day-to-day implementation | §5 — build loop |
| What to test, where | §6 |
| Definition of done | §7 |
| Start or end a session | §11 |
| Copy-paste session drivers | [`prompts.md`](prompts.md) |
| Business workflow agents (if any) | [`project.md`](project.md) |

## Where the work lives

Logical artifact names — **resolve paths from [`project.md`](project.md) § Paths**, not from memory:

| Artifact | Role |
|---|---|
| Worklist | What is open — epic, spec path, REQ ids, queue, debt |
| Progress | Rollup of shipped work |
| Ledger | **The gate** — behaviours with code and test links |
| Epics | User capabilities — scenarios linked to REQ rows |
| Product docs | What the system is |
| Open questions | Unresolved ambiguities (`OQ-NNN`) |
| Agent memories | Durable build gotchas |
| Product readme | Architecture, env, deployment |

## Starting a session

1. Read §0–§1 and §5.
2. Read [`project.md`](project.md) — paths, commands, scale profile.
3. Pick up the active row in the worklist — note epic, spec path, and REQ ids in scope.
4. Open linked ledger rows and epic scenarios. Do not start ad-hoc changes — see §11.

**Platform coding vs business agents.** §0–§13 cover building the product. Separate business workflow
agents live outside this process — see `project.md`.

---

## 0. Scale profiles

Pick one profile in `project.md` § Identity. Same rules apply; ceremony scales down.

| Profile | Ledger | Epics | Tiers | Ephemeral specs | Typical repo |
|---|---|---|---|---|---|
| **Minimal** | Single `REQUIREMENTS.md` | Optional | No | No | Single app, small team |
| **Standard** | One ledger per area/context | Yes | Optional | When 2+ REQs | Multi-module product |
| **Full** | Bounded contexts + index | Yes + index | Yes | Yes | Large monorepo, many agents |

**Minimal:** WORKLIST + ledger + gate. REQ ids may omit context prefix (`REQ-001`).

**Standard:** Epics link to ledger rows; multi-REQ work uses ephemeral specs.

**Full:** Everything in this manual, including verification tiers and ledger index.

Templates: [`_process/templates/`](_process/templates/).

---

## 1. The Non-Negotiables

These govern every change. A change that violates one is wrong even if its tests pass.

1. **Nothing is "done" without requirement, test, and code — cross-linked.** Every behaviour change
   names the requirement id(s) it touches; tests cite them; the ledger updates in the same change.
2. **Search before you build.** Grep the scope defined in `project.md` § Search scope.
3. **Run the full quality gate** — not tests alone. Commands in `project.md` § Commands. Build (or
   equivalent) catches bundler and boundary errors other checks miss.
4. **Deferral is explicit, never silent.** Work not done is recorded in the worklist with a reason,
   or the requirement row stays honestly `IMPLEMENTED` / `QUESTION`. Never omit deferral.
5. **Schema/data model is canonical.** Use the project's migration workflow — see `project.md`. Derive
   types from generated clients; do not hand-write model types.
6. **Shared code stays in shared modules** — not cross-imports between apps/services. Boundary rules
   in `project.md`.
7. **Configuration values are never literals.** Enums, thresholds, role sets, and labels live in one
   exported constant; every consumer imports it.
8. **Thin vertical slices.** One requirement (or slice) = data → logic → UI → test for one behaviour.
9. **Assert the OUTPUT, not the wiring.** Generated artifacts (PDFs, emails, exports, API envelopes)
   need at least one test on the artifact itself.
10. **User-visible work is verified in the real surface** before it is called done — browser, CLI, or
    API as appropriate, plus screenshot evidence where the project stores it (`project.md` § Paths).
11. **Reversible-by-default in production data.** Imports deduplicate; terminal states do not regress;
    destructive operations need confirmation — project-specific rules in `project.md`.

---

## 2. Repository map

See [`project.md`](project.md) § Repository map.

---

## 3. Commands

See [`project.md`](project.md) § Commands for dev, test, build, migrate, and deploy commands.

Note what **CI runs** vs what the **local gate adds** — a green CI is not always a complete definition
of done.

---

## 4. The Requirement Gate

The unit of work is a **requirement ledger row** — typically `REQ-<CTX>-NNN` (or `REQ-NNN` in minimal
profile). The ledger is the gate: no behaviour change merges without updating the row(s) it affects.

Ledger location: `project.md` § Paths → `ledger`.

### Traceability chain

```
Epic                         user capability, acceptance scenarios (SCN-<CTX>-NNN)
        ↕ linked
Ledger (REQ-<CTX>-NNN)       system guarantee — status, code ref, test ref
        ↕ enforced by
Test                         named assertion cited in the row
        ↕ satisfied by
Code
```

**Linking rules**

- Every acceptance scenario names the REQ row(s) it maps to.
- Every ledger row names its epic(s) and scenario(s) when epics are in use.
- A PR that changes behaviour lists affected REQ ids. If no row exists, write the row first.
- Worklist rows reference epic + REQ ids.

### Ledger status vocabulary

| Status | Meaning |
|---|---|
| `VERIFIED` | A named test asserts this — row cites file + test name |
| `IMPLEMENTED` | Code does this; no test. **Backlog — flip to VERIFIED when touched.** |
| `QUESTION` | Behaviour exists; correctness unresolved — link `OQ-NNN` in open questions doc |
| `GAP` | Behaviour that should exist and does not |

### Open questions (`OQ-NNN`)

When behaviour exists but correctness is unresolved, do not guess. Add an entry to the open questions
doc (`project.md` § Paths → `open_questions`):

- **ID:** `OQ-NNN` (sequential)
- **What the code does today**
- **Why it is a question**
- **What would answer it** (test, product decision, provider doc)

Link `QUESTION` ledger rows to `OQ-NNN`. Resolve by test + code change or explicit product decision.

### Verification tiers

If the project defines tiers and targets (`project.md` § Verification tiers), apply:

- **New behaviour** → epic scenario + `GAP` row → failing test → code → `VERIFIED` in same PR.
- **Touch rule** → changing code cited by an `IMPLEMENTED` row requires flipping to `VERIFIED` or
  explicit deferral in the worklist.
- **Extend-on-touch** → when fixing a module, add tests for neighbouring `IMPLEMENTED` rows in the
  same file when practical.
- **Never write `VERIFIED` without naming the test.**

### Epic specs (multi-REQ work)

For coordinated multi-REQ changes, use ephemeral spec files — template at
`_process/templates/spec.template.md`, location in `project.md` § Paths → `epic_spec_dir`. Lifecycle:

1. **Open** — spec from template; worklist links epic + spec + REQ ids.
2. **Build** — one REQ or vertical slice at a time; tick checklist as rows reach `VERIFIED`.
3. **Close** — gate green, surface verification, all REQs verified or deferred.
4. **Ship** — **delete the spec file.** Ledger + epic are the permanent record.

---

## 5. The Build Loop

```
 ORIENT    worklist + epic + spec (if any) + REQ row(s); agent-memories for the area
 RESEARCH  grep search scope — note reuse
 SPECIFY   GAP row + epic link if missing; name test layer and proof command
 RED       failing test for the RIGHT reason
 GREEN     smallest change that passes
 GATE      full quality gate (project.md)
 LOOK      real surface verification; screenshot evidence
 TRACE     ledger → VERIFIED with test citation; epic links; worklist
 COMMIT    conventional commit; body lists REQ ids
 CAPTURE   discoveries → worklist; gotchas → agent-memories
```

**Red must fail for the right reason.** **Green must pass for the right reason** — break the code
deliberately once to confirm the test catches absence, then restore.

**One REQ or one spec slice at a time.** Capture discoveries in the worklist; do not derail the current
slice.

---

## 6. What to Test, and Where

Framework-agnostic layers — map to concrete paths in `project.md` § Testing.

| Layer | Catches | Cost |
|---|---|---|
| **Pure logic** | Maths, transitions, dedup, formatting | free |
| **Application / API** | Auth, validation, error shape, side effects | free |
| **UI** | Rendered affordances, disabled states, labels | cheap |
| **Artifact** | Produced string/document content | cheap |
| **Integration / E2E** | Wiring, routing, auth guards, real flows | slow |
| **External provider** | Provider contract drift | credentialed |

**Rules of thumb**

- Prefer pure — extract decisions from plumbing.
- Every generated document gets a content assertion.
- E2E owns fixtures and cleans up.
- Test-only surfaces gated by env flag + secret.

---

## 7. Definition of Done

A change is **done** only when all hold:

1. Affected REQ row(s) updated — end as `VERIFIED` or have explicit deferral.
2. Epic scenario(s) link to REQ row(s) when epics are in use; PR lists REQ ids.
3. Full quality gate passes (`project.md`).
4. Schema changes use the project's migration workflow.
5. User-visible changes have surface verification (browser/E2E/CLI as appropriate).
6. Provider integrations verified per `project.md` when applicable.
7. Verification tier not regressed (if project uses tiers).
8. Multi-REQ spec complete → spec file deleted.
9. Conscious omissions written in worklist with reason.

---

## 8. Traceability

Conventions (branch naming, commit scopes, screenshot paths): `project.md` § Traceability.

- Commits list REQ ids when behaviour changes.
- Tests → REQ: ledger cites file + test name.
- Gotchas → agent-memories (`project.md` § Paths).

**PR / commit body template:**

```
REQ: REQ-XXX-001[, REQ-XXX-002]
Gate: «GATE_COMMAND» — passed
Surface: «screenshot path or manual note»
Deferred: «REQ ids left IMPLEMENTED + reason, or none»
```

---

## 9. WORKLIST and PROGRESS

Resolve paths from `project.md` § Paths.

**Worklist** — live control surface; updated in the same session as the change.

**Progress** — rollup of shipped work; append when significant work merges.

Neither file may claim a status that a commit, test run, or screenshot cannot back.

### Worklist row status

| Status | Meaning |
|---|---|
| `ACTIVE` | Being worked now — one at a time per contributor |
| `READY` | Spec exists and is clear enough to start |
| `PROPOSED` | Identified, not yet specified |
| `BLOCKED` | Cannot proceed; blocker recorded in the row |
| `DEFERRED` | Consciously postponed; reason recorded in the row |

Template: [`_process/templates/WORKLIST.template.md`](_process/templates/WORKLIST.template.md).

---

## 10. Code shape and traps

Read agent-memories before debugging build failures. Universal patterns:

- Keep mutation/handler modules thin; split near ~300 lines.
- Authorization at the mutation boundary, not only in routing/layout.
- Long work async; HTTP endpoints acknowledge quickly.

Repo-specific traps: `project.md` § Code traps.

### Agent memories lifecycle

- **Write** when a build or test failure teaches something non-obvious.
- **Promote** to product docs when the lesson is architectural, not incidental.
- **Delete** when the underlying code or toolchain fix makes the memory obsolete.
- **Name** by topic (`nextjs-basepath.md`), not by task id.

---

## 11. Session ritual

**Start:** §0–§1 + §5 + `project.md`; worklist; REQ row(s) in scope; agent-memories for the area.

**End:** gate green; ledger updated; worklist current; spec deleted if close checklist complete;
working tree coherent.

**Reporting rule.** State what was verified and how. Never describe a skipped check as a pass.

---

## 12. Review and audit

Trigger on: repeated bug shape · module > ~500 lines · green suite but user report · before large
spec · tier regression.

Measure, do not recall — audit commands in `project.md`. Every finding lands as worklist row,
ledger row, or agent-memory entry.

---

## 13. Quick reference

| Need | Where |
|---|---|
| Generic process | `AGENTS.md` (this file) |
| Project paths and config | `project.md` |
| Session prompts | `prompts.md` |
| Starter templates | `_process/templates/` |
| Requirement gate | `project.md` § Paths → `ledger` |
| Open work | `project.md` § Paths → `worklist` |
| Build gotchas | `project.md` § Paths → `agent_memories` |

**Discipline in one sentence:** every behaviour change names a requirement, starts with a failing
test, passes the full gate, is verified in the real surface, and updates the ledger — and deferrals
are written down, not forgotten.
