---
name: preference-learning
description: Manage user food preferences and learn from past selections
tools: [get_preferences, update_preferences, record_selection, get_past_selections, get_recommendation]
---

## Purpose

Track user food preferences (explicit and implicit) to provide personalized lunch recommendations.

## Preference Types

### Explicit Preferences

Set directly by user:
- **liked_cuisines**: ["Italian", "Thai", "Finnish"]
- **disliked_cuisines**: ["Fast food"]
- **dietary_restrictions**: ["vegetarian", "gluten-free"]
- **allergies**: ["shellfish", "peanuts"]
- **avoided_ingredients**: ["cilantro", "mushrooms"]
- **price_preference**: "moderate"
- **spice_tolerance**: "medium"
- **variety_preference**: "adventurous"

### Implicit Preferences

Learned from behavior:
- **cuisine_weights**: Adjusted based on ratings
- **restaurant_weights**: Favorite/avoided restaurants

## When to Update Preferences

Listen for cues in conversation:
- "I'm vegetarian" → `dietary_restrictions: ["vegetarian"]`
- "I love Thai food" → `liked_cuisines: [..., "Thai"]`
- "I'm allergic to nuts" → `allergies: ["nuts"]`
- "Keep it cheap" → `price_preference: "budget"`
- "I like trying new things" → `variety_preference: "adventurous"`

## Recording Selections

### When User Orders

```python
record_selection(
    restaurant_name="Ravintola Kuu",
    dish_name="Salmon soup",
    cuisine_type="Finnish",
    price=12.50,
    city="Helsinki"
)
```

### After Feedback

```python
record_selection(
    restaurant_name="Ravintola Kuu",
    dish_name="Salmon soup",
    rating=5,
    would_order_again=True,
    notes="Perfect comfort food"
)
```

## Implicit Learning

When a selection is recorded with a rating:
- **Rating 4-5**: Increases weights for that cuisine and restaurant
- **Rating 1-2**: Decreases weights
- **Rating 3**: Neutral, no change

Formula: `weight_delta = (rating - 3) * 0.1`

## Recommendation Logic

`get_recommendation` considers:

1. **Dietary Restrictions** (HARD FILTER - never violate)
2. **Liked Cuisines** (+20 score)
3. **Disliked Cuisines** (-30 score)
4. **Price Preference** (+10 if matches)
5. **Implicit Weights** (±15-20 based on history)
6. **Variety** (penalize recently visited)

### Variety Rules

- Exclude dishes eaten in last 7 days
- Exclude restaurants visited in last 3 days
- For "adventurous" users, penalize repeat restaurants

## Workflow Examples

### Learning Preferences

```
User: "I'm vegetarian and I don't like spicy food"

→ update_preferences(
    dietary_restrictions=["vegetarian"],
    spice_tolerance="none"
  )

→ "Got it! I've noted that you're vegetarian and prefer non-spicy food."
```

### Recording a Meal

```
User: "I had the pad thai at Thai Palace, it was great!"

→ record_selection(
    restaurant_name="Thai Palace",
    dish_name="Pad Thai",
    cuisine_type="Thai",
    rating=5  # infer from "great"
  )

→ "Noted! I'll remember you enjoyed the Pad Thai."
```

### Getting a Recommendation

```
User: "What should I have for lunch?"

→ get_recommendation(city="Helsinki")

Response considers:
- User's liked cuisines
- Dietary restrictions (MUST respect)
- What they haven't had recently
- Highly-rated past dishes at available restaurants
```

## Asking for Feedback

After a meal, proactively ask:
- "How was your lunch? Rate it 1-5?"
- "Would you order that again?"
- "Any notes for next time?"

This improves future recommendations.

## Privacy Note

All preference data is stored locally in the agent's memory folder. No data is sent externally beyond the current session with Gemini.
