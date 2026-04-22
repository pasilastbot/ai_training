---
name: minimax-music
description: Use for full-length music generation (vocals + instruments or instrumental) via MiniMax Music 2.6 on Replicate. Supports lyrics + style prompt, instrumental-only, auto-generated lyrics, BPM/key in prompt, and quality options (sample rate, bitrate, format).
---

## Command
`npm run minimax-music -- [options]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| -p, --prompt | Yes | Style direction — key, BPM, genre, mood, vocal/instrument hints (see [model README](https://replicate.com/minimax/music-2.6)) |
| -l, --lyrics | No* | Lyrics (section tags like `[Verse]`, `[Chorus]`); use `\n` for line breaks |
| --lyrics-file | No* | Path to UTF-8 lyrics file |
| -i, --instrumental | No | Instrumental track only (no vocals) |
| --lyrics-optimizer | No | Generate lyrics from the prompt (omit lyrics) |
| --sample-rate | No | `16000`, `24000`, `32000`, or `44100` |
| --bitrate | No | `32000`, `64000`, `128000`, or `256000` |
| --audio-format | No | `mp3` (default), `wav`, or `pcm` |
| --seed | No | Integer `0`–`1000000` for reproducibility |
| -o, --output | No | Output filename |
| -f, --folder | No | Output folder (default: `public/audio`) |

\* For vocal songs, supply `--lyrics` or `--lyrics-file`, unless `--lyrics-optimizer` is set. Instrumental mode ignores lyrics.

## Requirements
- `REPLICATE_API_TOKEN` in `.env.local` ([Replicate API tokens](https://replicate.com/account/api-tokens))

## Examples
```bash
# Song with lyrics and style
npm run minimax-music -- -p "E minor, 90 BPM, acoustic guitar ballad, male vocal, emotional" -l "[Verse]
Walking through the rain
[Chorus]
But I still remember you"

# Instrumental
npm run minimax-music -- -p "Cinematic orchestral, epic, sweeping strings, 90 BPM" -i

# Style-only: model writes lyrics
npm run minimax-music -- -p "Upbeat pop, summer vibes, female vocal" --lyrics-optimizer

# High quality WAV
npm run minimax-music -- -p "Lo-fi hip-hop, chill" -i --audio-format wav --sample-rate 44100 --bitrate 256000 -o chill.wav
```
