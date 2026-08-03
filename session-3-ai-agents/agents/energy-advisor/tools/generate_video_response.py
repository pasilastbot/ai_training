#!/usr/bin/env python3
"""
Generate Video Response Tool

Generates a talking-head video response using the video-avatar skill.
Uses the energy advisor's avatar image to create personalized video answers.

Usage:
    python generate_video_response.py --script "Hello, I'm your energy advisor!"
    python generate_video_response.py --script "Your district heating can save 20%." --voice "Puck (Male)"
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

AGENT_DIR = Path(__file__).parent.parent
PROJECT_ROOT = AGENT_DIR.parent.parent.parent
AVATAR_IMAGE = AGENT_DIR / "memory" / "data" / "advisor-avatar.png"
OUTPUT_DIR = AGENT_DIR / "memory" / "data" / "videos"


def generate_video_response(
    script: str,
    voice: str = "Puck (Male)",
    language: str = "English (US)",
    voice_prompt: str = "speak in a friendly, professional tone",
    resolution: str = "720p",
    output_name: str = None
) -> dict:
    """
    Generate a video response with the energy advisor avatar.
    
    Args:
        script: Text for the avatar to speak
        voice: Voice to use (default: Puck for male voice)
        language: Language for TTS
        voice_prompt: Speaking style instructions
        resolution: Video resolution (720p or 1080p)
        output_name: Optional custom output filename
    
    Returns:
        dict with video path and status
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not AVATAR_IMAGE.exists():
        return {
            "status": "error",
            "error": f"Avatar image not found: {AVATAR_IMAGE}"
        }
    
    if not output_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"energy-advisor-{timestamp}.mp4"
    
    cmd = [
        "npm", "run", "video-avatar", "--",
        "-i", str(AVATAR_IMAGE),
        "-s", script,
        "-V", voice,
        "-l", language,
        "-p", voice_prompt,
        "-r", resolution,
        "-o", output_name,
        "-f", str(OUTPUT_DIR)
    ]
    
    try:
        print(f"[VideoAvatar] Generating video with script: {script[:100]}...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=300  # 5 minute timeout for video generation
        )
        
        if result.returncode == 0:
            video_path = OUTPUT_DIR / output_name
            
            return {
                "status": "success",
                "video_path": str(video_path),
                "script": script,
                "voice": voice,
                "output": result.stdout.strip()
            }
        else:
            return {
                "status": "error",
                "error": result.stderr.strip() or result.stdout.strip() or "Video generation failed"
            }
    
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": "Video generation timed out (>5 minutes)"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def generate_greeting_video(customer_name: str = None) -> dict:
    """Generate a greeting video for a customer."""
    if customer_name:
        script = f"Hello {customer_name}! I'm your Energy Advisor from Leanheat. I'm here to help you optimize your building's heating and reduce energy costs. What would you like to know about energy savings today?"
    else:
        script = "Hello! I'm your Energy Advisor from Leanheat. I'm here to help you optimize your building's heating and reduce energy costs. Ask me anything about energy savings, AI-powered heating optimization, or demand response!"
    
    return generate_video_response(
        script=script,
        voice_prompt="speak warmly and professionally, like greeting a valued customer"
    )


def generate_answer_video(question: str, answer: str) -> dict:
    """Generate a video response to a customer question."""
    full_script = f"{answer}"
    
    return generate_video_response(
        script=full_script,
        voice_prompt="speak clearly and helpfully, explaining technical concepts in an accessible way"
    )


def main():
    parser = argparse.ArgumentParser(description="Generate Energy Advisor Video Response")
    parser.add_argument("--script", "-s", help="Script for the avatar to speak")
    parser.add_argument("--voice", "-V", default="Puck (Male)", help="Voice to use")
    parser.add_argument("--language", "-l", default="English (US)", help="Language")
    parser.add_argument("--voice-prompt", "-p", default="speak in a friendly, professional tone", 
                        help="Speaking style instructions")
    parser.add_argument("--resolution", "-r", choices=["720p", "1080p"], default="720p", 
                        help="Video resolution")
    parser.add_argument("--output", "-o", help="Output filename")
    parser.add_argument("--greeting", action="store_true", help="Generate greeting video")
    parser.add_argument("--customer-name", help="Customer name for personalized greeting")
    
    args = parser.parse_args()
    
    if args.greeting:
        result = generate_greeting_video(args.customer_name)
    elif args.script:
        result = generate_video_response(
            script=args.script,
            voice=args.voice,
            language=args.language,
            voice_prompt=args.voice_prompt,
            resolution=args.resolution,
            output_name=args.output
        )
    else:
        parser.print_help()
        return
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
