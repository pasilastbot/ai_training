---
name: ingredient-intake
description: Use when user provides pantry or free-text ingredient lists that need cleanup and normalization before searching.
tools: [parse_ingredients, pantry_manager]
---

## Purpose
Normalize user-provided ingredients into canonical names and optionally persist them in pantry memory.

## When to Use
- User pastes a free-text pantry list.
- Ingredient names contain mixed units, casing, or synonyms.
- Pantry memory must be updated before search.

## Tools Required
- `parse_ingredients`: Parse and normalize raw text.
- `pantry_manager`: Add/list/remove normalized pantry items for a user.

## Example
1. Parse: `python tools/parse_ingredients.py --input-text "2 eggs, tomato, spring onion"`
2. Save: `python tools/pantry_manager.py --operation add --user-id default --items '[{"ingredient_name":"egg"}]'`
