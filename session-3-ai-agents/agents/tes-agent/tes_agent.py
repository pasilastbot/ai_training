#!/usr/bin/env python3
"""
TES Agent (Työehtosopimus-Agent)

AI agent for Finnish collective bargaining agreements.
Indexes TES documents, extracts structured data, and provides
a bilingual chatbot for querying, comparing, and calculating salary terms.

Usage:
    python tes_agent.py --chat                              # Interactive chat
    python tes_agent.py "What is the minimum salary in tech TES?"
    python tes_agent.py --index "Teknologiateollisuuden TES"
    python tes_agent.py --compare tes_1,tes_2
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from agent_env import load_agent_environment
load_agent_environment()

from google import genai
from google.genai import types

from memory.memory import (
    get_tes, list_tes, search_tes, store_tes, get_stats,
    get_schema, init_database
)

DEFAULT_MODEL = "gemini-3-flash-preview"
AGENT_DIR = Path(__file__).parent


def get_client() -> genai.Client:
    """Get Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_AI_STUDIO_KEY required")
    return genai.Client(api_key=api_key)


def detect_language(text: str) -> str:
    """Detect if text is Finnish or English."""
    finnish_indicators = [
        'mikä', 'mitä', 'missä', 'miten', 'milloin', 'paljonko',
        'työehtosopimus', 'palkka', 'loma', 'työ', 'vuosi',
        'kerro', 'näytä', 'etsi', 'vertaa', 'laske'
    ]
    text_lower = text.lower()
    finnish_count = sum(1 for word in finnish_indicators if word in text_lower)
    return "fi" if finnish_count >= 2 else "en"


