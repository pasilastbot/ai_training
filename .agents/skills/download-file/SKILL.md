---
name: download-file
description: Use for downloading files from URLs with progress tracking and automatic file type detection. Supports custom output paths and filenames. No API keys required.
---

## Command
`npm run download-file -- [options]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| --url | Yes | URL of the file to download |
| --output | No | Complete output path including filename |
| --folder | No | Output folder path (default: downloads) |
| --filename | No | Output filename (derived from URL if not provided) |

## Requirements
- None

## Examples
```bash
# Download to default folder
npm run download-file -- --url https://example.com/image.jpg

# Download to specific folder with custom filename
npm run download-file -- --url https://example.com/image.jpg --folder public/images --filename hero.jpg

# Download with full output path
npm run download-file -- --url https://example.com/data.json --output ./data/local.json
```
