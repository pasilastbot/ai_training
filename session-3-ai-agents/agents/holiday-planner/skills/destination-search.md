---
name: destination-search
description: Finding and evaluating destinations based on family needs
tools: [search_destinations, get_destination_details, aggregate_family_wishes]
---

## Purpose

This skill finds destinations that match the whole family's wishes. It uses aggregated preferences to search for places where everyone can have a good time.

## When to Use

- Family has shared their preferences and ready to see options
- User asks for destination suggestions
- User wants to explore a specific type of holiday
- Comparing potential destinations

## Tools Required

| Tool | Purpose |
|------|---------|
| `aggregate_family_wishes` | Combine all member wishes first |
| `search_destinations` | Find matching destinations |
| `get_destination_details` | Deep dive on specific destination |

## Workflow

### 1. First Aggregate Wishes

Before searching, understand the family's combined needs:

```
aggregate_family_wishes(family_id="xxx")

Returns:
- Common ground (what everyone agrees on)
- Conflicts (where wishes diverge)
- Ideal trip profile
- Search criteria to use
```

### 2. Search Based on Aggregated Wishes

```
search_destinations(
  query="beach family holiday with activities for teens and seniors",
  family_id="xxx",
  num_results=5
)
```

The search considers:
- Family composition (ages, roles)
- Shared activity interests
- Must-haves and deal-breakers
- Budget and duration constraints
- Travel logistics

### 3. Evaluate Specific Destinations

```
get_destination_details(
  destination="Crete",
  country="Greece"
)

Returns:
- Activities for all ages
- Weather patterns
- Best areas to stay
- Budget estimates
- Family considerations
```

## Handling Conflicts

When family members want different things:

| Conflict | Resolution Strategy |
|----------|---------------------|
| Beach vs Mountains | Suggest coastal mountains (Amalfi, Croatia) |
| Adventure vs Relaxation | Split-activity destinations (resorts with tours) |
| Culture vs Fun | Cities with family attractions (Barcelona, Rome) |
| Budget differences | Show tier options for same destination |

## Search Strategies

### By Family Type

```
# Young children
"family resort with kids club, shallow beaches, Mediterranean"

# Teenagers
"adventure activities, water sports, theme parks, Europe"

# Multi-generational
"accessible, varied pace, mix of relaxation and culture"
```

### By Constraint

```
# Budget-conscious
"affordable family destination, all-inclusive options, Europe"

# Short flight time
"family beach within 4 hours from Helsinki"

# School holidays
"July family destinations avoiding crowds"
```

## Best Practices

1. **Always aggregate first**: Understand combined wishes before searching
2. **Present options fairly**: Show pros AND cons
3. **Explain fit**: Why this destination works for each family member
4. **Offer alternatives**: "If beach isn't available, consider..."
5. **Check seasonality**: Best time to visit matters
