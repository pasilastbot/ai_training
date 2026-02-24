# Prompt 04: Spec + Build Feature 2

**When to use:** After completing Feature 1 with TDD
**Goal:** Repeat the full cycle — spec → test → implement — for "Get 5-Day Forecast with Caching"

---

## Step 1: Write the Spec Yourself

Write a spec for the "Get 5-Day Forecast" feature. Save it as `specs/get-forecast.md`.

**Use the same format as your Feature 1 spec (which follows the AGENTS.md template).**

### Feature Requirements

The GET /forecast/:city endpoint returns a 5-day weather forecast with caching.

Behaviors to cover:
- Returning a forecast for a valid city (what does each day contain?)
- City not found
- Cache hit — fetched recently, return cached result (how to signal this?)
- Cache miss — first fetch or cache expired (what's the TTL?)

Technical constraints:
- Use mock data — no external API calls
- Cache uses a simple Map with TTL
- Response wrapper: `{ data: ForecastDay[] }`

---

## Step 2: Ask AI to Review Your Spec

```
@specs/get-forecast.md
@specs/get-weather.md

Review this spec for completeness:
1. Is every AC testable with a concrete assertion?
2. Are there missing edge cases?
3. Does the caching strategy make sense?
4. Does it follow the same format as get-weather.md?

List any issues found.
```

Fix any issues the AI identifies before proceeding.

---

## Step 3: TDD — RED for AC1

```
@specs/get-forecast.md
@src/types.ts
@src/services/weather-service.ts

Looking at AC1 (Return forecast for valid city), write a failing test.

Requirements:
- Use Vitest
- Test file: src/services/forecast-service.test.ts
- Test getForecast("Helsinki") returns array of 5 ForecastDay objects
- Do NOT implement yet

Run the test to confirm it fails.
```

**Verify:** `npm test` — the new test should FAIL.

---

## Step 4: GREEN for AC1

```
The forecast test is failing.

Implement getForecast() in src/services/forecast-service.ts to make the AC1 test pass.

Requirements:
- Look up the city in mock data
- Generate 5 forecast days
- Return the array or null if city not found
- Keep it simple — just make the test pass

Run tests to confirm they pass.
```

**Verify:** `npm test` — all tests pass (weather + forecast).

---

## Step 5: RED/GREEN for AC2 (City not found)

```
@specs/get-forecast.md
@src/services/forecast-service.test.ts

Add a test for AC2 (city not found):
- getForecast("Atlantis") should return null

Run tests. If it already passes, move on. If not, update implementation.
```

---

## Step 6: RED/GREEN for Caching ACs

```
@specs/get-forecast.md
@src/services/forecast-service.test.ts
@src/services/forecast-service.ts

Add tests for caching behavior from your spec.
Implement caching using a simple Map with TTL.
Run ALL tests (weather + forecast) to verify nothing broke.
```

---

## Wrap-Up

After both features:
- Start the server with `npm run dev`
- Test manually: `curl http://localhost:3000/weather/Helsinki`
- Verify: `curl http://localhost:3000/forecast/Helsinki`
- Run full test suite: `npm test`
