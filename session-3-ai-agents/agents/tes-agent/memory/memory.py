#!/usr/bin/env python3
"""
TES Agent Memory Store

SQLite-based storage for TES documents with schema evolution support.

Usage:
    python memory.py init                           # Initialize database
    python memory.py store --json <file>            # Store TES from JSON
    python memory.py get <id>                       # Get TES by ID
    python memory.py list [--industry X]            # List all TES
    python memory.py search <query>                 # Full-text search
    python memory.py schema                         # Show current schema
    python memory.py evolve-schema --field <path>   # Add field to schema
    python memory.py stats                          # Show statistics
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

MEMORY_DIR = Path(__file__).parent
DATA_DIR = MEMORY_DIR / "data"
DB_PATH = DATA_DIR / "tes.db"
TES_JSON_DIR = DATA_DIR / "tes"
PDF_DIR = DATA_DIR / "pdfs"
SCHEMA_PATH = MEMORY_DIR / "tes_schema.json"


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Initialize the SQLite database with required tables."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TES_JSON_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS tes_documents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            name_en TEXT,
            union_name TEXT,
            employer_org TEXT,
            industry TEXT,
            validity_start DATE,
            validity_end DATE,
            source_url TEXT NOT NULL,
            pdf_path TEXT,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version TEXT,
            data_json TEXT,
            schema_version INTEGER DEFAULT 1
        );
        
        CREATE TABLE IF NOT EXISTS salary_tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tes_id TEXT REFERENCES tes_documents(id) ON DELETE CASCADE,
            table_name TEXT,
            role_category TEXT,
            experience_level TEXT,
            minimum_salary REAL,
            hourly_rate REAL,
            effective_date DATE,
            notes TEXT,
            pdf_page INTEGER,
            section TEXT
        );
        
        CREATE TABLE IF NOT EXISTS schema_fields (
            field_path TEXT PRIMARY KEY,
            field_type TEXT,
            description TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            added_from_tes TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_tes_industry ON tes_documents(industry);
        CREATE INDEX IF NOT EXISTS idx_tes_validity ON tes_documents(validity_start, validity_end);
        CREATE INDEX IF NOT EXISTS idx_tes_union ON tes_documents(union_name);
        CREATE INDEX IF NOT EXISTS idx_salary_tes ON salary_tables(tes_id);
    """)
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='tes_fts'
    """)
    if not cursor.fetchone():
        cursor.execute("""
            CREATE VIRTUAL TABLE tes_fts USING fts5(
                id, name, name_en, union_name, employer_org, industry,
                content='tes_documents',
                content_rowid='rowid'
            )
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS tes_fts_insert AFTER INSERT ON tes_documents BEGIN
                INSERT INTO tes_fts(rowid, id, name, name_en, union_name, employer_org, industry)
                VALUES (NEW.rowid, NEW.id, NEW.name, NEW.name_en, NEW.union_name, NEW.employer_org, NEW.industry);
            END
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS tes_fts_delete AFTER DELETE ON tes_documents BEGIN
                INSERT INTO tes_fts(tes_fts, rowid, id, name, name_en, union_name, employer_org, industry)
                VALUES ('delete', OLD.rowid, OLD.id, OLD.name, OLD.name_en, OLD.union_name, OLD.employer_org, OLD.industry);
            END
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS tes_fts_update AFTER UPDATE ON tes_documents BEGIN
                INSERT INTO tes_fts(tes_fts, rowid, id, name, name_en, union_name, employer_org, industry)
                VALUES ('delete', OLD.rowid, OLD.id, OLD.name, OLD.name_en, OLD.union_name, OLD.employer_org, OLD.industry);
                INSERT INTO tes_fts(rowid, id, name, name_en, union_name, employer_org, industry)
                VALUES (NEW.rowid, NEW.id, NEW.name, NEW.name_en, NEW.union_name, NEW.employer_org, NEW.industry);
            END
        """)
    
    conn.commit()
    conn.close()
    print(json.dumps({"status": "initialized", "db_path": str(DB_PATH)}))


def store_tes(data: dict) -> dict:
    """Store a TES document in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    tes_id = data.get("id")
    if not tes_id:
        name = data.get("name", "unknown")
        validity = data.get("validity_start", datetime.now().strftime("%Y"))
        tes_id = f"tes_{name.lower().replace(' ', '_')}_{validity}"
        data["id"] = tes_id
    
    if "indexed_at" not in data:
        data["indexed_at"] = datetime.now().isoformat()
    
    json_file = TES_JSON_DIR / f"{tes_id}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    cursor.execute("""
        INSERT OR REPLACE INTO tes_documents (
            id, name, name_en, union_name, employer_org, industry,
            validity_start, validity_end, source_url, pdf_path,
            indexed_at, version, data_json, schema_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tes_id,
        data.get("name"),
        data.get("name_en"),
        data.get("union"),
        data.get("employer_org"),
        data.get("industry"),
        data.get("validity_start"),
        data.get("validity_end"),
        data.get("source_url", ""),
        data.get("pdf_path"),
        data.get("indexed_at"),
        data.get("version"),
        json.dumps(data, ensure_ascii=False),
        data.get("_schema_version", 1)
    ))
    
    salary_tables = data.get("salary_tables", [])
    if salary_tables:
        cursor.execute("DELETE FROM salary_tables WHERE tes_id = ?", (tes_id,))
        for table in salary_tables:
            exp_levels = table.get("experience_levels", [])
            if exp_levels:
                for level in exp_levels:
                    cursor.execute("""
                        INSERT INTO salary_tables (
                            tes_id, table_name, role_category, experience_level,
                            minimum_salary, hourly_rate, effective_date, notes,
                            pdf_page, section
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        tes_id,
                        table.get("table_name"),
                        table.get("role_category"),
                        level.get("level"),
                        level.get("minimum_salary"),
                        level.get("hourly_rate"),
                        table.get("effective_date"),
                        None,
                        table.get("pdf_page"),
                        table.get("section")
                    ))
            else:
                cursor.execute("""
                    INSERT INTO salary_tables (
                        tes_id, table_name, role_category, minimum_salary,
                        effective_date, pdf_page, section
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    tes_id,
                    table.get("table_name"),
                    table.get("role_category"),
                    table.get("minimum_salary"),
                    table.get("effective_date"),
                    table.get("pdf_page"),
                    table.get("section")
                ))
    
    conn.commit()
    conn.close()
    
    return {"status": "stored", "id": tes_id, "json_path": str(json_file)}


