---
name: semantic-search
description: Use for vector-based semantic search over documents indexed in ChromaDB. Supports Gemini and Ollama embeddings, metadata filtering, and distance thresholds. Requires a running ChromaDB instance with indexed data. For indexing data first, use data-indexing.
---

## Command
`npm run semantic-search -- [options] [query]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| query (positional) | Yes (unless --list-collections) | Search query text |
| -c, --collection | No | ChromaDB collection name (default: gemini-docs) |
| -n, --n-results | No | Number of results to return (default: 5) |
| -e, --embedding-model | No | Embedding model (default: gemini-embedding-001) |
| --use-ollama | No | Use Ollama for embeddings instead of Gemini |
| -f, --format | No | Output format: text or json (default: text) |
| --chroma-host | No | ChromaDB host (default: localhost) |
| --chroma-port | No | ChromaDB port (default: 8000) |
| --list-collections | No | List available collections |
| --where | No | JSON metadata filter (e.g. '{"source_url": "https://..."}') |
| --min-distance | No | Minimum distance threshold |
| --max-distance | No | Maximum distance threshold |

## Requirements
- `GOOGLE_AI_STUDIO_KEY` or `GEMINI_API_KEY` in `.env.local` (unless using Ollama)
- ChromaDB running (default: localhost:8000)
- Python 3 with: chromadb, google-genai, ollama, python-dotenv

## Examples
```bash
# Basic search
npm run semantic-search -- "how to deploy"

# Search specific collection with more results
npm run semantic-search -- "authentication flow" -c my-docs -n 10

# JSON output with metadata filter
npm run semantic-search -- "error handling" -f json --where '{"source_url": "https://example.com"}'

# List available collections
npm run semantic-search -- --list-collections

# Use Ollama embeddings
npm run semantic-search -- "search query" --use-ollama -e nomic-embed-text
```
