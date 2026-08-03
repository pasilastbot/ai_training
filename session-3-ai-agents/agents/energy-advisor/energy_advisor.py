#!/usr/bin/env python3
"""
Energy Advisor Agent

AI-powered energy advisor for building heating optimization.
Provides advice on energy savings, district heating, demand response,
and Leanheat Building technology. Supports video avatar responses.

Usage:
    python energy_advisor.py --chat                    # Interactive chat
    python energy_advisor.py "How can I save energy?"  # Single query
    python energy_advisor.py --apartment list          # Manage apartments
    python energy_advisor.py --video "Tell me about Leanheat"  # Video response
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from agent_env import load_agent_environment
load_agent_environment()

from google import genai
from google.genai import types

from memory.memory import (
    get_apartment, get_apartment_by_customer, list_apartments, create_apartment,
    update_apartment, search_apartments, get_apartment_summary, get_recommendations,
    create_recommendation, store_video_response, get_stats, init_database
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
        'missä', 'mitä', 'milloin', 'paljonko', 'mikä', 'miten',
        'energia', 'lämmitys', 'kaukolämpö', 'säästö', 'rakennus',
        'asunto', 'lämpötila', 'kulutus', 'kustannus', 'optimointi'
    ]
    text_lower = text.lower()
    finnish_count = sum(1 for word in finnish_indicators if word in text_lower)
    return "fi" if finnish_count >= 2 else "en"


def build_function_declarations() -> list:
    """Build function declarations for Gemini."""
    return [
        types.FunctionDeclaration(
            name="search_leanheat_knowledge",
            description="Search the Leanheat Building knowledge base for information about AI-powered heating optimization, energy savings, demand response, and district heating technology",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query about energy optimization, Leanheat features, or heating technology"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["feature", "benefit", "technology", "use_case", "statistic", "integration"],
                        "description": "Optional category filter"
                    }
                },
                "required": ["query"]
            }
        ),
        types.FunctionDeclaration(
            name="create_customer_apartment",
            description="Create a new customer apartment profile to store their building details for personalized energy advice",
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Unique customer identifier"
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name"
                    },
                    "city": {
                        "type": "string",
                        "description": "City where the apartment is located"
                    },
                    "building_type": {
                        "type": "string",
                        "enum": ["apartment", "house", "townhouse", "row_house", "commercial", "office"],
                        "description": "Type of building"
                    },
                    "size_sqm": {
                        "type": "number",
                        "description": "Apartment size in square meters"
                    },
                    "heating_type": {
                        "type": "string",
                        "enum": ["district_heating", "electric", "heat_pump", "oil", "gas", "geothermal"],
                        "description": "Primary heating system type"
                    },
                    "construction_year": {
                        "type": "integer",
                        "description": "Year the building was constructed"
                    },
                    "has_smart_controls": {
                        "type": "boolean",
                        "description": "Whether smart heating controls are installed"
                    }
                },
                "required": ["customer_id"]
            }
        ),
        types.FunctionDeclaration(
            name="get_customer_apartment",
            description="Get details of a customer's apartment for personalized energy advice",
            parameters={
                "type": "object",
                "properties": {
                    "apartment_id": {
                        "type": "string",
                        "description": "Apartment ID"
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "Or use customer ID to find their apartment"
                    }
                }
            }
        ),
        types.FunctionDeclaration(
            name="update_apartment_details",
            description="Update customer apartment details with new information",
            parameters={
                "type": "object",
                "properties": {
                    "apartment_id": {
                        "type": "string",
                        "description": "Apartment ID to update"
                    },
                    "annual_heating_kwh": {
                        "type": "number",
                        "description": "Annual heating energy consumption in kWh"
                    },
                    "annual_cost_eur": {
                        "type": "number",
                        "description": "Annual energy cost in EUR"
                    },
                    "preferred_temp_c": {
                        "type": "number",
                        "description": "Preferred indoor temperature in Celsius"
                    },
                    "residents_count": {
                        "type": "integer",
                        "description": "Number of residents"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional notes about the apartment"
                    }
                },
                "required": ["apartment_id"]
            }
        ),
        types.FunctionDeclaration(
            name="list_customer_apartments",
            description="List all registered customer apartments",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results"
                    }
                }
            }
        ),
        types.FunctionDeclaration(
            name="search_apartments",
            description="Search apartments by city, building type, or heating system",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (city, building type, heating type)"
                    }
                },
                "required": ["query"]
            }
        ),
        types.FunctionDeclaration(
            name="create_energy_recommendation",
            description="Create an energy saving recommendation for a customer's apartment",
            parameters={
                "type": "object",
                "properties": {
                    "apartment_id": {
                        "type": "string",
                        "description": "Apartment to recommend for"
                    },
                    "recommendation_type": {
                        "type": "string",
                        "enum": ["temperature_optimization", "smart_controls", "insulation", "behavior_change", "equipment_upgrade", "demand_response"],
                        "description": "Type of recommendation"
                    },
                    "title": {
                        "type": "string",
                        "description": "Recommendation title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed recommendation description"
                    },
                    "estimated_savings_percent": {
                        "type": "number",
                        "description": "Estimated energy savings percentage"
                    },
                    "estimated_savings_eur": {
                        "type": "number",
                        "description": "Estimated annual savings in EUR"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Implementation priority"
                    }
                },
                "required": ["apartment_id", "recommendation_type", "title"]
            }
        ),
        types.FunctionDeclaration(
            name="get_apartment_recommendations",
            description="Get all energy saving recommendations for an apartment",
            parameters={
                "type": "object",
                "properties": {
                    "apartment_id": {
                        "type": "string",
                        "description": "Apartment ID"
                    }
                },
                "required": ["apartment_id"]
            }
        ),
        types.FunctionDeclaration(
            name="generate_video_response",
            description="Generate a video response using the energy advisor avatar. Use for important explanations, greetings, or when customer requests video.",
            parameters={
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "Text for the advisor avatar to speak (keep concise, 2-4 sentences)"
                    },
                    "voice": {
                        "type": "string",
                        "description": "Voice to use (default: Puck for male)"
                    }
                },
                "required": ["script"]
            }
        ),
        types.FunctionDeclaration(
            name="get_system_stats",
            description="Get statistics about registered apartments and recommendations",
            parameters={"type": "object", "properties": {}}
        )
    ]


def execute_function(name: str, args: dict) -> dict:
    """Execute a function call."""
    try:
        if name == "search_leanheat_knowledge":
            from subagents.knowledge_search import search_knowledge
            return search_knowledge(
                args.get("query"),
                use_google_fallback=True,
                synthesize=True
            )
        
        elif name == "create_customer_apartment":
            return create_apartment(
                customer_id=args.get("customer_id"),
                customer_name=args.get("customer_name"),
                address={"city": args.get("city")} if args.get("city") else None,
                building_info={
                    "building_type": args.get("building_type"),
                    "construction_year": args.get("construction_year")
                } if args.get("building_type") or args.get("construction_year") else None,
                apartment_details={"size_sqm": args.get("size_sqm")} if args.get("size_sqm") else None,
                heating_system={
                    "type": args.get("heating_type"),
                    "has_smart_controls": args.get("has_smart_controls", False)
                } if args.get("heating_type") else None
            )
        
        elif name == "get_customer_apartment":
            if args.get("apartment_id"):
                apartment = get_apartment(args.get("apartment_id"))
            elif args.get("customer_id"):
                apartment = get_apartment_by_customer(args.get("customer_id"))
            else:
                return {"error": "apartment_id or customer_id required"}
            
            if apartment:
                return get_apartment_summary(apartment.get("id"))
            return {"error": "Apartment not found"}
        
        elif name == "update_apartment_details":
            updates = {}
            if args.get("annual_heating_kwh"):
                updates["energy_consumption"] = {"annual_heating_kwh": args["annual_heating_kwh"]}
            if args.get("annual_cost_eur"):
                updates.setdefault("energy_consumption", {})["annual_cost_eur"] = args["annual_cost_eur"]
            if args.get("preferred_temp_c"):
                updates["preferences"] = {"preferred_temp_c": args["preferred_temp_c"]}
            if args.get("residents_count"):
                updates["occupancy"] = {"residents_count": args["residents_count"]}
            if args.get("notes"):
                updates["notes"] = args["notes"]
            
            return update_apartment(args.get("apartment_id"), updates)
        
        elif name == "list_customer_apartments":
            return {"apartments": list_apartments(args.get("limit", 20))}
        
        elif name == "search_apartments":
            return {"results": search_apartments(args.get("query"))}
        
        elif name == "create_energy_recommendation":
            return create_recommendation(
                apartment_id=args.get("apartment_id"),
                recommendation_type=args.get("recommendation_type"),
                title=args.get("title"),
                description=args.get("description"),
                estimated_savings_eur=args.get("estimated_savings_eur"),
                estimated_savings_percent=args.get("estimated_savings_percent"),
                priority=args.get("priority", "medium")
            )
        
        elif name == "get_apartment_recommendations":
            return {"recommendations": get_recommendations(args.get("apartment_id"))}
        
        elif name == "generate_video_response":
            from tools.generate_video_response import generate_video_response
            result = generate_video_response(
                script=args.get("script"),
                voice=args.get("voice", "Puck (Male)")
            )
            
            if result.get("status") == "success":
                store_video_response(
                    question="Agent-generated response",
                    answer=args.get("script"),
                    video_path=result.get("video_path")
                )
            
            return result
        
        elif name == "get_system_stats":
            return get_stats()
        
        else:
            return {"error": f"Unknown function: {name}"}
    
    except Exception as e:
        return {"error": str(e)}


def build_system_prompt(language: str, apartment_context: dict = None) -> str:
    """Build system prompt based on language and context."""
    stats = get_stats()
    
    apartment_info = ""
    if apartment_context:
        apartment_info = f"""
