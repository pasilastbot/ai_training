---
name: sprite-animator
description: Use for generating sprite animation frames for game characters using AI. Creates sequences for walk, run, jump, idle, attack, fly, swim, and death animations. Can output individual frames or combine into sprite sheets.
---

## Command
`npm run sprite-animator -- [options]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| -c, --character | Yes | Character description (e.g. "pixel art knight") |
| -a, --animation | Yes | Animation type: walk, run, jump, idle, attack, fly, swim, death |
| -n, --frames | No | Number of frames 2–16 (default: 8) |
| -s, --style | No | Art style (default: "pixel art, 2D game sprite, centered, white background") |
| -o, --output | No | Output filename for sprite sheet (requires --sprite-sheet) |
| --folder | No | Output folder (default: public/sprites) |
| -m, --model | No | AI model: flux-schnell (fast) or sdxl (quality) (default: flux-schnell) |
| --sprite-sheet | No | Combine all frames into a single sprite sheet |
| --size | No | Frame size in sprite sheet WIDTHxHEIGHT (default: 64x64) |
| --transparent | No | Attempt to remove white/light backgrounds |

## Requirements
- `REPLICATE_API_TOKEN` in `.env.local`

## Examples
```bash
# Generate 8-frame walk cycle
npm run sprite-animator -- -c "pixel art knight" -a walk -n 8

# Create a sprite sheet with 12 frames
npm run sprite-animator -- -c "cute dragon" -a fly -n 12 --sprite-sheet -o dragon_fly.png --size 128x128

# Transparent background with custom style
npm run sprite-animator -- -c "8-bit wizard" -a attack -n 6 --transparent -s "retro pixel art, 16x16 sprite"

# High quality with SDXL model
npm run sprite-animator -- -c "cyberpunk hero" -a jump -n 10 -m sdxl
```
