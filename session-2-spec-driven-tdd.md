# Session 2: Spec-Driven Development & TDD with AI
**Duration:** 90 min | **Level:** Intermediate

**Prerequisites:** Session 1 (AI-Assisted Development Fundamentals)

**Goal:** Production-grade development — Specs, TDD, architecture

**Theme:** This is the hard engineering session. We move from rapid prototyping to building maintainable, production-ready code. Quality over speed.

---

## Vibe Coding vs Spec-Driven Development (10 min)
**Understanding the tradeoff**

### The Two Approaches

| Aspect | Vibe Coding | Spec-Driven Development |
|--------|-------------|------------------------|
| **Speed** | Fast start | Slower start |
| **Planning** | Minimal | Thorough |
| **Documentation** | None/minimal | Comprehensive |
| **Maintainability** | Low | High |
| **Best for** | Prototypes, experiments | Production systems |

### When to Use Each

**Vibe Coding is appropriate for:**
- Hackathons and demos
- Personal projects
- Proof of concepts
- Learning new tech

**SDD is required for:**
- Production systems
- Team projects
- Long-lived codebases
- Enterprise software

### The Proto → Production Transition

Session 1 gave you vibe coding skills. Now we add the engineering discipline:

```
SESSION 1 (Proto)          SESSION 2 (Production)
─────────────────          ────────────────────
Fast iteration      →      Deliberate design
AI-driven           →      Spec-driven
Works on my machine →      Works in production
Solo developer      →      Team collaboration
```

---

## ModernPath's 4-Step Process (15 min)
**Document → Spec → Develop → Audit**

### The Lifecycle

This is the core of ModernPath's approach. Each step produces artifacts that feed the next.

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  DOCUMENT   │───▶│    SPEC     │───▶│   DEVELOP   │───▶│    AUDIT    │
│             │    │             │    │             │    │             │
│ Understand  │    │ Contract    │    │ Implement   │    │ Verify      │
│ the problem │    │ the solution│    │ the code    │    │ correctness │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     │                   │                  │                  │
     ▼                   ▼                  ▼                  ▼
  ADRs, Docs         Specs, ACs         Code, Tests      Reports, Fixes
```

### Why This Order Matters

**Without this process:**
```
User: "Build authentication"
AI: *generates 500 lines of code*
User: "Wait, that's not what I wanted"
AI: *regenerates different 500 lines*
User: "Still wrong"
[repeat until frustrated]
```

**With this process:**
```
Document: "We need OAuth2 + MFA for enterprise compliance"
Spec: "Given admin user, when MFA enforced, then require TOTP"
Develop: AI implements exactly what spec says
Audit: Spec passes = feature complete
```

---

## Core Workflows (10 min)
**Research, spec, tdd, develop, fix, validate**

### Workflow Definitions

Each step in the lifecycle has associated workflows that AI agents execute:

| Workflow | Purpose | Inputs | Outputs |
|----------|---------|--------|---------|
| `research` | Understand before acting | Codebase, docs, web | Analysis report |
| `spec` | Define the contract | Requirements, research | Specification document |
| `tdd` | Write tests first | Specification | Failing tests |
| `develop` | Implement to pass tests | Spec, failing tests | Passing code |
| `fix` | Debug and resolve issues | Error logs, code | Working code |
| `validate` | Verify completeness | All artifacts | Audit report |

### Workflow Configuration Example

In your AGENTS.md or .cursor/rules/:

```markdown
## Workflow: research
When starting any new task:
1. Read related docs in @docs/
2. Search codebase for existing patterns: @codebase [topic]
3. Check for ADRs: @docs/adrs/
4. Produce analysis before proposing changes

## Workflow: spec
Before writing code:
1. Create spec in @specs/[feature-name].md
2. Include all acceptance criteria
3. Get human approval on spec
4. Only then proceed to development

## Workflow: tdd
When implementing:
1. Write failing test first
2. Run test to confirm it fails
3. Implement minimum code to pass
4. Refactor while keeping tests green
5. Repeat for each acceptance criterion

