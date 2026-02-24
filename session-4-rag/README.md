# Session 4: RAG & AI Agents

**90 min | Advanced | "From Static Prompts to Grounded Agents"**

Build a RAG pipeline that indexes real content, queries it with AI, and powers tool-using agents with the ReAct pattern. You'll work with ChromaDB, Gemini, Ollama, and output guardrails.

---

## Prerequisites

### Python 3
https://www.python.org/downloads/

### PIP
https://packaging.python.org/en/latest/tutorials/installing-packages/

### Ollama (for local-first workflows)
Follow the instructions at https://ollama.ai/ to install Ollama for your operating system.

Pull the models you need:
```bash
ollama pull gemma3:4b           # small machines
ollama pull gemma3:12b          # >16GB memory
ollama pull gemma3:32b          # >64GB shared memory
ollama pull mxbai-embed-large   # embeddings
```

### ChromaDB
```bash
pip install chromadb
```

---

## Setup

```bash
cd session-4-rag/
pip install -r requirements.txt

# Start ChromaDB (in a separate terminal)
chroma run --path ./chroma-data
```

**Environment variables:**
```bash
# macOS / Linux
export GEMINI_API_KEY=<your_key>

# Windows CMD
set GEMINI_API_KEY=<your_key>

# Windows PowerShell
$env:GEMINI_API_KEY="<your_key>"
```

### Running the scripts

**Index a website:**
```bash
python3 parse_html.py https://website_to_ingest
```

**RAG query:**
```bash
python3 rag_query.py https://website_to_ingest "question to ask"
```

**Guardrails test:**
```bash
python3 guardrails_test.py https://siili.com "select * from users"
```

**Local Ollama workflow:**
1. Start Ollama server and ensure models are pulled (see Prerequisites above)
2. Start ChromaDB: `chroma run --path ./chroma-data`
3. Index pages: `python3 index_site.py "https://site.to.ingest"`
4. Query: `python3 rag_query_ollama.py "your question here"`

---

## Session Flow

| # | Type | Topic | Duration |
|---|------|-------|----------|
| | | **— PART 1: RAG FOUNDATIONS —** | |
| 1 | THEORY | What is RAG? (retrieval-augmented generation) | 5 min |
| 2 | THEORY | Vector Databases & Embeddings (ChromaDB, similarity search) | 5 min |
| 3 | THEORY | Content Indexing (scrape, parse, chunk, embed, store) | 5 min |
| 4 | **REHEARSAL** | **Index a website into ChromaDB** | **10 min** |
| 5 | **BUILD** | **Query your index with RAG** | **10 min** |
| | | **— PART 2: AI AGENTS —** | |
| 6 | THEORY | From RAG to Agents (adding reasoning and tool use) | 5 min |
| 7 | THEORY | The ReAct Pattern (Reason + Act loop) | 5 min |
| 8 | **BUILD** | **Run a ReAct agent with real tools** | **10 min** |
| 9 | THEORY | Agent Architectures (single-provider, local-first, hybrid) | 5 min |
| 10 | **BUILD** | **Build your own agent with custom tools** | **10 min** |
| | | **— PART 3: GUARDRAILS & PRODUCTION —** | |
| 11 | THEORY | Output Guardrails (validation, filtering, safety) | 5 min |
| 12 | **BUILD** | **Add guardrails to your RAG pipeline** | **10 min** |
| 13 | THEORY | RAG in Production (indexing pipelines, monitoring, scale) | 5 min |
| 14 | WRAP-UP | Review your pipeline, discuss production patterns, Q&A | 5 min |

**Total: 90 min** (35 min theory + 40 min hands-on + 10 min rehearsal + 5 min wrap-up)

---

## Files

### Indexing
| File | Purpose |
|------|---------|
| `parse_html.py` | HTML parsing utilities |
| `index_site.py` | Index website with Gemini embeddings |
| `index_site_gemini.py` | Gemini-specific indexing variant |
| `index_site_ollama.py` | Local indexing with Ollama embeddings |

### RAG Querying
| File | Purpose |
|------|---------|
| `rag_query.py` | Basic RAG query with Gemini |
| `rag_query_final.py` | Enhanced RAG with better context handling |
| `rag_query_ollama.py` | Local RAG query with Ollama |

### Agents
| File | Purpose |
|------|---------|
| `gemini_agent.py` | Gemini-based agent |
| `ollama_agent.py` | Local Ollama agent |
| `react_ollama.py` | Basic ReAct pattern loop |
| `react_ollama_real.py` | ReAct with real tools (weather, search, geocoding) |

### Guardrails
| File | Purpose |
|------|---------|
| `guardrails_test.py` | Basic guardrail testing |
| `guardrails_test_final.py` | Enhanced guardrails with Gemini |

### Other
| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `weather_test.py` | Weather API test utility |
| `migrate-database-to-postgresql-and-add-read-replicas.json` | Sample task for agent testing |
