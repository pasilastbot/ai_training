#!/usr/bin/env python3
"""Shared core logic for recipe-finder-agent."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional

INGREDIENT_SYNONYMS = {
    "scallion": "green onion",
    "spring onion": "green onion",
    "garbanzo beans": "chickpeas",
    "chili": "chili pepper",
    "chilli": "chili pepper",
    "caster sugar": "sugar",
    "confectioners sugar": "powdered sugar",
    "bell pepper": "capsicum",
    "courgette": "zucchini",
    "aubergine": "eggplant",
    "cilantro": "coriander",
    "minced beef": "ground beef",
    "minced pork": "ground pork",
    "olive oil": "oil",
    "vegetable oil": "oil",
}

UNIT_ALIASES = {
    "tbsp": "tablespoon",
    "tbs": "tablespoon",
    "tsp": "teaspoon",
    "oz": "ounce",
    "lb": "pound",
    "g": "gram",
    "kg": "kilogram",
    "ml": "milliliter",
    "l": "liter",
    "clove": "clove",
    "cloves": "clove",
    "cup": "cup",
    "cups": "cup",
}

SUBSTITUTION_MAP = {
    "egg": [
        {"substitute": "flaxseed meal + water", "ratio": "1 tbsp + 3 tbsp", "confidence": 0.86, "impact": "Slightly denser texture"},
        {"substitute": "chia seed + water", "ratio": "1 tbsp + 3 tbsp", "confidence": 0.78, "impact": "Works well for binding"},
    ],
    "milk": [
        {"substitute": "oat milk", "ratio": "1:1", "confidence": 0.92, "impact": "Neutral, dairy-free"},
        {"substitute": "soy milk", "ratio": "1:1", "confidence": 0.9, "impact": "Higher protein"},
    ],
    "butter": [
        {"substitute": "olive oil", "ratio": "3:4", "confidence": 0.81, "impact": "Cleaner flavor"},
        {"substitute": "vegan butter", "ratio": "1:1", "confidence": 0.88, "impact": "Closest baking behavior"},
    ],
    "flour": [
        {"substitute": "gluten-free flour blend", "ratio": "1:1", "confidence": 0.93, "impact": "Gluten-free swap"},
        {"substitute": "almond flour", "ratio": "1:1", "confidence": 0.67, "impact": "More moist and nutty"},
    ],
    "soy sauce": [
        {"substitute": "tamari", "ratio": "1:1", "confidence": 0.95, "impact": "Gluten-free if labeled"},
        {"substitute": "coconut aminos", "ratio": "1:1", "confidence": 0.84, "impact": "Sweeter and less salty"},
    ],
    "ground beef": [
        {"substitute": "ground turkey", "ratio": "1:1", "confidence": 0.87, "impact": "Lean flavor"},
        {"substitute": "lentils", "ratio": "1:1 cooked", "confidence": 0.74, "impact": "Vegetarian protein"},
    ],
    "chicken": [
        {"substitute": "tofu", "ratio": "1:1", "confidence": 0.72, "impact": "Vegetarian alternative"},
        {"substitute": "chickpeas", "ratio": "1:1 cooked", "confidence": 0.76, "impact": "Firm texture in stews"},
    ],
}

RECIPE_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "r001",
        "title": "Chickpea Tomato Curry",
        "cuisine": "Indian",
        "dietary_tags": ["vegetarian", "vegan", "dairy-free"],
        "allergens": [],
        "cook_time_minutes": 30,
        "difficulty": "easy",
        "servings": 4,
        "ingredients": [
            "chickpeas",
            "tomato",
            "onion",
            "garlic",
            "ginger",
            "coconut milk",
            "oil",
            "salt",
            "cumin",
            "turmeric",
        ],
        "instructions": [
            "Saute onion, garlic, and ginger in oil.",
            "Add spices and cook until fragrant.",
            "Add tomatoes, chickpeas, and coconut milk.",
            "Simmer 15 minutes and season to taste.",
        ],
        "source_url": "https://example.com/chickpea-tomato-curry",
        "nutrition": {"calories": 420, "protein_g": 15, "carbs_g": 52, "fat_g": 16},
    },
    {
        "id": "r002",
        "title": "Veggie Omelette",
        "cuisine": "French",
        "dietary_tags": ["vegetarian", "gluten-free"],
        "allergens": ["egg", "dairy"],
        "cook_time_minutes": 15,
        "difficulty": "easy",
        "servings": 2,
        "ingredients": ["egg", "milk", "spinach", "capsicum", "onion", "salt", "pepper", "butter"],
        "instructions": [
            "Whisk eggs with milk and seasoning.",
            "Cook vegetables briefly in butter.",
            "Pour egg mixture and fold when set.",
        ],
        "source_url": "https://example.com/veggie-omelette",
        "nutrition": {"calories": 280, "protein_g": 18, "carbs_g": 8, "fat_g": 19},
    },
    {
        "id": "r003",
        "title": "Quick Pasta Arrabbiata",
        "cuisine": "Italian",
        "dietary_tags": ["vegan", "dairy-free"],
        "allergens": ["gluten"],
        "cook_time_minutes": 20,
        "difficulty": "easy",
        "servings": 3,
        "ingredients": ["pasta", "tomato", "garlic", "chili pepper", "oil", "salt", "parsley"],
        "instructions": [
            "Boil pasta until al dente.",
            "Prepare sauce with oil, garlic, chili, and tomato.",
            "Combine pasta and sauce, garnish with parsley.",
        ],
        "source_url": "https://example.com/pasta-arrabbiata",
        "nutrition": {"calories": 510, "protein_g": 14, "carbs_g": 83, "fat_g": 13},
    },
    {
        "id": "r004",
        "title": "Sheet Pan Lemon Chicken",
        "cuisine": "Mediterranean",
        "dietary_tags": ["high-protein", "dairy-free"],
        "allergens": [],
        "cook_time_minutes": 40,
        "difficulty": "medium",
        "servings": 4,
        "ingredients": ["chicken", "lemon", "potato", "garlic", "oil", "oregano", "salt", "pepper"],
        "instructions": [
            "Season chicken and potatoes with lemon, garlic, oil, and herbs.",
            "Roast on sheet pan at 220C for 35 minutes.",
            "Rest briefly and serve.",
        ],
        "source_url": "https://example.com/sheet-pan-lemon-chicken",
        "nutrition": {"calories": 560, "protein_g": 39, "carbs_g": 32, "fat_g": 30},
    },
    {
        "id": "r005",
        "title": "Black Bean Tacos",
        "cuisine": "Mexican",
        "dietary_tags": ["vegetarian"],
        "allergens": ["gluten"],
        "cook_time_minutes": 25,
        "difficulty": "easy",
        "servings": 4,
        "ingredients": ["black beans", "tortilla", "onion", "tomato", "lime", "capsicum", "cumin", "salt"],
        "instructions": [
            "Warm seasoned black beans in a pan.",
            "Prepare quick tomato-onion salsa.",
            "Assemble tacos and serve with lime.",
        ],
        "source_url": "https://example.com/black-bean-tacos",
        "nutrition": {"calories": 390, "protein_g": 14, "carbs_g": 58, "fat_g": 11},
    },
    {
        "id": "r006",
        "title": "Tofu Stir Fry",
        "cuisine": "Asian",
        "dietary_tags": ["vegan", "vegetarian", "dairy-free"],
        "allergens": ["soy"],
        "cook_time_minutes": 22,
        "difficulty": "easy",
        "servings": 3,
        "ingredients": ["tofu", "broccoli", "carrot", "soy sauce", "garlic", "ginger", "oil", "rice"],
        "instructions": [
            "Pan-sear tofu until golden.",
            "Stir-fry vegetables with garlic and ginger.",
            "Add soy sauce, combine with tofu, and serve over rice.",
        ],
        "source_url": "https://example.com/tofu-stir-fry",
        "nutrition": {"calories": 460, "protein_g": 23, "carbs_g": 49, "fat_g": 18},
    },
]


def canonicalize_ingredient(name: str) -> str:
    """Normalize an ingredient name to canonical lower-case form."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", "", name or "").strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        return ""
    return INGREDIENT_SYNONYMS.get(cleaned, cleaned)


