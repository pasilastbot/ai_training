# Session 2: Brownfield Development with AI

**90 min | Intermediate | "Taming Existing Codebases"**

Work with a real, large open-source codebase using AI. You'll learn to document, spec changes using SDD, and code review — all in unfamiliar code.

---

## Rehearsal Project: Suroi

**Repo:** https://github.com/HasangerGames/suroi
**What it is:** A 2D battle royale io-game (surviv.io clone), ~114k lines of TypeScript
**Live demo:** https://suroi.io

### Why Suroi?

- **~114k lines of TypeScript** — large enough that you NEED AI to navigate
- **Zero architecture docs** — README covers setup, not how the code works
- **Rich domain complexity** — game loop, entity system, physics, networking, map generation
- **Monorepo structure** — `client/`, `server/`, `common/` workspaces
- **Runs in browser** — change code, see results instantly
- **Real open issues** — actual bugs and feature requests to pick from

### Setup

```bash
git clone https://github.com/HasangerGames/suroi.git
cd suroi
cp /path/to/ai_training/AGENTS.md .
bun install
bun dev
# Open http://127.0.0.1:3000
```

**Important:** Copy `AGENTS.md` into the Suroi repo root. The prompts reference its templates for documentation and specs.

---

## Session Flow

| # | Type | Topic | Duration |
|---|------|-------|----------|
| | | **— PART 1: OVERVIEW —** | |
| 1 | THEORY | Greenfield vs Brownfield — 80% of work is brownfield | 5 min |
| 2 | THEORY | Vibe Coding vs Grounded SDD | 5 min |
| 3 | THEORY | ModernPath 4-Step Process (Document → Spec → Develop → Audit) | 5 min |
| | | **— PART 2: DOCUMENTATION —** | |
| 4 | **REHEARSAL** | **Clone Suroi, copy AGENTS.md, run `bun dev`, explore the codebase** | **10 min** |
| 5 | THEORY | Brownfield: 3-Tiered Documentation (High-level → Subsystem → Module) | 5 min |
| 6 | THEORY | Documentation Plan (content-plan.md — map what exists, index for AI) | 5 min |
| 7 | **BUILD** | **Document Suroi: create content-plan.md + document your subsystem** | **10 min** |
| 8 | THEORY | AI-Friendly Architecture *(side bite while AI documents)* | 5 min |
| 9 | **BUILD** | **Test & improve docs — ask AI questions about the codebase, iterate** | **5 min** |
| | | **— PART 3: SPEC-DRIVEN CHANGE —** | |
| 10 | **BUILD** | **Prompt a change to the game, generate specs using SDD** | **10 min** |
| 11 | THEORY | Code Review with AI (Critique loops, PR review prompts) | 5 min |
| 12 | **BUILD** | **Code review the change against the spec** | **10 min** |
| 13 | WRAP-UP | What you documented & improved, Q&A | 5 min |

**Total: 90 min** (30 min theory + 45 min hands-on + 5 min wrap-up + 10 min rehearsal)

---

## Pick a Subsystem

Choose ONE subsystem to focus on during the session:

| Subsystem | Location | What to document |
|-----------|----------|-----------------|
| **Game loop & entities** | `server/src/game.ts`, `server/src/objects/` | How the game tick works, entity lifecycle, collision |
| **Weapons & inventory** | `common/src/definitions/`, `server/src/inventory/` | Weapon definitions, damage calc, ammo system |
| **Networking** | `server/src/server.ts`, `client/src/game.ts` | Client-server protocol, state sync, WebSocket messages |
| **Map generation** | `server/src/map.ts`, `common/src/definitions/obstacles.ts` | How maps are generated, obstacle placement, terrain |
| **Rendering** | `client/src/rendering/` | PixiJS scene graph, camera, particle effects |

---

## Prompt Files

Follow these in order during the BUILD steps:
1. `prompts/01-explore.md` — Explore the codebase with AI (REHEARSAL, Part 2)
2. `prompts/02-document.md` — Create content-plan.md + 3-tiered docs using AGENTS.md templates (BUILD steps 7 + 9)
3. `prompts/03-spec-change.md` — Prompt a change, write a grounded spec using AGENTS.md spec template (BUILD step 10)
4. `prompts/04-review.md` — Code review the change against the spec (BUILD step 12)
