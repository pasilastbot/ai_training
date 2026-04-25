---
name: salary-calculation
description: Calculate minimum salaries based on TES rules
tools: [salary_calculator.py, calculate_salary.py]
---

## Purpose

Calculate minimum salaries based on TES salary tables, considering role category, experience level, and applicable bonuses.

## When to Use

- User asks "what is the minimum salary for X"
- User wants to know applicable bonuses
- User needs salary calculation for specific role/experience

## Tools Required

1. **salary_calculator.py** - Main calculator subagent
   - `--tes "id"` - TES ID
   - `--tes-name "name"` - TES name (will search)
   - `--role "role"` - Job role/category
   - `--experience N` - Years of experience
   - `--ai` - Use AI for detailed calculation

2. **calculate_salary.py** - CLI wrapper
   - Same arguments as above

## Calculation Process

1. Find matching salary table by role
2. Match experience level to salary tier
3. Apply any automatic adjustments
4. List applicable bonuses (shift, evening, night, etc.)

## Example

```bash
# Basic calculation
python subagents/salary_calculator.py --tes "tes_teknologia_2024" --role "engineer" --experience 5

# By TES name
python subagents/salary_calculator.py --tes-name "Teknologiateollisuuden TES" --role "specialist" --experience 3

# With AI analysis
python subagents/salary_calculator.py --tes "tes_1" --role "worker" --experience 10 --ai
```

## AI Mode

When `--ai` is enabled, the calculator:
- Interprets complex role matching
- Identifies all applicable bonuses
- Provides calculation breakdown
- Cites specific PDF pages/sections

## Output

```json
{
  "best_match": {
    "role_category": "Engineer",
    "experience_level": "5+ years",
    "minimum_salary": 3500,
    "hourly_rate": 20.5,
    "effective_date": "2024-01-01",
    "pdf_page": 42
  },
  "applicable_bonuses": [
    {"name": "Shift Allowance", "value": "15%"}
  ],
  "tes_name": "Teknologiateollisuuden TES",
  "tes_validity": "2024-01-01 - 2026-12-31"
}
```
