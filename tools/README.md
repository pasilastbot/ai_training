# Command Line Tools

This directory contains command-line tools for the project.

## Gemini CLI

The `gemini` tool allows you to interact with Google's Gemini API for text generation, chat, and multimodal tasks with advanced configuration options.

### Prerequisites

- Python 3.7+
- `google-generativeai` Python package
- A Google AI Studio API key (set as `GOOGLE_API_KEY` environment variable)

### Usage

```bash
./tools/gemini --prompt "Your prompt here" [options]
```

### Options

- `--prompt`: Text prompt or question for the model (required)
- `--model`: Model to use (default: "gemini-2.0-flash-001")
  - Available models: "gemini-2.0-flash-001", "gemini-2.0-flash-001", "Gemini-Exp-1206", "Gemini-2.0-Flash-Thinking-Exp-1219"
- `--temperature`: Sampling temperature between 0.0 and 1.0 (default: 0.7)
- `--max-tokens`: Maximum number of tokens to generate (default: 2048)
- `--image`: Path to image file for vision tasks
- `--chat-history`: Path to JSON file containing chat history
- `--stream`: Stream the response (default: false)
- `--safety-settings`: JSON string of safety threshold configurations
- `--schema`: JSON schema for structured output

### Examples

Simple text generation:
```bash
./tools/gemini --prompt "Explain quantum computing in simple terms"
```

Using a specific model with custom temperature:
```bash
./tools/gemini --prompt "Write a short poem about AI" --model "gemini-2.0-pro" --temperature 0.9
```

Vision task with an image:
```bash
./tools/gemini --prompt "What's in this image?" --image "path/to/image.jpg"
```

Streaming response:
```bash
./tools/gemini --prompt "Tell me a long story" --stream
```

Structured output with schema:
```bash
./tools/gemini --prompt "List 3 European capitals with their populations" --schema '{"type":"object","properties":{"cities":{"type":"array","items":{"type":"object","properties":{"name":{"type":"string"},"population":{"type":"number"}}}}}}'
```

## Gemini Image Generator

The `gemini-image` tool allows you to generate images using Google's Gemini API and Imagen models.

### Prerequisites

- Python 3.7+
- `google-generativeai` Python package
- `pillow` Python package
- A Google AI Studio API key (set as `GOOGLE_API_KEY` environment variable)

### Usage

```bash
./tools/gemini-image --prompt "Your image description" [options]
```

### Options

- `--prompt`: Text prompt describing the image to generate (required)
- `--model`: Model to use for image generation (default: "gemini-2.0-flash-exp-image-generation")
  - Available models: "gemini-2.0-flash-exp-image-generation", "imagen-3.0-generate-002"
- `--output`: Path to save the generated image(s) (default: "./generated_image.png")
- `--count`: Number of images to generate (1-4, only for Imagen model, default: 1)
- `--aspect-ratio`: Aspect ratio for generated image (only for Imagen model, default: "1:1")
  - Available ratios: "1:1", "3:4", "4:3", "9:16", "16:9"
- `--allow-persons`: Person generation policy (only for Imagen model, default: "ALLOW_ADULT")
  - Available options: "DONT_ALLOW", "ALLOW_ADULT"
- `--input-image`: Path to input image for editing (only for Gemini model)
- `--verbose`: Enable verbose output with more details about the API process

### Examples

Generate an image with Gemini:
```bash
./tools/gemini-image --prompt "A futuristic city with flying cars and tall skyscrapers"
```

Generate multiple images with Imagen:
```bash
./tools/gemini-image --prompt "A serene beach at sunset" --model imagen-3.0-generate-002 --count 3 --aspect-ratio 16:9
```

Edit an existing image with Gemini:
```bash
./tools/gemini-image --prompt "Add a dragon flying in the sky" --input-image "path/to/landscape.jpg" --output "modified_landscape.png"
```

Generate with verbose output:
```bash
./tools/gemini-image --prompt "A majestic mountain landscape" --verbose
``` 