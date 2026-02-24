---
name: generate-video
description: Use for AI video generation via Replicate models (Kling, MiniMax, Hunyuan, Mochi, LTX). Supports text-to-video and image-to-video. Can optionally generate an input image with OpenAI first, then animate it.
---

## Command
`npm run generate-video -- [options]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| --prompt | Yes | Text description of the desired video |
| --model | No | Replicate model: kling-1.6 (default), kling-2.0, minimax, hunyuan, mochi, ltx |
| --duration | No | Video duration in seconds (model-specific limits) |
| --image | No | Path to input image for image-to-video generation |
| --output | No | Output filename for the video |
| --folder | No | Output folder (default: public/videos) |
| --image-prompt | No | Text prompt for OpenAI to generate an initial image first |
| --openai-image-output | No | Output path for the OpenAI-generated image |
| --aspect-ratio | No | Aspect ratio (e.g. 16:9, 1:1) — model-dependent |

## Requirements
- `REPLICATE_API_TOKEN` in `.env.local`
- `OPENAI_API_KEY` in `.env.local` (only if using `--image-prompt`)

## Examples
```bash
# Text-to-video
npm run generate-video -- --prompt "A sunset over the ocean" --model kling-1.6 --duration 4

# Image-to-video (existing image)
npm run generate-video -- --prompt "Animate the scene" --image input.png --model kling-2.0

# Generate image with OpenAI, then animate it
npm run generate-video -- --image-prompt "A robot playing chess" --openai-image-output public/images/robot.png --prompt "Animate the robot" --image public/images/robot.png --model kling-1.6 --duration 4
```
