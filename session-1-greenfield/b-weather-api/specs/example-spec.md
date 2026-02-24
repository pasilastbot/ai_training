# Feature: Health Check Endpoint

> This is a reference example. Use this format for your own specs.

## Overview
A simple health check endpoint that confirms the API is running.

## Acceptance Criteria

### AC1: Returns healthy status
**Given** the server is running
**When** GET /health is called
**Then** return 200 with:
  - status: "ok"
  - uptime: number (seconds since start)

### AC2: Response format
**Given** the server is running
**When** GET /health is called
**Then** the response is JSON with Content-Type: application/json

## Technical Constraints
- No authentication required
- Response time < 50ms
- No external dependencies

## Test Strategy
- Integration test: start server, call /health, verify response