## Workflow: fix
When encountering errors:
1. Read error message carefully
2. Search codebase for similar patterns
3. Check docs/learnings.md for previous solutions
4. Hypothesize root cause
5. Implement fix
6. Validate with tests

## Workflow: validate
After implementation:
1. Run full test suite
2. Check linter
3. Verify against original spec
4. Document any deviations
```

---

## Writing Effective Specifications (20 min)
**Templates, acceptance criteria, testable requirements**

### The Specification Template

Every spec should follow this structure:

```markdown
# Feature: [Name]

## Overview
[2-3 sentences describing the feature and its business value]

## User Stories
As a [role], I want [capability], so that [benefit].

## Acceptance Criteria

### AC1: [Descriptive Name]
**Given** [precondition]
**When** [action]
**Then** [expected result]
**And** [additional assertions]

### AC2: [Descriptive Name]
**Given** [precondition]
**When** [action]
**Then** [expected result]

## Technical Constraints
- [Constraint 1: e.g., "Must use existing auth middleware"]
- [Constraint 2: e.g., "Response time < 200ms"]
- [Constraint 3: e.g., "Compatible with existing API v2 clients"]

## Out of Scope
- [What this feature explicitly does NOT include]

## Dependencies
- @src/path/to/dependency.ts - [why needed]
- @docs/related-doc.md - [reference]

## Test Strategy
- Unit tests for: [list components]
- Integration tests for: [list flows]
- E2E tests for: [list scenarios]
```

### Writing Testable Acceptance Criteria

**Bad AC (vague, untestable):**
```
The login should be secure and fast.
```

**Good AC (specific, testable):**
```
### AC1: Rate Limiting
**Given** a user has failed login 5 times in 10 minutes
**When** they attempt a 6th login
**Then** return 429 Too Many Requests
**And** include Retry-After header set to 300 seconds
**And** log security event with user IP and timestamp
```

**Why the good version works:**
- Numbers are concrete (5 times, 10 minutes, 300 seconds)
- Response is specific (429 status, specific header)
- Side effects are explicit (logging requirement)
- AI can convert this directly to a test

### The "Can AI Test This?" Check

Before finalizing a spec, ask:

1. **Is every AC measurable?** (numbers, states, not feelings)
2. **Are edge cases explicit?** (null inputs, errors, boundaries)
3. **Are side effects listed?** (logs, emails, database changes)
4. **Is the happy path AND error path defined?**
5. **Can this AC be copy-pasted into a test description?**

If any answer is "no," the spec needs more work.

### Converting AC to Tests

Each AC should map directly to a test:

```typescript
// From AC1: Rate Limiting
describe('Login Rate Limiting', () => {
  it('should return 429 after 5 failed attempts in 10 minutes', async () => {
    // Given: a user has failed login 5 times in 10 minutes
    const user = await createTestUser();
    for (let i = 0; i < 5; i++) {
      await loginWithWrongPassword(user.email);
    }
    
    // When: they attempt a 6th login
    const response = await loginWithWrongPassword(user.email);
    
    // Then: return 429 Too Many Requests
    expect(response.status).toBe(429);
    
    // And: include Retry-After header set to 300 seconds
    expect(response.headers['retry-after']).toBe('300');
  });
});
```

---

## AI-Friendly Architecture Deep Dive (15 min)
**Designing for AI maintainability**

### The Dependency Inversion Principle for AI

**Problem:** AI struggles with tightly coupled code because changes cascade unpredictably.

**Solution:** Depend on abstractions, not implementations.

```typescript
// ❌ Tightly coupled - AI can't safely modify
class UserService {
  async createUser(data: UserData) {
    const db = new PostgresDatabase(); // Hard dependency
    const user = await db.insert('users', data);
    const mailer = new SendGridMailer(); // Hard dependency
    await mailer.send(user.email, 'Welcome!');
    return user;
  }
}

// ✅ Loosely coupled - AI can safely modify each piece
interface Database {
  insert(table: string, data: unknown): Promise<unknown>;
}

interface Mailer {
  send(to: string, subject: string, body: string): Promise<void>;
}

