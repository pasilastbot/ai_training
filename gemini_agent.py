#!/usr/bin/env python3
"""
Gemini Agent CLI

A minimal command-line example showing how to call the Gemini API with
- Google Search grounding tool (enabled by default)
- Code Execution tool (enabled by default)
- URL Context tool (enabled by default)
- MCP stdio tool support (optional, hardcoded servers; toggle all on/off)
- Plan mode to generate a step-by-step JSON execution plan

Usage examples:
  # Interactive chat (tools enabled by default, MCP enabled by default if available)
  python gemini_agent.py --chat

  # Disable MCP entirely
  python gemini_agent.py --chat --no-mcp

  # Single-turn
  python gemini_agent.py "Who won the euro 2024?"

  # Select tools explicitly (comma-separated: search,code,url,all,none)
  python gemini_agent.py --tools search,code --chat

  # Plan mode (outputs JSON only and saves to a file)
  python gemini_agent.py --plan "Migrate database to PostgreSQL and add read replicas"
"""

import os
import sys
import argparse
import asyncio
import shutil
import json
import re
import subprocess
from typing import List, Optional, Dict, Set, Tuple, Any

# Prefer the new SDK import style used elsewhere in this repo
from google import genai
from google.genai import types

# MCP (optional)
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except Exception:  # pragma: no cover
    ClientSession = None  # type: ignore
    StdioServerParameters = None  # type: ignore
    stdio_client = None  # type: ignore


DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TOOL_SELECTION = {"search", "code", "url"}
VALID_TOOL_KEYS = {"search", "code", "url", "all", "none"}


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


def load_api_key() -> str:
    api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: API key not found. Set GOOGLE_AI_STUDIO_KEY or GOOGLE_API_KEY.")
        sys.exit(1)
    return api_key


def parse_tools_arg(arg: Optional[str]) -> Set[str]:
    if not arg:
        return set(DEFAULT_TOOL_SELECTION)
    tokens = [t.strip().lower() for t in arg.split(',') if t.strip()]
    if not tokens:
        return set(DEFAULT_TOOL_SELECTION)
    invalid = [t for t in tokens if t not in VALID_TOOL_KEYS]
    if invalid:
        print(f"Warning: unknown tool keys ignored: {', '.join(invalid)}")
    selected: Set[str] = set()
    if "all" in tokens:
        selected.update(DEFAULT_TOOL_SELECTION)
    elif "none" in tokens:
        selected.clear()
    else:
        for t in tokens:
            if t in {"search", "code", "url"}:
                selected.add(t)
    return selected


def build_tools_from_selection(selection: Set[str]) -> List[types.Tool]:
    tools: List[types.Tool] = []
    if "search" in selection:
        tools.append(types.Tool(google_search=types.GoogleSearch()))
    if "code" in selection:
        tools.append(types.Tool(code_execution=types.ToolCodeExecution()))
    if "url" in selection:
        tools.append(types.Tool(url_context=types.UrlContext()))
    return tools


# -------------------- CLI FUNCTION DECLARATIONS --------------------

