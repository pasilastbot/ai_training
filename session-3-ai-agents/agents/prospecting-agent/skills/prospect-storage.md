---
name: prospect-storage
description: Store and retrieve B2B prospects from the database
tools: [store_prospect.py, retrieve_prospects.py]
---

## Purpose

Manage prospect data persistence. Store newly found or enriched prospects and retrieve them for review, export, or further processing.

## When to Use

### Store Prospects

Use `store_prospect.py` when:
- Search subagent returns new prospects
- Enrich subagent completes enrichment
- User manually adds a prospect
- Importing prospects from external source

### Retrieve Prospects

Use `retrieve_prospects.py` when:
- User asks to see prospects
- Filtering by criteria (status, industry, score)
- Exporting prospects
- Checking for duplicates before storing
- Getting statistics

## Tools

### store_prospect.py

```bash
# Store single prospect from JSON file
python tools/store_prospect.py --file prospect.json

# Store from stdin (piped from search or enrich)
python subagents/prospect_search.py ... | jq '.prospects' | python tools/store_prospect.py --stdin

# Store with direct input
python tools/store_prospect.py --company "Acme Corp" --website "https://acme.com" --industry "SaaS" --score 85
```

**Input:** JSON prospect object or array
**Output:** `{"status": "success", "id": "prospect_xxx", "action": "stored"}`

### retrieve_prospects.py

```bash
# Get all prospects
python tools/retrieve_prospects.py --all --pretty

# Get by ID
python tools/retrieve_prospects.py --id prospect_123

# Filter by status and industry
python tools/retrieve_prospects.py --status enriched --industry SaaS --min-score 70

# Search
python tools/retrieve_prospects.py --search "AI company"

# Get statistics
python tools/retrieve_prospects.py --stats
```

**Output:** `{"count": N, "prospects": [...]}`

## Workflow Integration

### After Search

```python
# 1. Run search
search_result = run_subagent("prospect_search", icp=current_icp)

# 2. Store results
for prospect in search_result["prospects"]:
    store_result = run_tool("store_prospect", prospect=prospect)
    print(f"Stored: {store_result['id']}")
```

### After Enrichment

```python
# 1. Get prospects needing enrichment
prospects = run_tool("retrieve_prospects", status="new", limit=10)

# 2. Enrich each
for p in prospects["prospects"]:
    enriched = run_subagent("prospect_enrich", prospect=p)
    
    # 3. Update stored prospect
    run_tool("store_prospect", prospect=enriched)
```

## Data Model

Stored prospects include:
- **id**: Unique identifier
- **company_name**: Company name
- **website**: Company URL
- **industry/sub_industry**: Classification
- **employee_count**: Size estimate
- **revenue_estimate_usd**: Revenue estimate
- **funding_stage**: Seed, Series A, B, etc.
- **headquarters**: Location object
- **technologies**: Tech stack array
- **contacts**: Key people array
- **signals**: Buying signals object
- **score**: ICP fit score (0-100)
- **status**: new, researching, enriched, qualified, contacted, archived
- **created_at/updated_at/enriched_at**: Timestamps

## Best Practices

1. **Check before storing**: Search existing prospects to avoid duplicates
2. **Update vs insert**: Tool uses upsert - same ID updates existing record
3. **Use status**: Track prospect lifecycle with status field
4. **Score consistently**: Use 0-100 scale for ICP fit scoring
5. **Preserve source**: Always include how/where prospect was found
