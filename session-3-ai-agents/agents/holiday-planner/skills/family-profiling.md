---
name: family-profiling
description: Collecting and managing family profiles with member preferences
tools: [create_family_profile, add_family_member, update_member_preferences, set_family_constraints]
---

## Purpose

This skill handles creating and managing family profiles that capture each family member's travel preferences, must-haves, and constraints. A well-built family profile is the foundation for personalized destination recommendations.

## When to Use

- User wants to start planning a family holiday
- User mentions family members (kids, teens, grandparents, etc.)
- User needs to update preferences or add new family members
- Setting budget, duration, or travel date constraints

## Tools Required

| Tool | Purpose |
|------|---------|
| `create_family_profile` | Create new family with members |
| `add_family_member` | Add member to existing family |
| `update_member_preferences` | Set activities, must-haves, deal-breakers |
| `set_family_constraints` | Set budget, duration, departure location |

## Workflow

### 1. Create Family Profile

```
User: "We're a family of 4 - me and my wife, and kids aged 8 and 14"

Agent calls:
create_family_profile(
  name="Family",
  members=[
    {"name": "Dad", "role": "adult", "age": 40},
    {"name": "Mom", "role": "adult", "age": 38},
    {"name": "Teen", "role": "teen", "age": 14},
    {"name": "Child", "role": "child", "age": 8}
  ]
)
```

### 2. Gather Preferences for Each Member

Ask about each member's preferences:
- Activity interests (beach, culture, adventure, etc.)
- Must-haves (pool, kids club, nature)
- Deal-breakers (long flights, extreme heat)

```
update_member_preferences(
  family_id="xxx",
  member_name="Teen",
  activity_types=["adventure", "water_sports", "theme_parks"],
  must_haves=["wifi", "teens activities"],
  deal_breakers=["boring museums"]
)
```

### 3. Set Family Constraints

```
set_family_constraints(
  family_id="xxx",
  budget_max=5000,
  preferred_duration_days=10,
  departure_location="Helsinki",
  max_flight_hours=5,
  preferred_months=[6, 7, 8]
)
```

## Best Practices

1. **Ask about all ages**: Don't forget infants, teens, or grandparents
2. **Understand roles**: Teen needs differ from children
3. **Find conflicts early**: One wants beach, another wants mountains
4. **Set realistic constraints**: Budget should cover whole family
5. **Consider mobility**: Grandparents may have walking limitations

## Example Conversation

```
User: We need a summer holiday for our family

Agent: I'd love to help! To find the perfect destination, tell me about your family:
- How many people are traveling?
- What are the ages (especially kids)?
- Where would you be flying from?

User: 2 adults, our 10-year-old who loves animals, and grandma (72)

Agent: [Creates family profile]
       Let me understand everyone's wishes:
       - What activities does each person enjoy?
       - Any health or mobility considerations for grandma?
       - What's your budget for this trip?
```
