---
name: weather-lookup
description: Fetching weather data using Google Search and weather APIs
tools: [get_weather, get_forecast]
---

## Purpose
Retrieve current weather conditions and multi-day forecasts for any location worldwide.

## When to Use
Use this skill when the user:
- Asks about current weather ("What's the weather in Tokyo?")
- Requests a forecast ("What will the weather be like next week in London?")
- Needs weather data for planning ("Is it going to rain tomorrow in Paris?")
- Asks about temperature, humidity, or other weather metrics

## Tools Required

### get_weather
- **Purpose**: Get current weather conditions
- **Parameters**:
  - `location` (required): City name or coordinates
  - `units` (optional): "metric" or "imperial"
- **Returns**: Current temperature, conditions, humidity, wind, etc.

### get_forecast
- **Purpose**: Get multi-day weather forecast
- **Parameters**:
  - `location` (required): City name or coordinates
  - `days` (optional): Number of days (1-7, default: 5)
  - `units` (optional): "metric" or "imperial"
- **Returns**: Daily forecasts with high/low temps, conditions, precipitation probability

## Example Usage

### Current Weather
```
User: "What's the weather like in Helsinki right now?"
Tool Call: get_weather(location="Helsinki", units="metric")
Response:
{
  "weather": {
    "temperature": 5,
    "condition": "Partly cloudy",
    "humidity": 75,
    "wind": "12 km/h NW",
    "feels_like": 2
  }
}
```

### Multi-Day Forecast
```
User: "What's the forecast for New York for the next 5 days?"
Tool Call: get_forecast(location="New York", days=5, units="imperial")
Response:
{
  "forecast": [
    {"day": "Monday", "high": 72, "low": 58, "condition": "Sunny"},
    {"day": "Tuesday", "high": 68, "low": 55, "condition": "Cloudy"},
    ...
  ]
}
```

## Best Practices
1. Always check cache first to avoid redundant API calls
2. Default to metric units unless user specifies otherwise
3. Provide both numeric data and user-friendly descriptions
4. Include relevant warnings for severe weather conditions
5. Suggest the forecast extension if user might need more days