---
name: image-optimizer
description: Use for image optimization tasks — resizing, format conversion (png/jpeg/webp), quality adjustment, and AI background removal. For background removal without other optimizations, use remove-background instead.
---

## Command
`npm run optimize-image -- [options]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| -i, --input | Yes | Path to input image |
| -o, --output | Yes | Path to output image |
| --remove-bg | No | Remove image background using AI |
| --resize | No | Resize image (format: WIDTHxHEIGHT, e.g. 800x600) |
| --format | No | Convert to format: png, jpeg, or webp |
| --quality | No | Output quality 1–100 (default: 80) |

## Requirements
- `REPLICATE_API_TOKEN` in `.env.local` (only for `--remove-bg`)

## Examples
```bash
# Resize and convert to webp
npm run optimize-image -- -i input.png -o output.webp --resize 512x512 --format webp --quality 90

# Remove background
npm run optimize-image -- -i photo.jpg -o photo-nobg.png --remove-bg

# Just resize
npm run optimize-image -- -i large.png -o small.png --resize 200x200
```
