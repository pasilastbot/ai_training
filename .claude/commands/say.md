# Say — Text to Speech with Playback

Convert text to speech using Qwen3-TTS and immediately play the resulting audio.

## Input

$ARGUMENTS

If no arguments provided, ask the user what text they want spoken.

## Instructions

### Step 1: Parse Input

Extract from the arguments:
- **Text to speak** (required) — the main content, everything that isn't a recognized option
- **Voice style** (optional) — a voice prompt like "speak cheerfully", "whisper", "dramatic narrator". Default: none (model default)
- **Mode** (optional) — `voice` (default), `clone`, or `design`
- **Volume** (optional) — 0-100, default: system default

If the text is missing or empty, ask the user what they want said.

### Step 2: Generate Speech

Run the Qwen3-TTS tool to generate the audio file:

```bash
npx tsx tools/qwen3-tts.ts -t "<text>" -m voice -o "say-<timestamp>.wav" -f "public/audio"
```

If a voice style was specified, add the `-v` flag:

```bash
npx tsx tools/qwen3-tts.ts -t "<text>" -m voice -v "<voice style>" -o "say-<timestamp>.wav" -f "public/audio"
```

For the timestamp, use the current unix timestamp or a short identifier to avoid filename collisions.

Use a timeout of 120 seconds since the Replicate API may take time to process.

### Step 3: Play the Audio

Once the audio file is generated, immediately play it using the play-audio tool:

```bash
npx tsx tools/play-audio.ts <output-file-path>
```

If a volume was specified:

```bash
npx tsx tools/play-audio.ts <output-file-path> -v <volume>
```

### Step 4: Report Result

Tell the user:
- What text was spoken
- The voice style used (if any)
- The file path of the saved audio in case they want to reuse it

### Error Handling

- If TTS generation fails, report the error and suggest checking the `REPLICATE_API_TOKEN` in `.env.local`
- If audio playback fails, still report the saved file path so the user can play it manually
- If the text is very long (over 500 characters), warn the user that generation may be slow but proceed anyway
