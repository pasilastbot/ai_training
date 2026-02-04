# Data Model

## Overview

This system primarily deals with unstructured data (text, documents, web content) and AI-generated outputs. The main data structures are related to:

1. **RAG Pipeline** - Content chunks stored in ChromaDB
2. **Chat/Conversation** - Message history for agents
3. **Structured Extraction** - JSON schemas for content processing

---

## RAG Content Model

### Document Chunk Entity

When content is indexed via `data-indexing.py` or `index_site.py`, it's processed into structured chunks.

```json
{
  "topic": "Summary line of the chunk in English",
  "summary": "Short summary of the whole document",
  "language": "Original language of the text",
  "page_category": "article | collection | category | product | news | service | faq | home | other",
  "product": {
    "name": "Product title",
    "price": "Product price",
    "currency": "Currency code",
    "description": "Product description"
  },
  "service": {
    "name": "Service name",
    "price": "Service price",
    "description": "Service description"
  },
  "chapters": [
    {
      "topic": "Chapter topic in English",
      "question": "Question this chapter answers",
      "keywords": ["keyword1", "keyword2"],
      "image": {
        "image_url": "Absolute URL to image",
        "image_alt": "Alt text",
        "image_title": "Image title"
      },
      "table": {
        "table_name": "Table name",
        "headers": ["header1", "header2"],
        "rows": [["row1col1", "row1col2"]]
      },
      "content": "Full chapter content (100-500 words)"
    }
  ]
}
```

### ChromaDB Collection Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique identifier for the chunk |
| `embedding` | float[] | Vector embedding from Gemini/Ollama |
| `document` | string (JSON) | The serialized chunk object |
| `metadata` | object | Optional metadata (source URL, timestamp, etc.) |

**Collections:**
- `gemini-docs` - Default collection for Gemini-indexed content
- `docs` - Legacy collection for Ollama-indexed content
- Custom collections via `--collection` flag

---

## Chat/Conversation Model

### Message Structure (Gemini Format)

```python
{
    "role": "user" | "model" | "tool",
    "parts": [
        {"text": "Message content"},
        # or for tool responses:
        {"function_response": {"name": "tool_name", "response": {...}}}
    ]
}
```

### Message Structure (Ollama Format)

```python
{
    "role": "user" | "assistant" | "system" | "tool",
    "content": "Message content",
    # For tool calls:
    "tool_calls": [
        {
            "function": {
                "name": "tool_name",
                "arguments": {...}
            }
        }
    ]
}
```

---

## Tool Function Declaration Schema

### Gemini Function Declaration

```python
{
    "name": "function_name",
    "description": "What the function does",
    "parameters": {
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Parameter description"
            },
            "param2": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100
            }
        },
        "required": ["param1"]
    }
}
```

### Available Tool Functions

| Function | Parameters | Returns |
|----------|------------|---------|
| `html_to_md` | url, output?, selector? | Markdown content |
| `image_optimizer` | input, output, remove_bg?, resize?, format?, quality? | Optimized image path |
| `download_file` | url, output?, folder?, filename? | Downloaded file path |
| `openai_image_generate` | prompt, model?, size?, quality? | Generated image path |
| `openai_image_edit` | input_image, edit_prompt, model? | Edited image path |
| `gemini_image_generate` | prompt, model?, aspect_ratio? | Generated image path |
| `gemini_image_edit` | input_image, edit_prompt | Edited image path |
| `generate_video` | prompt, model?, duration?, image? | Generated video path |
| `nano_banana_generate` | prompt, output?, folder? | Generated image path |
| `nano_banana_edit` | prompt, input_image | Edited image path |
| `google_search` | query, max_results?, format? | Search results |
| `datetime` | format?, timezone?, utc?, timestamp? | Formatted date/time |
| `data_indexing` | url?, file?, collection? | Indexing status |
| `semantic_search` | query, collection?, n_results? | Search results |
| `qwen3_tts` | text, mode?, voice_prompt? | Audio file path |
| `play_audio` | file, volume?, background? | Playback status |

---

## Structured Output Schemas

### Recipe Schema (for `--json recipes`)

```typescript
{
  type: "ARRAY",
  items: {
    type: "OBJECT",
    properties: {
      recipeName: { type: "STRING" },
      ingredients: { type: "ARRAY", items: { type: "STRING" } },
      preparationTime: { type: "INTEGER" },
      difficulty: { type: "STRING" },
      instructions: { type: "ARRAY", items: { type: "STRING" } }
    },
    required: ["recipeName", "ingredients", "instructions"]
  }
}
```

### Task Schema (for `--json tasks`)

```typescript
{
  type: "ARRAY",
  items: {
    type: "OBJECT",
    properties: {
      taskName: { type: "STRING" },
      priority: { type: "STRING" },
      dueDate: { type: "STRING" },
      steps: { type: "ARRAY", items: { type: "STRING" } }
    },
    required: ["taskName", "priority"]
  }
}
```

### Product Schema (for `--json products`)

```typescript
{
  type: "ARRAY",
  items: {
    type: "OBJECT",
    properties: {
      productName: { type: "STRING" },
      price: { type: "NUMBER" },
      category: { type: "STRING" },
      features: { type: "ARRAY", items: { type: "STRING" } },
      rating: { type: "NUMBER" }
    },
    required: ["productName", "price", "category"]
  }
}
```

---

## Plan Mode Schema

When using `--plan` mode, the agent generates a state machine plan:

```json
{
  "name": "Plan name",
  "description": "Plan description",
  "start": "step_id",
  "steps": [
    {
      "id": "unique_step_id",
      "title": "Step title",
      "type": "ask_user | call_tool | decide | action | compute",
      "instructions": "What to do in this step",
      "tool": {
        "name": "tool_name",
        "args": {}
      },
      "transitions": [
        {
          "condition": "When to transition",
          "next": "next_step_id"
        }
      ]
    }
  ]
}
```

---

## API Response Models

### Dr. Sigmund 2000 Chat Response

```json
{
  "response": "The psychiatrist's response text",
  "mood": "thinking | amused | concerned | shocked | neutral",
  "ascii_art": "ASCII art representation of the mood"
}
```

### Tool Execution Result

```json
{
  "ok": true | false,
  "stdout": "Command standard output",
  "stderr": "Command standard error",
  "cmd": ["command", "arguments"]
}
```

---

## Data Flow Diagrams

### RAG Indexing Flow

```
Web URL / Local File
        ↓
    HTTP Fetch / File Read
        ↓
    HTML to Markdown Conversion
        ↓
    Gemini Content Extraction
    (Structured JSON with chapters)
        ↓
    Generate Embeddings
    (Gemini text-embedding-004 / Ollama mxbai-embed-large)
        ↓
    Store in ChromaDB
    (Collection: gemini-docs)
```

### RAG Query Flow

```
User Query
    ↓
Generate Query Embedding
    ↓
ChromaDB Similarity Search
    ↓
Retrieve Top-K Chunks
    ↓
Build Context Prompt
    ↓
LLM Generation (Gemini/Ollama)
    ↓
Response to User
```

### Agent Tool Calling Flow

```
User Message
    ↓
Agent (Gemini/Ollama)
    ↓
Function Call Decision
    ↓
Execute CLI Tool (npm run ...)
    ↓
Capture Output
    ↓
Return to Agent
    ↓
Generate Final Response
```
