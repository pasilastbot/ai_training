---
name: play-audio
description: Use for playing audio files from the command line using the system's native audio player. Works on macOS with volume control. No API keys required. Typically used after qwen3-tts to play generated speech.
---

## Command
`npm run play-audio -- [options]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| file (positional) or -f | Yes | Path to audio file to play |
| -v, --volume | No | Volume level 0–100 (macOS only) |
| -b, --background | No | Play in background without waiting |

## Requirements
- None (uses system audio player)

## Examples
```bash
# Play an audio file
npm run play-audio -- public/audio/speech.wav

# Play with volume control
npm run play-audio -- -f public/audio/speech.wav -v 50

# Play in background
npm run play-audio -- public/audio/speech.wav -b
```