class UserService {
  constructor(
    private db: Database,
    private mailer: Mailer
  ) {}

  async createUser(data: UserData) {
    const user = await this.db.insert('users', data);
    await this.mailer.send(user.email, 'Welcome!', welcomeTemplate(user));
    return user;
  }
}
```

**Why this helps AI:**
- Each interface is documented and testable independently
- AI can modify `UserService` without understanding Postgres internals
- Mock implementations make testing trivial
- Changes don't cascade to other parts of the system

### The "One Spec, One Module" Rule

Each specification should map to exactly one module:

```
specs/
├── user-authentication.md  ──────▶  src/features/auth/
├── user-profile.md         ──────▶  src/features/profile/
├── payment-processing.md   ──────▶  src/features/payments/
└── notification-system.md  ──────▶  src/features/notifications/
```

**Why:** AI can work on one spec → one module without needing to understand the entire codebase.

### Feature Folder Structure

```
src/features/auth/
├── README.md           # Module documentation (Tier 2)
├── SPEC.md             # Current specification
├── types.ts            # All TypeScript types for this feature
├── constants.ts        # Feature-specific constants
├── auth.service.ts     # Business logic
├── auth.controller.ts  # HTTP handlers
├── auth.repository.ts  # Data access
├── validators/         # Input validation
│   ├── login.validator.ts
│   └── register.validator.ts
├── __tests__/          # Co-located tests
│   ├── auth.service.test.ts
│   └── auth.integration.test.ts
└── __mocks__/          # Test mocks for this feature
    └── auth.service.mock.ts
```

**Key insight:** Everything the AI needs to understand and modify the auth feature is in one folder.

---

## TDD Cycle with AI (15 min)
**Write failing test → Generate implementation → Refactor**

### The Red-Green-Refactor Loop

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│    ┌─────────┐         ┌─────────┐         ┌─────────┐     │
│    │   RED   │────────▶│  GREEN  │────────▶│ REFACTOR│     │
│    │         │         │         │         │         │     │
│    │ Write   │         │ Write   │         │ Improve │     │
│    │ failing │         │ minimum │         │ code    │     │
│    │ test    │         │ code    │         │ quality │     │
│    └─────────┘         └─────────┘         └─────────┘     │
│         ▲                                       │          │
│         │                                       │          │
│         └───────────────────────────────────────┘          │
│                    Tests still pass                        │
└─────────────────────────────────────────────────────────────┘
```

### Step 1: RED - Write the Failing Test

**Prompt to AI:**
```
@specs/user-authentication.md

Looking at AC1 (Rate Limiting), write a failing test.

Requirements:
- Use Vitest and @testing-library
- Follow existing test patterns in @src/features/auth/__tests__/
- Include setup and teardown
- Test ONLY this one acceptance criterion
- Do not implement the feature yet

Run the test to confirm it fails.
```

### Step 2: GREEN - Write Minimum Code to Pass

**Prompt to AI:**
```
The test in @src/features/auth/__tests__/rate-limiting.test.ts is failing.

Implement the minimum code needed to make it pass.

Requirements:
- Add rate limiting to the login endpoint
- Use Redis for rate limit storage (existing client at @src/lib/redis.ts)
- Follow existing patterns in @src/features/auth/
- Do not over-engineer - just make the test pass

After implementing, run the test to confirm it passes.
```

### Step 3: REFACTOR - Improve Without Breaking

**Prompt to AI:**
```
The test passes. Now refactor the rate limiting code for:
1. Better error messages
2. Configurable limits (not hardcoded 5 attempts)
3. Proper TypeScript types
4. Documentation comments

Keep running the test after each change to ensure it still passes.
Do not add new functionality - only improve existing code.
```

**Key rule:** Tests must pass after every refactor step.

### Executable Specifications

When specs + tests align, your tests become living documentation:

```typescript
/**
 * @spec specs/password-reset.md
 * @ac AC1: Password Reset Request
 */
describe('Password Reset Request', () => {
  it('should send reset email for valid user', async () => {
    // Given: a registered user
    // When: they request password reset
    // Then: email is sent with reset link
  });

  it('should return success even for unknown email (security)', async () => {
    // Given: an email not in our system
    // When: they request password reset
    // Then: return 200 (don't reveal user existence)
  });
});
```

