# Prompt 04: Spec + Build Feature 2

**When to use:** After completing Feature 1 with TDD
**Goal:** Repeat the full cycle for "Get 5-Day Forecast with Caching"

---

## Step 1: Write the Spec

```
@specs/get-weather.md (use as format reference)
@src/types.ts

Write a spec for "Get 5-Day Forecast" with these acceptance criteria:

AC1: Return forecast for valid city
- Given "Helsinki" exists in mock data
- When GET /forecast/Helsinki
- Then return 200 with array of 5 ForecastDay objects (date, high, low, condition)

AC2: City not found
- Given "Atlantis" does not exist
- When GET /forecast/Atlantis
- Then return 404 with error message

AC3: Caching
- Given forecast was fetched for "Helsinki" less than 5 minutes ago
- When GET /forecast/Helsinki is called again
- Then return cached result without re-computing
- And response includes header: X-Cache: HIT

AC4: Cache miss
- Given forecast was never fetched or cache expired
- When GET /forecast/Helsinki
- Then compute fresh result
- And response includes header: X-Cache: MISS

Use the same spec format as get-weather.md.
Save as specs/get-forecast.md
```

---

## Step 2: TDD Implementation

```
@specs/get-forecast.md
@src/types.ts
@src/services/weather-service.ts

Implement "Get Forecast" using TDD:

1. Write failing tests for AC1 and AC2 in src/services/forecast-service.test.ts
2. Implement minimum code in src/services/forecast-service.ts
3. Add caching tests (AC3 + AC4) — use a simple Map for cache
4. Implement caching logic
5. Run ALL tests (weather + forecast) to verify nothing broke

Follow Red-Green-Refactor throughout.
```

---

## Wrap-Up

After both features:
- Start the server with `npm run dev`
- Test manually: `curl http://localhost:3000/weather/Helsinki`
- Verify: `curl http://localhost:3000/forecast/Helsinki`
- Run full test suite: `npm test`
