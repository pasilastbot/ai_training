---
name: personalized-recommendations
description: Use when user requests recommendations aligned with saved preferences and past interactions.
tools: [preference_manager, search_recipes, rank_recipes]
---

## Purpose
Use stored preferences to bias recipe discovery and ranking toward user taste and constraints.

## When to Use
- User asks for recommendations "for me" or "based on my preferences".
- Existing profile includes diets, disliked ingredients, cuisines, or cook-time limits.

## Tools Required
- `preference_manager`: Fetch/update stored user preferences.
- `search_recipes`: Find candidate recipes for current ingredients.
- `rank_recipes`: Score candidates with preference-aware weighting.

## Example
1. Preferences: `python tools/preference_manager.py --operation get --user-id default`
2. Search and rank using profile defaults.