def build_function_declarations() -> list:
    """Build function declarations for Gemini."""
    return [
        types.FunctionDeclaration(
            name="search_tes",
            description="Search for TES documents in the database by name, industry, or keywords",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (TES name, industry, union, etc.)"
                    }
                },
                "required": ["query"]
            }
        ),
        types.FunctionDeclaration(
            name="semantic_search",
            description="AI-powered semantic search across TES content using embeddings. Use this for finding specific terms, clauses, or concepts across all TES documents.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query in Finnish or English (e.g., 'iltatyölisä', 'sairausloma', 'overtime compensation')"
                    },
                    "tes_filter": {
                        "type": "string",
                        "description": "Optional: Filter results to a specific TES name"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 5, max 15)"
                    }
                },
                "required": ["query"]
            }
        ),
        types.FunctionDeclaration(
            name="list_tes",
            description="List all indexed TES documents, optionally filtered",
            parameters={
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "Filter by industry"
                    },
                    "union": {
                        "type": "string",
                        "description": "Filter by union name"
                    },
                    "valid_only": {
                        "type": "boolean",
                        "description": "Only show currently valid TES"
                    }
                }
            }
        ),
        types.FunctionDeclaration(
            name="get_tes_details",
            description="Get full details of a specific TES document",
            parameters={
                "type": "object",
                "properties": {
                    "tes_id": {
                        "type": "string",
                        "description": "TES document ID"
                    }
                },
                "required": ["tes_id"]
            }
        ),
        types.FunctionDeclaration(
            name="index_tes",
            description="Index a single TES document by searching for it, downloading the PDF, and extracting data",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "TES name or search query to find the PDF"
                    },
                    "url": {
                        "type": "string",
                        "description": "Direct URL to the TES PDF (optional)"
                    }
                },
                "required": ["query"]
            }
        ),
        types.FunctionDeclaration(
            name="index_multiple_tes",
            description="Index MULTIPLE TES documents IN PARALLEL. Use this when you need to index 2 or more TES documents at once - much faster than calling index_tes multiple times.",
            parameters={
                "type": "object",
                "properties": {
                    "tes_list": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "TES name or search query"},
                                "url": {"type": "string", "description": "Direct URL (optional)"}
                            },
                            "required": ["query"]
                        },
                        "description": "List of TES documents to index in parallel"
                    }
                },
                "required": ["tes_list"]
            }
        ),
        types.FunctionDeclaration(
            name="compare_tes",
            description="Compare multiple TES documents side-by-side",
            parameters={
                "type": "object",
                "properties": {
                    "tes_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of TES IDs to compare"
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fields to compare (e.g., salary_tables, vacation, working_hours)"
                    }
                },
                "required": ["tes_ids"]
            }
        ),
        types.FunctionDeclaration(
            name="calculate_salary",
            description="Calculate minimum salary based on TES rules",
            parameters={
                "type": "object",
                "properties": {
                    "tes_id": {
                        "type": "string",
                        "description": "TES ID or name"
                    },
                    "role": {
                        "type": "string",
                        "description": "Job role or category"
                    },
                    "experience_years": {
                        "type": "integer",
                        "description": "Years of experience"
                    }
                },
                "required": ["tes_id", "role"]
            }
        ),
        types.FunctionDeclaration(
            name="get_legal_references",
            description="Get Finnish labor law references (TSL, Työaikalaki, Vuosilomalaki) related to a specific topic or TES document",
            parameters={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic to get legal references for (e.g., 'sick_leave', 'overtime', 'vacation', 'notice_periods', 'trial_period')"
                    },
                    "tes_id": {
                        "type": "string",
                        "description": "Optional: Get all legal references relevant to a specific TES document"
                    }
                }
            }
        ),
        types.FunctionDeclaration(
            name="calculate_total_compensation",
            description="Calculate total compensation including base salary, shift work premiums, overtime, and allowances",
            parameters={
                "type": "object",
                "properties": {
                    "tes_id": {
                        "type": "string",
                        "description": "TES ID or name"
                    },
                    "base_salary": {
                        "type": "number",
                        "description": "Monthly base salary in euros"
                    },
                    "evening_hours": {
                        "type": "integer",
                        "description": "Evening shift hours per month"
                    },
                    "night_hours": {
                        "type": "integer",
                        "description": "Night shift hours per month"
                    },
                    "saturday_hours": {
                        "type": "integer",
                        "description": "Saturday hours per month"
                    },
                    "sunday_hours": {
                        "type": "integer",
                        "description": "Sunday hours per month"
                    },
                    "daily_overtime": {
                        "type": "number",
                        "description": "Daily overtime hours"
                    },
                    "weekly_overtime": {
                        "type": "number",
                        "description": "Weekly overtime hours"
                    }
                },
                "required": ["tes_id", "base_salary"]
            }
        ),
        types.FunctionDeclaration(
            name="calculate_vacation_pay",
            description="Calculate vacation pay and vacation bonus (lomaraha) based on TES rules",
            parameters={
                "type": "object",
                "properties": {
                    "tes_id": {
                        "type": "string",
                        "description": "TES ID or name"
                    },
                    "monthly_salary": {
                        "type": "number",
                        "description": "Monthly salary in euros"
                    },
                    "employment_years": {
                        "type": "integer",
                        "description": "Years of employment"
                    },
                    "vacation_days": {
                        "type": "integer",
                        "description": "Optional: Specific number of vacation days to calculate"
                    }
                },
                "required": ["tes_id", "monthly_salary"]
            }
        ),
        types.FunctionDeclaration(
            name="calculate_employer_cost",
            description="Calculate total annual employer cost including salary, contributions, and estimated additional costs",
            parameters={
                "type": "object",
                "properties": {
                    "tes_id": {
                        "type": "string",
                        "description": "TES ID or name"
                    },
                    "monthly_salary": {
                        "type": "number",
                        "description": "Monthly gross salary in euros"
                    },
                    "overtime_hours": {
                        "type": "integer",
                        "description": "Estimated annual overtime hours"
                    },
                    "sick_days": {
                        "type": "integer",
                        "description": "Estimated sick days per year"
                    },
                    "include_shift_work": {
                        "type": "boolean",
                        "description": "Include shift work premium estimate"
                    }
                },
                "required": ["tes_id", "monthly_salary"]
            }
        ),
        types.FunctionDeclaration(
            name="get_stats",
            description="Get statistics about indexed TES documents",
            parameters={
                "type": "object",
                "properties": {}
            }
        )
    ]


