#!/usr/bin/env python3
"""
Evolve Schema Tool

Adds new fields to the TES schema.

Usage:
    python evolve_schema.py --field "bonuses.travel_allowance" --type "string" --description "Travel allowance rules"
    python evolve_schema.py --show
    python evolve_schema.py --history
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from memory.memory import get_schema, evolve_schema, get_connection


def show_schema_fields():
    """Show all custom schema fields."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT field_path, field_type, description, added_at, added_from_tes
        FROM schema_fields
        ORDER BY added_at DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def main():
    parser = argparse.ArgumentParser(description="Evolve Schema Tool")
    parser.add_argument("--field", help="Field path to add (e.g., 'bonuses.travel_allowance')")
    parser.add_argument("--type", help="Field type (string, number, object, array, boolean)")
    parser.add_argument("--description", help="Field description")
    parser.add_argument("--from-tes", help="TES that introduced this field")
    parser.add_argument("--show", action="store_true", help="Show current schema")
    parser.add_argument("--history", action="store_true", help="Show schema evolution history")
    
    args = parser.parse_args()
    
    if args.show:
        schema = get_schema()
        print(json.dumps(schema, ensure_ascii=False, indent=2))
    
    elif args.history:
        fields = show_schema_fields()
        print(json.dumps({
            "count": len(fields),
            "custom_fields": fields
        }, ensure_ascii=False, indent=2))
    
    elif args.field and args.type and args.description:
        result = evolve_schema(
            args.field,
            args.type,
            args.description,
            args.from_tes
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
