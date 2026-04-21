---
name: delegation
description: When and how to delegate to subagents
tools: [prospect_search.py, prospect_enrich.py]
---

## Purpose

The main agent orchestrates work by delegating to specialized subagents. This skill describes when to use each subagent and how to coordinate their work.

## Available Subagents

### prospect_search.py

**Purpose:** Find new prospects matching ICP criteria

**Capabilities:**
- Google Search with grounding
- URL Context for website analysis
- Google Maps for location queries
- Returns structured prospect list

**When to Use:**
- User asks to "find companies" or "search for prospects"
- Starting a new prospecting campaign
- Expanding the prospect pool
- Searching specific criteria

### prospect_enrich.py

**Purpose:** Enrich a prospect with detailed information

**Capabilities:**
- Deep company research
- Website analysis
- Funding/revenue estimation
- Contact discovery
- Signal detection

**When to Use:**
- After initial search to enrich results
- User asks "tell me more about X"
- Before outreach to ensure data quality
- Scoring prospects for qualification

## Delegation Patterns

### Pattern 1: Search → Store

Simple search without enrichment.

```python
# User: "Find SaaS companies in the US"

# 1. Get or confirm ICP
icp = get_icp()

# 2. Delegate to search
results = run_subagent("prospect_search", icp=icp, query=user_query)

# 3. Store results
for prospect in results["prospects"]:
    store_prospect(prospect)

# 4. Report to user
report_results(results)
```

### Pattern 2: Search → Enrich → Store

Full pipeline with enrichment.

```python
# User: "Find and research AI companies in SF"

# 1. Search
search_results = run_subagent("prospect_search", 
    query="AI companies San Francisco",
    icp=get_icp()
)

# 2. Enrich each prospect
enriched_prospects = []
for prospect in search_results["prospects"]:
    enriched = run_subagent("prospect_enrich", prospect=prospect)
    enriched_prospects.append(enriched)
    store_prospect(enriched)

# 3. Report with enriched data
report_enriched_results(enriched_prospects)
```

### Pattern 3: Selective Enrichment

Enrich only high-potential prospects.

```python
# 1. Search
results = run_subagent("prospect_search", icp=icp)

# 2. Score and filter
high_potential = [p for p in results["prospects"] 
                  if p.get("relevance_score", 0) >= 70]

# 3. Enrich only high-potential
for prospect in high_potential:
    enriched = run_subagent("prospect_enrich", prospect=prospect)
    store_prospect(enriched)
```

### Pattern 4: On-Demand Enrichment

Enrich when user asks about specific prospect.

```python
# User: "Tell me more about Acme Corp"

# 1. Find in database
prospect = retrieve_prospect(name="Acme Corp")

# 2. Check if already enriched
if prospect["status"] != "enriched":
    # 3. Enrich now
    prospect = run_subagent("prospect_enrich", prospect=prospect)
    store_prospect(prospect)

# 4. Present to user
present_prospect_details(prospect)
```

## Coordination Rules

### 1. Always Have ICP

Before delegating to search:
```python
icp = get_icp()
if not icp:
    ask_user("What kind of companies are you looking for?")
    return
```

### 2. Handle Subagent Errors

```python
try:
    result = run_subagent("prospect_search", ...)
except SubagentError as e:
    # Log error
    log_error(e)
    # Inform user
    tell_user(f"Search failed: {e.message}. Would you like to try again?")
```

### 3. Rate Limiting

Avoid overwhelming APIs:
```python
# Add delay between enrichment calls
for i, prospect in enumerate(prospects):
    if i > 0:
        time.sleep(1)  # 1 second between calls
    enriched = run_subagent("prospect_enrich", prospect=prospect)
```

### 4. Progress Updates

For long operations:
```python
total = len(prospects)
for i, prospect in enumerate(prospects):
    tell_user(f"Enriching {i+1}/{total}: {prospect['company_name']}")
    enriched = run_subagent("prospect_enrich", prospect=prospect)
```

## Decision Matrix

| User Intent | Subagent | Store? | Enrich? |
|-------------|----------|--------|---------|
| "Find companies" | search | Yes | Optional |
| "Search for X" | search | Yes | Optional |
| "Tell me about X" | enrich | Yes | Yes |
| "Research X in detail" | enrich | Yes | Yes |
| "Qualify these prospects" | enrich | Yes | Yes |
| "Add X to my list" | (direct store) | Yes | No |

## Best Practices

1. **Confirm before large operations**: "I'll search for ~50 companies and enrich the top 10. Continue?"
2. **Store incrementally**: Don't wait until all enrichment completes
3. **Provide progress**: Keep user informed during long operations
4. **Handle partial failures**: Some enrichments may fail; continue with others
5. **Cache results**: Check if prospect already exists/enriched before re-processing