def execute_function(name: str, args: dict) -> dict:
    """Execute a function call."""
    try:
        if name == "search_tes":
            results = search_tes(args.get("query", ""), limit=10)
            return {"count": len(results), "results": results}
        
        elif name == "semantic_search":
            try:
                from tools.vector_search import search as vector_search, get_client
                client = get_client()
                results = vector_search(
                    args.get("query", ""),
                    n_results=min(args.get("num_results", 5), 15),
                    tes_filter=args.get("tes_filter"),
                    client=client
                )
                return {"query": args.get("query"), "results": results}
            except ImportError:
                return {"error": "Vector search not available - chromadb not installed"}
            except Exception as e:
                return {"error": f"Vector search failed: {str(e)}"}
        
        elif name == "list_tes":
            results = list_tes(
                industry=args.get("industry"),
                union=args.get("union"),
                valid_only=args.get("valid_only", False),
                limit=20
            )
            return {"count": len(results), "tes": results}
        
        elif name == "get_tes_details":
            tes = get_tes(args.get("tes_id", ""))
            if tes:
                return tes
            return {"error": f"TES not found: {args.get('tes_id')}"}
        
        elif name == "index_tes":
            result = subprocess.run(
                [
                    sys.executable,
                    str(AGENT_DIR / "subagents" / "tes_sourcing.py"),
                    "--search" if not args.get("url") else "--url",
                    args.get("url") or args.get("query", "")
                ],
                capture_output=True,
                text=True,
                cwd=str(AGENT_DIR)
            )
            
            if result.returncode == 0:
                try:
                    tes_data = json.loads(result.stdout)
                    if "error" not in tes_data:
                        store_result = store_tes(tes_data)
                        return {
                            "status": "indexed",
                            "tes_id": tes_data.get("id"),
                            "name": tes_data.get("name"),
                            "stored": store_result
                        }
                    return tes_data
                except json.JSONDecodeError:
                    return {"error": "Failed to parse sourcing result", "output": result.stdout[:500]}
            return {"error": "Sourcing failed", "stderr": result.stderr[:500]}
        
        elif name == "index_multiple_tes":
            import concurrent.futures
            
            tes_list = args.get("tes_list", [])
            if not tes_list:
                return {"error": "No TES documents to index"}
            
            def index_single(tes_item):
                """Index a single TES document."""
                query = tes_item.get("query", "")
                url = tes_item.get("url")
                
                cmd = [
                    sys.executable,
                    str(AGENT_DIR / "subagents" / "tes_sourcing.py"),
                    "--search" if not url else "--url",
                    url or query
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(AGENT_DIR))
                
                if result.returncode == 0:
                    try:
                        tes_data = json.loads(result.stdout)
                        if "error" not in tes_data:
                            store_result = store_tes(tes_data)
                            return {
                                "status": "indexed",
                                "query": query,
                                "tes_id": tes_data.get("id"),
                                "name": tes_data.get("name")
                            }
                        return {"status": "error", "query": query, "error": tes_data.get("error")}
                    except json.JSONDecodeError:
                        return {"status": "error", "query": query, "error": "Parse error"}
                return {"status": "error", "query": query, "error": result.stderr[:200] if result.stderr else "Unknown error"}
            
            # Run all indexing in parallel using ThreadPoolExecutor
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tes_list), 5)) as executor:
                future_to_tes = {executor.submit(index_single, tes): tes for tes in tes_list}
                for future in concurrent.futures.as_completed(future_to_tes):
                    results.append(future.result())
            
            successful = [r for r in results if r.get("status") == "indexed"]
            failed = [r for r in results if r.get("status") == "error"]
            
            return {
                "status": "completed",
                "total": len(tes_list),
                "successful": len(successful),
                "failed": len(failed),
                "results": results
            }
        
        elif name == "compare_tes":
            tes_ids = args.get("tes_ids", [])
            fields = args.get("fields")
            
            cmd = [
                sys.executable,
                str(AGENT_DIR / "subagents" / "tes_comparison.py"),
                "--ids", ",".join(tes_ids),
                "--format", "markdown",
                "--summarize"
            ]
            if fields:
                cmd.extend(["--fields", ",".join(fields)])
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(AGENT_DIR))
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse comparison", "output": result.stdout[:500]}
            return {"error": "Comparison failed", "stderr": result.stderr[:500]}
        
        elif name == "calculate_salary":
            cmd = [
                sys.executable,
                str(AGENT_DIR / "subagents" / "salary_calculator.py"),
                "--tes", args.get("tes_id", ""),
                "--role", args.get("role", ""),
                "--experience", str(args.get("experience_years", 0)),
                "--ai"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(AGENT_DIR))
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"error": "Failed to parse calculation", "output": result.stdout[:500]}
            return {"error": "Calculation failed", "stderr": result.stderr[:500]}
        
        elif name == "get_legal_references":
            from tools.legal_references import (
                get_legal_references as get_refs,
                get_all_references_for_tes,
                compare_to_statutory_minimum
            )
            
            topic = args.get("topic")
            tes_id = args.get("tes_id")
            
            if tes_id:
                tes = get_tes(tes_id)
                if not tes:
                    return {"error": f"TES not found: {tes_id}"}
                refs = get_all_references_for_tes(tes)
                comparisons = compare_to_statutory_minimum(tes)
                return {
                    "tes_name": tes.get("name"),
                    "legal_references": refs,
                    "statutory_comparisons": comparisons
                }
            elif topic:
                refs = get_refs(topic)
                if refs:
                    return {"topic": topic, "references": refs}
                return {"error": f"No references found for topic: {topic}"}
            else:
                return {"error": "Please provide either 'topic' or 'tes_id'"}
        
        elif name == "calculate_total_compensation":
            from tools.salary_calculators import (
                calculate_total_compensation as calc_total,
                get_tes_data
            )
            
            tes_data = get_tes_data(args.get("tes_id", "")) or get_tes(args.get("tes_id", ""))
            if not tes_data:
                return {"error": f"TES not found: {args.get('tes_id')}"}
            
            shift_work = None
            if any([args.get("evening_hours"), args.get("night_hours"), 
                   args.get("saturday_hours"), args.get("sunday_hours")]):
                shift_work = {
                    "evening_hours": args.get("evening_hours", 0),
                    "night_hours": args.get("night_hours", 0),
                    "saturday_hours": args.get("saturday_hours", 0),
                    "sunday_hours": args.get("sunday_hours", 0)
                }
            
            overtime = None
            if args.get("daily_overtime") or args.get("weekly_overtime"):
                overtime = {
                    "daily_overtime_hours": args.get("daily_overtime", 0),
                    "weekly_overtime_hours": args.get("weekly_overtime", 0)
                }
            
            return calc_total(args.get("base_salary", 0), tes_data, shift_work, overtime)
        
        elif name == "calculate_vacation_pay":
            from tools.salary_calculators import calculate_vacation_pay as calc_vacation, get_tes_data
            
            tes_data = get_tes_data(args.get("tes_id", "")) or get_tes(args.get("tes_id", ""))
            if not tes_data:
                return {"error": f"TES not found: {args.get('tes_id')}"}
            
            return calc_vacation(
                args.get("monthly_salary", 0),
                tes_data,
                args.get("employment_years", 1),
                args.get("vacation_days")
            )
        
        elif name == "calculate_employer_cost":
            from tools.salary_calculators import calculate_annual_employer_cost, get_tes_data
            
            tes_data = get_tes_data(args.get("tes_id", "")) or get_tes(args.get("tes_id", ""))
            if not tes_data:
                return {"error": f"TES not found: {args.get('tes_id')}"}
            
            return calculate_annual_employer_cost(
                args.get("monthly_salary", 0),
                tes_data,
                include_shift_work=args.get("include_shift_work", False),
                estimated_overtime_hours=args.get("overtime_hours", 0),
                estimated_sick_days=args.get("sick_days", 10)
            )
        
        elif name == "get_stats":
            return get_stats()
        
        else:
            return {"error": f"Unknown function: {name}"}
    
    except Exception as e:
        return {"error": str(e)}


