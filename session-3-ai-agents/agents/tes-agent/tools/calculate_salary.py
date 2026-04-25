#!/usr/bin/env python3
"""
Calculate Salary Tool

Calculates minimum salary based on TES rules.

Usage:
    python calculate_salary.py --tes "tes_example_2024" --role "engineer" --experience 5
    python calculate_salary.py --tes-name "Teknologiateollisuuden TES" --role "specialist" --experience 3 --ai
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from subagents.salary_calculator import calculate_salary


def main():
    parser = argparse.ArgumentParser(description="Calculate Salary Tool")
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
