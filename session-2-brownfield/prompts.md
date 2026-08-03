# Execution Prompts

Copy-paste prompts for the process in [`AGENTS.md`](AGENTS.md). Replace `«PLACEHOLDERS»`.

**Before running:** read [`project.md`](project.md) — especially § Paths, § Commands, § Search scope,
and § Prompt placeholders.

---

## Prompt 1 — Specify a capability (epic + REQ rows)

```
Read /AGENTS.md §0, §4 and /project.md § Paths (epic_index, ledger_exemplar, open_questions).

Topic: «what the user asked for, in their words»
Area: «app or package from project.md»
Context: «context code — see project.md»

Do NOT write product code in this pass.

1. RESEARCH FIRST. Grep /project.md § Search scope for anything that already does part of this.
   Record what exists, what is reused, and what was ruled out.
2. Epic (skip if minimal profile):
   - Extend an existing epic or draft EPIC-«CTX»-NNN with Outcome, User requirements (UR),
     Acceptance scenarios (SCN) — each SCN lists the REQ ids it maps to.
   - Scenarios are Given/When/Then, written from the user's outcome.
3. Ledger:
   - For each new behaviour, add REQ-«CTX»-NNN rows starting as GAP (or mark existing IMPLEMENTED
     rows that this work will verify).
   - Each row: title, status, epic + SCN link, Given/When/Then in detail block if non-obvious.
   - New REQs must plan to ship as VERIFIED — name the test layer (AGENTS.md §6) and file path.
4. Check verification tier (project.md). If context is below target, note catch-up REQs.
5. If 2+ REQs, schema migration, or cross-package scope → create spec from
   «EPIC_SPEC_TEMPLATE» under «epic_spec_dir» (project.md § Paths). See Prompt 9.
6. Add a row to the worklist (project.md § Paths → worklist): epic, spec path, REQ ids, next action.

Report: epic + REQ id list, spec path (if created), reuse summary, open questions (→ «OPEN_QUESTIONS»),
tier status, first REQ or slice to implement.
```

---

## Prompt 2 — Implement REQ row(s) (repeat)

```
Read /AGENTS.md §1, §4, §5, §7 and /project.md (gate, code traps, migration workflow, § Paths).
Epic: «EPIC-XXX-NNN». REQ(s): «REQ-XXX-001[, REQ-XXX-002]».
Spec (if any): «path under epic_spec_dir»

Open epic scenario(s), spec (if multi-REQ), and ledger row(s). Run the build loop on those REQ(s) ONLY:
ORIENT → RESEARCH → SPECIFY → RED → GREEN → GATE → LOOK → TRACE → COMMIT → CAPTURE.

Rules:
- New REQ → must end as VERIFIED with test citation. Never merge new behaviour as IMPLEMENTED.
- Touch rule → if you change code cited by an IMPLEMENTED row, flip to VERIFIED or defer in worklist.
- Confirm each test fails for the RIGHT reason before you make it pass.
- Apply code traps from project.md.
- Gate = «GATE_COMMAND» from project.md, workspace root.

TRACE: update ledger row(s) — status, code ref, test ref (file + test name).
Update epic SCN → REQ links. Tick spec checklist if a spec exists. Update worklist evidence.

Report: REQ ids verified (with test citations), spec slice ticked, deferred rows, gate output,
surface evidence path, tier impact, next slice/REQ.
```

---

## Prompt 3 — Verify and close an epic spec

```
Read /AGENTS.md §4, §7 and /project.md § Paths (screenshots), § Commands.
Epic: «EPIC-XXX-NNN». REQ scope: «list of REQ ids».
Spec: «path under epic_spec_dir» (omit if single-REQ, no spec)

1. Run «GATE_COMMAND». Paste the real output.
2. Run the relevant E2E / integration suite (project.md § Testing).
3. Verify in the real surface — navigation, real data. Screenshot into «screenshots» path.
4. Walk every REQ in scope: VERIFIED with citation? Still GAP/IMPLEMENTED? Leave status honest.
5. If spec exists: tick close checklist, then **delete the spec file**.
6. Check verification tier (ledger_index or project.md). Above/below target?
7. Update worklist and progress (project.md § Paths).

Report each REQ as verified / deferred / gap, with evidence. Never report an unrun check as a pass.
```

---

## Prompt 4 — Bugfix

```
Read /AGENTS.md §5, §6, §4 (touch rule) and /project.md § Code traps.

Symptom: «what the user saw, where, and when»

1. Find REQ row(s) — grep «LEDGER_GLOB» and epics. No row? Write one before the fix.
2. REPRODUCE — failing test at the layer that should have caught it.
3. Root cause. Check agent_memories path from project.md.
4. Fix, gate, surface-verify.
5. TRACE: flip affected REQ(s) to VERIFIED with test citation.
6. If the bug WROTE bad data, write a re-runnable check.
7. Small fix → commit with REQ ids in body (AGENTS.md §8 template). Multi-REQ → worklist + Prompt 9.

Report: root cause, REQ ids, blast radius, test citation, tier impact, data repair needed.
```

