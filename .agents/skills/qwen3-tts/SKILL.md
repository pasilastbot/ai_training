---
name: qwen3-tts
description: Use for text-to-speech generation via Qwen3-TTS model on Replicate. Three modes — voice (default with style instructions), clone (clone from reference audio), design (create voice from text description). For playing generated audio, use play-audio.
---

## Command
`npm run qwen3-tts -- [options]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| -t, --text | Yes | Text to convert to speech |
| -m, --mode | No | TTS mode: voice (default), clone, or design |
| -o, --output | No | Output filename (default: qwen3-tts-\<timestamp\>.wav) |
| --folder | No | Output folder (default: public/audio) |
| -v, --voice-prompt | No | [Voice mode] Style instruction (e.g. "speak cheerfully") |
| -a, --ref-audio | No | [Clone mode] Path or URL to reference audio (min 3 seconds) |
| -r, --ref-text | No | [Clone mode] Transcript of the reference audio |
| -d, --voice-description | No | [Design mode] Natural language voice description |

## Requirements
- `REPLICATE_API_TOKEN` in `.env.local`

## Examples
```bash
# Simple TTS with default voice
npm run qwen3-tts -- -t "Hello, world!"

# Voice mode with style instructions
npm run qwen3-tts -- -t "Welcome to our podcast" -m voice -v "speak with warmth and enthusiasm"

# Clone mode (clone a voice from audio)
npm run qwen3-tts -- -t "This is my cloned voice" -m clone -a reference.wav -r "This is the reference transcript"

# Design mode (create voice from description)
npm run qwen3-tts -- -t "A beautiful story begins" -m design -d "warm male storyteller with gentle pacing" -o story-intro.wav
```