Current customer apartment:
- Customer: {apartment_context.get('customer', 'Unknown')}
- Location: {apartment_context.get('location', 'Unknown')}
- Building: {apartment_context.get('building_type', 'Unknown')}, {apartment_context.get('size_sqm', 'N/A')} sqm
- Heating: {apartment_context.get('heating_type', 'Unknown')}
- Smart controls: {'Yes' if apartment_context.get('has_smart_controls') else 'No'}
- Energy class: {apartment_context.get('energy_class', 'N/A')}
"""
    
    if language == "fi":
        return f"""Olet energianeuvoja-agentti, joka on erikoistunut Leanheat Building -teknologiaan ja rakennusten lämmityksen optimointiin.

Tehtäväsi:
1. Vastata kysymyksiin energiansäästöstä, kaukolämmöstä ja älykkäästä lämmönohjauksesta
2. Antaa henkilökohtaisia neuvoja perustuen asiakkaan rakennuksen tietoihin
3. Selittää Leanheat Building -teknologian hyötyjä ja ominaisuuksia
4. Luoda energiansäästösuosituksia asiakkaille
5. Kertoa kysyntäjoustosta ja sen hyödyistä

Leanheat Building -avaintiedot:
- AI-pohjainen lämmönoptimointijärjestelmä
- Tyypillisesti 10-20% energiansäästöt
- Parantaa sisäilman laatua ja mukavuutta
- Integroituu kaukolämpöjärjestelmiin
- Tukee kysyntäjoustoa ja huippukuormien tasausta

