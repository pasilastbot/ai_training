#!/usr/bin/env python3
"""
Gemini - Command line tool for interacting with Google's Gemini API

This is a simple wrapper around gemini_cli.py that matches the interface 
described in the .cursorrules file.
"""

import os
import sys
import argparse
from pathlib import Path

# Get the absolute path to the directory containing this script
SCRIPT_DIR = Path(__file__).parent.absolute()
GEMINI_CLI = SCRIPT_DIR / "gemini_cli.py"

def setup_parser():
    """Set up command line argument parser according to .cursorrules specification."""
    parser = argparse.ArgumentParser(
        description="Interact with Google's Gemini API for text generation, chat, and multimodal tasks"
    )
    
    parser.add_argument(
        "--prompt", 
        type=str, 
        help="Text prompt or question for the model",
        required=True
    )
    
    parser.add_argument(
        "--model", 
        type=str, 
        default="gemini-2.0-flash-001",
        help="Model to use: 'gemini-2.0-flash-001' (default), 'gemini-2.0-flash-001', 'Gemini-Exp-1206', 'Gemini-2.0-Flash-Thinking-Exp-1219'"
    )
    
    parser.add_argument(
        "--temperature", 
        type=float, 
        default=0.7,
        help="Sampling temperature between 0.0 and 1.0 (default: 0.7)"
    )
    
    parser.add_argument(
        "--max-tokens", 
        type=int, 
        default=2048,
        help="Maximum number of tokens to generate (default: 2048)"
    )
    
    parser.add_argument(
        "--image", 
        type=str, 
        help="Path to image file for vision tasks"
    )
    
    parser.add_argument(
        "--chat-history", 
        type=str, 
        help="Path to JSON file containing chat history"
    )
    
    parser.add_argument(
        "--stream", 
        action="store_true", 
        help="Stream the response (default: false)"
    )
    
    parser.add_argument(
        "--safety-settings", 
        type=str, 
        help="JSON string of safety threshold configurations"
    )
    
    parser.add_argument(
        "--schema", 
        type=str, 
        help="JSON schema for structured output"
    )
    
    return parser

def main():
    # Parse arguments
    parser = setup_parser()
    args = parser.parse_args()
    
    # Build command to call gemini_cli.py
    cmd = [str(GEMINI_CLI)]
    
    # Add all arguments
    if args.prompt:
        cmd.extend(["--prompt", args.prompt])
    
    if args.model:
        cmd.extend(["--model", args.model])
    
    if args.temperature is not None:
        cmd.extend(["--temperature", str(args.temperature)])
    
    if args.max_tokens is not None:
        cmd.extend(["--max-tokens", str(args.max_tokens)])
    
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
    
    # Execute gemini_cli.py with arguments
    os.execv(sys.executable, [sys.executable] + cmd)

if __name__ == "__main__":
    main() 