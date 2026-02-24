---
name: gemini-image
description: Use for image generation and editing with Google Gemini 2.0 or Imagen 3.0 models. Supports generate (text-to-image) and edit (modify existing image) subcommands. For OpenAI image generation, use openai-image instead.
---

## Command
`node tools/gemini-image-tool.js <subcommand> [options]`

## Subcommands

### generate
Generate an image from a text prompt.

| Flag | Required | Description |
|------|----------|-------------|
| -p, --prompt | Yes | Text prompt for image generation |
| -m, --model | No | Model: `gemini-2.0` (default) or `imagen-3.0` |
| -o, --output | No | Output filename (default: gemini-generated-image.png) |
| --folder | No | Output folder (default: public/images) |
| -n, --num-outputs | No | Number of images, Imagen 3 only (default: 1, max: 4) |
| --negative-prompt | No | Negative prompt (Imagen 3 only) |
| --aspect-ratio | No | Aspect ratio, Imagen 3 only: 1:1, 16:9, 9:16, 4:3, 3:4 |

### edit
Edit an existing image using Gemini 2.0.

| Flag | Required | Description |
|------|----------|-------------|
| -i, --input-image | Yes | Path to the input image |
| -p, --edit-prompt | Yes | Text prompt describing the edit |
| -o, --output | No | Output filename (default: gemini-edited-image.png) |
| --folder | No | Output folder (default: public/images) |

## Requirements
- `GOOGLE_AI_STUDIO_KEY` or `GEMINI_API_KEY` in `.env.local`

## Examples
```bash
# Generate with Gemini 2.0
node tools/gemini-image-tool.js generate -p "A futuristic car"

# Generate with Imagen 3.0 (multiple outputs, widescreen)
node tools/gemini-image-tool.js generate -p "A futuristic car" -m imagen-3.0 -n 2 --aspect-ratio 16:9 -o car.png

# Edit an existing image
node tools/gemini-image-tool.js edit -i input.png -p "Add sunglasses to the person" -o edited.png
```