def get_tes(tes_id: str) -> Optional[dict]:
    """Get a TES document by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT data_json FROM tes_documents WHERE id = ?", (tes_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row["data_json"])
    return None


def list_tes(
    industry: Optional[str] = None,
    union: Optional[str] = None,
    valid_only: bool = False,
    limit: int = 100
) -> list[dict]:
    """List TES documents with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT id, name, name_en, union_name, employer_org, industry,
               validity_start, validity_end, indexed_at
        FROM tes_documents
        WHERE 1=1
    """
    params = []
    
    if industry:
        query += " AND industry LIKE ?"
        params.append(f"%{industry}%")
    
    if union:
        query += " AND union_name LIKE ?"
        params.append(f"%{union}%")
    
    if valid_only:
        today = datetime.now().strftime("%Y-%m-%d")
        query += " AND (validity_end IS NULL OR validity_end >= ?)"
        params.append(today)
    
    query += " ORDER BY name LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def search_tes(query: str, limit: int = 20) -> list[dict]:
    """Full-text search across TES documents."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Escape the query for FTS5 - wrap each term in quotes to prevent
    # special character interpretation (hyphens, "ja"/"tai" as operators)
    # Split on whitespace, quote each term, join with spaces
    terms = query.split()
    escaped_query = " ".join(f'"{term}"' for term in terms)
    
    try:
        cursor.execute("""
            SELECT d.id, d.name, d.name_en, d.union_name, d.industry,
                   d.validity_start, d.validity_end
            FROM tes_fts f
            JOIN tes_documents d ON f.id = d.id
            WHERE tes_fts MATCH ?
            LIMIT ?
        """, (escaped_query, limit))
        
        rows = cursor.fetchall()
    except Exception as e:
        # Fallback to LIKE search if FTS fails
        like_pattern = f"%{query}%"
        cursor.execute("""
            SELECT id, name, name_en, union_name, industry,
                   validity_start, validity_end
            FROM tes_documents
            WHERE name LIKE ? OR name_en LIKE ? OR industry LIKE ?
            LIMIT ?
        """, (like_pattern, like_pattern, like_pattern, limit))
        rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in rows]


