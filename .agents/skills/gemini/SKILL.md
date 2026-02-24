---
name: gemini
description: Use for text generation, chat, multimodal tasks (vision, document analysis), structured JSON output, and grounded Google Search via Google Gemini API. Do NOT use for image generation — use gemini-image or openai-image instead.
---

## Command
`npm run gemini -- [options]`

## Options
| Flag | Required | Description |
|------|----------|-------------|
| --prompt | Yes | Text prompt or question for the model |
| --model | No | Model: `gemini-2.0-flash` (default), `gemini-2.5-pro-exp-03-25` |
| --temperature | No | Sampling temperature 0.0–1.0 (default: 0.7) |
| --max-tokens | No | Maximum tokens to generate (default: 2048) |
| --image | No | Path to image file for vision tasks |
| --file | No | Path to local file (PDF, DOCX, TXT, etc.) for document analysis |
| --url | No | URL to a document to analyze (PDF, DOCX, TXT, etc.) |
| --mime-type | No | MIME type of the file (default: auto-detected) |
| --chat-history | No | Path to JSON file containing chat history |
| --stream | No | Stream the response (default: false) |
| --safety-settings | No | JSON string of safety threshold configurations |
| --schema | No | JSON schema for structured output |
| --json | No | Return structured JSON. Types: recipes, tasks, products, custom |
| --ground | No | Enable Google Search grounding for real-time info |
| --show-search-data | No | Show search entries used for grounding |

## Requirements
- `GOOGLE_AI_STUDIO_KEY` or `GEMINI_API_KEY` in `.env.local`

## Examples
```bash
# Simple text prompt
npm run gemini -- --prompt "What is the capital of France?"

# Vision: analyze an image
npm run gemini -- --prompt "Describe this image" --image photo.jpg

# Document analysis from URL
npm run gemini -- --prompt "Summarize in 5 key points" --url "https://example.com/doc.pdf"

# Local file analysis
npm run gemini -- --prompt "What is this about?" --file docs/report.pdf

# Grounded search (real-time information)
npm run gemini -- --prompt "Next solar eclipse in North America?" --ground --show-search-data

# Structured JSON output (predefined schema)
npm run gemini -- --prompt "List 3 cookie recipes" --json recipes

# Structured JSON output (custom schema)
npm run gemini -- --prompt "List 3 languages" --json custom --schema '{"type":"array","items":{"type":"object","properties":{"language":{"type":"string"},"useCases":{"type":"array","items":{"type":"string"}}},"required":["language","useCases"]}}'
```