def build_cli_function_declarations() -> List[Dict[str, Any]]:
    """Build function_declarations for project CLI tools based on command_line_tools.mdc."""
    return [
        {
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
        {
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
                    "quality": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Output quality"},
                },
                "required": ["input", "output"],
            },
        },
        {
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
        {
            "name": "openai_image_generate",
            "description": "Generate image using OpenAI via npm script openai-image (generate)",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "model": {"type": "string", "enum": ["gpt-image-1", "dall-e-3"]},
                    "output": {"type": "string"},
                    "folder": {"type": "string"},
                    "size": {"type": "string", "enum": ["1024x1024", "1792x1024", "1024x1792"]},
                    "quality": {"type": "string", "enum": ["standard", "hd"]},
                    "number": {"type": "integer", "minimum": 1, "maximum": 4},
                    "reference_image": {"type": "string"},
                    "creative": {"type": "string", "enum": ["standard", "vivid"]}
                },
                "required": ["prompt"],
            },
        },
        {
            "name": "openai_image_edit",
            "description": "Edit an image using OpenAI via npm script openai-image (edit)",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_image": {"type": "string"},
                    "edit_prompt": {"type": "string"},
                    "model": {"type": "string", "enum": ["gpt-image-1", "dall-e-3"]},
                    "output": {"type": "string"},
                    "folder": {"type": "string"},
                    "size": {"type": "string", "enum": ["1024x1024", "1792x1024", "1024x1792"]},
                    "creative": {"type": "string", "enum": ["standard", "vivid"]}
                },
                "required": ["input_image", "edit_prompt"],
            },
        },
        {
            "name": "gemini_image_generate",
            "description": "Generate an image using Gemini or Imagen via npm script gemini-image (generate)",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "model": {"type": "string", "enum": ["gemini-2.0", "imagen-3.0"]},
                    "output": {"type": "string"},
                    "folder": {"type": "string"},
                    "num_outputs": {"type": "integer", "minimum": 1, "maximum": 4},
                    "negative_prompt": {"type": "string"},
                    "aspect_ratio": {"type": "string", "enum": ["1:1", "16:9", "9:16", "4:3", "3:4"]},
                },
                "required": ["prompt"],
            },
        },
        {
            "name": "gemini_image_edit",
            "description": "Edit an existing image using Gemini via npm script gemini-image (edit)",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_image": {"type": "string"},
                    "edit_prompt": {"type": "string"},
                    "output": {"type": "string"},
                    "folder": {"type": "string"},
                },
                "required": ["input_image", "edit_prompt"],
            },
        },
        {
            "name": "generate_video",
            "description": "Generate video via npm script generate-video (Replicate models)",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "model": {"type": "string", "enum": ["kling-1.6", "kling-2.0", "minimax", "hunyuan", "mochi", "ltx"]},
                    "duration": {"type": "integer"},
                    "image": {"type": "string"},
                    "output": {"type": "string"},
                    "folder": {"type": "string"},
                    "image_prompt": {"type": "string"},
                    "openai_image_output": {"type": "string"},
                    "aspect_ratio": {"type": "string"},
                },
                "required": ["prompt"],
            },
        },
        {
            "name": "remove_background_advanced",
            "description": "Remove background using advanced method via npm script remove-background-advanced",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {"type": "string"},
                    "output": {"type": "string"},
                    "tolerance": {"type": "integer", "minimum": 0, "maximum": 255},
                },
                "required": ["input", "output"],
            },
        },
    ]


def build_cli_tools_wrapper() -> types.Tool:
    return types.Tool(function_declarations=build_cli_function_declarations())


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

    return {"ok": False, "error": f"Unknown function: {name}", "args": args}


def find_function_call_parts(response) -> List[Tuple[str, Dict[str, Any]]]:
    calls: List[Tuple[str, Dict[str, Any]]] = []
    try:
        parts = response.candidates[0].content.parts if response.candidates else []
    except Exception:
        parts = []
    for p in parts:
        fc = getattr(p, "function_call", None)
        if fc and getattr(fc, "name", None):
            calls.append((fc.name, dict(getattr(fc, "args", {}) or {})))
    return calls


def make_function_response_part(name: str, result: Dict[str, Any]) -> types.Part:
    return types.Part(function_response=types.FunctionResponse(name=name, response=result))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gemini API CLI agent with default tools and optional MCP")
    parser.add_argument("prompt", type=str, nargs="?", help="Prompt to send to Gemini (omit to start chat)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--chat", action="store_true", help="Start interactive chat mode")
    parser.add_argument("--tools", type=str, help="Comma-separated tools: search,code,url,all,none (default: all)")
    # Simplified MCP toggle (all or none, hardcoded servers)
    parser.add_argument("--no-mcp", action="store_true", help="Disable all MCP servers (hardcoded)")
    # Plan mode
    parser.add_argument("--plan", type=str, help="Generate a JSON plan for the given task")
    # CLI tools function-calling (off by default to avoid model limitation conflicts)
    parser.add_argument("--enable-cli-tools", action="store_true", help="Expose CLI tools via function-calling")
    return parser.parse_args()


