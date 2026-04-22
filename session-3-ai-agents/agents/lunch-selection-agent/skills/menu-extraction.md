---
name: menu-extraction
description: Extract today's lunch menu from restaurant websites using url_context
tools: [get_todays_menu]
---

## Purpose

Fetch and extract today's lunch menu from restaurant websites using Gemini's url_context tool.

## When to Use

Use `get_todays_menu` when:
- User asks what's for lunch at a specific restaurant
- Building recommendations (need current menu data)
- User wants to compare menus across restaurants
- Cached menu is stale (> 24 hours old)

## How It Works

1. **URL Context**: Gemini fetches the restaurant website
2. **Content Analysis**: Extracts lunch-relevant information
3. **Structured Output**: Returns dishes, prices, dietary info
4. **Cache Update**: Stores menu in restaurant record

## Tool Usage

```python
get_todays_menu(
    restaurant_url="https://ravintola.fi/lounas",
    restaurant_name="Ravintola Helsinki",
    restaurant_id="rest_123"  # optional, enables caching
)
```

## Response Structure

```json
{
  "restaurant": "Ravintola Helsinki",
  "menu_date": "2024-01-15",
  "weekday": "Monday",
  "menu_type": "daily_special",
  "dishes": [
    {
      "name": "Salmon soup",
      "description": "Creamy salmon soup with dill",
      "price": 12.50,
      "dietary": ["gluten-free", "lactose-free"],
      "category": "soup"
    }
  ],
  "lunch_hours": "11:00-14:00",
  "includes": ["salad bar", "bread", "coffee"],
  "buffet_price": null
}
```

## Finnish Menu Terms

Common terms to look for:
- **Lounas** - Lunch
- **Päivän** - Today's
- **Viikon** - Weekly
- **Buffet** - Buffet
- **Salaattipöytä** - Salad bar
- **Leipä** - Bread
- **Kahvi** - Coffee

Dietary indicators:
- **L** - Lactose-free
- **G** - Gluten-free
- **VE** - Vegan
- **M** - Milk-free
- **⊗** - Often indicates gluten-free

## Best Practices

1. **Use Menu URL**: If available, use dedicated lunch page URL
2. **Include Restaurant Name**: Helps extraction accuracy
3. **Pass Restaurant ID**: Enables automatic caching
4. **Handle Failures**: Some sites may block bots
5. **Respect Freshness**: Don't fetch same menu multiple times per day

## Workflow Example

```
User: "What's for lunch at Ravintola Kuu today?"

1. retrieve_restaurants(search_query="Ravintola Kuu")
   → Get restaurant with ID and URL

2. get_todays_menu(
     restaurant_url="https://ravintolakuu.fi/lounas",
     restaurant_name="Ravintola Kuu",
     restaurant_id="rest_123"
   )

3. Present menu with dietary indicators highlighted
4. Offer recommendation based on user preferences
```

## Error Handling

If extraction fails:
- Try the main website instead of menu URL
- Fall back to cached menu if recent
- Suggest user check website directly
- Report what was found instead (e.g., "Found dinner menu only")

## Caching Strategy

- Menu is cached with restaurant record
- `last_menu_fetch` timestamp tracks freshness
- Re-fetch if older than current date
- Weekday menus change daily - cache accordingly
