#!/usr/bin/env python3
"""
TES Comparison Sub-Agent

Compares multiple TES documents side-by-side.

Usage:
    python tes_comparison.py --ids tes_1 tes_2 tes_3
    python tes_comparison.py --ids tes_1 tes_2 --fields salary_tables,vacation,working_hours
    python tes_comparison.py --ids tes_1 tes_2 --format markdown
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_env import load_agent_environment
from memory.memory import get_tes, list_tes

load_agent_environment()

from google import genai
from google.genai import types

DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"

COMPARABLE_FIELDS = [
    "salary_tables",
    "working_hours",
    "vacation",
    "sick_leave",
    "notice_periods",
    "bonuses",
    "trial_period"
]


def get_client() -> genai.Client:
    """Get Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_AI_STUDIO_KEY required")
    return genai.Client(api_key=api_key)


def extract_field(tes_data: dict, field: str) -> dict:
    """Extract a specific field from TES data."""
    result = {
        "name": tes_data.get("name", "Unknown"),
        "id": tes_data.get("id"),
        "validity": f"{tes_data.get('validity_start', '?')} - {tes_data.get('validity_end', '?')}",
        "value": tes_data.get(field)
    }
    return result


def compare_field(tes_list: list[dict], field: str) -> dict:
    """Compare a specific field across multiple TES documents."""
    comparison = {
        "field": field,
        "tes_count": len(tes_list),
        "values": []
    }
    
    for tes in tes_list:
        extracted = extract_field(tes, field)
        comparison["values"].append(extracted)
    
    return comparison


def generate_comparison_table(comparisons: list[dict], format_type: str = "json") -> str:
    """Generate comparison output in specified format."""
    if format_type == "json":
        return json.dumps(comparisons, ensure_ascii=False, indent=2)
    
    elif format_type == "markdown":
        output = []
        for comp in comparisons:
            field = comp["field"]
            output.append(f"\n## {field.replace('_', ' ').title()}\n")
            
            if field == "salary_tables":
                output.append("| TES | Role | Experience | Min Salary | Effective |")
                output.append("|-----|------|------------|------------|-----------|")
                for val in comp["values"]:
                    tes_name = val["name"][:30]
                    tables = val.get("value") or []
                    if isinstance(tables, list):
                        for table in tables[:3]:
                            role = table.get("role_category", "-")[:20]
                            levels = table.get("experience_levels", [])
                            if levels:
                                for level in levels[:2]:
                                    exp = str(level.get("level", "-"))[:15]
                                    salary = level.get("minimum_salary", "-")
                                    if isinstance(salary, (int, float)):
                                        salary = f"€{salary:,.0f}"
                                    eff = table.get("effective_date", "-")
                                    output.append(f"| {tes_name} | {role} | {exp} | {salary} | {eff} |")
                            else:
                                salary = table.get("minimum_salary", "-")
                                if isinstance(salary, (int, float)):
                                    salary = f"€{salary:,.0f}"
                                output.append(f"| {tes_name} | {role} | - | {salary} | - |")
                    else:
                        output.append(f"| {tes_name} | - | - | - | - |")
            
            elif field == "working_hours":
                output.append("| TES | Weekly Hours | Daily Hours | Annual Hours |")
                output.append("|-----|--------------|-------------|--------------|")
                for val in comp["values"]:
                    tes_name = val["name"][:30]
                    hours = val.get("value") or {}
                    weekly = hours.get("weekly_hours", "-")
                    daily = hours.get("daily_hours", "-")
                    annual = hours.get("annual_hours", "-")
                    output.append(f"| {tes_name} | {weekly} | {daily} | {annual} |")
            
            elif field == "vacation":
                output.append("| TES | First Year | Standard | Senior | Senior After |")
                output.append("|-----|------------|----------|--------|--------------|")
                for val in comp["values"]:
                    tes_name = val["name"][:30]
                    vac = val.get("value") or {}
                    first = vac.get("days_first_year", "-")
                    std = vac.get("days_standard", "-")
                    senior = vac.get("days_senior", "-")
                    threshold = vac.get("senior_threshold_years", "-")
                    if threshold != "-":
                        threshold = f"{threshold} yrs"
                    output.append(f"| {tes_name} | {first} | {std} | {senior} | {threshold} |")
            
            elif field == "notice_periods":
                output.append("| TES | Type | Service Years | Notice Period |")
                output.append("|-----|------|---------------|---------------|")
                for val in comp["values"]:
                    tes_name = val["name"][:30]
                    periods = val.get("value") or {}
                    for notice_type in ["employee_notice", "employer_notice"]:
                        notices = periods.get(notice_type, [])
                        type_label = "Employee" if "employee" in notice_type else "Employer"
                        if isinstance(notices, list):
                            for n in notices[:3]:
                                years = n.get("service_years", "-")
                                period = n.get("notice_period", "-")
                                output.append(f"| {tes_name} | {type_label} | {years} | {period} |")
            
            else:
                output.append("| TES | Validity | Value |")
                output.append("|-----|----------|-------|")
                for val in comp["values"]:
                    tes_name = val["name"][:30]
                    validity = val["validity"]
                    value = val.get("value")
                    if isinstance(value, dict):
                        value = json.dumps(value, ensure_ascii=False)[:50] + "..."
                    elif isinstance(value, list):
                        value = f"[{len(value)} items]"
                    else:
                        value = str(value)[:50] if value else "-"
                    output.append(f"| {tes_name} | {validity} | {value} |")
        
        return "\n".join(output)
    
    return json.dumps(comparisons, ensure_ascii=False, indent=2)


