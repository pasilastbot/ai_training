# Prompt 03: Implement Feature 1 with TDD

**When to use:** After the TDD Cycle theory block
**Goal:** Implement "Get Current Weather" using Red-Green-Refactor

---

## Step 1: RED — Write Failing Test for AC1

Copy-paste this prompt:

```
@specs/get-weather.md
@src/types.ts
@src/services/weather-service.ts

Looking at AC1 (Return weather for valid city), write a failing test.

Requirements:
- Use Vitest
- Test file: src/services/weather-service.test.ts
- Test the service function directly (not the Express route)
- Test ONLY AC1: getWeather("Helsinki") returns WeatherData with correct fields
- Do NOT modify the service implementation yet

Run the test to confirm it fails.
```

**Verify:** Run `npm test` — it should FAIL (red). This is correct!

---

## Step 2: GREEN — Implement AC1

```
The test in weather-service.test.ts is failing.

Implement getWeather() in src/services/weather-service.ts to make the AC1 test pass.

Requirements:
- Look up the city in src/data/mock-weather.ts
- Return WeatherData if found, null if not
- Keep it simple — just make the test pass

Run tests to confirm they pass.
```

**Verify:** Run `npm test` — it should PASS (green).

---

## Step 3: RED — Add AC2 test (City not found)

```
@specs/get-weather.md
@src/services/weather-service.test.ts

Add a test for AC2 (city not found):
- getWeather("Atlantis") should return null

Run tests to confirm the new test passes (it may already pass from Step 2).
If it already passes, that's OK — move to Step 4.
```

**Verify:** Run `npm test` — all tests should pass.

---

## Step 4: RED/GREEN — Add AC3 (case-insensitive)

```
@specs/get-weather.md
@src/services/weather-service.test.ts
@src/services/weather-service.ts

Add a test for AC3 (case-insensitive lookup):
- getWeather("helsinki") should return the same data as getWeather("Helsinki")

Run the test — it will likely FAIL (red).
Then update the implementation to make it pass.
All existing tests must still pass.
```

**Verify:** Run `npm test` — all tests should pass.

---

## Step 5: Refactor

```
All tests pass. Refactor the weather service:
1. Add proper TypeScript return types
2. Extract the city lookup logic into a helper function
3. Add the updatedAt timestamp to the response

Keep all tests passing after each change.
```

**Key rule:** Run tests after EVERY change. If they break, undo and try again.
