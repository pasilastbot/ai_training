#!/usr/bin/env python3
"""
Gemini Image Generator - Generate images using Google's Gemini API

This tool allows you to generate images using either Gemini 2.0 Flash or Imagen 3
models directly from the command line.

Usage:
  python gemini_image.py --prompt "Your prompt here" 
                         [--model MODEL]
                         [--output OUTPUT_PATH]
                         [--count COUNT]
                         [--aspect-ratio RATIO]
                         [--allow-persons MODE]
"""

import os
import sys
import json
import argparse
import base64
from typing import Optional, Dict, Any, List
from io import BytesIO
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

def setup_parser() -> argparse.ArgumentParser:
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate images using Google's Gemini API models"
    )
    
    parser.add_argument(
        "--prompt", 
        type=str, 
        help="Text prompt describing the image to generate", 
        required=True
    )
    
    parser.add_argument(
        "--model", 
        type=str, 
        default="gemini-2.0-flash-exp-image-generation", 
        choices=["gemini-2.0-flash-exp-image-generation", "imagen-3.0-generate-002"],
        help="Model to use for image generation (default: gemini-2.0-flash-exp-image-generation)"
    )
    
    parser.add_argument(
        "--output", 
        type=str, 
        default="./generated_image.png", 
        help="Path to save the generated image(s) (default: ./generated_image.png)"
    )
    
    parser.add_argument(
        "--count", 
        type=int, 
        default=1, 
        choices=range(1, 5),
        help="Number of images to generate (1-4, only for Imagen model, default: 1)"
    )
    
    parser.add_argument(
        "--aspect-ratio", 
        type=str, 
        default="1:1", 
        choices=["1:1", "3:4", "4:3", "9:16", "16:9"],
        help="Aspect ratio for generated image (only for Imagen model, default: 1:1)"
    )
    
    parser.add_argument(
        "--allow-persons", 
        type=str, 
        default="ALLOW_ADULT", 
        choices=["DONT_ALLOW", "ALLOW_ADULT"],
        help="Person generation policy (only for Imagen model, default: ALLOW_ADULT)"
    )
    
    parser.add_argument(
        "--input-image", 
        type=str, 
        help="Path to input image for editing (only for Gemini model)"
    )
    
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Enable verbose output with more details about the API process"
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

def load_image(image_path: str) -> Optional[Image.Image]:
    """Load image from file path."""
    try:
        img = Image.open(image_path)
        return img
    except Exception as e:
        print(f"Error loading image: {e}")
        sys.exit(1)

