# Prompt 02: Write Your Feature Spec

**When to use:** After the SDD + Specifications theory blocks
**Goal:** Write a spec for Feature 1 (Get Current Weather) using the AGENTS.md spec template

---

## Your Task

Write a spec for the "Get Current Weather" feature. Save it as `specs/get-weather.md`.

**Use the spec template from `../../AGENTS.md` (Workflow: spec → Spec Template) as your format.**

### Feature Requirements

The GET /weather/:city endpoint returns current weather data from mock data.

Behaviors to cover:
- Returning weather for a valid city (what fields? what types?)
- City not found (what status code? what error message?)
- Case-insensitive city lookup (e.g., "helsinki" vs "Helsinki")
- Response format (what JSON wrapper structure?)

Technical constraints:
- Use mock data only — no external API calls
- Service function is pure (takes city name, returns data or null)
- Success response: `{ data: WeatherData }`
- Error response: `{ error: string }`

---

## The "Can AI Test This?" Check

Before moving on, verify each AC you wrote:
1. Does every AC have specific expected values (status codes, field names, types)?
2. Could you write an `expect()` assertion for each **Then** clause?
3. Are error cases covered with exact error messages?

If any answer is "no" — rewrite the AC until it's testable.

---

## Ask AI to Review Your Spec

```
@specs/get-weather.md
@../../AGENTS.md

Review this spec against the spec template in AGENTS.md:
1. Is every AC testable with a concrete assertion?
2. Are there missing edge cases?
3. Does the response format match the technical constraints?
4. Is the test strategy complete?

List any issues found.
```