def normalize_ingredient_list(ingredients: Iterable[str]) -> List[str]:
    """Normalize and deduplicate ingredient names."""
    seen = set()
    out: List[str] = []
    for item in ingredients:
        canonical = canonicalize_ingredient(item)
        if canonical and canonical not in seen:
            out.append(canonical)
            seen.add(canonical)
    return out


def parse_ingredient_line(line: str) -> Dict[str, Any]:
    """Parse a single free-text ingredient line."""
    pattern = re.compile(r"^\s*(?:(\d+(?:\.\d+)?)\s*)?(?:(\w+)\s+)?(.+?)\s*$")
    match = pattern.match(line)
    if not match:
        return {
            "raw": line,
            "quantity": None,
            "unit": None,
            "canonical_name": canonicalize_ingredient(line),
            "confidence": 0.5,
        }

    quantity_str, unit_raw, name_raw = match.groups()
    quantity: Optional[float] = float(quantity_str) if quantity_str else None
    unit = UNIT_ALIASES.get((unit_raw or "").lower(), unit_raw.lower() if unit_raw else None)
    canonical_name = canonicalize_ingredient(name_raw)

    confidence = 0.95 if canonical_name else 0.4
    if quantity is None:
        confidence -= 0.05
    if unit is None:
        confidence -= 0.03

    return {
        "raw": line,
        "quantity": quantity,
        "unit": unit,
        "canonical_name": canonical_name,
        "confidence": max(min(confidence, 0.99), 0.2),
    }


