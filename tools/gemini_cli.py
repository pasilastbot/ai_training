#!/usr/bin/env python3
"""
Gemini CLI Tool - Interact with Google's Gemini API from the command line

This tool allows you to send prompts to Google's Gemini AI models and
receive responses directly in your terminal.

Usage:
  python gemini_cli.py --prompt "Your prompt here" 
                        [--model MODEL] 
                        [--temperature TEMP] 
                        [--max-tokens MAX_TOKENS]
                        [--image IMAGE_PATH]
                        [--chat-history HISTORY_FILE]
                        [--stream]
                        [--safety-settings SAFETY_JSON]
                        [--schema SCHEMA_JSON]
"""

import os
import sys
import json
import argparse
from typing import Optional, Dict, Any, List
import google.generativeai as genai

def setup_parser() -> argparse.ArgumentParser:
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Interact with Google's Gemini API from the command line."
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
        help="Model to use (default: gemini-2.0-flash-001)"
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
        help="Stream the response"
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

def load_api_key() -> str:
    """Load Gemini API key from environment variables."""
    # Try to get the key from GOOGLE_AI_STUDIO_KEY first
    api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY")
    
    # If not found, try GOOGLE_API_KEY (used elsewhere in the project)
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY")
    
    # Check for demo mode
    if api_key == "DEMO_MODE":
        return "DEMO_MODE"
    
    if not api_key:
        print("Error: API key not found.")
        print("Please set your Gemini API key with either:")
        print("export GOOGLE_AI_STUDIO_KEY='your-api-key'")
        print("or")
        print("export GOOGLE_API_KEY='your-api-key'")
        print("\nOr use demo mode: export GOOGLE_API_KEY=DEMO_MODE")
        sys.exit(1)
    
    return api_key

def load_image(image_path: str) -> Optional[Any]:
    """Load image from file path."""
    try:
        from PIL import Image
        img = Image.open(image_path)
        return img
    except ImportError:
        print("Error: PIL module not installed. Install with 'pip install pillow'")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading image: {e}")
        sys.exit(1)

def load_chat_history(history_path: str) -> List[Dict[str, str]]:
    """Load chat history from JSON file."""
    try:
        with open(history_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading chat history: {e}")
        sys.exit(1)

def parse_json_arg(json_str: str) -> Dict[str, Any]:
    """Parse JSON string into dict."""
    try:
        return json.loads(json_str)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)

def setup_generation_config(args: argparse.Namespace) -> Dict[str, Any]:
    """Set up generation configuration."""
    config = {
        "temperature": args.temperature,
        "max_output_tokens": args.max_tokens,
    }
    
    if args.safety_settings:
        config["safety_settings"] = parse_json_arg(args.safety_settings)
    
    return config

def handle_streaming_response(response):
    """Process streaming response."""
    for chunk in response:
        print(chunk.text, end="", flush=True)
    print()  # Add newline at the end

def handle_regular_response(response):
    """Process regular (non-streaming) response."""
    print(response.text)

def main():
    """Main function to process arguments and call Gemini API."""
    parser = setup_parser()
    args = parser.parse_args()
    
    # Load and configure API key
    api_key = load_api_key()
    
    # Check for demo mode
    if api_key == "DEMO_MODE":
        print(f"[DEMO MODE] Using model: {args.model}, temperature: {args.temperature}")
        print(f"[DEMO MODE] Prompt: {args.prompt}")
        if args.image:
            print(f"[DEMO MODE] Including image: {args.image}")
        if args.stream:
            print("[DEMO MODE] Streaming response...")
            
        print("\n--- Simulated Response ---")
        print("This is a demonstration response from the Gemini CLI.")
        print("In actual use, this would be a response from the Gemini API.")
        print("To use the real API, set a valid API key in the environment variables.")
        return
    
    genai.configure(api_key=api_key)
    
    # Set up generation config
    generation_config = setup_generation_config(args)
    
    # Prepare model
    model = genai.GenerativeModel(
        model_name=args.model,
        generation_config=generation_config
    )
    
    # Handle structured output if schema provided
    if args.schema:
        schema = parse_json_arg(args.schema)
        model = model.with_structured_output(schema)
    
    # Process based on input types and options
    try:
        if args.image:
            # Handle multimodal (text + image) request
            image = load_image(args.image)
            
            if args.stream:
                response = model.generate_content([args.prompt, image], stream=True)
                handle_streaming_response(response)
            else:
                response = model.generate_content([args.prompt, image])
                handle_regular_response(response)
                
        elif args.chat_history:
            # Handle chat request with history
            history = load_chat_history(args.chat_history)
            chat = model.start_chat(history=history)
            
            if args.stream:
                response = chat.send_message(args.prompt, stream=True)
                handle_streaming_response(response)
            else:
                response = chat.send_message(args.prompt)
                handle_regular_response(response)
                
        else:
            # Handle simple text request
            if args.stream:
                response = model.generate_content(args.prompt, stream=True)
                handle_streaming_response(response)
            else:
                response = model.generate_content(args.prompt)
                handle_regular_response(response)
                
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 