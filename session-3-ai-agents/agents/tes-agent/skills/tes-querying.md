---
name: tes-querying
description: Answer questions about TES terms and conditions
tools: [retrieve_tes.py, memory.py]
---

## Purpose

Answer user questions about specific TES terms, conditions, and requirements using the indexed database.

## When to Use

- User asks about specific TES terms
- User wants to know vacation/sick leave/notice period rules
- User asks in Finnish or English about TES content

## Tools Required

1. **retrieve_tes.py** - Query TES data
   - `--id "tes_id"` - Get full TES details
   - `--search "query"` - Search TES by keyword
   - `--list` - List all TES with filters

2. **memory.py** - Direct database access
   - `search <query>` - Full-text search
   - `get <id>` - Get TES by ID
   - `list` - List all TES
   - `stats` - Database statistics

## Query Patterns

### Finding TES
```bash
# Search by name
python tools/retrieve_tes.py --search "teknologia"

# List by industry
python tools/retrieve_tes.py --list --industry "technology"

# Valid TES only
python tools/retrieve_tes.py --list --valid-only
```

### Getting Details
```bash
# Full TES data
python tools/retrieve_tes.py --id "tes_teknologia_2024"

# Using memory CLI
python memory/memory.py get "tes_teknologia_2024"
```

## Language Detection

The agent automatically detects query language:
- Finnish queries: Respond in Finnish
- English queries: Respond in English

Finnish keywords trigger Finnish mode:
- mikä, mitä, missä, miten, paljonko
- työehtosopimus, palkka, loma, työ

## Response Format

Always include:
1. Clear answer to the question
2. Source TES name and validity
3. PDF page/section reference if available
4. Any relevant caveats or conditions

## Example Queries

- "What is the vacation policy in tech TES?"
- "Kuinka monta lomapäivää PAM:n TES:ssä?"
- "Compare notice periods in retail vs tech"
- "What bonuses apply to night work?"
