---
name: substitution-planning
description: Use when candidate recipes require missing ingredients or dietary-safe alternatives.
tools: [suggest_substitutions, rank_recipes]
---

## Purpose
Offer alternatives for missing ingredients while preserving dietary constraints and recipe quality.

## When to Use
- Recipe has unavailable ingredients.
- User asks for allergen-safe swaps.
- User needs fallback options before cooking.

## Tools Required
- `suggest_substitutions`: Generate substitutions with confidence and impact notes.
- `rank_recipes`: Re-rank recipes after considering substitutions.

## Example
1. Substitute: `python tools/suggest_substitutions.py --missing-ingredients egg milk --dietary-restrictions vegan`
2. Re-rank: `python tools/rank_recipes.py --recipes candidates.json --available-ingredients flour banana`
