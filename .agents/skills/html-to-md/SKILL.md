---
name: html-to-md
description: Use for scraping a webpage and converting its HTML content to Markdown. Supports CSS selectors to target specific content. No API keys required.
---

## Command
`npm run html-to-md -- [options]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| --url | Yes | URL of the webpage to scrape |
| --output | No | Output file path (default: output.md) |
| --selector | No | CSS selector to target specific content |

## Requirements
- None

## Examples
```bash
# Scrape full page
npm run html-to-md -- --url https://example.com --output docs/scraped.md

# Scrape only the main content
npm run html-to-md -- --url https://example.com --output docs/main.md --selector main

# Scrape a specific section
npm run html-to-md -- --url https://example.com/docs --selector ".content" --output docs/content.md
```
