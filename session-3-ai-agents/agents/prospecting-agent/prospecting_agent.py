#!/usr/bin/env python3
"""
Prospecting Agent CLI

An AI agent for B2B prospect research and enrichment. Uses Gemini's integrated
tools (Google Search, URL Context, Maps) along with subagent delegation.

Usage:
  # Interactive chat mode
  python prospecting_agent.py --chat

  # Single query
  python prospecting_agent.py "Find AI startups in San Francisco"

  # With specific ICP file
  python prospecting_agent.py --icp memory/data/sample_icp.json "Find matching companies"

  # Show help
  python prospecting_agent.py --help
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from agent_env import load_agent_environment

load_agent_environment()

from google import genai
from google.genai import types

# Add local modules to path
AGENT_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENT_DIR / "memory"))
sys.path.insert(0, str(AGENT_DIR / "tools"))
sys.path.insert(0, str(AGENT_DIR / "subagents"))

from memory import MemoryStore

# Configuration
DEFAULT_MODEL = "gemini-3-flash-preview"


def load_api_key() -> str:
    """Load Gemini API key from environment."""
    api_key = (
        os.environ.get("GOOGLE_AI_STUDIO_KEY") or 
        os.environ.get("GEMINI_API_KEY") or 
        os.environ.get("GOOGLE_API_KEY")
    )
    if not api_key:
        print("Error: API key not found. Set GOOGLE_AI_STUDIO_KEY, GEMINI_API_KEY, or GOOGLE_API_KEY.")
        sys.exit(1)
    return api_key


def load_skills() -> str:
    """Load all skill files and return as context."""
    skills_dir = AGENT_DIR / "skills"
    skills_content = []
    
    if skills_dir.exists():
        for skill_file in skills_dir.glob("*.md"):
            try:
                with open(skill_file, "r") as f:
                    content = f.read()
                    skills_content.append(f"## Skill: {skill_file.stem}\n\n{content}")
            except Exception:
                pass
    
    return "\n\n---\n\n".join(skills_content) if skills_content else ""


def build_function_declarations() -> List[Dict[str, Any]]:
    """Build function declarations for the agent's tools."""
    return [
        {
            "name": "search_prospects",
            "description": "Search for B2B prospects matching ICP criteria using Google Search, URL Context, and Maps grounding. Delegates to the prospect_search subagent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query describing the prospects to find"
                    },
                    "industries": {
                        "type": "string",
                        "description": "Comma-separated list of target industries"
                    },
                    "geography": {
                        "type": "string",
                        "description": "Comma-separated list of target regions"
                    },
                    "company_size": {
                        "type": "string",
                        "description": "Company size range (e.g., '50-500')"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "enrich_prospect",
            "description": "Enrich a prospect with detailed information about the company. Delegates to the prospect_enrich subagent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name of the company to enrich"
                    },
                    "website": {
                        "type": "string",
                        "description": "Company website URL"
                    },
                    "prospect_id": {
                        "type": "string",
                        "description": "ID of existing prospect to enrich"
                    }
                },
                "required": []
            }
        },
        {
            "name": "store_prospect",
            "description": "Store a prospect to the database",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Company name"
                    },
                    "website": {
                        "type": "string",
                        "description": "Company website"
                    },
                    "industry": {
                        "type": "string",
                        "description": "Industry"
                    },
                    "score": {
                        "type": "integer",
                        "description": "ICP fit score (0-100)"
                    },
                    "prospect_json": {
                        "type": "string",
                        "description": "Full prospect data as JSON string"
                    }
                },
                "required": ["company_name"]
            }
        },
        {
            "name": "retrieve_prospects",
            "description": "Retrieve prospects from the database with optional filters",
            "parameters": {
                "type": "object",
                "properties": {
                    "prospect_id": {
                        "type": "string",
                        "description": "Get specific prospect by ID"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["new", "researching", "enriched", "qualified", "contacted", "archived"],
                        "description": "Filter by status"
                    },
                    "industry": {
                        "type": "string",
                        "description": "Filter by industry"
                    },
                    "min_score": {
                        "type": "integer",
                        "description": "Minimum ICP fit score"
                    },
                    "search_query": {
                        "type": "string",
                        "description": "Search prospects by name or description"
                    },
                    "get_stats": {
                        "type": "boolean",
                        "description": "Get statistics instead of prospects"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return"
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_icp",
            "description": "Get the current Ideal Customer Profile (ICP) - the targeting criteria",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "update_icp",
            "description": "Update the Ideal Customer Profile (ICP) targeting criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_industries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Target industries"
                    },
                    "geography": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Target regions/countries"
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords to look for"
                    },
                    "company_size_min": {
                        "type": "integer",
                        "description": "Minimum employee count"
                    },
                    "company_size_max": {
                        "type": "integer",
                        "description": "Maximum employee count"
                    },
                    "funding_stage": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Target funding stages"
                    },
                    "exclusions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords to exclude"
                    }
                },
                "required": []
            }
        }
    ]