def ai_summarize_comparison(comparisons: list[dict], tes_names: list[str], client: genai.Client) -> str:
    """Use AI to summarize the comparison."""
    prompt = f"""Analyze and summarize this comparison of Finnish collective bargaining agreements (TES).

TES being compared: {', '.join(tes_names)}

Comparison data:
{json.dumps(comparisons, ensure_ascii=False, indent=2)}

Provide a concise summary highlighting:
1. Key differences between the agreements
2. Which TES has better terms in each category
3. Notable patterns or outliers
4. Recommendations based on the comparison

Write in a professional tone suitable for HR/payroll specialists.
If the user wrote in Finnish, respond in Finnish. Otherwise respond in English."""

    response = client.models.generate_content(
        model=DEFAULT_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.3)
    )
    
    return response.text


def compare_tes(
    tes_ids: list[str],
    fields: Optional[list[str]] = None,
    format_type: str = "json",
    summarize: bool = False
) -> dict:
    """Compare multiple TES documents."""
    if len(tes_ids) < 2:
        return {"error": "Need at least 2 TES IDs to compare"}
    
    tes_list = []
    missing = []
    for tes_id in tes_ids:
        tes = get_tes(tes_id)
        if tes:
            tes_list.append(tes)
        else:
            missing.append(tes_id)
    
    if missing:
        return {"error": f"TES not found: {', '.join(missing)}"}
    
    if len(tes_list) < 2:
        return {"error": "Need at least 2 valid TES documents to compare"}
    
    fields_to_compare = fields or COMPARABLE_FIELDS
    
    comparisons = []
    for field in fields_to_compare:
        comparison = compare_field(tes_list, field)
        comparisons.append(comparison)
    
    result = {
        "tes_compared": [{"id": t.get("id"), "name": t.get("name")} for t in tes_list],
        "fields_compared": fields_to_compare,
        "comparisons": comparisons
    }
    
    if format_type == "markdown":
        result["markdown"] = generate_comparison_table(comparisons, "markdown")
    
    if summarize:
        client = get_client()
        tes_names = [t.get("name", t.get("id")) for t in tes_list]
        result["ai_summary"] = ai_summarize_comparison(comparisons, tes_names, client)
    
    return result


def main():
    parser = argparse.ArgumentParser(description="TES Comparison Sub-Agent")
    parser.add_argument("--ids", required=True, help="Comma-separated TES IDs to compare")
    parser.add_argument("--fields", help="Comma-separated fields to compare (default: all)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json",
                       help="Output format")
    parser.add_argument("--summarize", action="store_true", 
                       help="Include AI summary of comparison")
    
    args = parser.parse_args()
    
    tes_ids = [id.strip() for id in args.ids.split(",")]
    fields = [f.strip() for f in args.fields.split(",")] if args.fields else None
    
    result = compare_tes(
        tes_ids=tes_ids,
        fields=fields,
        format_type=args.format,
        summarize=args.summarize
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
