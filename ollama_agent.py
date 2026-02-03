#!/usr/bin/env python3
"""
Ollama Agent CLI

A minimal command-line example showing how to call the Ollama API with
- CLI function/tool support (enabled by default)
- Interactive chat mode

Usage examples:
  # Interactive chat
  python ollama_agent.py --chat

  # Single-turn
  python ollama_agent.py "What is the capital of France?"

  # Specify model
  python ollama_agent.py --model glm4:9b "Tell me a joke"
"""

import os
import sys
import argparse
import json
import re
import subprocess
from datetime import datetime
from typing import List, Optional, Dict, Tuple, Any
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

import ollama

DEFAULT_MODEL = "glm-4.7-flash"


def load_env_files() -> None:
    """Load simple KEY=VALUE pairs from .env.local and .env if present.
    Existing environment variables are not overridden.
    """
    for filename in (".env.local", ".env"):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
        except FileNotFoundError:
            continue
        except Exception:
            # Fail-safe: ignore malformed lines/files silently
            continue


# -------------------- CLI FUNCTION DECLARATIONS --------------------

def build_cli_function_declarations() -> List[Dict[str, Any]]:
    """Build function_declarations for project CLI tools based on command_line_tools.mdc.
    Uses OpenAI-style function format that Ollama supports.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "html_to_md",
                "description": "Scrape a webpage and convert HTML to Markdown via npm script html-to-md",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to scrape"},
                        "output": {"type": "string", "description": "Output markdown file path"},
                        "selector": {"type": "string", "description": "CSS selector to target content"},
                    },
                    "required": ["url"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "image_optimizer",
                "description": "Optimize images using Sharp and optional background removal via npm script image-optimizer",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "Path to input image"},
                        "output": {"type": "string", "description": "Path to output image"},
                        "remove_bg": {"type": "boolean", "description": "Remove background using AI"},
                        "resize": {"type": "string", "description": "Resize in WIDTHxHEIGHT format (e.g., 800x600)"},
                        "format": {"type": "string", "enum": ["png", "jpeg", "webp"], "description": "Output format"},
                        "quality": {"type": "integer", "description": "Output quality (1-100)"},
                    },
                    "required": ["input", "output"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "download_file",
                "description": "Download a file from URL via npm script download-file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL of the file to download"},
                        "output": {"type": "string", "description": "Complete output path including filename"},
                        "folder": {"type": "string", "description": "Output folder path"},
                        "filename": {"type": "string", "description": "Output filename"},
                    },
                    "required": ["url"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "openai_image_generate",
                "description": "Generate image using OpenAI via npm script openai-image (generate)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Text prompt for image generation"},
                        "model": {"type": "string", "enum": ["gpt-image-1", "dall-e-3"], "description": "Model to use"},
                        "output": {"type": "string", "description": "Output filename"},
                        "folder": {"type": "string", "description": "Output folder"},
                        "size": {"type": "string", "enum": ["1024x1024", "1792x1024", "1024x1792"], "description": "Image size"},
                        "quality": {"type": "string", "enum": ["standard", "hd"], "description": "Image quality"},
                        "number": {"type": "integer", "description": "Number of images (1-4)"},
                        "reference_image": {"type": "string", "description": "Reference image path"},
                        "creative": {"type": "string", "enum": ["standard", "vivid"], "description": "Creativity level"}
                    },
                    "required": ["prompt"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "openai_image_edit",
                "description": "Edit an image using OpenAI via npm script openai-image (edit)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_image": {"type": "string", "description": "Path to input image"},
                        "edit_prompt": {"type": "string", "description": "Edit instructions"},
                        "model": {"type": "string", "enum": ["gpt-image-1", "dall-e-3"], "description": "Model to use"},
                        "output": {"type": "string", "description": "Output filename"},
                        "folder": {"type": "string", "description": "Output folder"},
                        "size": {"type": "string", "enum": ["1024x1024", "1792x1024", "1024x1792"], "description": "Image size"},
                        "creative": {"type": "string", "enum": ["standard", "vivid"], "description": "Creativity level"}
                    },
                    "required": ["input_image", "edit_prompt"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "gemini_image_generate",
                "description": "Generate an image using Gemini or Imagen via npm script gemini-image (generate)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Text prompt for image generation"},
                        "model": {"type": "string", "enum": ["gemini-2.0", "imagen-3.0"], "description": "Model to use"},
                        "output": {"type": "string", "description": "Output filename"},
                        "folder": {"type": "string", "description": "Output folder"},
                        "num_outputs": {"type": "integer", "description": "Number of images (1-4)"},
                        "negative_prompt": {"type": "string", "description": "Negative prompt"},
                        "aspect_ratio": {"type": "string", "enum": ["1:1", "16:9", "9:16", "4:3", "3:4"], "description": "Aspect ratio"},
                    },
                    "required": ["prompt"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "gemini_image_edit",
                "description": "Edit an existing image using Gemini via npm script gemini-image (edit)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_image": {"type": "string", "description": "Path to input image"},
                        "edit_prompt": {"type": "string", "description": "Edit instructions"},
                        "output": {"type": "string", "description": "Output filename"},
                        "folder": {"type": "string", "description": "Output folder"},
                    },
                    "required": ["input_image", "edit_prompt"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generate_video",
                "description": "Generate video via npm script generate-video (Replicate models)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Video description"},
                        "model": {"type": "string", "enum": ["kling-1.6", "kling-2.0", "minimax", "hunyuan", "mochi", "ltx"], "description": "Model to use"},
                        "duration": {"type": "integer", "description": "Duration in seconds"},
                        "image": {"type": "string", "description": "Input image path"},
                        "output": {"type": "string", "description": "Output filename"},
                        "folder": {"type": "string", "description": "Output folder"},
                        "image_prompt": {"type": "string", "description": "Image prompt for OpenAI"},
                        "openai_image_output": {"type": "string", "description": "OpenAI image output path"},
                        "aspect_ratio": {"type": "string", "description": "Aspect ratio"},
                    },
                    "required": ["prompt"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "remove_background_advanced",
                "description": "Remove background using advanced method via npm script remove-background-advanced",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input": {"type": "string", "description": "Input image path"},
                        "output": {"type": "string", "description": "Output image path"},
                        "tolerance": {"type": "integer", "description": "Color tolerance (0-255)"},
                    },
                    "required": ["input", "output"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "nano_banana_generate",
                "description": "Generate images using Gemini 2.5 Flash Image Preview model via npm script nano-banana",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Text prompt for image generation"},
                        "output": {"type": "string", "description": "Output filename"},
                        "folder": {"type": "string", "description": "Output folder path"},
                    },
                    "required": ["prompt"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "nano_banana_edit",
                "description": "Edit images using Gemini 2.5 Flash Image Preview model via npm script nano-banana",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Text prompt for image editing"},
                        "input_image": {"type": "string", "description": "Path to input image for editing"},
                        "output": {"type": "string", "description": "Output filename"},
                        "folder": {"type": "string", "description": "Output folder path"},
                    },
                    "required": ["prompt", "input_image"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "google_search",
                "description": "Perform Google search using Gemini's grounded search capability via npm script google-search",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "model": {"type": "string", "description": "Gemini model to use"},
                        "max_results": {"type": "integer", "description": "Maximum number of sources to show"},
                        "show_sources": {"type": "boolean", "description": "Show source URLs and titles"},
                        "format": {"type": "string", "enum": ["text", "json"], "description": "Output format"},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "datetime",
                "description": "Get current date and time in various formats via npm script datetime",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "format": {"type": "string", "enum": ["iso", "date", "time", "full", "short", "compact"], "description": "Output format"},
                        "timezone": {"type": "string", "description": "Timezone (e.g., America/New_York)"},
                        "utc": {"type": "boolean", "description": "Show UTC time"},
                        "timestamp": {"type": "boolean", "description": "Show Unix timestamp"},
                        "locale": {"type": "string", "description": "Locale for formatting"},
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "data_indexing",
                "description": "Index web content or files using Gemini for chunking and embeddings, store in ChromaDB via npm script data-indexing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL of webpage to index"},
                        "file": {"type": "string", "description": "Path to local file to index"},
                        "output": {"type": "string", "description": "Output file to save processed document JSON"},
                        "collection": {"type": "string", "description": "ChromaDB collection name"},
                        "model": {"type": "string", "description": "Gemini model for content processing"},
                        "embedding_model": {"type": "string", "description": "Gemini model for embeddings"},
                        "chroma_host": {"type": "string", "description": "ChromaDB host"},
                        "chroma_port": {"type": "integer", "description": "ChromaDB port"},
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "semantic_search",
                "description": "Search ChromaDB using Gemini embeddings for semantic similarity via npm script semantic-search",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query text"},
                        "collection": {"type": "string", "description": "ChromaDB collection name"},
                        "n_results": {"type": "integer", "description": "Number of results to return"},
                        "embedding_model": {"type": "string", "description": "Gemini model for embeddings"},
                        "format": {"type": "string", "enum": ["text", "json"], "description": "Output format"},
                        "chroma_host": {"type": "string", "description": "ChromaDB host"},
                        "chroma_port": {"type": "integer", "description": "ChromaDB port"},
                        "where_filter": {"type": "string", "description": "JSON filter for metadata"},
                        "min_distance": {"type": "number", "description": "Minimum distance threshold"},
                        "max_distance": {"type": "number", "description": "Maximum distance threshold"},
                    },
                    "required": ["query"],
                },
            },
        },
    ]


# -------------------- CLI EXECUTION --------------------

def _run_cmd(cmd: List[str]) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        return 1, "", f"Exception running command: {e}"


def execute_cli_function(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a known CLI function by assembling the correct npm command.
    Returns a JSON-serializable dict with results.
    """
    if name == "html_to_md":
        cmd = ["npm", "run", "html-to-md", "--", "--url", args.get("url", "")]
        if args.get("output"):
            cmd += ["--output", args["output"]]
        if args.get("selector"):
            cmd += ["--selector", args["selector"]]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "image_optimizer":
        cmd = ["npm", "run", "image-optimizer", "--", "-i", args.get("input", ""), "-o", args.get("output", "")]
        if args.get("remove_bg"):
            cmd += ["--remove-bg"]
        if args.get("resize"):
            cmd += ["--resize", str(args["resize"])]
        if args.get("format"):
            cmd += ["--format", str(args["format"])]
        if args.get("quality") is not None:
            cmd += ["--quality", str(args["quality"])]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "download_file":
        cmd = ["npm", "run", "download-file", "--", "--url", args.get("url", "")]
        if args.get("output"):
            cmd += ["--output", args["output"]]
        if args.get("folder"):
            cmd += ["--folder", args["folder"]]
        if args.get("filename"):
            cmd += ["--filename", args["filename"]]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "openai_image_generate":
        cmd = ["npm", "run", "openai-image", "--", "generate", "-p", args.get("prompt", "")]
        if args.get("model"):
            cmd += ["-m", args["model"]]
        if args.get("output"):
            cmd += ["-o", args["output"]]
        if args.get("folder"):
            cmd += ["-f", args["folder"]]
        if args.get("size"):
            cmd += ["-s", args["size"]]
        if args.get("quality"):
            cmd += ["-q", args["quality"]]
        if args.get("number") is not None:
            cmd += ["-n", str(args["number"])]
        if args.get("reference_image"):
            cmd += ["--reference-image", args["reference_image"]]
        if args.get("creative"):
            cmd += ["-c", args["creative"]]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "openai_image_edit":
        cmd = ["npm", "run", "openai-image", "--", "edit", "-i", args.get("input_image", ""), "-p", args.get("edit_prompt", "")]
        if args.get("model"):
            cmd += ["-m", args["model"]]
        if args.get("output"):
            cmd += ["-o", args["output"]]
        if args.get("folder"):
            cmd += ["-f", args["folder"]]
        if args.get("size"):
            cmd += ["-s", args["size"]]
        if args.get("creative"):
            cmd += ["-c", args["creative"]]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "gemini_image_generate":
        cmd = ["node", "tools/gemini-image-tool.js", "generate", "-p", args.get("prompt", "")]
        if args.get("model"):
            cmd += ["-m", args["model"]]
        if args.get("output"):
            cmd += ["-o", args["output"]]
        if args.get("folder"):
            cmd += ["-f", args["folder"]]
        if args.get("num_outputs") is not None:
            cmd += ["-n", str(args["num_outputs"])]
        if args.get("negative_prompt"):
            cmd += ["--negative-prompt", args["negative_prompt"]]
        if args.get("aspect_ratio"):
            cmd += ["--aspect-ratio", args["aspect_ratio"]]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "gemini_image_edit":
        cmd = ["node", "tools/gemini-image-tool.js", "edit", "-i", args.get("input_image", ""), "-p", args.get("edit_prompt", "")]
        if args.get("output"):
            cmd += ["-o", args["output"]]
        if args.get("folder"):
            cmd += ["-f", args["folder"]]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "generate_video":
        cmd = ["npm", "run", "generate-video", "--", "--prompt", args.get("prompt", "")]
        if args.get("model"):
            cmd += ["--model", args["model"]]
        if args.get("duration") is not None:
            cmd += ["--duration", str(args["duration"])]
        if args.get("image"):
            cmd += ["--image", args["image"]]
        if args.get("output"):
            cmd += ["--output", args["output"]]
        if args.get("folder"):
            cmd += ["--folder", args["folder"]]
        if args.get("image_prompt"):
            cmd += ["--image-prompt", args["image_prompt"]]
        if args.get("openai_image_output"):
            cmd += ["--openai-image-output", args["openai_image_output"]]
        if args.get("aspect_ratio"):
            cmd += ["--aspect-ratio", args["aspect_ratio"]]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "remove_background_advanced":
        cmd = ["npm", "run", "remove-background-advanced", "--", "--input", args.get("input", ""), "--output", args.get("output", "")]
        if args.get("tolerance") is not None:
            cmd += ["--tolerance", str(args["tolerance"])]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "nano_banana_generate":
        cmd = ["npm", "run", "nano-banana", "--", "-p", args.get("prompt", "")]
        if args.get("output"):
            cmd += ["-o", args["output"]]
        if args.get("folder"):
            cmd += ["-f", args["folder"]]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "nano_banana_edit":
        cmd = ["npm", "run", "nano-banana", "--", "-p", args.get("prompt", ""), "-i", args.get("input_image", "")]
        if args.get("output"):
            cmd += ["-o", args["output"]]
        if args.get("folder"):
            cmd += ["-f", args["folder"]]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "google_search":
        cmd = ["npm", "run", "google-search", "--", "-q", args.get("query", "")]
        if args.get("model"):
            cmd += ["-m", args["model"]]
        if args.get("max_results") is not None:
            cmd += ["-n", str(args["max_results"])]
        if args.get("show_sources"):
            cmd += ["-s"]
        if args.get("format"):
            cmd += ["-f", args["format"]]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "datetime":
        cmd = ["npm", "run", "datetime", "--"]
        if args.get("format"):
            cmd += ["--format", args["format"]]
        if args.get("timezone"):
            cmd += ["--timezone", args["timezone"]]
        if args.get("utc"):
            cmd += ["--utc"]
        if args.get("timestamp"):
            cmd += ["--timestamp"]
        if args.get("locale"):
            cmd += ["--locale", args["locale"]]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "data_indexing":
        cmd = ["npm", "run", "data-indexing", "--"]
        if args.get("url"):
            cmd += ["--url", args["url"]]
        if args.get("file"):
            cmd += ["--file", args["file"]]
        if args.get("output"):
            cmd += ["--output", args["output"]]
        if args.get("collection"):
            cmd += ["--collection", args["collection"]]
        if args.get("model"):
            cmd += ["--model", args["model"]]
        if args.get("embedding_model"):
            cmd += ["--embedding-model", args["embedding_model"]]
        if args.get("chroma_host"):
            cmd += ["--chroma-host", args["chroma_host"]]
        if args.get("chroma_port") is not None:
            cmd += ["--chroma-port", str(args["chroma_port"])]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    if name == "semantic_search":
        cmd = ["npm", "run", "semantic-search", "--", args.get("query", "")]
        if args.get("collection"):
            cmd += ["--collection", args["collection"]]
        if args.get("n_results") is not None:
            cmd += ["--n-results", str(args["n_results"])]
        if args.get("embedding_model"):
            cmd += ["--embedding-model", args["embedding_model"]]
        if args.get("format"):
            cmd += ["--format", args["format"]]
        if args.get("chroma_host"):
            cmd += ["--chroma-host", args["chroma_host"]]
        if args.get("chroma_port") is not None:
            cmd += ["--chroma-port", str(args["chroma_port"])]
        if args.get("where_filter"):
            cmd += ["--where", args["where_filter"]]
        if args.get("min_distance") is not None:
            cmd += ["--min-distance", str(args["min_distance"])]
        if args.get("max_distance") is not None:
            cmd += ["--max-distance", str(args["max_distance"])]
        code, out, err = _run_cmd(cmd)
        return {"ok": code == 0, "stdout": out, "stderr": err, "cmd": cmd}

    return {"ok": False, "error": f"Unknown function: {name}", "args": args}