def print_response(response) -> None:
    # Safely access parts
    try:
        parts = response.candidates[0].content.parts if response.candidates else []
    except Exception:
        parts = []

    # Print text exactly once, aggregated from parts
    text_chunks: List[str] = []

    for part in parts:
        if getattr(part, "text", None):
            text_chunks.append(part.text)

    if text_chunks:
        print("\n".join(text_chunks))

    # Print any generated code parts and execution results
    for part in parts:
        if getattr(part, "executable_code", None) and getattr(part.executable_code, "code", None):
            print("\n# Generated Code:\n" + part.executable_code.code)
        if getattr(part, "code_execution_result", None) and getattr(part.code_execution_result, "output", None):
            print("\n# Execution Output:\n" + part.code_execution_result.output)

    # If grounded, optionally show citation metadata (URIs)
    meta = None
    try:
        meta = response.candidates[0].grounding_metadata  # may not exist
    except Exception:
        meta = None
    if meta and getattr(meta, "grounding_chunks", None):
        print("\nSources:")
        for idx, chunk in enumerate(meta.grounding_chunks):
            uri = getattr(getattr(chunk, "web", None), "uri", None)
            title = getattr(getattr(chunk, "web", None), "title", None)
            if uri:
                if title:
                    print(f"[{idx+1}] {title}: {uri}")
                else:
                    print(f"[{idx+1}] {uri}")


def get_hardcoded_mcp_params(enabled: bool) -> Optional[StdioServerParameters]:
    """Return Weather MCP via npx if enabled and available; else None."""
    if not enabled:
        return None
    if ClientSession is None or StdioServerParameters is None or stdio_client is None:
        return None
    if shutil.which("npx") is None:
        return None
    return StdioServerParameters(command="npx", args=["-y", "@philschmid/weather-mcp"], env=None)


def _describe_mcp(params: Optional[StdioServerParameters]) -> str:
    if not params:
        return "(none)"
    try:
        cmd = params.command
        args = " ".join(params.args or [])
        return f"{cmd} {args}".strip()
    except Exception:
        return "(unknown)"


def run_single_turn_sync(client: genai.Client, model: str, user_prompt: str, selection: Set[str]):
    tools = build_tools_from_selection(selection)
    config = types.GenerateContentConfig(tools=tools)
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=config,
    )
    print_response(response)


def add_cli_function_tools(tools_list: List[types.Tool]) -> List[types.Tool]:
    try:
        cli_tool = types.Tool(function_declarations=build_cli_function_declarations())
        tools_list = tools_list + [cli_tool]
    except Exception:
        pass
    return tools_list


