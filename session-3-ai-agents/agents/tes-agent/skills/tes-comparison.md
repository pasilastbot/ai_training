---
name: tes-comparison
description: Compare terms across multiple TES documents
tools: [tes_comparison.py, retrieve_tes.py]
---

## Purpose

Compare specific fields across multiple TES documents to help HR professionals and payroll specialists understand differences between collective bargaining agreements.

## When to Use

- User wants to compare two or more TES documents
- User asks "which TES has better X"
- User needs a side-by-side view of terms

## Tools Required

1. **tes_comparison.py** - Main comparison subagent
   - `--ids "id1,id2,id3"` - TES IDs to compare
   - `--fields "field1,field2"` - Fields to compare (optional)
   - `--format json|markdown` - Output format
   - `--summarize` - Include AI summary

2. **retrieve_tes.py** - Get TES data
   - `--id "tes_id"` - Get specific TES
   - `--list` - List available TES

## Comparable Fields

- `salary_tables` - Minimum salaries by role and experience
- `working_hours` - Weekly, daily, annual hours
- `vacation` - Vacation days by seniority
- `sick_leave` - Sick leave rules
- `notice_periods` - Notice requirements
- `bonuses` - Allowances and bonuses
- `trial_period` - Probation rules

## Example

```bash
# Compare two TES
python subagents/tes_comparison.py --ids "tes_teknologia_2024,tes_kauppa_2024" --summarize

# Compare specific fields
python subagents/tes_comparison.py --ids "tes_1,tes_2,tes_3" --fields "salary_tables,vacation"

# Markdown output
python subagents/tes_comparison.py --ids "tes_1,tes_2" --format markdown
```

## Output Format

The comparison returns:
- List of TES documents compared
- For each field, values from each TES
- Markdown tables for easy reading
- AI summary highlighting key differences
