# Spec-Driven Development - Quick Start

## TL;DR

```bash
# 1. Research: Read documentation FIRST
Read: docs/description.md, architecture.md, datamodel.md

# 2. Create spec from template
Copy: specs/TEMPLATE.md → specs/features/my-feature.md

# 3. Fill in the contract
- What does it do? (Requirements)
- What are the inputs/outputs? (API Contract)
- How do we test it? (Acceptance Criteria)

# 4. Get approval
- Review with team/user
- Update spec based on feedback

# 5. Implement
- Code to fulfill the contract
- Verify against spec

# 6. Validate
- Run tests defined in spec
- Check acceptance criteria
```

## The 5-Minute Spec

If you only have 5 minutes, include these sections:

### 1. Overview (30 seconds)
```markdown
## Overview
This feature allows users to [action] by [method].
```

### 2. API Contract (1 minute)
```markdown
## API Contract
Input: { param1: string, param2: number }
Output: { result: string, status: 'success' | 'error' }
Errors: 'invalid_input', 'timeout', 'server_error'
```

### 3. Testing Strategy (2 minutes - MANDATORY)
```markdown
## Testing Strategy
**Unit Tests:**
- Test [function1] with valid input → expected output
- Test [function1] with invalid input → error thrown
- Test [function2] edge case (empty, null) → handles gracefully

**Integration Tests:**
- Test API endpoint success case → 200 OK
- Test API endpoint error case → 400 Bad Request

**E2E Tests:**
- User completes [main flow] → sees success
- User triggers error → sees error message, can recover
```

### 4. Acceptance Criteria (1 minute)
```markdown
## Acceptance Criteria
- [ ] User can [action]
- [ ] System responds within 2 seconds
- [ ] Errors are handled gracefully
- [ ] All unit tests pass (minimum 3 tests)
- [ ] All integration tests pass (minimum 2 tests)
- [ ] All E2E tests pass (minimum 2 scenarios)
```

### 5. Files to Change (30 seconds)
```markdown
## Component Structure
Create: tools/my-tool.ts, tests/my-tool.test.ts
Modify: package.json, gemini_agent.py
```

**Done!** You have a minimal spec. Expand as needed.

**⚠️ CRITICAL:** Never skip the Testing Strategy section. A spec without tests is incomplete.

## Common Spec Types

### CLI Tool Spec
Focus on:
- Command-line options
- Input validation
- Output format (stdout/file)
- Error messages

### API Endpoint Spec
Focus on:
- HTTP method and path
- Request/response schemas
- Status codes
- Authentication

### UI Component Spec
Focus on:
- Props interface
- User interactions
- Visual states (loading, error, success)
- Accessibility

### Agent Function Spec
Focus on:
- Function declaration for LLM
- Parameter schema
- Return value format
- Tool execution logic

## Workflow Cheat Sheet

| Step | Command | What It Does |
|------|---------|--------------|
| **Research** | Use `<research>` workflow | Reads docs, searches codebase |
| **Spec** | Use `<spec>` workflow | Creates specification |
| **Implement** | Use `<develop>` workflow | Codes according to spec |
| **Test** | Use `<validate>` workflow | Verifies implementation |
| **Record** | Use `<record>` workflow | Updates changelog |

## Documentation Reading Checklist

Before writing a spec, read these (use Read tool):

- [ ] `docs/description.md` - App purpose and features
- [ ] `docs/architecture.md` - Tech stack and patterns
- [ ] `docs/datamodel.md` - Existing data structures

For frontend features:
- [ ] `docs/frontend.md` - UI/UX patterns

For backend features:
- [ ] `docs/backend.md` - API patterns

For AI features:
- [ ] `tools/gemini.ts` or `gemini_agent.py` - Existing patterns

## Spec Status States

```
Draft → In Review → Approved → Implemented
```

- **Draft:** Work in progress, may have gaps
- **In Review:** Ready for feedback
- **Approved:** Ready to implement
- **Implemented:** Code exists and works

Update the status in your spec header:
```markdown
> **Status:** Approved
```

## Red Flags (Common Mistakes)

❌ **No API contract** → How will callers know what to send?
❌ **Vague requirements** → "Should be fast" vs "Response < 2 seconds"
❌ **No acceptance criteria** → How do you know when you're done?
❌ **Skipping documentation** → Context matters! Read docs first
❌ **Spec after code** → Defeats the purpose of spec-driven development
❌ **Missing test plan** → **CRITICAL ERROR** - Feature cannot be validated
❌ **Vague tests** → "Test that it works" vs "Test function(input) returns expected_output"
❌ **No E2E tests** → Unit tests pass but user flow is broken
❌ **No error tests** → Only testing happy path, no edge cases

✅ **Good spec:** Clear contract, testable criteria, concrete examples
✅ **Great spec:** Comprehensive test plan (unit + integration + E2E)
✅ **Excellent spec:** References existing patterns, includes test data/fixtures

## Example: Minimal CLI Tool Spec

```markdown
# Tool: Markdown to PDF Converter

> **Status:** Approved

## Overview
Convert markdown files to PDF using Pandoc.

## API Contract
```bash
npm run md-to-pdf -- --input file.md --output file.pdf
```

**Options:**
- `--input` (required): Markdown file path
- `--output` (optional): PDF output path (default: same name as input)

## Component Structure
- Create: `tools/md-to-pdf.ts`
- Modify: `package.json` (add script)

## Acceptance Criteria
- [ ] Tool converts MD to PDF
- [ ] Handles missing input file gracefully
- [ ] Outputs to specified path or default
- [ ] Returns non-zero exit code on error

## Dependencies
- `pandoc`: PDF generation (external dependency)
```

That's it! A complete, implementable spec in ~20 lines.

## Pro Tips

1. **Start with examples** - Show sample input/output before explaining
2. **Link to related code** - Reference existing patterns to follow
3. **Think in contracts** - What goes in? What comes out? What can fail?
4. **Update during implementation** - Specs are living documents
5. **Use the template** - It's there to help you remember important sections

## Questions?

- See full guide: `specs/README.md`
- See example: `specs/features/example-chat-feature.md`
- See template: `specs/TEMPLATE.md`
- See workflows: `.cursor/rules/workflows.mdc`
