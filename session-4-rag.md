# Session 4: RAG & AI Agents
**Duration:** 90 min | **Level:** Advanced

**Prerequisites:** Session 1 (Greenfield) & Session 2 (Brownfield). Python basics helpful.

**Goal:** Build retrieval-augmented generation (RAG) pipelines and tool-using AI agents

**Theme:** You've built tools and workflows (Sessions 1-3). Now we go deeper: index real content into a vector database, query it with AI, and build agents that reason and use tools. From static prompts to grounded, knowledge-aware agents.

**Materials:** Python scripts in `session-4-rag/` — indexing, querying, agents, ReAct pattern, and guardrails.

---

## PART 1: RAG FOUNDATIONS

### 1. What is RAG? (5 min)
**Retrieval-Augmented Generation — why it matters**

LLMs have knowledge cutoffs and hallucinate. RAG solves this by:

```
User Query → Retrieve relevant docs → Augment prompt with context → Generate grounded answer
```

| Approach | Pros | Cons |
|----------|------|------|
| **Plain LLM** | Simple, fast | Hallucination, outdated |
| **Fine-tuning** | Domain expert | Expensive, static |
| **RAG** | Current, grounded, traceable | Requires indexing pipeline |

**When to use RAG:** Your data changes, you need citations, you need domain-specific accuracy.

---

### 2. Vector Databases & Embeddings (5 min)
**ChromaDB, embeddings, similarity search**

The core pipeline:

```
Documents → Chunk → Embed (Gemini/Ollama) → Store in ChromaDB
                                                    ↓
Query → Embed → Similarity Search → Top-K Results → LLM
```

| Component | Our Stack | Alternatives |
|-----------|-----------|-------------|
| **Vector DB** | ChromaDB | Pinecone, Weaviate, Qdrant |
| **Embeddings** | Gemini / Ollama | OpenAI, Cohere |
| **LLM** | Gemini / Ollama | GPT-4, Claude |

---

### 3. Content Indexing (5 min)
**Scrape → Parse → Chunk → Embed → Store**

Key decisions in indexing:
- **Chunk size:** Too small = no context, too large = noise
- **Overlap:** Adjacent chunks share boundary text for continuity
- **Metadata:** Source URL, timestamps, section headers for filtering

**Scripts:**
- `index_site.py` — Index a website with Gemini embeddings
- `index_site_gemini.py` — Gemini-specific indexing
- `index_site_ollama.py` — Local indexing with Ollama
- `parse_html.py` — HTML parsing utilities

---

### REHEARSAL: Index a Website (10 min)
**Set up ChromaDB, index real content**

```bash
cd session-4-rag/
pip install -r requirements.txt

# Start ChromaDB
chroma run --path ./chroma-data

# Index a website
python index_site.py --url https://example.com --collection my-docs
```

**Try it:** Index a documentation site you use daily. Experiment with different chunk sizes.

---

### BUILD: Query Your Index (10 min)
**Ask questions, see RAG in action**

Using the RAG query scripts:

```bash
# Basic RAG query
python rag_query.py --query "How does authentication work?" --collection my-docs

# With Ollama (local, no API key)
python rag_query_ollama.py --query "How does authentication work?" --collection my-docs
```

**Scripts:**
- `rag_query.py` — RAG query with Gemini
- `rag_query_final.py` — Enhanced RAG query with better context handling
- `rag_query_ollama.py` — Local RAG with Ollama

Compare answers with and without RAG context. Notice how grounded answers differ from plain LLM responses.

---

## PART 2: AI AGENTS

### 4. From RAG to Agents (5 min)
**Adding reasoning and tool use**

RAG retrieves knowledge. Agents act on it:

```
RAG:    Query → Retrieve → Answer
Agent:  Query → Reason → Use Tools → Observe → Reason → Answer
```

| Capability | RAG | Agent |
|-----------|-----|-------|
| Knowledge retrieval | Yes | Yes |
| Multi-step reasoning | No | Yes |
| Tool use | No | Yes |
| Action taking | No | Yes |

---

### 5. The ReAct Pattern (5 min)
**Reason + Act — the agent loop**

ReAct alternates between thinking and doing:

```
Thought: I need to find the weather in Helsinki
Action:  get_weather(location="Helsinki")
Observation: Temperature: 5°C, cloudy
Thought: I have the answer now
Answer:  The weather in Helsinki is 5°C and cloudy
```

This is implemented in:
- `react_ollama.py` — Basic ReAct loop
- `react_ollama_real.py` — ReAct with real tools (weather, search, geocoding)

---

### BUILD: Run a ReAct Agent (10 min)
**Agent with real tools**

```bash
# ReAct agent with weather + search tools
python react_ollama_real.py --query "What's the weather like in Helsinki?"
```

**Available tools in the agent:**
- Weather lookup (real API)
- Google Search (via Gemini grounding)
- Geocoding (location → coordinates)

