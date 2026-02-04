# Architecture

## Technology Stack

### Languages & Runtimes
| Layer | Technology | Version |
|-------|------------|---------|
| **TypeScript** | tsx runtime | ^4.19.4 |
| **Python** | Python 3 | 3.9+ |
| **Node.js** | Node.js | 18+ |

### AI/ML Libraries
| Provider | Package | Purpose |
|----------|---------|---------|
| **Google Gemini** | `@google/genai` (TS), `google-genai` (Python) | Primary AI provider |
| **OpenAI** | `openai` ^5.0.2 | Image generation, GPT-image-1 |
| **Ollama** | `ollama` (Python) | Local LLM support |
| **Replicate** | `replicate` ^1.0.1 | Video generation, TTS |

### Vector Database
| Component | Technology |
|-----------|------------|
| **Database** | ChromaDB ^3.0.14 |
| **Embeddings** | Gemini `text-embedding-004` / Ollama `mxbai-embed-large` |

### Web & API
| Purpose | Package |
|---------|---------|
| **Web Server** | Flask ^3.0.0 |
| **CORS** | flask-cors ^4.0.0 |
| **HTTP Client** | axios ^1.9.0, node-fetch ^3.3.2, requests |

### Image Processing
| Package | Purpose |
|---------|---------|
| **Sharp** | ^0.34.2 - Image manipulation, resizing, format conversion |
| **Pillow** | ^10.4.0 - Python image processing |

### CLI & Development
| Package | Purpose |
|---------|---------|
| **commander** | ^13.0.0 - CLI argument parsing |
| **yargs** | ^17.7.2 - Alternative CLI parsing |
| **dotenv** | ^16.6.1 - Environment variable management |
| **rich** | Python console formatting |

## Folder Structure

```
ai_training/
├── .cursor/                    # Cursor IDE configuration
│   ├── hooks/                  # Git hooks
│   └── rules/                  # AI agent rules (.mdc files)
│       ├── behavioral_rules.mdc
│       ├── command_line_tools.mdc
│       ├── documentation.mdc
│       ├── main_process.mdc
│       └── workflows.mdc
│
├── .github/                    # GitHub Actions workflows
│   └── workflows/
│       ├── claude-code-review.yml
│       └── claude.yml
│
├── docs/                       # Documentation (this folder)
│   ├── description.md
│   ├── architecture.md
│   ├── datamodel.md
│   ├── frontend.md
│   ├── backend.md
│   ├── todo.md
│   ├── ai_changelog.md
│   └── learnings.md
│
├── specs/                      # Specifications (Spec-Driven Development)
│   ├── README.md               # Spec-driven development guide
│   ├── TEMPLATE.md             # Specification template
│   ├── features/               # Feature specifications
│   ├── apis/                   # API specifications
│   └── components/             # Component specifications
│
├── public/                     # Static assets
│   └── psychiatrist/           # Dr. Sigmund 2000 demo app
│       └── index.html
│
├── tools/                      # CLI tools (TypeScript & Python)
│   ├── data-indexing.py        # RAG data ingestion
│   ├── semantic-search.py      # RAG query
│   ├── semantic-search-gemini.py
│   ├── gemini.ts               # Gemini API CLI
│   ├── gemini.py
│   ├── gemini-image-tool.js    # Image generation
│   ├── google-search.ts        # Grounded search
│   ├── nano-banana.ts          # Gemini image generation
│   ├── generate-video.ts       # Video generation
│   ├── qwen3-tts.ts            # Text-to-speech
│   ├── play-audio.ts           # Audio playback
│   ├── download-file.ts        # File downloader
│   ├── datetime.ts             # Date/time utility
│   ├── remove-background-advanced.ts
│   └── utils/
│       └── download.ts
│
├── # Python Agents (root level)
├── gemini_agent.py             # Main Gemini agent with tools
├── ollama_agent.py             # Local Ollama agent
│
├── # RAG Pipeline Scripts
├── index_site.py               # Index with Ollama embeddings
├── index_site_gemini.py        # Index with Gemini embeddings
├── index_site_ollama.py        # Ollama-specific indexing
├── rag_query.py                # Basic RAG query
├── rag_query_final.py          # Enhanced RAG query
├── rag_query_ollama.py         # Ollama RAG query
│
├── # Demo Application
├── psychiatrist_api.py         # Dr. Sigmund 2000 backend
│
├── # Legacy/Test Scripts
├── parse_html.py               # HTML parsing utility
├── guardrails_test.py          # Guardrails testing
├── guardrails_test_final.py
├── react_ollama.py             # ReAct pattern tests
├── react_ollama_real.py
├── weather_test.py
│
├── # Configuration Files
├── package.json                # npm scripts and dependencies
├── tsconfig.json               # TypeScript configuration
├── requirements.txt            # Python dependencies
├── .gitignore
├── .env.local                  # API keys (not in git)
├── .env.example                # API key template
│
├── # Documentation
├── README.md                   # Main readme
├── READMORE.md                 # Extended documentation
├── CLAUDE.md                   # Claude Code guidance
└── agents.md                   # Agent instructions reference
```

