# Exercise 2: RAG-Backed Memory Skill

**Duration:** 10 min | **Type:** Build

---

## Goal

Create a skill that uses RAG (Retrieval-Augmented Generation) to give your agent persistent, searchable memory.

---

## What is a RAG-Backed Memory Skill?

A memory skill that:
1. **Embeds** knowledge into a vector database on trigger
2. **Stores** it persistently (survives restarts)
3. **Retrieves** semantically similar content on recall

This turns your agent from stateless to learning.

---

## The Prompt

```
Create a RAG-backed memory skill: [your description]
```

The AI generates the complete skill with embed/store/retrieve logic.

---

## Skill Ideas

| Skill | What it does |
|-------|-------------|
| **remember-learnings** | Embed lessons learned → retrieve similar past insights when facing new problems |
| **project-context** | Index project docs (stack, conventions) → semantic search for grounded answers |
| **decision-log** | Embed architectural decisions + rationale → query "why did we choose X?" |
| **error-patterns** | Embed bug reports + fixes → auto-retrieve matching solutions for new errors |
| **meeting-notes** | Embed meeting summaries → recall "what did we decide about X?" |
| **code-patterns** | Index code snippets + explanations → find similar patterns when coding |

---

## Example Prompt

```
Create a RAG-backed memory skill called "remember-learnings":

When I say "remember: [lesson]", embed the lesson into ChromaDB.
When I ask about a topic, automatically retrieve similar past learnings 
and include them in your response.

Use Gemini embeddings (gemini-embedding-001) and ChromaDB.
```

---

## Prerequisites

Make sure ChromaDB is running:

```bash
# Start ChromaDB (in a separate terminal)
chroma run --path ./chroma-data
```

---

## What the AI Should Generate

1. **Embedding function** — Convert text to vectors using Gemini
2. **Store function** — Save embeddings + metadata to ChromaDB
3. **Retrieve function** — Find semantically similar memories
4. **Trigger logic** — When to embed vs when to retrieve

---

## Checkpoint

After 10 minutes:

- [ ] Skill code exists
- [ ] You can store a memory (embed + save)
- [ ] You can retrieve relevant memories (semantic search)
- [ ] You understand the embed → store → retrieve flow

---

## Keep Your Skill

Save this skill — you'll integrate it into your agent in Exercise 3.

---

## Testing Your Skill

Quick test (if time allows):

```python
# Store a learning
store_memory("Always validate user input before processing")

# Retrieve relevant memories
results = retrieve_memory("How should I handle user data?")
print(results)  # Should return the validation learning
```