def parse_ingredients_text(input_text: str, locale: str = "en-US") -> List[Dict[str, Any]]:
    """Parse free-text ingredient block into normalized ingredient objects."""
    del locale
    split_parts = re.split(r"\n|,|;", input_text or "")
    parsed: List[Dict[str, Any]] = []
    for part in split_parts:
        token = part.strip()
        if token:
            parsed.append(parse_ingredient_line(token))
    return parsed


def dietary_compatible(recipe: Dict[str, Any], filters: Optional[List[str]]) -> bool:
    """Check if recipe satisfies dietary/allergen filters."""
    if not filters:
        return True

    filter_set = {f.lower() for f in filters}
    tags = {tag.lower() for tag in recipe.get("dietary_tags", [])}
    allergens = {a.lower() for a in recipe.get("allergens", [])}

    for item in filter_set:
        if item in {"vegetarian", "vegan", "dairy-free", "gluten-free", "nut-free", "high-protein"}:
            if item == "gluten-free" and "gluten" in allergens:
                return False
            elif item == "nut-free" and "nuts" in allergens:
                return False
            elif item not in {"gluten-free", "nut-free"} and item not in tags:
                return False
        elif item.endswith("-free"):
            allergen_name = item.replace("-free", "")
            if allergen_name in allergens:
                return False
    return True


