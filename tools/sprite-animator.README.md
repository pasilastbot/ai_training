# Sprite Animation Generator

Generate sprite animation frames for game characters using AI image generation. Creates sequences for common game animations and can combine them into sprite sheets.

## Features

- **8 Animation Types**: walk, run, jump, idle, attack, fly, swim, death
- **Smart Frame Generation**: Each animation has predefined motion sequences that create smooth, natural movement
- **Sprite Sheet Export**: Combine frames into a single grid layout for game engines
- **Multiple Art Styles**: Pixel art, hand-drawn, 3D-rendered, etc.
- **Background Removal**: Optional transparency for easy compositing
- **Multiple AI Models**: Choose between speed (flux-schnell) or quality (sdxl)

## Usage

### Basic Usage

```bash
# Generate 8-frame walk animation
npm run sprite-animator -- -c "pixel art knight" -a walk

# Generate 6-frame attack animation
npm run sprite-animator -- -c "cute dragon" -a attack -n 6
```

### Create Sprite Sheets

```bash
# Create sprite sheet with 12 frames
npm run sprite-animator -- \
  -c "cyberpunk hero" \
  -a run \
  -n 12 \
  --sprite-sheet \
  -o hero_run.png \
  --size 128x128
```

### With Transparent Background

```bash
# Generate with background removal
npm run sprite-animator -- \
  -c "fantasy wizard" \
  -a idle \
  -n 4 \
  --transparent \
  -s "16-bit pixel art, centered"
```

### High Quality Output

```bash
# Use SDXL for higher quality
npm run sprite-animator -- \
  -c "detailed warrior character" \
  -a jump \
  -n 10 \
  -m sdxl \
  -s "detailed pixel art, RPG style"
```

## Animation Types

Each animation type uses a predefined motion sequence:

### `walk`
- 4-phase cycle: left leg forward → neutral → right leg forward → neutral
- Best with 8 frames for smooth motion
- Side view perspective

### `run`
- Dynamic running motion with both legs tucked/extended
- Recommended 8-12 frames
- Shows high energy movement

### `jump`
- 5-phase sequence: crouch → launch → peak → descend → land
- Works well with 6-10 frames
- Full jump arc from ground to ground

### `idle`
- Subtle breathing/standing animation
- Good for 4-8 frames
- Minimal movement, adds life to standing characters

### `attack`
- 4-phase attack: prepare → swing → follow-through → recover
- Recommended 6-8 frames
- Generic melee attack motion

### `fly`
- Wing flapping cycle: up → level → down → level
- Best with 6-8 frames
- For flying creatures/characters

### `swim`
- Swimming stroke cycle with arms
- Works with 6-8 frames
- Horizontal swimming position

### `death`
- 3-phase sequence: hit reaction → falling → defeated
- Good for 6-10 frames
- Dramatic defeat animation

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `-c, --character` | Character description (required) | - |
| `-a, --animation` | Animation type (required) | - |
| `-n, --frames` | Number of frames (2-16) | 8 |
| `-s, --style` | Art style description | "pixel art, 2D game sprite..." |
| `-o, --output` | Sprite sheet filename | - |
| `-f, --folder` | Output folder | public/sprites |
| `-m, --model` | AI model (flux-schnell/sdxl) | flux-schnell |
| `--sprite-sheet` | Create sprite sheet | false |
| `--size` | Frame size in sheet (WxH) | 64x64 |
| `--transparent` | Remove backgrounds | false |

## Output

### Individual Frames
- Saved as `frame_000.png`, `frame_001.png`, etc.
- Transparent versions prefixed with `transparent_` if requested
- Consistent naming for easy loading

### Sprite Sheet
- All frames arranged in a grid
- Calculates optimal rows/columns automatically
- PNG with transparency support
- Metadata includes grid dimensions

### Metadata File
- JSON file with animation details
- Frame-by-frame prompts used
- Timestamp and configuration
- Example: `walk_animation.json`

```json
{
  "character": "pixel art knight",
  "animation": "walk",
  "frames": 8,
  "style": "pixel art, 2D game sprite",
  "size": "64x64",
  "transparent": true,
  "generatedAt": "2026-02-04T12:00:00.000Z",
  "frames": [
    {
      "number": 0,
      "prompt": "pixel art knight, walking animation frame, left leg forward, side view",
      "file": "frame_000.png"
    }
  ]
}
```

## Tips

### Character Descriptions
- Be specific: "8-bit wizard with blue robes" vs "wizard"
- Mention size: "16x16 pixel sprite", "128x128 character"
- Include style: "hand-drawn", "low-poly 3D", "retro pixel art"

### Frame Count
- **Walk/Run**: 8-12 frames for smooth cycles
- **Jump**: 8-10 frames for full arc
- **Idle**: 4-6 frames for subtle movement
- **Attack**: 6-8 frames for clear action
- **Death**: 6-10 frames for drama

### Style Presets
```bash
# Retro 8-bit
-s "8-bit pixel art, NES style, 16x16 sprite, limited colors"

# Modern pixel art
-s "detailed pixel art, 64x64 sprite, smooth shading, centered"

# Hand-drawn
-s "hand-drawn 2D animation, cartoon style, clean lines"

# Low-poly 3D
-s "low-poly 3D render, isometric view, game ready"
```

## Integration with Game Engines

### Unity
1. Import sprite sheet
2. Use Sprite Editor to slice
3. Set grid size to match `--size` option
4. Create animation clips

### Godot
1. Import sprite sheet
2. Use AnimatedSprite node
3. Set hframes/vframes based on grid
4. Assign to animation player

### Phaser
1. Load sprite sheet
2. Define frame dimensions
3. Create animations from frames
4. Play in game loop

## Requirements

- `REPLICATE_API_TOKEN` in `.env.local`
- Node.js dependencies (installed via `npm install`)

## Examples

### Complete Character Set
```bash
# Generate all animations for a character
for anim in walk run jump idle attack; do
  npm run sprite-animator -- \
    -c "pixel knight" \
    -a $anim \
    --sprite-sheet \
    -o knight_$anim.png
done
```

### Boss Character
```bash
# Large boss with high quality
npm run sprite-animator -- \
  -c "giant dragon boss" \
  -a fly \
  -n 16 \
  -m sdxl \
  --size 512x512 \
  --sprite-sheet \
  -s "epic fantasy art, detailed scales, fire breathing"
```

### Retro Game Character
```bash
# Classic 16x16 sprite
npm run sprite-animator -- \
  -c "hero character" \
  -a walk \
  -n 4 \
  -s "8-bit pixel art, 16x16, Game Boy style, 4 colors" \
  --transparent \
  --sprite-sheet \
  --size 16x16
```

## Troubleshooting

### Background Not Fully Removed
- Use `--transparent` flag
- Specify "white background" in style
- May need manual cleanup for complex backgrounds

### Inconsistent Character Design
- Be very specific in character description
- Include consistent details (colors, clothing, etc.)
- Use same style description for all frames

### Frames Don't Align in Sheet
- Ensure character is centered in prompts
- Use consistent size descriptions
- May need to manually adjust in image editor

## Cost Considerations

- **flux-schnell**: Fast and economical (~$0.003/image)
- **sdxl**: Higher quality, more expensive (~$0.01/image)
- An 8-frame animation: ~$0.024 (flux) or ~$0.08 (sdxl)

## Future Enhancements

Potential additions:
- [ ] Attack direction variants (up, down, forward)
- [ ] Emotion expressions (happy, sad, angry)
- [ ] Custom animation sequences via config file
- [ ] Automatic color palette consistency
- [ ] Multi-angle generation (4/8 directions)
