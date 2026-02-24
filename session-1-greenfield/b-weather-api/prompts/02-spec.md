# Prompt 02: Write Your Feature Spec

**When to use:** After the SDD + Specifications theory blocks
**Goal:** Write a spec for Feature 1 (Get Current Weather)

---

## Create `specs/get-weather.md`

```markdown
# Feature: Get Current Weather

## Overview
Returns current weather data for a given city from the mock data source.

## User Story
As an API consumer, I want to get current weather for a city so that I can display it in my dashboard.

## Acceptance Criteria

### AC1: Return weather for valid city
**Given** "Helsinki" exists in the mock data
**When** GET /weather/Helsinki is called
**Then** return 200 with:
  - city: "Helsinki"
  - temperature: number (in Celsius)
  - condition: string (e.g., "Cloudy", "Sunny")
  - humidity: number (percentage)
  - windSpeed: number (km/h)

### AC2: City not found
**Given** "Atlantis" does not exist in mock data
**When** GET /weather/Atlantis is called
**Then** return 404 with error: "City not found: Atlantis"

### AC3: Case-insensitive lookup
**Given** "Helsinki" exists in mock data
**When** GET /weather/helsinki is called (lowercase)
**Then** return the same data as GET /weather/Helsinki

### AC4: Response format
**Given** any valid city request
**When** the response is returned
**Then** it matches this shape:
  ```json
  {
    "data": {
      "city": "string",
      "temperature": "number",
      "condition": "string",
      "humidity": "number",
      "windSpeed": "number",
      "updatedAt": "ISO 8601 string"
    }
  }
  ```

## Technical Constraints
- Use mock data only — no external API calls
- Service function is a pure function (takes city name, returns WeatherData or null)
- Response wrapper: `{ data: WeatherData }` for success, `{ error: string }` for errors

## Test Strategy
- Unit tests for weather-service (AC1, AC2, AC3)
- Test response format separately (AC4)
```

---

## Validate your spec

Run the "Can AI Test This?" check on each AC:
- Can you write `expect(response.status).toBe(200)` for AC1?
- Can you write `expect(response.body.error).toBe("City not found: Atlantis")` for AC2?
- Are all field names and types explicit?
