# Prompt 03: Implement Feature 1 with TDD

**When to use:** After the TDD Cycle theory block
**Goal:** Implement "Get Current Weather" using Red-Green-Refactor

---

## Step 1: RED — Write Failing Test

```
@specs/get-weather.md
@src/types.ts
@src/services/weather-service.ts

Looking at AC1 (Return weather for valid city) and AC2 (City not found),
write failing tests.

Requirements:
- Use Vitest
- Test file: src/services/weather-service.test.ts
- Test the service function directly (not the Express route)
- Test AC1: getWeather("Helsinki") returns WeatherData
- Test AC2: getWeather("Atlantis") returns null
- Do NOT modify the service implementation yet

Run the test to confirm it fails.
```

---

## Step 2: GREEN — Implement

```
The tests in weather-service.test.ts are failing.

Implement getWeather() in src/services/weather-service.ts to make them pass.

Requirements:
- Look up the city in src/data/mock-weather.ts
- Return WeatherData if found, null if not
- Keep it simple — just make the tests pass

Run tests to confirm they pass.
```

---

## Step 3: Add AC3 (case-insensitive)

```
@specs/get-weather.md
@src/services/weather-service.test.ts
@src/services/weather-service.ts

Add a test for AC3 (case-insensitive lookup).
Then update the implementation to make it pass.
All existing tests must still pass.
```

---

## Step 4: Refactor

```
All tests pass. Refactor the weather service:
1. Add proper TypeScript return types
2. Extract the city lookup logic into a helper function
3. Add the updatedAt timestamp to the response

Keep all tests passing after each change.
```
