# Prompt 01: Scaffold Your Project

**When to use:** After the Context Sandwich + Model Selection theory blocks
**Goal:** Use a Context Sandwich prompt to scaffold the API project

---

## Your Context Sandwich Prompt

```
@CLAUDE.md
@package.json
@tsconfig.json

Create the initial project structure for a weather dashboard API.

The API should have these endpoints:
- GET /weather/:city — current weather for a city
- GET /forecast/:city — 5-day forecast for a city
- GET /health — health check

Set up the following folder structure:
- src/index.ts — Express server setup, mount routes
- src/types.ts — TypeScript interfaces (WeatherData, ForecastDay, City)
- src/routes/weather.ts — route handlers for /weather and /forecast
- src/services/weather-service.ts — business logic (fetch, transform, cache)
- src/data/mock-weather.ts — mock weather data for development (no real API calls)

Requirements:
- Follow the coding standards in CLAUDE.md
- Define all TypeScript interfaces in types.ts first
- Create placeholder functions that return mock data
- Express server should listen on PORT env var or 3000
- Do NOT implement caching yet — just the basic structure
```

---

## What to look for

After AI generates:
1. Are all interfaces defined in types.ts?
2. Is the route handler separate from business logic?
3. Does mock-weather.ts have realistic sample data?
4. Does the server start and respond to `/health`?