---

## Code Review with AI (10 min)
**Critique loops, PR review prompts, quality feedback**

### The Critique Loop

AI-assisted code review follows a feedback cycle:

```
┌─────────────────────────────────────────────────────────────┐
│                    CRITIQUE LOOP                            │
│                                                             │
│    ┌─────────┐         ┌─────────┐         ┌─────────┐     │
│    │ SUBMIT  │────────▶│ AI      │────────▶│ REVISE  │     │
│    │ CODE    │         │ REVIEW  │         │         │     │
│    └─────────┘         └─────────┘         └─────────┘     │
│         ▲                   │                   │          │
│         │                   ▼                   │          │
│         │              ┌─────────┐              │          │
│         └──────────────│FEEDBACK │◀─────────────┘          │
│                        └─────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### PR Review Prompts

Use specialized prompts for different review aspects:

**Security Review:**
```
Review this code for security vulnerabilities:
- SQL injection
- XSS vulnerabilities
- Authentication bypasses
- Sensitive data exposure
- Input validation gaps

@src/features/auth/login.service.ts
```

**Performance Review:**
```
Review this code for performance issues:
- N+1 queries
- Unnecessary re-renders
- Memory leaks
- Missing caching opportunities
- Inefficient algorithms

@src/features/dashboard/analytics.service.ts
```

**Edge Case Review:**
```
Review this code for edge cases:
- Null/undefined handling
- Empty arrays/objects
- Boundary conditions
- Error states
- Concurrent access

@src/features/payments/checkout.service.ts
```

### Multi-Pass Review Strategy

For thorough reviews, run multiple passes:

```markdown
## Code Review Checklist

Pass 1: Logic Correctness
- Does it do what the spec says?
- Are all acceptance criteria covered?

Pass 2: Error Handling
- Are all errors caught and handled?
- Are error messages helpful?
- Is there proper logging?

Pass 3: Security
- Input validation?
- Authentication/authorization checks?
- Data sanitization?

Pass 4: Performance
- Database query efficiency?
- Caching where appropriate?
- No blocking operations?

Pass 5: Maintainability
- Clear naming?
- Appropriate comments?
- Test coverage?
```

### AI Catches What Humans Miss

Studies show AI excels at finding:
- **Pattern violations** — inconsistent naming, style drift
- **Subtle bugs** — off-by-one errors, null dereferencing
- **Missing error handling** — uncaught exceptions, silent failures
- **Copy-paste mistakes** — duplicated code with wrong variables

**Rule:** Run AI review on every PR before human review. AI handles tedium, humans handle judgment.

---

## The Fix Workflow (10 min)
**Systematic debugging, error resolution, documenting learnings**

### The 5-Step Fix Process

When encountering errors, AI should follow this systematic approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    THE FIX WORKFLOW                         │
│                                                             │
│  1. REPRODUCE ──▶ 2. HYPOTHESIZE ──▶ 3. VALIDATE           │
│      🐛              💡                 🧪                  │
│                                          │                  │
│                                          ▼                  │
│              5. DOCUMENT ◀── 4. FIX                        │
│                  📖            🔧                           │
└─────────────────────────────────────────────────────────────┘
```

### Step-by-Step Breakdown

**Step 1: REPRODUCE**
```markdown
Before fixing anything:
1. Read the error message completely
2. Identify the exact steps to reproduce
3. Note the environment (dev, staging, prod)
4. Capture relevant logs and stack traces
```

**Step 2: HYPOTHESIZE**
```markdown
Form a hypothesis about the root cause:
1. Check docs/learnings.md for similar past issues
2. Search codebase for related patterns
3. Identify 1-2 most likely causes
4. Rank by probability and ease of testing
```

**Step 3: VALIDATE**
```markdown
Test your hypothesis before implementing:
1. Add temporary logging if needed
2. Run targeted tests
3. Use debugger to inspect state
4. Confirm or reject hypothesis
```