def find_tool_calls(response: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """Extract tool calls from Ollama response."""
    calls: List[Tuple[str, Dict[str, Any]]] = []
    message = response.get("message", {})
    tool_calls = message.get("tool_calls") or []
    
    for tool_call in tool_calls:
        func = tool_call.get("function", {})
        name = func.get("name")
        # Arguments may be a string or dict depending on Ollama version
        args = func.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        if name:
            calls.append((name, args))
    
    return calls


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ollama API CLI agent with CLI tools")
    parser.add_argument("prompt", type=str, nargs="?", help="Prompt to send to Ollama (omit to start chat)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--chat", action="store_true", help="Start interactive chat mode")
    parser.add_argument("--no-tools", action="store_true", help="Disable CLI tools")
    return parser.parse_args()


def build_system_prompt() -> str:
    """Build a comprehensive system prompt for improved task planning and function calling"""
    cli_functions = build_cli_function_declarations()
    function_list = "\n".join([f"- {func['function']['name']}: {func['function']['description']}" for func in cli_functions])
    
    # Get current date and time
    current_datetime = datetime.now()
    current_date = current_datetime.strftime("%A, %B %d, %Y")
    current_time = current_datetime.strftime("%I:%M %p")
    
    return f"""You are a helpful AI assistant with access to powerful CLI tools. You excel at task planning, breaking down complex requests, and efficiently using available functions to accomplish goals.

## CURRENT DATE & TIME
Today is {current_date} at {current_time} (local time).

## AVAILABLE FUNCTIONS
You have access to {len(cli_functions)} specialized functions:
{function_list}

## CORE PRINCIPLES

### 1. TASK ANALYSIS & PLANNING
- Always analyze the user's request to understand the full scope
- Break complex tasks into logical steps
- Identify which functions can help accomplish each step
- Plan the sequence of function calls needed

### 2. FUNCTION CALLING EXCELLENCE
- **BE PROACTIVE**: When a task clearly requires a function, call it immediately
- **BE SPECIFIC**: Use precise parameters that match the user's intent
- **BE EFFICIENT**: Choose the most appropriate function for each task
- **BE THOROUGH**: Don't stop after one function call if the task requires more

### 3. COMMON USE CASES
- **Search requests**: Use google_search for current information, research, facts
- **Image generation**: Use nano_banana_generate for creating images from text descriptions
- **Image editing**: Use nano_banana_edit to modify existing images
- **Web content**: Use html_to_md to extract and convert web page content
- **File operations**: Use download_file for retrieving files from URLs
- **Image optimization**: Use image_optimizer to enhance, resize, or process images
- **Date/time operations**: Use datetime for timestamps, scheduling, time zones, or any time-related queries
- **Data indexing**: Use data_indexing to process and index web content or files into ChromaDB for later RAG queries
- **Semantic search**: Use semantic_search to query indexed content in ChromaDB using semantic similarity

### 4. RESPONSE PATTERNS
- When you call a function, explain what you're doing and why
- After function results, interpret and summarize the information for the user
- **IMPORTANT**: When image generation/editing functions complete, always extract and clearly present the file path to the user
- Parse tool outputs for file paths (look for "File path:" or similar patterns) and present them prominently
- If a function fails, try alternative approaches or explain limitations
- Always aim to fully satisfy the user's request, not just partially

### 5. MULTI-STEP WORKFLOWS
For complex requests:
1. Acknowledge the full request
2. Outline your planned approach
3. Execute functions in logical sequence
4. Provide updates on progress
5. Summarize final results

Remember: Your goal is to be maximally helpful by actively using your functions to accomplish user goals, not just to provide information or suggestions."""


def print_response(response: Dict[str, Any]) -> None:
    """Print the response from Ollama."""
    message = response.get("message", {})
    content = message.get("content", "")
    
    if content:
        print(content)


def run_single_turn(model: str, user_prompt: str, use_tools: bool = True) -> None:
    """Run a single turn conversation with Ollama."""
    tools = build_cli_function_declarations() if use_tools else None
    system_prompt = build_system_prompt()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    response = ollama.chat(
        model=model,
        messages=messages,
        tools=tools,
    )
    
    # Handle tool calls in a loop (up to 3 iterations)
    for _ in range(3):
        calls = find_tool_calls(response)
        if not calls:
            break
        
        name, fargs = calls[0]
        print(f"\n[Calling tool: {name}]")
        result = execute_cli_function(name, fargs)
        
        # Add assistant message and tool result to conversation
        messages.append(response["message"])
        messages.append({
            "role": "tool",
            "content": json.dumps(result),
        })
        
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=tools,
        )
    
    print_response(response)


