#!/usr/bin/env python3
"""
Gemini - Python wrapper that proxies to the Node CLI (npm run gemini).

This aligns the Python entrypoint with the available Node implementation.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Interact with Google's Gemini API for text generation, chat, and multimodal tasks"
    )

    parser.add_argument("--prompt", type=str, required=True, help="Text prompt or question for the model")
    parser.add_argument("--model", type=str, default="gemini-2.0-flash-001", help="Model to use")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature (0.0-1.0)")
    parser.add_argument("--max-tokens", type=int, default=2048, help="Maximum tokens to generate")
    parser.add_argument("--image", type=str, help="Path to image file for vision tasks")
    parser.add_argument("--chat-history", type=str, help="Path to JSON file containing chat history")
    parser.add_argument("--stream", action="store_true", help="Stream the response")
    parser.add_argument("--safety-settings", type=str, help="JSON string for safety thresholds")
    parser.add_argument("--schema", type=str, help="JSON schema for structured output")
    parser.add_argument("--mime-type", type=str, help="MIME type for file inputs", default="auto")
    parser.add_argument("--url", type=str, help="URL to a document to analyze")
    parser.add_argument("--json", type=str, help="Structured JSON type (recipes|tasks|products|custom)")
    parser.add_argument("--ground", action="store_true", help="Enable Google Search grounding")
    parser.add_argument("--show-search-data", action="store_true", help="Show grounding sources")
    return parser


def main() -> int:
    parser = setup_parser()
    args = parser.parse_args()

    # Build npm command
    cmd = [
        "npm",
        "run",
        "gemini",
        "--",
        "--prompt",
        args.prompt,
        "--model",
        args.model,
        "--temperature",
        str(args.temperature),
        "--max-tokens",
        str(args.max_tokens),
    ]

    # Optional flags
    if args.image:
        cmd.extend(["--image", args.image])
    if args.chat_history:
        cmd.extend(["--chat-history", args.chat_history])
    if args.stream:
        cmd.append("--stream")
    if args.safety_settings:
        cmd.extend(["--safety-settings", args.safety_settings])
    if args.schema:
        cmd.extend(["--schema", args.schema])
    if args.mime_type:
        cmd.extend(["--mime-type", args.mime_type])
    if args.url:
        cmd.extend(["--url", args.url])
    if args.json:
        cmd.extend(["--json", args.json])
    if args.ground:
        cmd.append("--ground")
    if args.show_search_data:
        cmd.append("--show-search-data")

    # Execute and stream output
    try:
        proc = subprocess.run(cmd, check=False)
        return proc.returncode
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())