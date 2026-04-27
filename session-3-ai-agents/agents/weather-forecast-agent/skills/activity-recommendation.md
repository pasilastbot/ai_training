---
name: activity-recommendation
description: Recommending outdoor activities based on weather conditions
tools: [get_weather, get_forecast, get_activity_recommendations]
---

## Purpose
Suggest appropriate outdoor activities based on current and forecasted weather conditions.

## When to Use
Use this skill when the user:
- Asks what activities are suitable for the weather ("What can I do outside today?")
- Wants suggestions for outdoor plans ("Is it a good day for a picnic?")
- Needs activity recommendations for specific locations ("What should I do in Seattle today?")
- Asks about clothing or gear for activities ("What should I wear for running today?")

## Tools Required

### get_weather
- **Purpose**: Get current weather to assess conditions
- **Parameters**: location, units

### get_forecast
- **Purpose**: Check upcoming conditions for multi-day activities
- **Parameters**: location, days, units

### get_activity_recommendations
- **Purpose**: Get AI-powered activity suggestions based on weather
- **Parameters**: location
- **Returns**: Recommended activities, clothing tips, weather considerations

## Weather-Based Activity Guidelines

### Sunny & Warm (20-30°C / 68-86°F)
**Activities**: Hiking,ycling, beach, outdoor sports, gardening, picnics
**Considerations**: Sun protection, hydration

### Sunny & Cool (10-20°C / 50-68°F)
**Activities**: Walking, light hiking, outdoor dining, photography
**Considerations**: Light layers, comfortable shoes

### Cloudy/Mild (10-20°C / 50-68°F)
**Activities**: Running, walking, fishing, golf, sightseeing
**Considerations**: Good for long-distance activities (no sunburn risk)

### Rainy
**Activities**: Indoor alternatives, or rainy-day activities with proper gear
**Considerations**: Waterproof clothing, umbrella, traction on wet surfaces

### Cold (<10°C / 50°F)
**Activities**: Winter sports (snow available), short walks, indoor activities
**Considerations**: Warm layers, insulation, avoid prolonged exposure

### Snowy/Icy
**Activities**: Skiing, snowboarding, sledding, ice skating
**Considerations**: Winter gear, check conditions, safety equipment

### Windy
**Activities**: Shorter duration activities, sheltered locations
**Considerations**: Wind layers, eye protection, avoid loose objects

### Stormy/Severe Weather
**Activities**: Stay indoors - no outdoor activities recommended
**Considerations**: Safety first, monitor weather alerts

## Example Usage

### Simple Request
```
User: "Is it good for hiking in Denver today?"
Tool Call: get_weather(location="Denver")
Response: Weather shows 18°C, sunny, light winds
Recommendation: "Perfect hiking weather! Clear skies and comfortable temperature. Bring sunscreen and 1-2L of water."
```

### With Forecast
```
User: "Planning a camping trip for the weekend in Portland. What should I know?"
Tool Call: get_forecast(location="Portland", days=5)
Response: Forecast shows rain Friday, clearing Saturday
Recommendation: "Plan for wet weather Friday. Saturday looks great for hiking. Pack a quality tent and rain gear."
```

## Best Practices
1. Always check weather alerts before recommending activities
2. Consider temperature, precipitation, wind, and visibility
3. Suggest indoor alternatives when outdoor conditions are poor
4. Include safety warnings for severe weather
5. Recommend appropriate clothing and gear
6. Factor in user's location preferences and saved places