**Step 4: FIX**
```markdown
Implement the fix:
1. Make minimal changes (don't fix unrelated issues)
2. Follow existing patterns
3. Run tests after each change
4. Ensure fix doesn't break other things
```

**Step 5: DOCUMENT**
```markdown
Record the learning in docs/learnings.md:
1. Symptoms observed
2. Root cause identified
3. Solution applied
4. How to prevent in future
```

### The 3-Attempt Rule

```
┌─────────────────────────────────────────────────────────────┐
│ ATTEMPT 1: Most likely hypothesis                          │
│    ↓                                                       │
│ ATTEMPT 2: Second hypothesis (if first fails)              │
│    ↓                                                       │
│ ATTEMPT 3: Third approach                                  │
│    ↓                                                       │
│ ❌ STOP: Ask human for guidance                            │
│                                                            │
│ Never loop more than 3 times on the same core issue        │
│ without human input.                                       │
└─────────────────────────────────────────────────────────────┘
```

### learnings.md Template

Every fix should update the team's knowledge base:

```markdown
## [Date]: [Brief Issue Description]

### Symptoms
- Error message: "..."
- Occurred when: [action]
- Environment: [dev/staging/prod]

### Root Cause
[Explanation of what caused the issue]

### Solution
[Code changes made, with file paths]

### Prevention
- [ ] Add validation for X
- [ ] Add test case for Y
- [ ] Update documentation for Z

### Related Files
- @src/path/to/affected/file.ts
```

### Why Document Every Fix?

1. **Team knowledge** — Others won't repeat your debugging
2. **AI context** — Future AI sessions can reference past solutions
3. **Pattern recognition** — Recurring issues indicate systemic problems
4. **Onboarding** — New team members learn from documented war stories

**Rule:** If you spent more than 30 minutes debugging, it deserves a learnings.md entry.

---

## 💡 DEMO 1: The Full SDD Loop (10 min)

### Live Demonstration

We'll walk through the complete Spec-Driven Development loop:

1. **Document** - Understand the requirement
2. **Spec** - Create specification with testable ACs
3. **Develop** - TDD cycle (Red → Green → Refactor)
4. **Audit** - Verify against spec

Watch AI:
1. Write the test from AC
2. Confirm it fails
3. Implement the code
4. Confirm it passes
5. Refactor

---

## 💡 SHARED LEARNING: Writing the Perfect Spec (10 min)

### Group Exercise

**The Challenge:** A team member wrote this spec. Is it machine-testable?

```markdown
# Feature: User Notifications

## Acceptance Criteria

### AC1: Send Notifications
Users receive notifications for important events.

### AC2: Read Notifications  
Users can mark notifications as read.
```

**Your Task (in small groups):**

1. **Identify problems** with each AC
2. **Rewrite AC1** to be specific and testable
3. **Add missing details** (what events? what channels? what data?)

**Target Rewrite for AC1:**
```markdown
### AC1: Send Notification on New Comment
**Given** a user has enabled comment notifications
**And** they authored a post
**When** another user comments on their post
**Then** create a notification record with:
  - type: "new_comment"
  - recipientId: post author's ID
  - senderId: commenter's ID
  - read: false
**And** if email notifications enabled, queue email job
```

---

## Key Takeaways

1. **Vibe → SDD transition** — Proto is fast, production needs discipline
2. **Document → Spec → Develop → Audit** — Follow the lifecycle religiously
3. **Specs must be testable** — If AI can't convert it to a test, rewrite it
4. **Architecture enables AI** — Loose coupling, one spec → one module
5. **TDD with AI** — Red → Green → Refactor
6. **Quality checkpoints** — Gates ensure quality at each stage
7. **Code review with AI** — Multi-pass critique loops catch what humans miss
8. **The Fix Workflow** — Reproduce → Hypothesize → Validate → Fix → Document

---

## Preparation for Session 3

Before the next session:
1. Write a spec for a feature in your project using the template
2. Implement one feature using full TDD with AI
3. Create or update your project's .cursor/rules/ with testing standards
4. Read: Multi-agent architectures in AI coding tools
