#!/usr/bin/env python3
"""
Salary Calculator Sub-Agent

Calculates minimum salaries based on TES rules.

Usage:
    python salary_calculator.py --tes "tes_teknologiateollisuus_2024" --role "engineer" --experience 5
    python salary_calculator.py --tes-name "Teknologiateollisuuden TES" --role "specialist" --experience 3
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_env import load_agent_environment
from memory.memory import get_tes, list_tes, search_tes, get_salary_tables

load_agent_environment()

from google import genai
from google.genai import types

DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"


def get_client() -> genai.Client:
    """Get Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_AI_STUDIO_KEY required")
    return genai.Client(api_key=api_key)


def find_tes(tes_id: Optional[str] = None, tes_name: Optional[str] = None) -> Optional[dict]:
    """Find TES by ID or name."""
    if tes_id:
        return get_tes(tes_id)
    
    if tes_name:
        results = search_tes(tes_name, limit=1)
        if results:
            return get_tes(results[0]["id"])
    
    return None


def find_matching_salary(
    tes_data: dict,
    role: str,
    experience_years: int
) -> dict:
    """Find the matching salary from TES salary tables."""
    salary_tables = tes_data.get("salary_tables", [])
    
    if not salary_tables:
        return {
            "error": "No salary tables found in this TES",
            "tes_name": tes_data.get("name")
        }
    
    matches = []
    role_lower = role.lower()
    
    for table in salary_tables:
        table_role = (table.get("role_category") or table.get("table_name") or "").lower()
        
        role_match_score = 0
        if role_lower in table_role or table_role in role_lower:
            role_match_score = 2
        elif any(word in table_role for word in role_lower.split()):
            role_match_score = 1
        
        if role_match_score == 0 and len(salary_tables) > 1:
            continue
        
        exp_levels = table.get("experience_levels", [])
        
        if exp_levels:
            best_level = None
            for level in exp_levels:
                level_str = str(level.get("level", "0"))
                
                try:
                    if "-" in level_str:
                        parts = level_str.replace(" ", "").split("-")
                        min_years = int(parts[0]) if parts[0].isdigit() else 0
                        max_years = int(parts[1]) if parts[1].isdigit() else 99
                    elif "+" in level_str or ">" in level_str:
                        min_years = int(''.join(filter(str.isdigit, level_str)) or 0)
                        max_years = 99
                    elif "<" in level_str:
                        min_years = 0
                        max_years = int(''.join(filter(str.isdigit, level_str)) or 99)
                    else:
                        years = int(''.join(filter(str.isdigit, level_str)) or 0)
                        min_years = years
                        max_years = years + 4
                    
                    if min_years <= experience_years <= max_years:
                        if best_level is None or min_years > int(''.join(filter(str.isdigit, str(best_level.get("level", "0")))) or 0):
                            best_level = level
                    elif experience_years >= min_years and best_level is None:
                        best_level = level
                
                except (ValueError, IndexError):
                    if best_level is None:
                        best_level = level
            
            if best_level:
                matches.append({
                    "role_category": table.get("role_category") or table.get("table_name"),
                    "experience_level": best_level.get("level"),
                    "minimum_salary": best_level.get("minimum_salary"),
                    "hourly_rate": best_level.get("hourly_rate"),
                    "effective_date": table.get("effective_date"),
                    "pdf_page": table.get("pdf_page"),
                    "section": table.get("section"),
                    "match_score": role_match_score
                })
        
        elif table.get("minimum_salary"):
            matches.append({
                "role_category": table.get("role_category") or table.get("table_name"),
                "minimum_salary": table.get("minimum_salary"),
                "effective_date": table.get("effective_date"),
                "pdf_page": table.get("pdf_page"),
                "section": table.get("section"),
                "match_score": role_match_score
            })
    
    if not matches:
        return {
            "error": f"No matching salary found for role '{role}'",
            "tes_name": tes_data.get("name"),
            "available_roles": [t.get("role_category") or t.get("table_name") for t in salary_tables]
        }
    
    matches.sort(key=lambda x: (-x.get("match_score", 0), -(x.get("minimum_salary") or 0)))
    
    return {
        "best_match": matches[0],
        "other_matches": matches[1:] if len(matches) > 1 else [],
        "tes_name": tes_data.get("name"),
        "tes_validity": f"{tes_data.get('validity_start', '?')} - {tes_data.get('validity_end', '?')}"
    }