def log_status(message: str):
    """Log a status message to stderr for UI streaming."""
    print(message, file=sys.stderr, flush=True)


def run_subagent(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Run a subagent and return its output."""
    log_status(f"Calling subagent: {name}")
    subagent_path = AGENT_DIR / "subagents" / f"{name}.py"
    
    if not subagent_path.exists():
        return {"error": f"Subagent not found: {name}"}
    
    cmd = ["python", str(subagent_path)]
    
    # Build command arguments based on subagent
    if name == "prospect_search":
        if args.get("query"):
            cmd.extend(["--query", args["query"]])
        if args.get("industries"):
            cmd.extend(["--industries", args["industries"]])
        if args.get("geography"):
            cmd.extend(["--geography", args["geography"]])
        if args.get("company_size"):
            cmd.extend(["--size", args["company_size"]])
        if args.get("icp_file"):
            cmd.extend(["--icp-file", args["icp_file"]])
        cmd.append("--pretty")
    
    elif name == "prospect_enrich":
        if args.get("company_name"):
            cmd.extend(["--company", args["company_name"]])
        if args.get("website"):
            cmd.extend(["--website", args["website"]])
        if args.get("prospect_file"):
            cmd.extend(["--prospect-file", args["prospect_file"]])
        cmd.append("--pretty")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(AGENT_DIR)
        )
        
        if result.returncode == 0:
            log_status(f"Subagent {name} completed successfully")
            try:
                output = json.loads(result.stdout)
                # Log summary of results
                if "prospects" in output:
                    log_status(f"Found {len(output.get('prospects', []))} prospects")
                return output
            except json.JSONDecodeError:
                return {"raw_output": result.stdout}
        else:
            log_status(f"Subagent {name} failed: {result.stderr[:100] if result.stderr else 'unknown error'}")
            return {"error": result.stderr or "Subagent failed", "stdout": result.stdout}
    
    except subprocess.TimeoutExpired:
        log_status(f"Subagent {name} timed out")
        return {"error": "Subagent timed out"}
    except Exception as e:
        log_status(f"Subagent {name} error: {str(e)}")
        return {"error": str(e)}


def run_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Run a tool and return its output."""
    log_status(f"Running tool: {name}")
    tool_path = AGENT_DIR / "tools" / f"{name}.py"
    
    if not tool_path.exists():
        return {"error": f"Tool not found: {name}"}
    
    cmd = ["python", str(tool_path)]
    
    # Build command arguments
    if name == "store_prospect":
        if args.get("prospect_json"):
            # Store via stdin
            try:
                result = subprocess.run(
                    cmd + ["--stdin"],
                    input=args["prospect_json"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(AGENT_DIR)
                )
                return json.loads(result.stdout) if result.returncode == 0 else {"error": result.stderr}
            except Exception as e:
                return {"error": str(e)}
        else:
            if args.get("company_name"):
                cmd.extend(["--company", args["company_name"]])
            if args.get("website"):
                cmd.extend(["--website", args["website"]])
            if args.get("industry"):
                cmd.extend(["--industry", args["industry"]])
            if args.get("score"):
                cmd.extend(["--score", str(args["score"])])
    
    elif name == "retrieve_prospects":
        if args.get("prospect_id"):
            cmd.extend(["--id", args["prospect_id"]])
        elif args.get("get_stats"):
            cmd.append("--stats")
        elif args.get("search_query"):
            cmd.extend(["--search", args["search_query"]])
        else:
            if args.get("status"):
                cmd.extend(["--status", args["status"]])
            if args.get("industry"):
                cmd.extend(["--industry", args["industry"]])
            if args.get("min_score"):
                cmd.extend(["--min-score", str(args["min_score"])])
            if args.get("limit"):
                cmd.extend(["--limit", str(args["limit"])])
            else:
                cmd.extend(["--limit", "20"])
        cmd.append("--pretty")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(AGENT_DIR)
        )
        
        if result.returncode == 0:
            log_status(f"Tool {name} completed successfully")
            try:
                output = json.loads(result.stdout)
                # Log summary
                if name == "retrieve_prospects" and "prospects" in output:
                    log_status(f"Retrieved {len(output.get('prospects', []))} prospects")
                elif name == "store_prospect" and output.get("status") == "success":
                    log_status(f"Stored prospect: {output.get('company_name', 'unknown')}")
                return output
            except json.JSONDecodeError:
                return {"raw_output": result.stdout}
        else:
            log_status(f"Tool {name} failed")
            return {"error": result.stderr or "Tool failed", "stdout": result.stdout}
    
    except subprocess.TimeoutExpired:
        log_status(f"Tool {name} timed out")
        return {"error": "Tool timed out"}
    except Exception as e:
        log_status(f"Tool {name} error: {str(e)}")
        return {"error": str(e)}


def execute_function(name: str, args: Dict[str, Any], memory: MemoryStore) -> Dict[str, Any]:
    """Execute a function call and return results."""
    log_status(f"Executing function: {name}")
    
    if name == "search_prospects":
        log_status("Searching for prospects matching criteria...")
        # Delegate to search subagent
        return run_subagent("prospect_search", args)
    
    elif name == "enrich_prospect":
        # Delegate to enrich subagent
        company = args.get("company_name", "unknown company")
        log_status(f"Enriching prospect: {company}")
        return run_subagent("prospect_enrich", args)
    
    elif name == "store_prospect":
        # Store prospect
        log_status("Saving prospect to database...")
        return run_tool("store_prospect", args)
    
    elif name == "retrieve_prospects":
        # Retrieve prospects
        log_status("Querying prospect database...")
        return run_tool("retrieve_prospects", args)
    
    elif name == "get_icp":
        # Get ICP from memory
        log_status("Fetching current ICP settings...")
        icp = memory.get_icp()
        return icp if icp else {"message": "No ICP defined yet. Would you like to set one?"}
    
    elif name == "update_icp":
        # Update ICP
        current_icp = memory.get_icp() or {"name": "default", "target_industries": [], "geography": []}
        
        if args.get("target_industries"):
            current_icp["target_industries"] = args["target_industries"]
        if args.get("geography"):
            current_icp["geography"] = args["geography"]
        if args.get("keywords"):
            current_icp["keywords"] = args["keywords"]
        if args.get("company_size_min") or args.get("company_size_max"):
            current_icp["company_size"] = {
                "min_employees": args.get("company_size_min", current_icp.get("company_size", {}).get("min_employees", 1)),
                "max_employees": args.get("company_size_max", current_icp.get("company_size", {}).get("max_employees", 10000))
            }
        if args.get("funding_stage"):
            current_icp["funding_stage"] = args["funding_stage"]
        if args.get("exclusions"):
            current_icp["exclusions"] = args["exclusions"]
        
        if memory.set_icp(current_icp):
            return {"status": "success", "message": "ICP updated", "icp": current_icp}
        else:
            return {"error": "Failed to update ICP"}
    
    else:
        return {"error": f"Unknown function: {name}"}


def find_function_calls(response) -> List[Tuple[str, Dict[str, Any]]]:
    """Extract function calls from response."""
    calls = []
    try:
        parts = response.candidates[0].content.parts if response.candidates else []
        for part in parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                name = fc.name
                args = dict(fc.args) if fc.args else {}
                calls.append((name, args))
    except Exception:
        pass
    return calls


def make_function_response(name: str, result: Dict[str, Any]) -> types.Part:
    """Create a function response part."""
    return types.Part(
        function_response=types.FunctionResponse(
            name=name,
            response=result
        )
    )


def build_system_prompt(icp: Optional[Dict] = None) -> str:
    """Build the system prompt with skills and context."""
    skills = load_skills()
    
    icp_context = ""
    if icp:
        icp_context = f"""
## Current ICP (Ideal Customer Profile)
```json
{json.dumps(icp, indent=2)}
```
"""
    
    return f"""You are a B2B Prospecting Agent. Your job is to help users find and research potential customers (prospects).

## Your Capabilities

1. **Search for Prospects**: Find companies matching criteria using Google Search with grounding
2. **Enrich Prospects**: Research companies in detail to gather comprehensive information
3. **Manage ICP**: Help users define and refine their Ideal Customer Profile
4. **Store & Retrieve**: Save prospects to database and query them later

## CRITICAL: User Query vs. ICP

- The ICP (below) is a DEFAULT reference, NOT a hard constraint
- When the user specifies criteria (location, industry, type), USE THEIR CRITERIA
- Example: If user says "find AI startups in Oulu", search for AI startups in Oulu - don't filter by ICP geography
- Only apply ICP criteria when user asks for "prospects matching our ICP" or similar
- User's explicit request ALWAYS takes priority over stored ICP

## How to Work

1. **Listen to the User**: Their request defines what to search for
2. **Use Tools Appropriately**: 
   - `search_prospects` - pass the user's actual query, don't filter it through ICP
   - `enrich_prospect` - get detailed info about specific companies
   - `store_prospect` - save found prospects
   - `retrieve_prospects` - query saved prospects
   - `get_icp` / `update_icp` - manage targeting criteria when user asks

3. **Be Proactive**: Act on clear requests immediately. Don't just describe what you could do.

4. **Quality Focus**: Prioritize local companies, startups, scale-ups - not multinationals with offices
{icp_context}
## Skills Reference

{skills}

## Response Style

- Be concise but informative
- Present data in clear formats (tables, bullet points)
- Explain your actions ("Searching for...", "Found X prospects...")
- Offer next steps ("Would you like me to enrich these?", "Should I store these?")

Remember: Follow the user's request. The ICP is just context, not a filter for every search."""


def print_response(response) -> str:
    """Print and return model response text."""
    text_parts = []
    try:
        parts = response.candidates[0].content.parts if response.candidates else []
        for part in parts:
            if hasattr(part, "text") and part.text:
                text_parts.append(part.text)
    except Exception:
        pass
    
    text = "\n".join(text_parts)
    if text:
        print(text)
    return text


async def run_chat_loop(client: genai.Client, model: str, memory: MemoryStore, initial_icp: Optional[Dict] = None):
    """Run interactive chat loop."""
    print("Prospecting Agent - Interactive Mode")
    print("=" * 40)
    print("Commands: 'exit' to quit, 'help' for commands")
    print()
    
    # Get initial ICP
    icp = initial_icp or memory.get_icp()
    
    if icp:
        print(f"Loaded ICP: {icp.get('name', 'default')}")
        print(f"  Industries: {', '.join(icp.get('target_industries', []))}")
        print(f"  Geography: {', '.join(icp.get('geography', []))}")
    else:
        print("No ICP loaded. Start by describing your ideal customer profile.")
    print()
    
    # Build tools
    function_declarations = build_function_declarations()
    tools = [types.Tool(function_declarations=function_declarations)]
    
    # Initialize conversation
    system_prompt = build_system_prompt(icp)
    history: List[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=system_prompt)]),
        types.Content(role="model", parts=[types.Part(text="I'm ready to help you find and research prospects. What would you like to do?")])
    ]
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in {"exit", "quit", ":q", "/exit"}:
            print("Goodbye!")
            break
        
        if user_input.lower() == "help":
            print("""
Available commands:
  find <criteria>     - Search for prospects
  enrich <company>    - Get detailed info about a company
  list                - Show saved prospects
  stats               - Show prospect statistics
  icp                 - Show current ICP
  set icp <criteria>  - Update ICP
  exit                - Quit
            """)
            continue
        
        # Add user message
        history.append(types.Content(role="user", parts=[types.Part(text=user_input)]))
        
        # Configure request
        config = types.GenerateContentConfig(tools=tools)
        
        # Generate response
        response = await client.aio.models.generate_content(
            model=model,
            contents=history,
            config=config
        )
        
        # Handle function calls (up to 5 iterations)
        for _ in range(5):
            function_calls = find_function_calls(response)
            
            if not function_calls:
                break
            
            # Append the model's response (preserves thought_signature for Gemini 3)
            if response.candidates and response.candidates[0].content:
                history.append(response.candidates[0].content)
            
            # Execute function calls and collect results
            function_responses = []
            for func_name, func_args in function_calls:
                print(f"\n[Executing: {func_name}]")
                result = execute_function(func_name, func_args, memory)
                
                # Show brief result
                if "prospects" in result:
                    count = len(result.get("prospects", []))
                    print(f"[Found {count} prospects]")
                elif "error" in result:
                    print(f"[Error: {result['error']}]")
                
                function_responses.append(make_function_response(func_name, result))
            
            # Add function responses as a single user message
            history.append(types.Content(
                role="user",
                parts=function_responses
            ))
            
            # Get next response
            response = await client.aio.models.generate_content(
                model=model,
                contents=history,
                config=config
            )
        
        # Print final response
        print("\nAgent:", end=" ")
        response_text = print_response(response)
        
        # Add final response to history (preserves thought_signature)
        if response.candidates and response.candidates[0].content:
            history.append(response.candidates[0].content)


