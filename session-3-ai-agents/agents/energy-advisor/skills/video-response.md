---
name: video-response
description: Generate talking-head video responses with the energy advisor avatar
tools: [generate_video_response]
---

## Purpose

Generate video responses using the energy advisor avatar to provide personalized, engaging explanations about energy optimization topics.

## When to Use

- User explicitly requests a video response
- Explaining complex energy concepts
- Providing personalized greetings
- Delivering important recommendations
- Creating educational content

## Tools Required

| Tool | Purpose |
|------|---------|
| `tools/generate_video_response.py` | Generate avatar video with TTS |

## Prerequisites

- `REPLICATE_API_TOKEN` in environment
- Avatar image at `memory/data/advisor-avatar.png`

## Example

```bash
# Generate a video response
python tools/generate_video_response.py --script "Hello! Let me explain how Leanheat saves energy."

# Generate greeting video
python tools/generate_video_response.py --greeting --customer-name "John"

# Custom voice and language
python tools/generate_video_response.py \
  --script "Your district heating can be optimized" \
  --voice "Zephyr (Female)" \
  --language "Finnish"
```

## Available Voices

**Male:** Puck (default), Charon, Fenrir, Orus, Enceladus, Iapetus, Umbriel

**Female:** Zephyr, Kore, Leda, Aoede, Callirrhoe, Autonoe, Despina

## Languages

English (US), English (UK), Finnish, Swedish, German, French, Spanish

## Pricing

- 720p: $0.025 per second
- 1080p: $0.045 per second

Example: 10-second video at 720p = $0.25

## Tips

- Keep scripts concise (2-4 sentences optimal)
- Use clear, simple language
- Include greeting for personalization
- Store video path in database for later retrieval
