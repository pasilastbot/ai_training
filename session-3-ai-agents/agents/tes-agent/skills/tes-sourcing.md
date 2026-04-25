---
name: tes-sourcing
description: Find, download, and index TES documents
tools: [tes_sourcing.py, download_pdf.py, store_tes.py]
---

## Purpose

Index new TES (Työehtosopimus) documents by searching the web, downloading PDFs, and extracting structured data using Gemini.

## When to Use

- User asks about a TES that is not in the database
- User explicitly requests to index a new TES
- User provides a URL to a TES PDF

## Tools Required

1. **tes_sourcing.py** - Main sourcing subagent
   - `--search "query"` - Search for TES by name
   - `--url "url"` - Download from specific URL
   - `--file "path"` - Process local PDF file

2. **download_pdf.py** - Download PDF helper
   - `--url "url"` - URL to download
   - `--name "name"` - Name for the file

3. **store_tes.py** - Store extracted data
   - `--json "file"` - JSON file with TES data
   - `--stdin` - Read JSON from stdin

## Process Flow

1. Search for TES PDF using Google Search
2. Download PDF to `memory/data/pdfs/`
3. Send PDF to Gemini for extraction
4. Evolve schema if new fields found
5. Store in SQLite database and JSON file

## Example

```bash
# Search and index
python subagents/tes_sourcing.py --search "Teknologiateollisuuden TES 2024"

# From URL
python subagents/tes_sourcing.py --url "https://finlex.fi/data/tes/teknologia.pdf" --name "Teknologiateollisuuden TES"

# Store result
python subagents/tes_sourcing.py --search "PAM TES" | python tools/store_tes.py --stdin
```

## Schema Evolution

When extracting a TES, the agent may discover new fields not in the current schema.
These are placed in `other_terms` and tracked in `_suggested_fields`.
If a field appears in multiple TES documents, it can be promoted to the main schema.