Try multi-step queries: "Compare the weather in Helsinki and Tokyo" — watch the agent reason through multiple tool calls.

---

### 6. Agent Architectures (5 min)
**Simple agents vs multi-provider agents**

| Architecture | Use Case | Script |
|-------------|----------|--------|
| **Single-provider** | One LLM handles everything | `gemini_agent.py` |
| **Local-first** | Privacy-sensitive, offline | `ollama_agent.py` |
| **Hybrid** | Best of both worlds | `react_ollama_real.py` |

**Design decisions:**
- Gemini for grounded search + embeddings
- Ollama for local reasoning + privacy
- Tools as external capabilities

---

### BUILD: Build Your Agent (10 min)
**Customize tools and behavior**

Using `gemini_agent.py` or `ollama_agent.py`:

1. Study the existing agent implementation
2. Add a new tool (file reader, calculator, API call)
3. Test the agent with queries that require your new tool

---

## PART 3: GUARDRAILS & PRODUCTION

### 7. Output Guardrails (5 min)
**Validating, filtering, and constraining agent output**

Agents can produce harmful, inaccurate, or off-topic output. Guardrails prevent this:

| Guardrail | Purpose | Example |
|-----------|---------|---------|
| **Topic filter** | Stay on-topic | Block competitor mentions |
| **Fact checking** | Verify against sources | Check RAG citations |
| **Format validation** | Structured output | JSON schema validation |
| **Safety filter** | Block harmful content | PII, toxicity |

**Scripts:**
- `guardrails_test.py` — Basic guardrail testing
- `guardrails_test_final.py` — Enhanced guardrails with Gemini

---

### BUILD: Add Guardrails (10 min)
**Protect your RAG pipeline**

```bash
# Test guardrails
python guardrails_test_final.py --query "Tell me about competitors"
```

1. Study the existing guardrail implementations
2. Add a custom guardrail (e.g., ensure responses cite sources)
3. Test with adversarial queries

---

### 8. RAG in Production (5 min)
**Indexing pipelines, monitoring, evaluation**

Moving from demo to production:

| Concern | Solution |
|---------|----------|
| **Stale data** | Scheduled re-indexing |
| **Quality** | Retrieval evaluation metrics (precision, recall) |
| **Cost** | Embedding caching, batch processing |
| **Scale** | Managed vector DB (Pinecone, Weaviate Cloud) |
| **Monitoring** | Track retrieval quality, latency, user satisfaction |

---

### Session 4 Wrap-Up (5 min)
**What You Built**

**Recap of what you accomplished:**
1. **INDEXING:** Scraped and indexed real content into ChromaDB
2. **RAG:** Queried your index with grounded, citation-backed answers
3. **AGENTS:** Built tool-using agents with the ReAct pattern
4. **GUARDRAILS:** Added output validation and safety filters

**The progression:** Data → Embeddings → Retrieval → Agents → Guardrails

**Key takeaway:** RAG gives your AI grounded knowledge. Agents give it the ability to reason and act. Guardrails keep it safe. Together, they form the foundation of production AI applications.

---

## Files Reference

| File | Purpose | Used in |
|------|---------|---------|
| `requirements.txt` | Python dependencies | Setup |
| `parse_html.py` | HTML parsing utilities | Part 1 |
| `index_site.py` | Index website with Gemini | REHEARSAL |
| `index_site_gemini.py` | Gemini-specific indexing | REHEARSAL |
| `index_site_ollama.py` | Local indexing with Ollama | REHEARSAL |
| `rag_query.py` | RAG query with Gemini | BUILD: Query |
| `rag_query_final.py` | Enhanced RAG query | BUILD: Query |
| `rag_query_ollama.py` | Local RAG query with Ollama | BUILD: Query |
| `react_ollama.py` | Basic ReAct agent loop | Part 2 |
| `react_ollama_real.py` | ReAct with real tools | BUILD: ReAct Agent |
| `gemini_agent.py` | Gemini-based agent | BUILD: Agent |
| `ollama_agent.py` | Ollama-based local agent | BUILD: Agent |
| `guardrails_test.py` | Basic guardrail testing | Part 3 |
| `guardrails_test_final.py` | Enhanced guardrails | BUILD: Guardrails |
| `weather_test.py` | Weather API test utility | Reference |

---

## Next Steps After Training

### Immediate (This Week)
1. Index your project's documentation into ChromaDB
2. Build a RAG query tool for your codebase
3. Experiment with chunk sizes and overlap

### Short-term (This Month)
1. Build a ReAct agent with domain-specific tools
2. Add guardrails for your use case
3. Evaluate retrieval quality with test queries

### Long-term (This Quarter)
1. Set up scheduled indexing pipelines
2. Move to a managed vector database
3. Build multi-agent systems combining RAG with agentic workflows
4. Integrate with the tools and skills from Session 3
