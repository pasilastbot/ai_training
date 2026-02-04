# Technical Learnings

This document captures technical learnings, best practices, and solutions to problems encountered while working on this project.

---

## Process & Methodology

### Honest Implementation Reviews

**Learning:** Always conduct a thorough, honest review comparing implementation against specification before declaring "complete."

**Workflow:** Use the `<review>` workflow documented in `.cursor/rules/workflows.mdc`

**Key Principles:**

1. **Be Brutally Honest**
   - Don't claim 100% if it's actually 78%
   - Identify real gaps, even if embarrassing
   - Example: "Frontend tests: 0/5 written" not "mostly complete"

2. **Be Specific with Evidence**
   - Cite line numbers: "Spec line 730-756 requires vitest tests"
   - Reference files: "Missing `persona-select.css` (spec line 503)"
   - Show proof: "Test coverage 77% (not 100%)"

3. **Check Everything the Spec Requires**
   - Files to create/modify (not just code)
   - Test coverage goals (not just "tests pass")
   - Non-functional requirements (performance, responsive)
   - Asset generation (sprites, images)

4. **Common Gaps to Watch For**
   ```markdown
   ❌ Frontend tests specified but not written
   ❌ Asset generation skipped (sprites, images)
   ❌ Separate files specified but embedded instead
   ❌ Only 2/6 variants tested, not all
   ❌ Responsive design specified but not tested
   ❌ Performance targets specified but not measured
   ```

5. **Create a Gap Analysis Table**
   ```markdown
   | Category | Spec | Delivered | Score |
   |----------|------|-----------|-------|
   | Backend  | Full | ✅ 95%    | ✅    |
   | Frontend | Full | ⚠️ 70%    | ⚠️    |
   | Tests    | 100% | ⚠️ 50%    | ⚠️    |
   ```

**Example: Multi-Persona Review (2026-02-04)**

Initial claim: "✅ ALL TESTS PASSED, 100% complete"

Honest review revealed:
- Backend: 95% (excellent)
- Frontend: 70% (works but undertested)
- **Overall: 78% spec-compliant**

Gaps found:
1. 0/5 frontend unit tests (spec required vitest)
2. 0/5 sprite generation (spec provided commands)
3. 2/6 personas personality-tested (spec required all)
4. Missing separate CSS file (spec line 503)
5. No responsive testing (spec required 600px+)

**Template for Review Report:**
```markdown
## Executive Summary
- Overall Compliance: X%
- Production Ready: Yes/No/Partial
- Critical Gaps: [list]

## Spec Compliance Audit
- FR-1: ✅ MET (evidence)
- FR-2: ❌ UNMET (gap details)

## Security Audit
- Input validation
- Dependencies
- CORS/CSP

## Architecture Audit
- Code organization
- Design patterns
- Data flow

## Recommendations
1. Must-fix (critical)
2. Should-fix (gaps)
3. Nice-to-have (enhancements)
```

**Why This Matters:**

Before honest review:
> "Feature complete! 34 tests passing! Production ready!"

After honest review:
> "Backend excellent (95%), Frontend functional but undertested (70%). 78% spec-compliant. Works for MVP, needs 5-6 hours for 100% compliance."

**When to Review:**
- Before declaring "feature complete"
- Before marking as "production ready"
- When user asks "review against spec"
- After major implementation milestones

**Review Checklist:**
- [ ] Read entire spec file
- [ ] List all required files, check if created
- [ ] List all test requirements, count actual tests
- [ ] Run test coverage report, compare to targets
- [ ] Test all variants/personas/cases (not just 2/6)
- [ ] Verify performance targets measured (not assumed)
- [ ] Check responsive design if specified
- [ ] Run security audit (npm audit, dependency check)
- [ ] Generate honest review report in `/temp/`
- [ ] Present findings with specific gaps

**Result:** Builds trust, prevents false confidence, creates clear action items for reaching 100%.

---

## AI/LLM Integration

### Gemini SDK Versions

**Learning:** Use `@google/genai` (newer) instead of `@google/generative-ai` (legacy).

```typescript
// ✅ Correct - newer SDK
import { GoogleGenAI } from '@google/genai';
const ai = new GoogleGenAI({ apiKey: API_KEY });

// ❌ Avoid - legacy SDK
import { GoogleGenerativeAI } from '@google/generative-ai';
```

**Reason:** The newer SDK (`@google/genai`) has better TypeScript support, improved streaming, and is actively maintained.

---

### API Key Loading Pattern

**Learning:** Always check multiple environment variable names for API keys.

```python
# Python pattern
API_KEY = os.getenv('GOOGLE_AI_STUDIO_KEY') or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
```

```typescript
// TypeScript pattern
const API_KEY = process.env.GOOGLE_AI_STUDIO_KEY || process.env.GEMINI_API_KEY;
```

**Reason:** Different users may have set up their API keys with different variable names. Supporting multiple names improves compatibility.

---

### Structured Output with Gemini

**Learning:** Use `responseMimeType: 'application/json'` and `responseSchema` for reliable JSON output.

```python
response = client.models.generate_content(
    model='gemini-2.0-flash-001',
    contents=[prompt],
    config=types.GenerateContentConfig(
        temperature=0,
        response_mime_type='application/json',
        response_schema=schema
    )
)
```