def run_single_query(client: genai.Client, model: str, query: str, memory: MemoryStore, icp: Optional[Dict] = None):
    """Run a single query."""
    log_status(f"Processing query: {query[:50]}...")
    
    # Build tools
    function_declarations = build_function_declarations()
    tools = [types.Tool(function_declarations=function_declarations)]
    
    # Get ICP if not provided
    if not icp:
        icp = memory.get_icp()
        if icp:
            log_status(f"Using ICP: {icp.get('name', 'default')}")
    
    # Build conversation
    system_prompt = build_system_prompt(icp)
    contents = [
        types.Content(role="user", parts=[types.Part(text=system_prompt)]),
        types.Content(role="model", parts=[types.Part(text="Ready.")]),
        types.Content(role="user", parts=[types.Part(text=query)])
    ]
    
    config = types.GenerateContentConfig(tools=tools)
    
    # Generate response
    log_status("Sending request to Gemini API...")
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
    log_status("Received initial response from Gemini")
    
    # Handle function calls
    iteration = 0
    for _ in range(5):
        function_calls = find_function_calls(response)
        
        if not function_calls:
            break
        
        iteration += 1
        log_status(f"Processing function calls (iteration {iteration})...")
        
        # Append the model's response (preserves thought_signature for Gemini 3)
        if response.candidates and response.candidates[0].content:
            contents.append(response.candidates[0].content)
        
        # Execute functions and collect results
        function_responses = []
        for func_name, func_args in function_calls:
            result = execute_function(func_name, func_args, memory)
            function_responses.append(make_function_response(func_name, result))
        
        # Append function results as a single user/tool message
        contents.append(types.Content(
            role="user",
            parts=function_responses
        ))
        
        log_status("Continuing conversation with Gemini...")
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
    
    log_status("Generating final response...")
    print_response(response)


def main():
    parser = argparse.ArgumentParser(
        description="Prospecting Agent - B2B prospect research assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "query",
        nargs="?",
        help="Query to process (if not using --chat)"
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Start interactive chat mode"
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Gemini model to use (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--icp",
        help="Path to ICP JSON file to load"
    )
    
    args = parser.parse_args()
    
    if not args.chat and not args.query:
        parser.print_help()
        sys.exit(1)
    
    # Initialize
    api_key = load_api_key()
    client = genai.Client(api_key=api_key)
    memory = MemoryStore()
    
    # Load ICP if specified
    icp = None
    if args.icp:
        try:
            with open(args.icp, "r") as f:
                icp = json.load(f)
                memory.set_icp(icp)
        except Exception as e:
            print(f"Warning: Could not load ICP file: {e}")
    
    if args.chat:
        asyncio.run(run_chat_loop(client, args.model, memory, icp))
    else:
        run_single_query(client, args.model, args.query, memory, icp)


if __name__ == "__main__":
    main()
