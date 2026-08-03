---
name: energy-knowledge
description: Search Leanheat Building knowledge base for energy optimization facts
tools: [recall_knowledge, knowledge_search]
---

## Purpose

Search the RAG-backed Leanheat Building knowledge base for information about AI-powered heating optimization, energy savings, demand response, and district heating technology.

## When to Use

- User asks about Leanheat Building technology
- User wants to know about energy savings percentages
- User inquires about demand response or grid flexibility
- User asks about district heating optimization
- User wants to understand AI/IoT heating technology
- User needs statistics or case studies

## Tools Required

| Tool | Purpose |
|------|---------|
| `tools/recall_knowledge.py` | Direct CLI access to leanheat-memory |
| `subagents/knowledge_search.py` | Comprehensive search with Google fallback |

## Example

```bash
# Search knowledge base
python tools/recall_knowledge.py "How does Leanheat reduce energy costs?"

# Search with category filter
python tools/recall_knowledge.py "energy savings" --category statistic

# Use subagent with Google fallback
python subagents/knowledge_search.py "demand response benefits"
```

## Integration with Agent

The main `energy_advisor.py` agent automatically:
1. Searches the Leanheat knowledge base first
2. Falls back to Google Search if KB results are insufficient
3. Synthesizes answers from multiple sources using Gemini
