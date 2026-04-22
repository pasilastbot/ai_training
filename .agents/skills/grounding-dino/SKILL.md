---
name: grounding-dino
description: Use for open-vocabulary object detection in images via Grounding DINO on Replicate — supply an image URL or local path and comma-separated queries; returns labeled boxes, confidence scores, optional annotated preview, and optional Sharp bbox crops filtered by label (e.g. only chairs). Requires REPLICATE_API_TOKEN.
---

## Command
`npm run grounding-dino -- [options]`

## How it works
1. **URL mode:** Fetches the image with the same downloader as [`download-file`](.agents/skills/download-file/SKILL.md) (`tools/utils/download.ts` — HTTP GET to a temp file under `downloads/grounding-dino-temp/`, then the file is removed after inference).
2. **Local mode:** Pass `--image` if you already used `npm run download-file` or have a file on disk.
3. Runs [adirik/grounding-dino](https://replicate.com/adirik/grounding-dino) on Replicate and prints detections (`bbox` in pixels: x1, y1, x2, y2), `label`, and `confidence`.
4. **Optional crops:** With `--crop`, each box is cut out with [Sharp](https://sharp.pixelplumbing.com/) from the same image file used for inference. Use `--crop-label` to keep only detections whose label contains that substring (case-insensitive), e.g. `chair` matches `chair` and `wooden chair`.

## Options
| Flag | Required | Description |
|------|----------|-------------|
| -u, --url | No* | Image URL to download and analyze |
| -i, --image | No* | Path to a local image file |
| -q, --query | Yes | Comma-separated object names or short phrases (e.g. `person, laptop, coffee mug`) |
| --box-threshold | No | Box confidence floor, 0–1 (default `0.25`) |
| --text-threshold | No | Label/text match threshold, 0–1 (default `0.25`) |
| --show-visualisation | No | When true (default), API may return `result_image` URL with boxes drawn |
| --json | No | Print JSON only: `{ detections, result_image?, cropPaths? }` |
| --crop | No | Save each bbox as a separate image file |
| --crop-label | No | Only save crops whose `label` contains this text (implies `--crop` if set) |
| --crop-dir | No | Output folder for crops (default `downloads/grounding-dino-crops`) |
| --crop-format | No | `png` (default) or `jpeg` |

\* Provide either `--url` or `--image`, not both.

**Programmatic use:** import `cropDetections(imagePath, detections, { labelFilter?, outputDir, format? })` from `tools/grounding-dino.ts` to crop from any image + detection list.

## Requirements
- `REPLICATE_API_TOKEN` in `.env.local` ([Replicate API tokens](https://replicate.com/account/api-tokens))

## Examples
```bash
# From URL — download + detect
npm run grounding-dino -- -u https://example.com/scene.jpg -q "car, bicycle, traffic light"

# JSON for scripting
npm run grounding-dino -- -u https://example.com/scene.jpg -q "dog, leash" --json

# Two-step: download first, then local file
npm run download-file -- --url https://example.com/p.jpg --folder downloads --filename scene.jpg
npm run grounding-dino -- -i downloads/scene.jpg -q "window, chair"

# Only chairs — saves chair-01.png, chair-02.png, … under --crop-dir
npm run grounding-dino -- -u https://example.com/bbq.jpg -q "chair, table, person" --crop --crop-label chair
```

## API reference
- Model & inputs: [replicate.com/adirik/grounding-dino/api](https://replicate.com/adirik/grounding-dino/api)
- The CLI pins a specific model **version** ID for Replicate compatibility (see `MODEL_REF` in `tools/grounding-dino.ts`); update it if you need a newer release from the [versions](https://replicate.com/adirik/grounding-dino/versions) tab.
