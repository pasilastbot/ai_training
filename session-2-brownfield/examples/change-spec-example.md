# Change Spec: Add Request Logging to Auth Middleware

> This is a reference example. Use this format for your Suroi change spec.

## Current Behavior
The auth middleware (`src/middleware/auth.ts`) validates JWT tokens and attaches the user to the request. Failed auth attempts return 401 but are not logged. There is no visibility into authentication failures.

## Proposed Change
Add structured logging for all auth events (success and failure) to help with debugging and security monitoring.

## Acceptance Criteria

### AC1: Log successful authentication
**Given** a request with a valid JWT token
**When** the auth middleware processes it
**Then** log at INFO level: `{ event: "auth_success", userId: string, path: string, timestamp: ISO8601 }`

### AC2: Log failed authentication — invalid token
**Given** a request with an invalid JWT token
**When** the auth middleware processes it
**Then** log at WARN level: `{ event: "auth_failure", reason: "invalid_token", path: string, timestamp: ISO8601 }`
**And** return 401 as before

### AC3: Log failed authentication — missing token
**Given** a request without a JWT token
**When** the auth middleware processes it
**Then** log at WARN level: `{ event: "auth_failure", reason: "missing_token", path: string, timestamp: ISO8601 }`

## Files to Modify

| File | Change |
|------|--------|
| `src/middleware/auth.ts` | Add logging calls at success and failure points |
| `src/utils/logger.ts` | Add `authEvent()` helper if it doesn't exist |

## Risk Assessment
- **Low risk:** Logging is additive — it doesn't change auth behavior
- **Watch for:** Performance impact if logging is synchronous (use async logger)
- **Could break:** Nothing — auth logic is unchanged

## Test Strategy
- **Unit test:** Mock logger, verify `authEvent()` is called with correct params
- **Manual:** Make requests with valid/invalid/missing tokens, check server logs