def run_chat_loop(model: str, use_tools: bool = True) -> None:
    """Run an interactive chat loop with Ollama."""
    print("Interactive chat started. Type 'exit' or press Ctrl-D to quit.\n")
    
    tools = build_cli_function_declarations() if use_tools else None
    system_prompt = build_system_prompt()
    
    # Initialize conversation history
    history: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt}
    ]
    
    print(f"Model: {model}")
    print(f"CLI tools: {'enabled' if use_tools else 'disabled'}\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            break
        
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", ":q", "/exit"}:
            break
        
        # Add user message to history
        history.append({"role": "user", "content": user_input})
        
        response = ollama.chat(
            model=model,
            messages=history,
            tools=tools,
        )
        
        # Handle tool calls in a loop (up to 3 iterations)
        for _ in range(3):
            calls = find_tool_calls(response)
            if not calls:
                break
            
            name, fargs = calls[0]
            print(f"\n[Calling tool: {name}]")
            result = execute_cli_function(name, fargs)
            
            # Add assistant message and tool result to conversation
            history.append(response["message"])
            history.append({
                "role": "tool",
                "content": json.dumps(result),
            })
            
            response = ollama.chat(
                model=model,
                messages=history,
                tools=tools,
            )
        
        print("\nAssistant:", end=" ")
        print_response(response)
        print()
        
        # Add final assistant message to history
        if response.get("message"):
            history.append(response["message"])


def main() -> None:
    # Load env files
    load_env_files()
    
    args = parse_args()
    
    use_tools = not args.no_tools
    
    # If no prompt and not explicitly --chat, default to chat
    if not args.prompt:
        args.chat = True
    
    if args.chat:
        run_chat_loop(args.model, use_tools=use_tools)
        return
    
    run_single_turn(args.model, args.prompt, use_tools=use_tools)


if __name__ == "__main__":
    main()
