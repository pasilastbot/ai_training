---
name: openai-image
description: Use for image generation and editing with OpenAI GPT-image-1 or DALL-E 3 models. Supports generate (text-to-image with optional reference image) and edit (modify existing image) subcommands. For Google/Gemini image generation, use gemini-image instead.
---

## Command
`npm run openai-image -- <subcommand> [options]`

## Subcommands

### generate
Generate an image from a text prompt.

| Flag | Required | Description |
|------|----------|-------------|
| -p, --prompt | Yes | Text prompt for image generation |
| -m, --model | No | Model: `gpt-image-1` (default) or `dall-e-3` |
| -o, --output | No | Output filename (default: openai-generated-image.png) |
| --folder | No | Output folder (default: public/images) |
| -s, --size | No | Size: 1024x1024, 1792x1024, 1024x1792 (default: 1024x1024) |
| --quality | No | Quality: standard or hd — DALL-E only (default: standard) |
| --number | No | Number of images 1–4 — DALL-E only (default: 1) |
| --reference-image | No | Reference image path for gpt-image-1 |
| -c, --creative | No | Creativity: standard or vivid (default: standard) |

### edit
Edit an existing image.

| Flag | Required | Description |
|------|----------|-------------|
| -i, --input-image | Yes | Path to the input image |
| -p, --edit-prompt | Yes | Text prompt describing the edit |
| -m, --model | No | Model: `gpt-image-1` (default) or `dall-e-3` |
| -o, --output | No | Output filename (default: openai-edited-image.png) |
| --folder | No | Output folder (default: public/images) |
| -s, --size | No | Size: 1024x1024, 1792x1024, 1024x1792 |
| -c, --creative | No | Creativity: standard or vivid |

## Requirements
- `OPENAI_API_KEY` in `.env.local`

## Examples
```bash
# Generate with GPT-image-1
npm run openai-image -- generate -p "A futuristic cityscape at sunset" -s 1792x1024 -c vivid

# Generate with DALL-E 3
npm run openai-image -- generate -p "A watercolor painting" -m dall-e-3 --quality hd

# Edit an existing image
npm run openai-image -- edit -i input.jpg -p "Change background to a tropical beach"
```
