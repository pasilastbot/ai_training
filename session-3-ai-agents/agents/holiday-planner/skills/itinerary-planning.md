---
name: itinerary-planning
description: Creating detailed day-by-day itineraries balanced for all family members
tools: [create_itinerary, find_activities, get_weather_info]
---

## Purpose

This skill creates realistic, family-friendly itineraries that balance activities for all ages while including appropriate rest time and flexibility.

## When to Use

- Family has chosen a destination and wants detailed planning
- Creating trip plan with day-by-day activities
- Optimizing existing itinerary based on feedback
- Planning around specific must-do activities

## Tools Required

| Tool | Purpose |
|------|---------|
| `create_itinerary` | Generate full day-by-day plan |
| `find_activities` | Find activities at destination |
| `get_weather_info` | Check weather for planning |

## Workflow

### 1. Gather Context

Before creating itinerary:
- Load family profile (ages, preferences)
- Get destination details
- Check weather for travel dates
- Note any pre-booked activities

### 2. Create Itinerary

```
create_itinerary(
  destination="Barcelona",
  duration_days=7,
  family_id="xxx",
  pace="balanced",
  priorities=["Sagrada Familia", "beach time", "Tibidabo"]
)
```

### 3. Find Specific Activities

```
find_activities(
  destination="Barcelona",
  family_id="xxx",
  activity_types=["beaches", "culture", "kids"]
)
```

## Itinerary Principles

### Pacing by Family Type

| Family Type | Daily Activities | Rest Time |
|-------------|------------------|-----------|
| Young children | 1-2 major | Long afternoon break |
| School-age | 2-3 activities | Mid-day break |
| Teens | 3-4 activities | Sleep in mornings |
| Multi-gen | 2 activities | Flexible pace |

### Daily Structure Template

```
Morning (9-12):
- Main activity (suitable for all)
- Consider museum/indoor if hot weather

Midday (12-15):
- Lunch (family-friendly restaurant)
- Rest/pool/beach time
- Nap time for young children

Afternoon (15-18):
- Secondary activity
- Often split options (adventure vs relaxation)

Evening (18-21):
- Dinner
- Light activity/stroll
- Early for families with kids
```

### Balancing Different Interests

#### Rotation Strategy
- Day 1: Culture focus (adults happy, kids get treat after)
- Day 2: Adventure focus (teens happy, adults relax nearby)
- Day 3: Beach/pool day (everyone relaxes)

#### Split Activities
- Morning: Parents do museum, teens sleep in
- Afternoon: Together at beach
- Evening: Kids club while parents dine

## Day Types

### Arrival Day
- Check-in (allow 2-3 hours)
- Explore neighborhood
- Easy dinner nearby
- Early night (jet lag)

### Active Day
- Major attraction morning
- Lunch break
- Secondary activity
- Evening exploration

### Rest Day
- Sleep in
- Pool/beach
- Leisurely lunch
- Optional light activity

### Adventure Day
- Early start
- Full-day excursion
- Return by evening
- Quick dinner, early bed

### Departure Day
- Morning free time
- Pack and checkout
- Airport transfer
- Arrive 3 hours before flight

## Best Practices

1. **Don't over-schedule**: Families need flexibility
2. **Include buffer time**: Kids move slower
3. **Plan meals**: Research family-friendly restaurants
4. **Rainy day backup**: Always have indoor alternatives
5. **Book in advance**: Popular attractions need reservations
6. **Consider energy levels**: Big activity = light next day
7. **Accommodate all ages**: Something for everyone daily