Tietokannassa on {stats.get('total_apartments', 0)} rekisteröityä asuntoa.
{apartment_info}

Vastaa selkeästi ja ammattimaisesti. Tarjoa konkreettisia neuvoja ja lukuja kun mahdollista."""
    
    else:
        return f"""You are an Energy Advisor agent specializing in Leanheat Building technology and building heating optimization.

Your tasks:
1. Answer questions about energy savings, district heating, and smart heating controls
2. Provide personalized advice based on customer building information
3. Explain Leanheat Building technology benefits and features
4. Create energy saving recommendations for customers
5. Educate about demand response and its benefits

Leanheat Building key facts:
- AI-powered heating optimization system
- Typically delivers 10-20% energy savings
- Improves indoor air quality and comfort
- Integrates with district heating systems
- Supports demand response and peak load management
- Reduces CO2 emissions through smarter heating

Database has {stats.get('total_apartments', 0)} registered apartments.
{apartment_info}

Search the Leanheat knowledge base for accurate, up-to-date information.
Provide clear, professional answers with specific numbers and benefits when possible.
When discussing energy savings, be realistic and cite typical ranges.
Offer to generate video responses for complex explanations."""


def process_query(
    query: str,
    client: genai.Client,
    apartment_id: str = None,
    customer_id: str = None,
    history: list = None,
    generate_video: bool = False,
    log_callback=None
) -> tuple[str, list, dict]:
    """Process a user query and return response with updated history."""
    def log(msg):
        print(f"[EnergyAdvisor] {msg}", file=sys.stderr)
        if log_callback:
            log_callback(msg)
    
    log(f"Query: {query[:100]}..." if len(query) > 100 else f"Query: {query}")
    
    language = detect_language(query)
    log(f"Language: {language}")
    
    apartment_context = None
    if apartment_id:
        apartment_context = get_apartment_summary(apartment_id)
        log(f"Apartment context loaded: {apartment_id}")
    elif customer_id:
        apartment = get_apartment_by_customer(customer_id)
        if apartment:
            apartment_context = get_apartment_summary(apartment.get("id"))
            log(f"Customer apartment loaded: {customer_id}")
    
    tools = [types.Tool(
        function_declarations=build_function_declarations(),
        google_search=types.GoogleSearch()
    )]
    
    config = types.GenerateContentConfig(
        system_instruction=build_system_prompt(language, apartment_context),
        tools=tools,
        temperature=0.4
    )
    
    contents = []
    
    if history:
        log(f"Loading {len(history)} messages from history")
        for msg in history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                contents.append(types.Content(role="user", parts=[types.Part(text=content)]))
            elif role == 'assistant':
                contents.append(types.Content(role="model", parts=[types.Part(text=content)]))
    
    if generate_video:
        query = f"{query}\n\n[Please generate a video response for this answer]"
    
    contents.append(types.Content(role="user", parts=[types.Part(text=query)]))
    
    max_iterations = 10
    log(f"Starting processing (max {max_iterations} iterations)")
    
    video_result = None
    
    for iteration in range(max_iterations):
        log(f"--- Iteration {iteration + 1}/{max_iterations} ---")
        
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=contents,
            config=config
        )
        
        if not response.candidates:
            log("ERROR: No response candidates")
            return "No response generated.", [], None
        
        candidate = response.candidates[0]
        
        function_calls = []
        text_parts = []
        
        for part in candidate.content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                function_calls.append(part.function_call)
            elif hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        
        if text_parts:
            preview = text_parts[0][:100] + "..." if len(text_parts[0]) > 100 else text_parts[0]
            log(f"Text: {preview}")
        
        if not function_calls:
            log("DONE: No more function calls")
            final_text = " ".join(text_parts).strip()
            return final_text if final_text else "I couldn't generate a response.", [], video_result
        
        log(f"Function calls: {len(function_calls)}")
        contents.append(candidate.content)
        
        import concurrent.futures
        
        def execute_and_log(fc):
            args = dict(fc.args) if fc.args else {}
            args_preview = str(args)[:80] + "..." if len(str(args)) > 80 else str(args)
            log(f"  [START] {fc.name}({args_preview})")
            
            result = execute_function(fc.name, args)
            
            if fc.name == "generate_video_response":
                nonlocal video_result
                video_result = result
            
            if isinstance(result, dict) and "error" in result:
                log(f"  [DONE] {fc.name} -> ERROR: {result['error'][:80]}")
            else:
                log(f"  [DONE] {fc.name} -> OK")
            
            return (fc.name, result)
        
        function_response_parts = []
        if len(function_calls) > 1:
            log(f"  Running {len(function_calls)} calls in PARALLEL...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(function_calls), 10)) as executor:
                futures = {executor.submit(execute_and_log, fc): fc for fc in function_calls}
                results_map = {}
                for future in concurrent.futures.as_completed(futures):
                    fc = futures[future]
                    name, result = future.result()
                    results_map[id(fc)] = result
                
                for fc in function_calls:
                    result = results_map[id(fc)]
                    function_response_parts.append(
                        types.Part.from_function_response(name=fc.name, response=result)
                    )
        else:
            for fc in function_calls:
                name, result = execute_and_log(fc)
                function_response_parts.append(
                    types.Part.from_function_response(name=fc.name, response=result)
                )
        
        contents.append(types.Content(role="user", parts=function_response_parts))
    
    log(f"ERROR: Maximum iterations ({max_iterations}) reached!")
    
    if text_parts:
        return " ".join(text_parts).strip(), [], video_result
    
    return "Maximum iterations reached. Please try a simpler query.", [], video_result


def chat_mode(client: genai.Client, apartment_id: str = None, customer_id: str = None):
    """Interactive chat mode."""
    print("\n" + "="*60)
    print("Energy Advisor - AI-Powered Building Energy Expert")
    print("Powered by Leanheat Building Technology")
    print("="*60)
    print("Ask me about energy savings, heating optimization,")
    print("or Leanheat Building features. Type 'exit' to end.\n")
    
    if apartment_id:
        apartment = get_apartment(apartment_id)
        if apartment:
            print(f"Loaded apartment: {apartment.get('customer_name', apartment_id)}")
            print(f"Heating: {apartment.get('heating_system', {}).get('type', 'Unknown')}\n")
    
    history = []
    
    while True:
        try:
            query = input("You: ").strip()
            if not query:
                continue
            if query.lower() in ['exit', 'quit', 'q']:
                print("Thank you for using Energy Advisor. Save energy!")
                break
            
            generate_video = query.lower().startswith("video:")
            if generate_video:
                query = query[6:].strip()
            
            response, history, video = process_query(
                query, client, apartment_id, customer_id, history, generate_video
            )
            print(f"\nAdvisor: {response}")
            
            if video and video.get("status") == "success":
                print(f"\n📹 Video generated: {video.get('video_path')}")
            
            print()
            
        except KeyboardInterrupt:
            print("\nThank you for using Energy Advisor!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    parser = argparse.ArgumentParser(description="Energy Advisor Agent - AI Building Energy Expert")
    parser.add_argument("query", nargs="?", help="Query to process")
    parser.add_argument("--chat", action="store_true", help="Interactive chat mode")
    parser.add_argument("--apartment-id", "-a", help="Use specific apartment context")
    parser.add_argument("--customer-id", "-c", help="Use customer's apartment context")
    parser.add_argument("--apartment", nargs="+", help="Apartment operations: create | list | get <id>")
    parser.add_argument("--video", action="store_true", help="Generate video response")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    try:
        init_database()
    except:
        pass
    
    if args.chat:
        client = get_client()
        chat_mode(client, args.apartment_id, args.customer_id)
    
    elif args.apartment:
        action = args.apartment[0]
        if action == "create":
            customer_id = input("Customer ID: ").strip() or None
            customer_name = input("Customer Name: ").strip()
            result = create_apartment(
                customer_id=customer_id or "cust_" + str(hash(customer_name))[:8],
                customer_name=customer_name
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif action == "list":
            result = list_apartments()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif action == "get" and len(args.apartment) > 1:
            result = get_apartment(args.apartment[1])
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Usage: --apartment create | list | get <id>")
    
    elif args.stats:
        stats = get_stats()
        print(json.dumps(stats, indent=2))
    
    elif args.query:
        client = get_client()
        response, _, video = process_query(
            args.query, client, args.apartment_id, args.customer_id, 
            generate_video=args.video
        )
        print(response)
        if video and video.get("status") == "success":
            print(f"\n📹 Video: {video.get('video_path')}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