---

## Prompt 5 — Triage and replan

```
Read /AGENTS.md §4, §9, §12 and /project.md (tier targets, audit commands, § Paths).

Reconcile worklist against reality:
- git log since last reconcile — ledger updates missed?
- Stale code refs on REQ rows?
- Contexts below tier target?
- IMPLEMENTED rows touched in recent commits but not flipped?
- Does product readme still describe what exists?

Rewrite worklist: every row has epic + REQ ids and evidence.
Refresh progress for merged work. Flag tier gaps.

Report: what moved, new REQs, tier gaps, highest-value next REQ.
```

---

## Prompt 6 — Review and audit

```
Read /AGENTS.md §4, §12 and /project.md § Audit commands.
Scope: «whole repo / specific area»

MEASURE first — paste output of audit commands from project.md:
  per-context VERIFIED counts and tier targets
  largest source files
  per-package test counts
  boundary violations (must stay 0 if applicable)

Review hardest on recent work:
- Ledger: IMPLEMENTED in high-tier contexts; stale refs; SCN without REQ links
- Boundaries: cross-module imports, duplicated constants
- Artifacts: output assertions on generated documents?
- Data: recent write defect — repeatable check?

Land every finding as worklist row, GAP/QUESTION ledger row, or agent-memory entry.

Report: findings with the defect each already caused.
```

---

## Prompt 7 — Run a business workflow agent

```
Read /project.md § Business agents, then @agents/«agent-name»/instructions.md.

Execute «agent-name» for: «input description»

Business workflow — not platform development. Do not use the REQ ledger unless changing platform code.

Follow the agent workflow. Platform writes use the integration path in project.md — never direct DB writes.

Report: output location, what a human must check before use.
```

---

## Prompt 8 — Update ledger after a behaviour change

```
Read /AGENTS.md §4 and /project.md § Paths (ledger, open_questions).

Change scope: «diff summary or description»
Context: «context code»

1. Grep ledger for touched action, route, or model. Grep epics for affected SCN.
2. Per REQ row: code ref accurate? test asserts behaviour? → VERIFIED with citation.
   Behaviour changed → update detail block. Touch rule → test + flip IMPLEMENTED → VERIFIED.
   Behaviour removed → GAP or strike with reason.
3. No row for new behaviour → add GAP row, link SCN, RED test or stop.
4. Update epic SCN ↔ REQ links.
5. Recount tier vs target (project.md).
6. Worklist: tick evidence or defer with reason.

Do NOT mark VERIFIED without a test that fails when the behaviour is removed.

Report: REQ id · old → new status · test citation · SCN link.
```

---

## Prompt 9 — Open an epic spec (multi-REQ)

```
Read /AGENTS.md §4, «EPIC_SPEC_TEMPLATE», and /project.md § Search scope.

Epic: «EPIC-XXX-NNN» · Topic: «…» · Spec slug: «kebab-slug»

Do NOT write product code.

1. RESEARCH — grep search scope. Fill reuse table honestly.
2. Extend epic at epics path — SCN scenarios with REQ ids.
3. Write GAP rows in ledger for every new behaviour.
4. Create spec under epic_spec_dir from template: decisions, REQ checklist, test plan (§6 layers),
   implementation order (vertical slices).
5. Add worklist row: epic, spec path, REQ ids, first slice.

Report: spec path, REQ ids, reuse, open questions, first slice.
```

---

## Prompt 10 — Validate ledger rows (IMPLEMENTED → VERIFIED)

```
Read /AGENTS.md §4, ledger_index, /project.md § Active programs (if any).

Phase: «audit-flip / RED+GREEN»
Context: «context code»
REQ scope: «REQ-XXX-001[, …]» or «all IMPLEMENTED in CTX»

For each REQ:

1. Read row — statement, code ref, detail block.
2. Open cited code — update file:line if stale.
3. Find or write test:
   - Audit-flip: existing `it(...)` asserts behaviour; fails for RIGHT reason if removed → VERIFIED.
   - RED+GREEN: smallest failing test, confirm red, then green if fixing code.
4. Update ledger: status, Tests column, detail block.
5. Epic SCN ↔ REQ links still match?
6. Recount tier vs target (project.md).
7. Worklist evidence; defer intentionally unverified rows.

Do NOT mark VERIFIED without a real test.

Report: REQ id · old → new · citation · tier before/after.
```

---

## Tips

1. **One REQ or one implementation-order row per run.**
2. **Ledger is the gate.** PRs list REQ ids. New behaviour never merges as IMPLEMENTED.
3. **Paths live in project.md** — resolve worklist, ledger, screenshots, open questions from § Paths.
4. **Reuse beats build.** Grep search scope first.
5. **Extend-on-touch** for neighbouring IMPLEMENTED rows in the same module.
6. **Scale profile** (AGENTS.md §0) — minimal repos skip epics/tiers; do not over-ceremony a small app.
7. **Specs are ephemeral** — delete when close checklist is green.
8. **Templates:** `_process/templates/` for bootstrapping a new repo.