async def run_single_turn_async(client: genai.Client, model: str, user_prompt: str, *, mcp_params: Optional[StdioServerParameters], selection: Set[str], enable_cli_tools: bool = False) -> None:
    tools = build_tools_from_selection(selection)
    if enable_cli_tools:
        tools = add_cli_function_tools(tools)
    if mcp_params is None:
        config = types.GenerateContentConfig(tools=tools)
        response = await client.aio.models.generate_content(
            model=model,
            contents=user_prompt,
            config=config,
        )
        # Loop up to 3 function calls
        for _ in range(3):
            calls = find_function_call_parts(response)
            if not calls:
                break
            name, fargs = calls[0]
            result = execute_cli_function(name, fargs)
            response = await client.aio.models.generate_content(
                model=model,
                contents=[user_prompt, make_function_response_part(name, result)],
                config=config,
            )
        print_response(response)
        return

    async with stdio_client(mcp_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print(f"[MCP] Session attached: {_describe_mcp(mcp_params)}")
            config = types.GenerateContentConfig(tools=tools + [session])
            response = await client.aio.models.generate_content(
                model=model,
                contents=user_prompt,
                config=config,
            )
            if enable_cli_tools:
                for _ in range(3):
                    calls = find_function_call_parts(response)
                    if not calls:
                        break
                    name, fargs = calls[0]
                    result = execute_cli_function(name, fargs)
                    response = await client.aio.models.generate_content(
                        model=model,
                        contents=[user_prompt, make_function_response_part(name, result)],
                        config=config,
                    )
            if enable_cli_tools:
                for _ in range(3):
                    calls = find_function_call_parts(response)
                    if not calls:
                        break
                    name, fargs = calls[0]
                    result = execute_cli_function(name, fargs)
                    response = await client.aio.models.generate_content(
                        model=model,
                        contents=[user_prompt, make_function_response_part(name, result)],
                        config=config,
                    )
            print_response(response)


async def run_chat_loop_async(client: genai.Client, model: str, *, mcp_params: Optional[StdioServerParameters], selection: Set[str], enable_cli_tools: bool = False) -> None:
    print("Interactive chat started. Type 'exit' or press Ctrl-D to quit. Use /tools to view or change tools.\n")
    history: List[types.Content] = []

    def tools_status_line(sel: Set[str], mcp_on: bool) -> str:
        active = ",".join(sorted(sel)) if sel else "(none)"
        return f"Active tools: {active}; MCP: {'on' if mcp_on else 'off'}"

    print(tools_status_line(selection, mcp_params is not None))
    if mcp_params is not None:
        print(f"[MCP] Default server: {_describe_mcp(mcp_params)}")

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

        # Handle /tools commands locally
        if user_input.lower().startswith("/tools"):
            cmd = user_input[len("/tools"):].strip()
            if not cmd or cmd == "show":
                print(tools_status_line(selection, mcp_params is not None))
                continue
            if cmd.startswith("set"):
                _, _, arg = cmd.partition("set")
                new_sel = parse_tools_arg(arg.strip())
                selection.clear()
                selection.update(new_sel)
                print("Updated " + tools_status_line(selection, mcp_params is not None))
                continue
            if cmd.startswith("add"):
                _, _, arg = cmd.partition("add")
                add_sel = parse_tools_arg(arg.strip())
                selection.update(add_sel)
                print("Updated " + tools_status_line(selection, mcp_params is not None))
                continue
            if cmd.startswith("remove"):
                _, _, arg = cmd.partition("remove")
                rem_sel = parse_tools_arg(arg.strip())
                for k in rem_sel:
                    selection.discard(k)
                print("Updated " + tools_status_line(selection, mcp_params is not None))
                continue
            print("Usage: /tools [show|set <list>|add <list>|remove <list>]. Example: /tools set search,code")
            continue

        contents: List[types.Content] = []
        contents.extend(history)
        contents.append(types.Content(role="user", parts=[types.Part(text=user_input)]))
        tools = build_tools_from_selection(selection)
        if enable_cli_tools:
            tools = add_cli_function_tools(tools)
        if mcp_params is None:
            config = types.GenerateContentConfig(tools=tools)
            response = await client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            if enable_cli_tools:
                for _ in range(3):
                    calls = find_function_call_parts(response)
                    if not calls:
                        break
                    name, fargs = calls[0]
                    result = execute_cli_function(name, fargs)
                    contents.append(types.Content(role="tool", parts=[make_function_response_part(name, result)]))
                    response = await client.aio.models.generate_content(
                        model=model,
                        contents=contents,
                        config=config,
                    )
        else:
            async with stdio_client(mcp_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    print(f"[MCP] Session attached: {_describe_mcp(mcp_params)}")
                    config = types.GenerateContentConfig(tools=tools + [session])
                    response = await client.aio.models.generate_content(
                        model=model,
                        contents=contents,
                        config=config,
                    )
                    if enable_cli_tools:
                        for _ in range(3):
                            calls = find_function_call_parts(response)
                            if not calls:
                                break
                            name, fargs = calls[0]
                            result = execute_cli_function(name, fargs)
                            contents.append(types.Content(role="tool", parts=[make_function_response_part(name, result)]))
                            response = await client.aio.models.generate_content(
                                model=model,
                                contents=contents,
                                config=config,
                            )
        print_response(response)
        try:
            model_content = response.candidates[0].content
            if model_content is not None:
                history.append(model_content)
        except Exception:
            pass


def slugify_filename(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    if not slug:
        slug = "plan"
    if len(slug) > 80:
        slug = slug[:80].rstrip("-")
    return f"{slug}.json"


def extract_json_text(full_text: str) -> str:
    # Try to parse as-is
    try:
        obj = json.loads(full_text)
        return json.dumps(obj, separators=(",", ":"))
    except Exception:
        pass
    # Fallback: extract first {...} block
    start = full_text.find("{")
    end = full_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = full_text[start:end+1]
        try:
            obj = json.loads(candidate)
            return json.dumps(obj, separators=(",", ":"))
        except Exception:
            return candidate
    return full_text


def build_plan_prompt(task: str) -> str:
    return (
        "You are an expert AI planner. Create a step-by-step STATE MACHINE plan to accomplish the following task. "
        "The plan should model interactive execution: asking the user clarifying questions, calling tools when needed, "
        "and deciding when to proceed to the next step based on conditions.\n\n"
        "STRICTLY output JSON only matching this schema (no prose, no markdown):\n"
        "{"
        "\"name\": string,"
        "\"description\": string,"
        "\"start\": string,"
        "\"steps\": ["
        "  {"
        "    \"id\": string,"
        "    \"title\": string,"
        "    \"type\": one of [\"ask_user\", \"call_tool\", \"decide\", \"action\", \"compute\"],"
        "    \"instructions\": string,"
        "    \"tool\": {\"name\": string, \"args\": object} (optional, for call_tool),"
        "    \"transitions\": [{\"condition\": string, \"next\": string}]"
        "  }"
        "]"
        "}\n\n"
        "Task: " + task + "\n"
        "Constraints:\n"
        "- Use concise, descriptive step titles.\n"
        "- Include at least one ask_user step if clarification is likely.\n"
        "- Include call_tool steps only as placeholders (do not execute).\n"
        "- Ensure transitions cover success and error/clarification paths.\n"
        "- The output MUST be valid minifiable JSON and nothing else."
    )


def run_plan_mode(client: genai.Client, model: str, task: str) -> int:
    prompt = build_plan_prompt(task)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0),
    )
    # Aggregate text
    try:
        parts = response.candidates[0].content.parts if response.candidates else []
    except Exception:
        parts = []
    full_text = "\n".join([p.text for p in parts if getattr(p, "text", None)])
    json_text = extract_json_text(full_text).strip()
    # Print ONLY JSON
    print(json_text)
    # Save to file
    filename = slugify_filename(task)
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(json_text)
    except Exception:
        return 1
    return 0


def main() -> None:
    # Load env files before reading API key
    load_env_files()

    args = parse_args()

    # Plan mode takes precedence and prints ONLY JSON
    if args.plan:
        api_key = load_api_key()
        client = genai.Client(api_key=api_key)
        exit_code = run_plan_mode(client, args.model, args.plan)
        sys.exit(exit_code)

    # If CLI tools are enabled and user didn't specify --tools, disable Google tools by default
    if getattr(args, "enable_cli_tools", False) and not args.tools:
        selection = set()
    else:
        selection = parse_tools_arg(args.tools)

    # Initialize client (Client takes api_key directly; configure() is not required)
    api_key = load_api_key()
    client = genai.Client(api_key=api_key)

    # Prepare hardcoded MCP params (Weather MCP) based on single toggle
    mcp_params: Optional[StdioServerParameters] = get_hardcoded_mcp_params(enabled=not args.no_mcp)

    # If no prompt and not explicitly --chat, default to chat
    if not args.prompt:
        args.chat = True

    # Route to async flow if MCP is enabled, else use sync
    if mcp_params is not None:
        if args.chat:
            asyncio.run(run_chat_loop_async(client, args.model, mcp_params=mcp_params, selection=selection, enable_cli_tools=args.enable_cli_tools))
            return
        asyncio.run(run_single_turn_async(client, args.model, args.prompt, mcp_params=mcp_params, selection=selection, enable_cli_tools=args.enable_cli_tools))
        return

    # Non-MCP paths
    if args.chat:
        # Use async client for consistency
        asyncio.run(run_chat_loop_async(client, args.model, mcp_params=None, selection=selection, enable_cli_tools=args.enable_cli_tools))
        return

    run_single_turn_sync(client, args.model, args.prompt, selection)


if __name__ == "__main__":
    main()
