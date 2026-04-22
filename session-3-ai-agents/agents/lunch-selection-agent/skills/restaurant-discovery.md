---
name: restaurant-discovery
description: Find lunch restaurants in a city and store them to the database
tools: [search_restaurants, store_restaurant, retrieve_restaurants]
---

## Purpose

Discover lunch restaurants in a specified city using Google Search, then store them for future use.

## When to Use

### Search for Restaurants

Use `search_restaurants` when:
- User asks to find lunch options in a city
- User wants to discover new restaurants
- No restaurants stored for the specified city
- User wants a specific cuisine type

### Store Restaurants

Use `store_restaurant` when:
- Search returns new restaurants not in database
- User manually adds a restaurant
- Enriching existing restaurant with new data

### Retrieve Restaurants

Use `retrieve_restaurants` when:
- Checking what's already stored for a city
- Filtering by cuisine or price range
- Getting statistics about stored data

## Workflow

### 1. Check Existing Data First

```
1. Call retrieve_restaurants with city filter
2. If restaurants exist, can skip search or complement
3. If empty, proceed with search
```

### 2. Search for Restaurants

```python
search_restaurants(
    city="Helsinki",
    cuisine="Italian",  # optional
    query="best lunch spots"  # optional custom query
)
```

Returns:
- Restaurant name, address, website
- Cuisine types
- Price range estimates
- Opening hours if available

### 3. Store Found Restaurants

After search, store each restaurant:

```python
store_restaurant(
    name="Ravintola Kuu",
    city="Helsinki",
    website="https://ravintolakuu.fi",
    cuisine_types=["Finnish", "Nordic"],
    price_range="moderate"
)
```

## Data Quality Tips

1. **Website is Critical**: Menu extraction needs a valid URL
2. **Menu URL**: If restaurant has a dedicated lunch page, store it separately
3. **Cuisine Types**: Be specific (e.g., "Thai" not just "Asian")
4. **Price Range**: Use budget/moderate/expensive consistently
5. **Deduplication**: Check if restaurant already exists before storing

## Example Flow

User: "Find me lunch places in Tampere"

```
1. retrieve_restaurants(city="Tampere") → 0 results
2. search_restaurants(city="Tampere")
3. For each result:
   - store_restaurant(name=..., city="Tampere", ...)
4. Report: "Found and stored 8 restaurants in Tampere"
5. Offer to get menus: "Want me to check today's menus?"
```

## Handling Updates

- Restaurants change - periodically re-search to find new places
- Update stored restaurants when you find new information
- Track `updated_at` to know data freshness