**Reason:** Without the schema constraint, LLMs may include markdown code blocks or extra text that breaks JSON parsing.

---

## Tool/Function Calling

### Function Declaration Best Practices

**Learning:** Be explicit about parameter types and include clear descriptions.

```python
{
    "name": "tool_name",
    "description": "Clear, action-oriented description",
    "parameters": {
        "type": "object",
        "properties": {
            "param": {
                "type": "string",
                "description": "What this parameter controls",
                "enum": ["option1", "option2"]  # When applicable
            }
        },
        "required": ["param"]  # List required params
    }
}
```

**Reason:** Better descriptions lead to more accurate tool selection and parameter filling by the LLM.

---

### CLI Tool Execution Pattern

**Learning:** Use subprocess with captured output and proper error handling.

```python
def _run_cmd(cmd: List[str]) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        return 1, "", f"Exception: {e}"
```

**Reason:** Capturing both stdout and stderr allows for proper debugging when tools fail.

---

## RAG Pipeline

### Chunk Size Considerations

**Learning:** Let Gemini handle chunking using structured extraction rather than fixed character limits.

The `query_chunks` function uses a detailed prompt to extract chapters/sections naturally:

```python
"chapters": [{
    "topic": "topic of the chapter",
    "content": "chapter contents 100-500 words"
}]
```

**Reason:** LLM-based chunking respects semantic boundaries (paragraphs, sections) better than arbitrary character splits.

---

### ChromaDB Client Mode

**Learning:** Use HTTP client mode for persistence and multi-process access.

```python
# Client-server mode (recommended)
client = chromadb.HttpClient(host='localhost', port=8000)

# Ephemeral mode (data lost on restart)
client = chromadb.Client()
```

Start server with: `chroma run --path ./chroma`

**Reason:** HTTP client mode allows multiple scripts to access the same data and persists data across restarts.

---

### Embedding Model Selection

| Model | Provider | Dimensions | Use Case |
|-------|----------|------------|----------|
| `text-embedding-004` | Gemini | 768 | Cloud-based, high quality |
| `mxbai-embed-large` | Ollama | 1024 | Local, no API needed |

**Learning:** Match embedding models - documents and queries must use the same model.

---

## Python Patterns

### Dotenv Loading

**Learning:** Load `.env.local` explicitly for local development.

```python
from dotenv import load_dotenv
load_dotenv('.env.local')  # Explicit path
```

**Reason:** Default `load_dotenv()` only loads `.env`, missing local overrides in `.env.local`.

---

### Flask CORS Setup

**Learning:** Enable CORS for local development APIs.

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow all origins for development
```

**Reason:** Browser-based frontends need CORS headers to call local APIs.

---

## TypeScript Patterns

### CLI Argument Parsing with Commander

**Learning:** Use `--` to separate npm script arguments from tool arguments.

```bash
npm run tool -- --option value
```

**Reason:** Without `--`, npm consumes the arguments instead of passing them to the script.

---

### Environment Variables in TypeScript

**Learning:** Load dotenv before accessing process.env.

```typescript
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });  // Must be at top

const API_KEY = process.env.GOOGLE_AI_STUDIO_KEY;  // Now available
```

---

## Error Handling

### Graceful JSON Parsing

**Learning:** Always wrap JSON.parse in try-catch with fallback.

```python
try:
    parsed = json.loads(response.text)
except json.JSONDecodeError:
    # Create a valid fallback structure
    parsed = {"error": "Failed to parse", "raw": response.text}
```

**Reason:** LLMs occasionally produce invalid JSON despite schema constraints.

---

### API Error Responses

**Learning:** Return helpful error messages in the API's "voice".

```python
# Dr. Sigmund example - errors stay in character
return jsonify({
    "error": str(e),
    "response": "*SYSTEM ERROR* My therapeutic algorithms have encountered a Y2K bug!",
    "mood": "shocked"
}), 500
```

---

## Performance

### Async vs Sync Patterns

**Learning:** Use async for I/O-bound operations (API calls), sync for CPU-bound.

```python
# Async for API calls
async def run_chat_loop_async(client, model, ...):
    response = await client.aio.models.generate_content(...)

# Sync wrapper for CLI
def main():
    asyncio.run(run_chat_loop_async(...))
```

---

## Common Pitfalls

### 1. Missing API Keys
**Symptom:** "API key not found" errors
**Solution:** Check `.env.local` exists and is properly formatted

### 2. ChromaDB Connection Refused
**Symptom:** Connection errors to localhost:8000
**Solution:** Start ChromaDB server: `chroma run --path ./chroma`

### 3. Ollama Model Not Found
**Symptom:** Model loading errors
**Solution:** Pull required models: `ollama pull mxbai-embed-large`

### 4. npm Script Arguments Not Passed
**Symptom:** Tool runs with default options only
**Solution:** Use `--` separator: `npm run tool -- --flag value`

### 5. JSON Parsing Failures
**Symptom:** JSONDecodeError on LLM responses
**Solution:** Use response schemas and add fallback parsing

---

## Resources

- [Google GenAI SDK Documentation](https://ai.google.dev/docs)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Commander.js Documentation](https://github.com/tj/commander.js)
