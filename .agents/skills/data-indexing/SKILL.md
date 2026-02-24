---
name: data-indexing
description: Use for indexing documents (web pages or local files) into ChromaDB for later semantic search. Uses Gemini for content processing and embedding generation. Requires a running ChromaDB instance. For querying indexed data, use semantic-search.
---

## Command
`npm run data-indexing -- [options]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| -u, --url | One of url/file | URL of webpage to index |
| -f, --file | One of url/file | Path to local file to index |
| -o, --output | No | Output file to save processed document JSON |
| -c, --collection | No | ChromaDB collection name (default: gemini-docs) |
| -m, --model | No | Gemini model for content processing (default: gemini-2.5-flash) |
| -e, --embedding-model | No | Gemini model for embeddings (default: gemini-embedding-001) |
| --chroma-host | No | ChromaDB host (default: localhost) |
| --chroma-port | No | ChromaDB port (default: 8000) |

## Requirements
- `GOOGLE_AI_STUDIO_KEY` or `GEMINI_API_KEY` in `.env.local`
- ChromaDB running (default: localhost:8000)
- Python 3 with: chromadb, google-genai, html2text, requests, python-dotenv

## Examples
```bash
# Index a webpage
npm run data-indexing -- --url https://example.com/docs --collection my-docs

# Index a local file
npm run data-indexing -- --file docs/report.pdf --collection reports

# Index with custom models
npm run data-indexing -- --url https://example.com --model gemini-2.5-flash --embedding-model gemini-embedding-001
```