def get_salary_tables(tes_id: str) -> list[dict]:
    """Get salary tables for a specific TES."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM salary_tables WHERE tes_id = ?
        ORDER BY role_category, experience_level
    """, (tes_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_schema() -> dict:
    """Get the current TES schema."""
    if SCHEMA_PATH.exists():
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def evolve_schema(field_path: str, field_type: str, description: str, from_tes: str = None) -> dict:
    """Add a new field to the schema."""
    schema = get_schema()
    
    parts = field_path.split(".")
    current = schema.get("properties", {})
    
    for i, part in enumerate(parts[:-1]):
        if part not in current:
            current[part] = {"type": "object", "properties": {}}
        if "properties" not in current[part]:
            current[part]["properties"] = {}
        current = current[part]["properties"]
    
    field_name = parts[-1]
    current[field_name] = {
        "type": field_type,
        "description": description
    }
    
    with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO schema_fields (field_path, field_type, description, added_from_tes)
        VALUES (?, ?, ?, ?)
    """, (field_path, field_type, description, from_tes))
    conn.commit()
    conn.close()
    
    return {"status": "evolved", "field": field_path, "type": field_type}


def get_stats() -> dict:
    """Get statistics about stored TES documents."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM tes_documents")
    total = cursor.fetchone()["count"]
    
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT COUNT(*) as count FROM tes_documents 
        WHERE validity_end IS NULL OR validity_end >= ?
    """, (today,))
    valid = cursor.fetchone()["count"]
    
    cursor.execute("""
        SELECT industry, COUNT(*) as count FROM tes_documents 
        GROUP BY industry ORDER BY count DESC LIMIT 10
    """)
    by_industry = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT COUNT(*) as count FROM salary_tables")
    salary_entries = cursor.fetchone()["count"]
    
    cursor.execute("SELECT COUNT(*) as count FROM schema_fields")
    schema_fields = cursor.fetchone()["count"]
    
    conn.close()
    
    return {
        "total_tes": total,
        "valid_tes": valid,
        "by_industry": by_industry,
        "salary_table_entries": salary_entries,
        "custom_schema_fields": schema_fields
    }


def main():
    parser = argparse.ArgumentParser(description="TES Memory Store")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    subparsers.add_parser("init", help="Initialize database")
    
    store_parser = subparsers.add_parser("store", help="Store TES from JSON")
    store_parser.add_argument("--json", required=True, help="JSON file path")
    
    get_parser = subparsers.add_parser("get", help="Get TES by ID")
    get_parser.add_argument("id", help="TES ID")
    
    list_parser = subparsers.add_parser("list", help="List TES documents")
    list_parser.add_argument("--industry", help="Filter by industry")
    list_parser.add_argument("--union", help="Filter by union")
    list_parser.add_argument("--valid-only", action="store_true", help="Only show valid TES")
    list_parser.add_argument("--limit", type=int, default=100, help="Max results")
    
    search_parser = subparsers.add_parser("search", help="Search TES documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results")
    
    subparsers.add_parser("schema", help="Show current schema")
    
    evolve_parser = subparsers.add_parser("evolve-schema", help="Add field to schema")
    evolve_parser.add_argument("--field", required=True, help="Field path (e.g., 'bonuses.travel_allowance')")
    evolve_parser.add_argument("--type", required=True, help="Field type")
    evolve_parser.add_argument("--description", required=True, help="Field description")
    evolve_parser.add_argument("--from-tes", help="TES that introduced this field")
    
    salary_parser = subparsers.add_parser("salaries", help="Get salary tables")
    salary_parser.add_argument("id", help="TES ID")
    
    subparsers.add_parser("stats", help="Show statistics")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_database()
    
    elif args.command == "store":
        with open(args.json, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = store_tes(data)
        print(json.dumps(result, ensure_ascii=False))
    
    elif args.command == "get":
        result = get_tes(args.id)
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": "TES not found", "id": args.id}))
            sys.exit(1)
    
    elif args.command == "list":
        results = list_tes(
            industry=args.industry,
            union=args.union,
            valid_only=args.valid_only,
            limit=args.limit
        )
        print(json.dumps({"count": len(results), "tes": results}, ensure_ascii=False, indent=2))
    
    elif args.command == "search":
        results = search_tes(args.query, limit=args.limit)
        print(json.dumps({"count": len(results), "results": results}, ensure_ascii=False, indent=2))
    
    elif args.command == "schema":
        schema = get_schema()
        print(json.dumps(schema, ensure_ascii=False, indent=2))
    
    elif args.command == "evolve-schema":
        result = evolve_schema(
            args.field,
            args.type,
            args.description,
            args.from_tes
        )
        print(json.dumps(result, ensure_ascii=False))
    
    elif args.command == "salaries":
        results = get_salary_tables(args.id)
        print(json.dumps({"count": len(results), "tables": results}, ensure_ascii=False, indent=2))
    
    elif args.command == "stats":
        stats = get_stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