def build_system_prompt(language: str) -> str:
    """Build system prompt based on language."""
    stats = get_stats()
    
    if language == "fi":
        return f"""Olet TES-agentti (Työehtosopimus-agentti), asiantuntija suomalaisissa työehtosopimuksissa.

Tehtäväsi on auttaa palkanlaskijoita ja HR-ammattilaisia ymmärtämään ja vertailemaan TES-dokumentteja.

Tietokannassa on {stats.get('total_tes', 0)} TES-dokumenttia indeksoituna.

Voit:
1. Etsiä ja indeksoida TES-dokumentteja
2. Tehdä semanttisia hakuja (semantic_search) löytääksesi tietoja TES-sisällöstä
3. Vertailla eri TES:ien ehtoja
4. Laskea minimipalkkoja TES:n perusteella
5. Laskea kokonaiskompensaatioita (peruspalkka + lisät + ylityöt)
6. Laskea lomapalkat ja lomarahat
7. Laskea työnantajan kokonaiskustannukset
8. Hakea lakiviittauksia (TSL, Työaikalaki, Vuosilomalaki)
9. Vastata kysymyksiin työehdoista (palkat, lomat, työajat, irtisanomisajat)

Käytä työkaluja tiedon hakemiseen. Anna aina lähteet (TES-nimi, sivu, osio) vastauksissa.
Kun käyttäjä kysyy lakiin liittyviä asioita, käytä get_legal_references-työkalua.
Jos TES:iä ei löydy tietokannasta, tarjoudu indeksoimaan se.

Vastaa suomeksi kun käyttäjä kirjoittaa suomeksi."""
    
    else:
        return f"""You are the TES Agent (Työehtosopimus-Agent), an expert on Finnish collective bargaining agreements.

Your role is to help payroll specialists and HR professionals understand and compare TES documents.

Currently {stats.get('total_tes', 0)} TES documents are indexed in the database.

You can:
1. Search for and index TES documents
2. Perform semantic search (semantic_search) to find information across TES content
3. Compare terms across different TES agreements
4. Calculate minimum salaries based on TES rules
5. Calculate total compensation (base salary + allowances + overtime)
6. Calculate vacation pay and vacation bonus (lomaraha)
7. Calculate total employer cost including contributions
8. Get legal references (TSL, Työaikalaki, Vuosilomalaki) for TES topics
9. Answer questions about employment terms (salaries, vacation, working hours, notice periods)

Use the available tools to retrieve information. Always cite sources (TES name, page, section) in your answers.
When users ask about legal requirements, use the get_legal_references tool to provide statutory context.
If a TES is not found in the database, offer to index it.

Respond in the same language as the user's query."""


