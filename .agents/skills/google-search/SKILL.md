---
name: google-search
description: Use for real-time Google Search via Gemini with search grounding. Returns comprehensive answers with source URLs. For general Gemini text/vision tasks without search, use gemini instead.
---

## Command
`npm run google-search -- [options] <query>`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| query (positional) | Yes | Search query |
| -m, --model | No | Gemini model (default: gemini-2.5-flash-lite) |
| -n, --max-results | No | Max source URLs to show (default: 10) |
| -s, --show-sources | No | Show source URLs and titles |
| -f, --format | No | Output format: text or json (default: text) |

## Requirements
- `GOOGLE_AI_STUDIO_KEY` or `GEMINI_API_KEY` in `.env.local`

## Examples
```bash
# Simple search
npm run google-search -- "latest Node.js LTS version"

# Show sources
npm run google-search -- "React Server Components" -s

# JSON output
npm run google-search -- "TypeScript 5 new features" -f json

# Use a specific model
npm run google-search -- "next solar eclipse" -m gemini-2.5-flash
```
