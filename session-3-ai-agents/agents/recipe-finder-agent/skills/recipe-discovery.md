---
name: recipe-discovery
description: Use when user asks for recipes from available ingredients with optional constraints.
tools: [search_recipes, rank_recipes, get_recipe_details]
---

## Purpose
Discover candidate recipes, rank them for fit, and fetch detailed instructions for selected recipes.

## When to Use
- User asks what they can cook now.
- User includes dietary/cuisine/time constraints.
- User wants full recipe steps after ranking.

## Tools Required
- `search_recipes`: Find matching candidates.
- `rank_recipes`: Score by pantry fit and preferences.
- `get_recipe_details`: Retrieve full details for a selected recipe id.

## Example
1. Search: `python tools/search_recipes.py --ingredients tomato onion garlic --dietary-filters vegan`
2. Rank: `python tools/rank_recipes.py --recipes recipes.json --available-ingredients tomato onion garlic`
3. Detail: `python tools/get_recipe_details.py --recipe-id r001 --include-nutrition`
