# Session 1: AI-Assisted Development Fundamentals
**Duration:** 90 min | **Level:** Beginner

**Goal:** Build rapid prototypes with AI — From zero to working demo

**Theme:** This session establishes your proto capability. You'll learn to leverage AI tools to quickly build working prototypes and proof-of-concepts. Speed over perfection.

---

## 1. AI Coding Tools Landscape (20 min)
**Cursor, Copilot, Claude Code, Codex**

### Tool Overview

The AI coding landscape has evolved rapidly. Understanding the strengths of each tool helps you choose the right one for each task.

| Tool | Strengths | Best For |
|------|-----------|----------|
| **Cursor** | Deep codebase understanding, multi-file edits, agent mode | Complex refactoring, brownfield projects |
| **GitHub Copilot** | Fast inline completion, tight VS Code integration | Rapid boilerplate, small edits |
| **Claude Code** | Long context window, reasoning transparency | Architecture decisions, spec writing |
| **Codex CLI** | Terminal-native, scriptable | CI/CD integration, automation |

### Rules and Instructions Configuration

Every AI tool can be configured with persistent instructions. This is your **codebase constitution**.

```
project-root/
├── .cursor/
│   └── rules/           # Cursor-specific rules
│       ├── main.mdc     # Always-applied rules
│       └── testing.mdc  # Applied when working on tests
├── CLAUDE.md            # Claude Code instructions
└── AGENTS.md            # Cross-tool neutral format
```

**Why This Matters:** Without rules, AI makes inconsistent decisions. With rules, every team member's AI assistant behaves the same way.

### Getting Started with CLAUDE.md / AGENTS.md

These files tell the AI:
- Project structure and conventions
- Common commands and scripts
- Testing requirements
- Code style preferences
- What NOT to do (guardrails)

**Example AGENTS.md structure:**

```markdown
# AGENTS.md

## Project Overview
This is a Next.js 14 app with App Router, TypeScript strict mode, and Tailwind CSS.

## Key Commands
- `npm run dev` - Start development server
- `npm run test` - Run Vitest tests
- `npm run lint` - ESLint + Prettier

## Coding Standards
- All components must be functional with TypeScript interfaces
- Use `use client` directive only when necessary
- Prefer server components by default

## Testing Requirements
- Every feature needs unit tests before merge
- Use @testing-library/react for component tests
- Mock external APIs with MSW

## Do NOT
- Commit .env files
- Use `any` type without explicit reason
- Skip error handling in async functions
```

---

## 2. Effective Prompting Patterns (20 min)
**Context sandwich, incremental approach, review requests**

### The Context Sandwich

The most common AI failure: vague prompts with no grounding. The **Context Sandwich** fixes this:

```
TOP BREAD (Context):
@src/auth/login.ts
@docs/architecture.md

FILLING (Request):
"Refactor the login function to use the new OAuth2 flow 
documented in architecture.md"

BOTTOM BREAD (Constraints):
"Keep the existing error handling. 
Add unit tests for the new flow."
```

**Why it works:** The AI has evidence (files), a clear task (refactor), and constraints (keep errors, add tests). No guessing required.

### The @ Symbol: Your Context Injection Tool

| Symbol | What It Does | Example |
|--------|--------------|---------|
| `@file` | Include specific file | `@src/utils/auth.ts` |
| `@folder` | Include folder contents | `@src/components/` |
| `@codebase` | Semantic search across project | `@codebase how does caching work?` |
| `@docs` | Include documentation | `@docs/api-spec.md` |
| `@web` | Search the internet | `@web Next.js 14 server actions` |
| `@git` | Include git context | `@git diff HEAD~3` |

**Pro Tip:** Over-specify context rather than under-specify. Token cost is cheap; debugging AI hallucinations is expensive.

### Incremental Approach

Never ask AI to "build the whole feature." Break it down:

**Bad:**
> "Build a user authentication system with OAuth, MFA, and session management"

**Good (5-step sequence):**
1. "Create the OAuth2 callback handler following our existing patterns in `@src/auth/`"
2. "Add the session token generation using the algorithm documented in `@docs/security.md`"
3. "Implement MFA verification as a middleware. Here's the spec: `@specs/mfa.md`"
4. "Write unit tests for the OAuth flow. Use `@src/auth/__tests__/` as reference"
5. "Add integration test for the full login → MFA → session flow"

### Review Requests

Before executing, ask the AI to review its own plan:

```
"Before making changes:
1. List all files you'll modify
2. Explain the risk of each change
3. Identify what could break
4. Suggest what tests should cover this"
```