def process_query(query: str, client: genai.Client, history: list = None, log_callback=None) -> tuple[str, list]:
    """Process a user query and return response with updated history.
    
    Uses the Chat API which automatically handles thought signatures for Gemini 3 models.
    
    Args:
        query: User's question
        client: Gemini client
        history: Previous conversation history
        log_callback: Optional function to call with log messages (for streaming to UI)
    """
    import concurrent.futures
    
    def log(msg):
        """Log message to stderr and callback if provided."""
        print(f"[TES-Agent] {msg}", file=sys.stderr)
        if log_callback:
            log_callback(msg)
    
    log(f"Query: {query[:100]}..." if len(query) > 100 else f"Query: {query}")
    
    language = detect_language(query)
    log(f"Language detected: {language}")
    
    tools = [
        types.Tool(
            function_declarations=build_function_declarations()
        )
    ]
    
    config = types.GenerateContentConfig(
        system_instruction=build_system_prompt(language),
        tools=tools,
        temperature=0.3
    )
    
    # Use Chat API - handles thought signatures automatically
    chat = client.chats.create(model=DEFAULT_MODEL, config=config)
    
    # Add previous conversation history
    if history:
        log(f"Loading {len(history)} messages from history")
        for msg in history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                chat._curated_history.append(
                    types.Content(role="user", parts=[types.Part.from_text(content)])
                )
            elif role == 'assistant':
                chat._curated_history.append(
                    types.Content(role="model", parts=[types.Part.from_text(content)])
                )
    
    max_iterations = 15
    log(f"Starting processing (max {max_iterations} iterations)")
    
    # Send initial query
    response = chat.send_message(query)
    text_parts = []
    
    for iteration in range(max_iterations):
        log(f"--- Iteration {iteration + 1}/{max_iterations} ---")
        
        if not response.candidates:
            log("ERROR: No response candidates")
            return "No response generated.", []
        
        candidate = response.candidates[0]
        
        # Check for finish reason
        if hasattr(candidate, 'finish_reason'):
            log(f"Finish reason: {candidate.finish_reason}")
        
        # Get function calls from response
        function_calls = response.function_calls if hasattr(response, 'function_calls') and response.function_calls else []
        
        # Extract text parts
        text_parts = []
        for part in candidate.content.parts:
            if hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        
        if text_parts:
            preview = text_parts[0][:100] + "..." if len(text_parts[0]) > 100 else text_parts[0]
            log(f"Text response: {preview}")
        
        # If no function calls, we're done
        if not function_calls:
            log(f"DONE: No more function calls, returning response")
            final_text = " ".join(text_parts).strip()
            return final_text if final_text else "I couldn't generate a response.", []
        
        log(f"Function calls: {len(function_calls)}")
        
        # Execute function calls
        def execute_and_log(fc):
            """Execute a function call and return result."""
            args = dict(fc.args) if fc.args else {}
            args_preview = str(args)[:100] + "..." if len(str(args)) > 100 else str(args)
            log(f"  [START] {fc.name}({args_preview})")
            
            result = execute_function(fc.name, args)
            
            # Log result summary
            if isinstance(result, dict):
                if "error" in result:
                    log(f"  [DONE] {fc.name} -> ERROR: {result.get('error', '')[:100]}")
                elif "count" in result:
                    log(f"  [DONE] {fc.name} -> {result['count']} items")
                else:
                    log(f"  [DONE] {fc.name} -> keys: {list(result.keys())[:5]}")
            else:
                log(f"  [DONE] {fc.name} -> {str(result)[:50]}")
            
            return (fc, result)
        
        # Execute function calls (parallel if multiple)
        results = []
        if len(function_calls) > 1:
            log(f"  Running {len(function_calls)} calls in PARALLEL...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(function_calls), 10)) as executor:
                futures = {executor.submit(execute_and_log, fc): fc for fc in function_calls}
                results_map = {}
                for future in concurrent.futures.as_completed(futures):
                    fc, result = future.result()
                    results_map[id(fc)] = (fc, result)
                # Preserve original order
                for fc in function_calls:
                    results.append(results_map[id(fc)])
        else:
            for fc in function_calls:
                results.append(execute_and_log(fc))
        
        # Build function response parts
        function_response_parts = []
        for fc, result in results:
            function_response_parts.append(
                types.Part.from_function_response(
                    name=fc.name,
                    response={"result": result} if not isinstance(result, dict) else result
                )
            )
        
        # Send function responses using chat API (handles thought signatures automatically)
        response = chat.send_message(function_response_parts)
    
    log(f"ERROR: Maximum iterations ({max_iterations}) reached!")
    
    if text_parts:
        return " ".join(text_parts).strip(), []
    
    return "Maximum iterations reached. Please try a simpler query.", []


def chat_mode(client: genai.Client):
    """Interactive chat mode."""
    print("\n" + "="*60)
    print("TES Agent - Työehtosopimus-agentti")
    print("="*60)
    print("Ask about Finnish collective bargaining agreements.")
    print("Type 'exit' or 'quit' to end.\n")
    
    history = []
    
    while True:
        try:
            query = input("You: ").strip()
            if not query:
                continue
            if query.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            
            response, history = process_query(query, client, history)
            print(f"\nAgent: {response}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    parser = argparse.ArgumentParser(description="TES Agent - Finnish Collective Bargaining Agreement Assistant")
    parser.add_argument("query", nargs="?", help="Query to process")
    parser.add_argument("--chat", action="store_true", help="Interactive chat mode")
    parser.add_argument("--index", help="Index a TES by name/search query")
    parser.add_argument("--compare", help="Comma-separated TES IDs to compare")
    parser.add_argument("--list", action="store_true", help="List all indexed TES")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    
    args = parser.parse_args()
    
    try:
        init_database()
    except:
        pass
    
    if args.chat:
        client = get_client()
        chat_mode(client)
    
    elif args.index:
        client = get_client()
        result = execute_function("index_tes", {"query": args.index})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.compare:
        client = get_client()
        tes_ids = [id.strip() for id in args.compare.split(",")]
        result = execute_function("compare_tes", {"tes_ids": tes_ids})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.list:
        results = list_tes(limit=50)
        print(json.dumps({"count": len(results), "tes": results}, ensure_ascii=False, indent=2))
    
    elif args.stats:
        stats = get_stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    elif args.query:
        client = get_client()
        response, _ = process_query(args.query, client)
        print(response)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
