---
name: datetime
description: Use for getting current date/time in various formats and timezones. Supports ISO, Unix timestamp, UTC, locale-specific formatting, and custom timezone conversion. No API keys required.
---

## Command
`npm run datetime -- [options]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| -f, --format | No | Format: iso, date, time, full, short, compact, or custom |
| -t, --timezone | No | Timezone (e.g. America/New_York, Europe/Helsinki, Asia/Tokyo) |
| -u, --utc | No | Show UTC time |
| -s, --timestamp | No | Show Unix timestamp (milliseconds) |
| -l, --locale | No | Locale for formatting (default: en-US) |

## Requirements
- None

## Examples
```bash
# Current time (default format)
npm run datetime

# ISO format
npm run datetime -- -f iso

# Specific timezone
npm run datetime -- -t Europe/Helsinki

# Unix timestamp
npm run datetime -- -s

# Finnish locale with full format
npm run datetime -- -f full -l fi-FI

# UTC time
npm run datetime -- -u
```