This catches errors before they happen. The AI often spots its own mistakes when forced to explain.

### The Critique Loop

When AI output isn't right, don't start over. Critique it:

```
"This implementation has issues:
1. The error handling doesn't match our pattern in @src/utils/errors.ts
2. Missing null checks on line 23
3. No TypeScript interface for the response

Fix these while keeping the core logic."
```

**Why it works:** Iterative refinement is faster than regeneration. The AI already has context; use it.

---

## 3. Model Selection (15 min)
**Claude vs GPT vs Gemini, strengths and use cases**

### Understanding the "Brains"

Different models excel at different tasks. Match the model to the job.

| Model | Reasoning | Speed | Context | Best For |
|-------|-----------|-------|---------|----------|
| **Claude Opus 4** | ★★★★★ | ★★☆☆☆ | 200K | Architecture, complex refactoring |
| **Claude Sonnet 4** | ★★★★☆ | ★★★★☆ | 200K | Daily coding, balanced tasks |
| **GPT-4o** | ★★★★☆ | ★★★★☆ | 128K | General purpose, API integration |
| **GPT-4o-mini** | ★★★☆☆ | ★★★★★ | 128K | Fast iteration, simple edits |
| **Gemini 2.5 Pro** | ★★★★★ | ★★★☆☆ | 1M+ | Massive codebases, long documents |
| **Gemini 2.5 Flash** | ★★★☆☆ | ★★★★★ | 1M+ | Quick search, fast responses |

### Strengths and Use Cases

**Use high-reasoning models (Opus, GPT-4) when:**
- Making architectural decisions
- Debugging complex issues
- Writing specifications
- Reviewing security-critical code

**Use fast models (Sonnet, Flash, mini) when:**
- Writing boilerplate code
- Making simple edits
- Running quick searches
- Iterating rapidly on UI

### Practical Model Switching

In Cursor, you can switch models mid-conversation:
1. Start with **Sonnet** for initial exploration
2. Switch to **Opus** when you need deep reasoning
3. Drop to **Flash** for quick follow-up questions

**Cost Awareness:**
- Opus: ~$15 per 1M input tokens
- Sonnet: ~$3 per 1M input tokens  
- Flash: ~$0.075 per 1M input tokens

One Opus call ≈ 40 Flash calls. Use Opus for decisions, Flash for execution.

---

## 4. Greenfield vs Brownfield Development (10 min)
**Different AI approaches for new vs. existing codebases**

### The Strategic Shift

AI coding tools were built for greenfield (new projects). But 80% of enterprise work is brownfield (existing systems). You need different strategies.

| Aspect | Greenfield | Brownfield |
|--------|------------|------------|
| **Context** | You define it | You must discover it |
| **Architecture** | Design for AI | Adapt AI to existing patterns |
| **Risk** | Low (fresh start) | High (breaking changes) |
| **AI Strength** | Generation | Understanding first, then changes |

### Key Insight

- **Greenfield:** Design for AI maintainability from day one
- **Brownfield:** Invest in documentation before attempting AI-assisted changes

---

## 5. Greenfield Development (15 min)
**Intro to spec-driven development, AI-friendly architecture**

### Intro to Spec-Driven Development (SDD)

When starting fresh, **write the specification BEFORE the code**:

```markdown
# Feature: User Profile Update

## Overview
Users can update their profile information including name, email, and avatar.

## Acceptance Criteria
- GIVEN a logged-in user
- WHEN they submit the profile form with valid data
- THEN their profile is updated and a success message appears

## Technical Constraints
- Use existing `@src/api/users.ts` patterns
- Avatar uploads go to S3 via `@src/utils/upload.ts`
- Max avatar size: 5MB
```

This spec becomes the AI's instruction manual. Without it, you're "vibe coding" and hoping for the best.

### AI-Friendly Architecture

Design systems that AI can navigate and maintain:

**Principles:**
- **Modularity:** Each feature is self-contained
- **Cohesion:** Related code lives together
- **Testability:** Tests next to implementation

**Feature Folder Structure:**
```
src/features/
├── auth/
│   ├── README.md       # Feature documentation
│   ├── types.ts        # All types for this feature
│   ├── auth.service.ts # Business logic
│   ├── auth.controller.ts
│   └── __tests__/      # Co-located tests
└── profile/
    └── ...
```

**Key insight:** Everything the AI needs to understand and modify a feature is in one folder. One Spec → One Module → One Folder.

---

## 6. Brownfield Development (10 min)
**Documenting existing codebases, AI-navigable 3-tiered documentation**

### Documenting Existing Codebases

For existing codebases, **understand before changing**:

#### The Content Plan Index

Start every brownfield project by creating `content-plan.md`:

```markdown
# Documentation Content Plan

This file serves as the AI-navigable index for this codebase.

## Generated Documentation
| Module | Status | Path |
|--------|--------|------|
| Architecture Overview | ✅ Done | `docs/architecture.md` |
| Auth System | ✅ Done | `docs/auth-system.md` |
| Database Schema | 🔄 In Progress | `docs/database.md` |
| API Endpoints | ❌ Not Started | `docs/api.md` |

## Generation Instructions
When generating docs, follow this order:
1. High-level architecture first
2. Then core systems (auth, database)
3. Then features
4. Finally, API reference
```

**Why it works:** The AI can read this index and understand what documentation exists, what's missing, and in what order to generate new docs.

### AI-Navigable 3-Tiered Documentation Structure

Create documentation at three levels of detail:

**Tier 1: High-Level (README.md, ADRs)**
```markdown
# Authentication System

## Purpose
Handles all user authentication including login, OAuth, and session management.

## Key Decisions
- JWT for stateless auth (ADR-003)
- Redis for session cache (ADR-007)

## Entry Points
- `src/auth/login.ts` - Main login flow
- `src/auth/oauth/` - OAuth providers
```

**Tier 2: Module Overview (feature/README.md)**
```markdown
# OAuth Integration

## Flow
1. User clicks "Login with Google"
2. Redirect to `GET /auth/google`
3. Google callback hits `GET /auth/google/callback`
4. Token exchange in `exchangeToken()`
5. Session created via `createSession()`

## Dependencies
- `@src/auth/session.ts` - Session management
- `@src/utils/crypto.ts` - Token signing
```

**Tier 3: Code-Level (inline comments + tests)**
```typescript
/**
 * Exchanges OAuth authorization code for access token.
 * 
 * @param code - Authorization code from OAuth provider
 * @param provider - OAuth provider (google, github, etc.)
 * @returns Access token and user info
 * 
 * @see docs/auth-system.md for full flow
 */
export async function exchangeToken(
  code: string, 
  provider: OAuthProvider
): Promise<TokenResponse> {
  // Implementation
}
```

---

## 💡 DEMO 1: Setting up AGENTS.md (10 min)

### Live Exercise

We'll create an AGENTS.md file for a sample project together:

1. **Analyze the project structure**
   ```
   @codebase What is the overall structure of this project?
   ```

2. **Identify key patterns**
   ```
   @src/ What coding patterns and conventions are used here?
   ```

3. **Draft the AGENTS.md**
   - Project overview
   - Key commands
   - Coding standards
   - Testing requirements
   - Guardrails

4. **Test it**
   - Ask AI to make a small change
   - Observe if it follows the new rules

---

## 💡 SHARED LEARNING: The Context Sandwich (15 min)

### Collaborative Exercise

**The Challenge:** Transform a "vibe prompt" into a grounded "sandwich prompt."

**Starting Prompt (Vibe):**
> "Make the login page better"

**Your Task (in pairs):**

1. **Identify what files to include as context**
   - Where is the current login page?
   - What design system do we use?
   - Are there related components?

2. **Clarify the actual request**
   - What does "better" mean? Faster? Prettier? More secure?
   - What specific improvements?

3. **Add constraints**
   - What must NOT change?
   - What tests need to pass?
   - What's the deadline/scope?

**Target Output:**
```
@src/pages/login.tsx
@src/components/ui/Button.tsx
@docs/design-system.md

"Improve the login page by:
1. Adding loading state to the submit button
2. Showing inline validation errors (not alerts)
3. Adding 'Forgot Password' link below the form

Keep the existing form validation logic.
Match the button style from the design system.
Add unit tests for the new loading state."
```

---

## Key Takeaways

1. **Proto capability** — This session gives you rapid prototyping skills
2. **Configure your AI** with AGENTS.md/CLAUDE.md — it's your codebase constitution
3. **Use the Context Sandwich** — always ground prompts with @ symbols
4. **Match model to task** — Opus/Sonnet for thinking, Flash/Haiku for doing
5. **Greenfield: Spec first** — write the contract before the code
6. **Brownfield: Document first** — understand before changing
7. **Documentation Plan** — content-plan.md works for both greenfield and brownfield

---

## Preparation for Session 2

Before the next session:
1. Create an AGENTS.md for your own project
2. Practice the Context Sandwich on 3 real tasks
3. Build one rapid prototype using the techniques from this session
4. Read: `product/gtm/20-delivery-playbooks.md` (Spec-Driven Development section)
