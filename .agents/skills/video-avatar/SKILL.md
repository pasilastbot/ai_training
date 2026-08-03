---
name: video-avatar
description: Use for generating talking-head videos from a portrait image. Supports text-to-speech (30 voices, 10 languages) or lip-sync to existing audio. Outputs 720p or 1080p MP4. Uses Pruna AI's p-video-avatar model on Replicate.
---

## Command
`npm run video-avatar -- [options]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| -i, --image | Yes | Path or URL to portrait image (jpg, jpeg, png, webp) |
| -s, --script | No* | Text script for the avatar to speak (uses built-in TTS) |
| -a, --audio | No* | Path or URL to audio file for lip-sync (overrides script if both provided) |
| -V, --voice | No | Voice for TTS (default: "Zephyr (Female)") — see voices list below |
| -l, --language | No | Language for TTS (default: "English (US)") — see languages list below |
| -p, --voice-prompt | No | Speaking style instructions (e.g., "speak with enthusiasm") |
| --video-prompt | No | Video prompt describing actions (e.g., "the person is gesturing") |
| -r, --resolution | No | Output resolution: 720p (default, $0.025/sec) or 1080p ($0.045/sec) |
| -o, --output | No | Output filename (default: video-avatar-\<timestamp\>.mp4) |
| -f, --folder | No | Output folder (default: public/videos) |
| --seed | No | Random seed for reproducible generation |
| --disable-safety-filter | No | Disable content safety filter (default: true) |
| --disable-prompt-upsampling | No | Skip prompt enhancement (default: false) |

*Either `--script` or `--audio` is required.

## Available Voices (30 options)
**Female:** Zephyr, Kore, Leda, Aoede, Callirrhoe, Autonoe, Despina, Erinome, Laomedeia, Achernar, Gacrux, Pulcherrima, Vindemiatrix, Sulafat

**Male:** Puck, Charon, Fenrir, Orus, Enceladus, Iapetus, Umbriel, Algenib, Algieba, Schedar, Achird, Zubenelgenubi, Sadachbia, Sadaltager, Alnilam, Rasalgethi

## Available Languages (10 options)
English (US), English (UK), Spanish, French, German, Italian, Portuguese (Brazil), Japanese, Korean, Hindi

## Requirements
- `REPLICATE_API_TOKEN` in `.env.local`

## Pricing
- **720p:** $0.025 per second of output video
- **1080p:** $0.045 per second of output video

Example: A 10-second clip at 720p costs $0.25

## Examples
```bash
# Basic avatar with TTS
npm run video-avatar -- -i portrait.jpg -s "Hello, welcome to our product demo!"

# French avatar with specific voice
npm run video-avatar -- -i portrait.png -s "Bonjour, bienvenue!" -l French -V "Kore (Female)"

# Lip-sync to existing audio
npm run video-avatar -- -i portrait.jpg -a narration.mp3

# With speaking style and video action prompts
npm run video-avatar -- -i portrait.jpg -s "This is exciting news!" \
  -p "speak with enthusiasm and energy" \
  --video-prompt "the person is gesturing with their hands"

# High-resolution output with custom filename
npm run video-avatar -- -i portrait.jpg -s "Welcome!" -r 1080p -o welcome-video.mp4

# Reproducible generation with seed
npm run video-avatar -- -i portrait.jpg -s "Hello!" --seed 42
```

## Tips for Best Results
- Use clear, front-facing portrait images with good lighting
- Avoid heavy angles, occlusion, or low resolution images
- For audio lip-sync, use clean speech with minimal background noise
- Use `--voice-prompt` for performance direction (tone, pacing), not content
- Start with 720p for testing, upgrade to 1080p for final production