def ai_calculate_salary(
    tes_data: dict,
    role: str,
    experience_years: int,
    additional_factors: Optional[dict] = None,
    client: genai.Client = None
) -> dict:
    """Use AI to interpret salary rules and calculate."""
    if client is None:
        client = get_client()
    
    salary_tables = tes_data.get("salary_tables", [])
    bonuses = tes_data.get("bonuses", {})
    working_hours = tes_data.get("working_hours", {})
    
    prompt = f"""Calculate the minimum salary based on this Finnish TES (Työehtosopimus).

TES: {tes_data.get('name')}
Role requested: {role}
Experience years: {experience_years}
{f"Additional factors: {json.dumps(additional_factors)}" if additional_factors else ""}

Salary tables from TES:
{json.dumps(salary_tables, ensure_ascii=False, indent=2)}

Bonuses and allowances:
{json.dumps(bonuses, ensure_ascii=False, indent=2)}

Working hours:
{json.dumps(working_hours, ensure_ascii=False, indent=2)}

Calculate and return JSON with:
{{
    "base_monthly_salary": <number>,
    "hourly_rate": <number if applicable>,
    "role_category_used": "<which role category was matched>",
    "experience_level_used": "<which experience level was applied>",
    "applicable_bonuses": [
        {{"name": "<bonus name>", "amount": "<amount or percentage>", "conditions": "<when applicable>"}}
    ],
    "total_with_typical_bonuses": <estimated total if typical bonuses apply>,
    "calculation_notes": "<explanation of how the salary was determined>",
    "citations": [
        {{"field": "<field name>", "pdf_page": <page>, "section": "<section>"}}
    ]
}}

Return ONLY valid JSON."""

    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1)
        )
        
        text = response.text.strip()
        if text.startswith("```"):
            import re
            text = re.sub(r'^```(?:json)?\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
        
        result = json.loads(text)
        result["tes_name"] = tes_data.get("name")
        result["tes_id"] = tes_data.get("id")
        result["query"] = {
            "role": role,
            "experience_years": experience_years,
            "additional_factors": additional_factors
        }
        
        return result
        
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse AI response: {str(e)}",
            "raw_response": text[:1000] if 'text' in dir() else None
        }
    except Exception as e:
        return {"error": f"AI calculation failed: {str(e)}"}


def calculate_salary(
    tes_id: Optional[str] = None,
    tes_name: Optional[str] = None,
    role: str = "",
    experience_years: int = 0,
    use_ai: bool = False,
    additional_factors: Optional[dict] = None
) -> dict:
    """Calculate salary based on TES rules."""
    tes_data = find_tes(tes_id, tes_name)
    
    if not tes_data:
        return {
            "error": f"TES not found: {tes_id or tes_name}",
            "hint": "Use 'memory.py list' to see available TES documents"
        }
    
    if use_ai:
        return ai_calculate_salary(
            tes_data, role, experience_years, additional_factors
        )
    
    result = find_matching_salary(tes_data, role, experience_years)
    
    if "error" not in result and result.get("best_match"):
        match = result["best_match"]
        bonuses = tes_data.get("bonuses", {})
        
        result["applicable_bonuses"] = []
        if bonuses:
            for key, value in bonuses.items():
                if key not in ["pdf_page", "section"] and value:
                    result["applicable_bonuses"].append({
                        "name": key.replace("_", " ").title(),
                        "value": value
                    })
    
    result["query"] = {
        "role": role,
        "experience_years": experience_years
    }
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Salary Calculator Sub-Agent")
    parser.add_argument("--tes", help="TES ID")
    parser.add_argument("--tes-name", help="TES name (will search)")
    parser.add_argument("--role", required=True, help="Job role/category")
    parser.add_argument("--experience", type=int, default=0, help="Years of experience")
    parser.add_argument("--ai", action="store_true", help="Use AI for complex calculation")
    parser.add_argument("--shift", action="store_true", help="Include shift work")
    parser.add_argument("--evening", action="store_true", help="Include evening work")
    parser.add_argument("--night", action="store_true", help="Include night work")
    
    args = parser.parse_args()
    
    if not args.tes and not args.tes_name:
        print(json.dumps({"error": "Must provide --tes or --tes-name"}))
        sys.exit(1)
    
    additional_factors = {}
    if args.shift:
        additional_factors["shift_work"] = True
    if args.evening:
        additional_factors["evening_work"] = True
    if args.night:
        additional_factors["night_work"] = True
    
    result = calculate_salary(
        tes_id=args.tes,
        tes_name=args.tes_name,
        role=args.role,
        experience_years=args.experience,
        use_ai=args.ai,
        additional_factors=additional_factors if additional_factors else None
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