## Two-Stack Architecture

### TypeScript Stack (`tools/`)
- All CLI tools executed via `tsx` (TypeScript execution)
- Uses `@google/genai` SDK (newer version)
- CLI parsing with `commander` or `yargs`
- Invoked through npm scripts in `package.json`

### Python Stack (root)
- AI agents (`gemini_agent.py`, `ollama_agent.py`)
- RAG pipeline scripts (`index_site*.py`, `rag_query*.py`)
- Flask web applications (`psychiatrist_api.py`)
- Uses `google-genai` package

## Key Design Patterns

### 1. Spec-Driven Development
```
Documentation → Specification → Code → Tests
     ↑              ↓                      ↓
     └──────── Validate & Update ─────────┘
```

**Philosophy:** Write the contract before the code.

**Process:**
1. **Research:** Read documentation (`docs/*.md`) and search codebase
2. **Specify:** Create spec in `specs/features/[name].md` defining:
   - Requirements (functional & non-functional)
   - API contracts (input/output types)
   - Data model changes
   - Test scenarios
   - Acceptance criteria
3. **Review:** Get spec approved before coding
4. **Implement:** Code fulfills the specification contract
5. **Validate:** Tests verify implementation matches spec
6. **Update:** If implementation reveals changes, update spec first

**Benefits:**
- Clear requirements before coding
- Better design decisions (thinking through contracts)
- Fewer implementation surprises
- Specs serve as living documentation
- Easier collaboration and review

See `specs/README.md` for detailed workflow.

### 2. Environment Variable Management
```
.env.local → dotenv → Environment Variables
```
- Both stacks load from `.env.local` using `dotenv`
- API keys: `GOOGLE_AI_STUDIO_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, `REPLICATE_API_TOKEN`

### 3. CLI Tool Pattern (TypeScript)
```typescript
// Standard pattern for TypeScript tools
import { program } from 'commander';
import dotenv from 'dotenv';
dotenv.config({ path: '.env.local' });

program
  .option('-p, --prompt <text>', 'Description')
  .parse(process.argv);

const options = program.opts();
// ... tool implementation
```

### 4. Agent Tool Calling Pattern
```python
# Agents define function declarations
def build_cli_function_declarations():
    return [
        {
            "name": "tool_name",
            "description": "What the tool does",
            "parameters": { ... }
        }
    ]

# Execute tools by name
def execute_cli_function(name, args):
    cmd = ["npm", "run", name, "--", ...args]
    return subprocess.run(cmd, ...)
```

### 5. RAG Pipeline Pattern
```
URL/File → HTML to Markdown → Gemini Chunking → Embeddings → ChromaDB
                                     ↓
Query → Embed Query → Similarity Search → Context → LLM Response
```

## Testing

### Current Testing Status
- No formal test framework implemented
- Manual testing via CLI tools
- Test scripts in root directory (`guardrails_test.py`, `weather_test.py`)

### Recommended Testing Stack
| Layer | Recommended Tool |
|-------|------------------|
| TypeScript Unit Tests | vitest (already in devDependencies) |
| Python Unit Tests | pytest |
| E2E Tests | Playwright / Cypress |
| API Tests | supertest |

## Deployment Considerations

### Local Development
1. Run `npm install` for Node dependencies
2. Run `pip install -r requirements.txt` for Python
3. Configure `.env.local` with API keys
4. Start ChromaDB for RAG features: `chroma run --path ./chroma`

### Production
- Consider containerization (Docker)
- ChromaDB can run as a separate service
- Separate Python and Node.js services as needed