def get_base64_from_image(image_path: str) -> Optional[str]:
    """Convert image to base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error converting image to base64: {e}")
        sys.exit(1)

def generate_with_gemini(genai_module, prompt: str, input_image_path: Optional[str] = None, verbose: bool = False) -> List[Image.Image]:
    """Generate image using Gemini 2.0 Flash Exp model."""
    try:
        if verbose:
            print(f"Generating image with Gemini 2.0 Flash Exp model")
            print(f"Prompt: {prompt}")
            if input_image_path:
                print(f"Input image: {input_image_path}")
        
        # Create client
        if verbose:
            print("Creating Gemini client...")
        
        client = genai_module.Client()
        
        # Prepare contents based on whether we have an input image
        if input_image_path:
            if verbose:
                print("Mode: Image editing")
                
            # Load the image
            image = load_image(input_image_path)
            
            # Format with text and image
            contents = [prompt, image]
        else:
            if verbose:
                print("Mode: Text-to-image generation")
                
            # Just use the text prompt
            contents = prompt
        
        if verbose:
            print("Sending request to Gemini API with response_modalities...")
        
        # Generate content with response_modalities
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=['Text', 'Image']
            )
        )
        
        if verbose:
            print("Processing response...")
        
        # Process response
        images = []
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(f"Model response: {part.text}")
            elif part.inline_data is not None:
                # Extract and process the image data
                if verbose:
                    print("Received image data")
                    
                image = Image.open(BytesIO(part.inline_data.data))
                
                if verbose:
                    print(f"Image dimensions: {image.width}x{image.height}")
                    
                images.append(image)
        
        if verbose:
            print(f"Generated {len(images)} images")
        
        return images
    
    except Exception as e:
        print(f"Error generating image with Gemini: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def generate_with_imagen(genai_module, prompt: str, count: int, aspect_ratio: str, allow_persons: str, verbose: bool = False) -> List[Image.Image]:
    """Generate image using Imagen 3 model."""
    try:
        if verbose:
            print(f"Generating {count} image(s) with Imagen 3 model")
            print(f"Prompt: {prompt}")
            print(f"Aspect ratio: {aspect_ratio}")
            print(f"Person generation policy: {allow_persons}")
        
        # Create client with API key
        if verbose:
            print("Creating Imagen client...")
        
        api_key = load_api_key()
        client = genai_module.Client(api_key=api_key)
        
        if verbose:
            print("Setting up config for Imagen generation...")
        
        # Configure the image generation parameters
        config = types.GenerateImagesConfig(
            number_of_images=count,
        )
        
        # Add aspect ratio if specified (not in the minimal example)
        if aspect_ratio:
            config.aspect_ratio = aspect_ratio
            
        # Add person generation if specified (not in the minimal example)
        if allow_persons:
            config.person_generation = allow_persons
        
        if verbose:
            print("Sending request to Imagen API...")
        
        try:
            # Generate images using the documented approach
            response = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=prompt,
                config=config
            )
        except genai_module.errors.ClientError as e:
            if "Imagen API is only accessible to billed users" in str(e):
                print("\n⚠️ ERROR: Imagen API is only accessible to billed users.")
                print("You need a Google Cloud account with billing enabled to use Imagen.")
                print("Please see the Google AI documentation for more information.")
                print("In the meantime, you can use the Gemini model instead:")
                print("  ./tools/gemini-image --prompt \"Your prompt\" --model gemini-2.0-flash-exp-image-generation\n")
                sys.exit(1)
            else:
                raise
        
        if verbose:
            print("Processing response...")
        
        # Process response
        images = []
        for generated_image in response.generated_images:
            if verbose:
                print("Received image data")
                
            image = Image.open(BytesIO(generated_image.image.image_bytes))
            
            if verbose:
                print(f"Image dimensions: {image.width}x{image.height}")
                
            images.append(image)
        
        if verbose:
            print(f"Generated {len(images)} images")
        
        return images
    
    except Exception as e:
        print(f"Error generating image with Imagen: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def save_images(images: List[Image.Image], output_path: str, verbose: bool = False) -> None:
    """Save generated images to disk."""
    if not images:
        print("No images were generated.")
        return
    
    if verbose:
        print(f"Preparing to save {len(images)} images")
    
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        if verbose:
            print(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir)
    
    base_path, ext = os.path.splitext(output_path)
    if not ext:
        ext = ".png"
        if verbose:
            print("No file extension specified, using .png")
    
    for i, image in enumerate(images):
        # If multiple images, add index to filename
        if len(images) > 1:
            path = f"{base_path}_{i+1}{ext}"
        else:
            path = f"{base_path}{ext}"
        
        if verbose:
            print(f"Saving image {i+1}/{len(images)} to {path}")
        
        image.save(path)
        print(f"Image saved to: {path}")

def main():
    """Main function to process arguments and generate images."""
    parser = setup_parser()
    args = parser.parse_args()
    
    # Load API key
    api_key = load_api_key()
    
    # Check for demo mode
    if api_key == "DEMO_MODE":
        print(f"[DEMO MODE] Using model: {args.model}")
        print(f"[DEMO MODE] Prompt: {args.prompt}")
        if args.model == "imagen-3.0-generate-002":
            print(f"[DEMO MODE] Count: {args.count}, Aspect ratio: {args.aspect_ratio}")
        if args.input_image:
            print(f"[DEMO MODE] Including input image: {args.input_image}")
            
        print("\n--- Simulated Response ---")
        print("In actual use, this would generate and save images based on your prompt.")
        print("To use the real API, set a valid API key in the environment variables.")
        return
    
    # We don't need to configure since we're using the Client approach
    if args.verbose:
        print(f"API key loaded")
        print(f"Using model: {args.model}")
    
    # Generate images based on selected model
    if args.model == "gemini-2.0-flash-exp-image-generation":
        images = generate_with_gemini(genai, args.prompt, args.input_image, args.verbose)
    else:  # imagen-3.0-generate-002
        images = generate_with_imagen(genai, args.prompt, args.count, args.aspect_ratio, args.allow_persons, args.verbose)
    
    # Save generated images
    save_images(images, args.output, args.verbose)
    
    if args.verbose:
        print("Image generation completed successfully")

if __name__ == "__main__":
    main() 