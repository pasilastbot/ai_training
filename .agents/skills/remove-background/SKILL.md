---
name: remove-background
description: Use for advanced background removal using Sharp with color tolerance and edge detection. Works locally without API keys. For AI-powered background removal, use image-optimizer with --remove-bg flag instead.
---

## Command
`npm run remove-background-advanced -- [options]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| --input | Yes | Path to input image |
| --output | Yes | Path to output image |
| --tolerance | No | Color tolerance for background detection 0–255 (default: 30) |

## Requirements
- None (uses Sharp locally)

## Examples
```bash
# Basic background removal
npm run remove-background-advanced -- --input input.png --output output.png

# With higher tolerance for varied backgrounds
npm run remove-background-advanced -- --input input.png --output output.png --tolerance 40
```