def search_candidate_recipes(
    ingredients: List[str],
    dietary_filters: Optional[List[str]] = None,
    max_cook_time_minutes: Optional[int] = None,
    cuisine: Optional[str] = None,
    servings: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Return candidate recipes with match metadata."""
    available = set(normalize_ingredient_list(ingredients))
    candidates: List[Dict[str, Any]] = []

    for recipe in RECIPE_CATALOG:
        if not dietary_compatible(recipe, dietary_filters):
            continue
        if max_cook_time_minutes is not None and recipe.get("cook_time_minutes", 0) > max_cook_time_minutes:
            continue
        if cuisine and recipe.get("cuisine", "").lower() != cuisine.lower():
            continue
        if servings and recipe.get("servings", 0) < servings:
            continue

        needed = set(normalize_ingredient_list(recipe.get("ingredients", [])))
        matched = sorted(list(needed.intersection(available)))
        missing = sorted(list(needed.difference(available)))

        result = deepcopy(recipe)
        result["matched_ingredients"] = matched
        result["missing_ingredients"] = missing
        result["match_ratio"] = round(len(matched) / len(needed), 3) if needed else 0.0
        candidates.append(result)

    return candidates


def _difficulty_penalty(level: str) -> float:
    mapping = {"easy": 0.0, "medium": 0.08, "hard": 0.18}
    return mapping.get(level.lower(), 0.1)


def rank_recipe_candidates(
    recipes: List[Dict[str, Any]],
    available_ingredients: List[str],
    user_preferences: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Score and sort recipes based on fit and preferences."""
    prefs = user_preferences or {}
    liked_cuisines = {c.lower() for c in prefs.get("favorite_cuisines", [])}
    disliked_ingredients = {canonicalize_ingredient(i) for i in prefs.get("disliked_ingredients", [])}
    dietary_restrictions = [d.lower() for d in prefs.get("dietary_restrictions", [])]
    max_time_pref = prefs.get("max_cook_time_minutes")

    available = set(normalize_ingredient_list(available_ingredients))
    ranked: List[Dict[str, Any]] = []

    for recipe in recipes:
        needed = set(normalize_ingredient_list(recipe.get("ingredients", [])))
        if not needed:
            continue

        matched = needed.intersection(available)
        missing = needed.difference(available)

        score = len(matched) / len(needed)
        score -= len(missing) * 0.03
        score -= _difficulty_penalty(recipe.get("difficulty", "medium"))

        cook_time = recipe.get("cook_time_minutes", 0)
        score -= min(cook_time / 300.0, 0.22)

        cuisine = recipe.get("cuisine", "").lower()
        if cuisine and cuisine in liked_cuisines:
            score += 0.08

        if max_time_pref and cook_time <= max_time_pref:
            score += 0.05

        ingredient_hit = {canonicalize_ingredient(i) for i in recipe.get("ingredients", [])}
        if ingredient_hit.intersection(disliked_ingredients):
            score -= 0.22

        if dietary_restrictions and not dietary_compatible(recipe, dietary_restrictions):
            score -= 0.5

        ranked_recipe = deepcopy(recipe)
        ranked_recipe["matched_ingredients"] = sorted(list(matched))
        ranked_recipe["missing_ingredients"] = sorted(list(missing))
        ranked_recipe["score"] = round(max(0.0, min(1.0, score)), 4)
        ranked_recipe["ranking_reasons"] = [
            f"ingredient_match={len(matched)}/{len(needed)}",
            f"cook_time={cook_time}m",
            f"difficulty={recipe.get('difficulty', 'unknown')}",
        ]
        ranked.append(ranked_recipe)

    ranked.sort(key=lambda x: (x.get("score", 0), x.get("match_ratio", 0), -x.get("cook_time_minutes", 0)), reverse=True)
    return ranked


def suggest_substitutions_for_missing(
    missing_ingredients: List[str],
    dietary_restrictions: Optional[List[str]] = None,
    available_ingredients: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Return substitution suggestions for missing ingredients."""
    dietary = {d.lower() for d in (dietary_restrictions or [])}
    available = set(normalize_ingredient_list(available_ingredients or []))

    results: List[Dict[str, Any]] = []

    for item in normalize_ingredient_list(missing_ingredients):
        candidates = SUBSTITUTION_MAP.get(item, [])
        filtered: List[Dict[str, Any]] = []
        for candidate in candidates:
            name = canonicalize_ingredient(candidate["substitute"].split("+")[0].strip())
            blocked = False
            if "vegan" in dietary and item in {"egg", "milk", "butter", "chicken", "ground beef"}:
                blocked = False
            if "nut-free" in dietary and "almond" in candidate["substitute"].lower():
                blocked = True
            if not blocked:
                with_availability = deepcopy(candidate)
                with_availability["in_pantry"] = name in available
                filtered.append(with_availability)

        if not filtered:
            filtered = [
                {
                    "substitute": "No direct substitute found",
                    "ratio": "n/a",
                    "confidence": 0.2,
                    "impact": "Recipe flavor/texture may change significantly",
                    "in_pantry": False,
                }
            ]

        results.append(
            {
                "missing_ingredient": item,
                "substitutions": sorted(filtered, key=lambda s: (s.get("in_pantry", False), s.get("confidence", 0)), reverse=True),
            }
        )

    return results


def get_recipe_by_id(recipe_id: str) -> Optional[Dict[str, Any]]:
    """Fetch full recipe detail by ID."""
    for recipe in RECIPE_CATALOG:
        if recipe.get("id") == recipe_id:
            return deepcopy(recipe)
    return None
