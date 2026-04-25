---
name: comparison
description: Comparing holiday options objectively for family decision-making
tools: [compare_options, compare_budgets, compare_weather]
---

## Purpose

This skill helps families make decisions by comparing options side-by-side. It provides objective analysis considering each family member's fit.

## When to Use

- Family has 2+ destination options to choose between
- User asks "which is better for us?"
- Comparing different trip configurations
- Budget comparison across options

## Tools Required

| Tool | Purpose |
|------|---------|
| `compare_options` | Full comparison with family fit analysis |
| `compare_budgets` | Budget-focused comparison |
| `compare_weather` | Weather and timing comparison |

## Workflow

### 1. Comprehensive Comparison

```
compare_options(
  destinations=["Crete", "Costa Brava", "Algarve"],
  family_id="xxx",
  aspects=["budget", "activities", "weather", "family_fit"]
)
```

Returns:
- Budget comparison (total, per person, per day)
- Activity comparison (what's available where)
- Weather comparison (best timing)
- Family fit scores (by member and overall)
- Trade-offs and recommendations

### 2. Budget-Focused Comparison

```
compare_budgets(
  destinations=["Thailand", "Greece", "Portugal"],
  duration_days=14,
  family_id="xxx"
)
```

### 3. Weather/Timing Comparison

```
compare_weather(
  destinations=["Croatia", "Spain", "Italy"],
  family_id="xxx"
)
```

## Comparison Aspects

### Budget

| Aspect | What to Compare |
|--------|-----------------|
| Total cost | Full trip estimate |
| Daily rate | Per person per day |
| Flight costs | From departure city |
| Value rating | What you get for money |

### Family Fit

| Aspect | How Measured |
|--------|--------------|
| Overall score | 0-100 aggregated fit |
| Member scores | Individual fit per person |
| Matching wishes | Which wishes are met |
| Concerns | Potential issues for family |

### Activities

| Aspect | Details |
|--------|---------|
| Variety | Range of activity types |
| Age suitability | Coverage for all ages |
| Must-have matches | Specific requested activities |

### Logistics

| Aspect | Consideration |
|--------|---------------|
| Flight time | Duration from departure |
| Visa requirements | EU/non-EU considerations |
| Language barrier | Communication ease |
| Health/safety | Family travel advisories |

## Presenting Comparisons

### Good Format

```markdown
## Comparing: Crete vs Costa Brava vs Algarve

### Budget (family of 4, 10 days)
| | Crete | Costa Brava | Algarve |
|---|---|---|---|
| Total | €4,200 | €4,800 | €4,500 |
| Best value | ✓ | | |

### Family Fit
| | Crete | Costa Brava | Algarve |
|---|---|---|---|
| Overall | 88% | 82% | 85% |
| For teens | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| For grandma | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

### Recommendation
**Crete** offers the best balance of value, activities for all ages,
and accessible terrain for grandma, while still having enough
adventure options for your teenager.
```

## Best Practices

1. **Be objective**: Present facts, let family decide
2. **Highlight trade-offs**: Cheaper but longer flight, etc.
3. **Consider each member**: Don't optimize for majority only
4. **Include deal-breakers**: Flag if any option fails constraints
5. **Give clear recommendation**: With reasoning
