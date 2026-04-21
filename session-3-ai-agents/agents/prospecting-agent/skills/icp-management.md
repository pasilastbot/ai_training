---
name: icp-management
description: Manage Ideal Customer Profile (ICP) preferences
tools: [memory_tool.py]
---

## Purpose

Manage the user's Ideal Customer Profile (ICP) - the criteria that define what makes a good prospect. The ICP guides search and scoring.

## When to Use

### Get ICP

- Before running prospect search
- When user asks about current targeting
- To explain why a prospect was scored certain way

### Update ICP

- User specifies new targeting criteria
- User says "focus on X" or "add Y to my targets"
- User provides feedback on prospect quality
- Learning from user's prospect selections

## Tool Commands

### Get Current ICP

```bash
python tools/memory_tool.py icp get --pretty
```

Returns current ICP with all criteria.

### Set ICP from File

```bash
python tools/memory_tool.py icp set --file new_icp.json
```

Replaces entire ICP with contents of file.

### Update Specific Field

```bash
# Update target industries
python tools/memory_tool.py icp update --key target_industries --value '["SaaS", "Fintech", "HealthTech"]'

# Update geography
python tools/memory_tool.py icp update --key geography --value '["US", "UK", "Germany"]'

# Update keywords
python tools/memory_tool.py icp update --key keywords --value '["AI", "machine learning", "automation"]'

# Update company size
python tools/memory_tool.py icp update --key company_size --value '{"min_employees": 50, "max_employees": 500}'

# Update exclusions
python tools/memory_tool.py icp update --key exclusions --value '["consulting", "agency"]'
```

## ICP Schema

```json
{
  "name": "Profile name",
  "target_industries": ["SaaS", "Fintech"],
  "company_size": {"min_employees": 50, "max_employees": 500},
  "revenue_range": {"min_usd": 5000000, "max_usd": 100000000},
  "geography": ["US", "UK", "Germany"],
  "keywords": ["AI", "automation"],
  "technologies": ["AWS", "Python"],
  "exclusions": ["consulting", "agency"],
  "funding_stage": ["series-a", "series-b", "series-c"],
  "decision_makers": ["CTO", "VP Engineering"],
  "signals": {
    "hiring": true,
    "recent_funding": true,
    "tech_adoption": true,
    "growth": true
  }
}
```

## User Intent Mapping

Map user requests to ICP updates:

| User Says | Action |
|-----------|--------|
| "Focus on SaaS companies" | Update `target_industries` |
| "Only US and Europe" | Update `geography` to `["US", "UK", "Germany", "France"]` |
| "Smaller companies, under 100 people" | Update `company_size.max_employees` |
| "They should be using AWS" | Add "AWS" to `technologies` |
| "Exclude consulting firms" | Add "consulting" to `exclusions` |
| "Series A or B stage" | Update `funding_stage` |
| "Companies that are hiring" | Set `signals.hiring` to true |

## Workflow

### 1. Initial Setup

```python
# Check if ICP exists
icp = run_tool("memory_tool", "icp", "get")
if not icp:
    # Ask user to define ICP
    prompt_user("What kind of companies are you looking for?")
```

### 2. Refining ICP

```python
# User says: "Focus more on AI companies"
current_icp = run_tool("memory_tool", "icp", "get")
keywords = current_icp.get("keywords", [])
if "AI" not in keywords:
    keywords.append("AI")
run_tool("memory_tool", "icp", "update", key="keywords", value=keywords)
```

### 3. Using ICP in Search

```python
# Get ICP before search
icp = run_tool("memory_tool", "icp", "get")

# Pass to search subagent
results = run_subagent("prospect_search", icp=icp)
```

## Best Practices

1. **Always check ICP**: Before searching, ensure ICP is defined
2. **Confirm changes**: Confirm ICP updates with user before applying
3. **Explain scoring**: When showing prospects, explain how they match ICP
4. **Learn from feedback**: If user rejects prospects, consider ICP refinement
5. **Save named profiles**: Allow multiple ICPs for different campaigns
