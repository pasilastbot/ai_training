#!/usr/bin/env python3
"""
Store Prospect Tool

Stores prospect data to PostgreSQL or SQLite database.

Usage:
  python store_prospect.py --file prospect.json
  echo '{"company_name": "Acme", ...}' | python store_prospect.py --stdin
  python store_prospect.py --company "Acme" --website "https://acme.com" --industry "SaaS"
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

# Try PostgreSQL
try:
    import psycopg2
    from psycopg2.extras import Json
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "")
SQLITE_PATH = Path(__file__).parent.parent / "memory" / "data" / "prospects.db"


class ProspectStorage:
    """Prospect storage with PostgreSQL and SQLite support."""
    
    def __init__(self):
        self.use_postgres = bool(DATABASE_URL) and POSTGRES_AVAILABLE
        self.conn = None
        self._connect()
        self._init_schema()
    
    def _connect(self):
        """Connect to database."""
        if self.use_postgres:
            self.conn = psycopg2.connect(DATABASE_URL)
        else:
            SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(SQLITE_PATH))
            self.conn.row_factory = sqlite3.Row
    
    def _init_schema(self):
        """Initialize database schema."""
        if self.use_postgres:
            schema = """
            CREATE TABLE IF NOT EXISTS prospects (
                id VARCHAR(255) PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL,
                website VARCHAR(500),
                industry VARCHAR(255),
                sub_industry VARCHAR(255),
                description TEXT,
                employee_count INTEGER,
                revenue_estimate_usd BIGINT,
                funding_stage VARCHAR(50),
                total_funding_usd BIGINT,
                headquarters JSONB,
                technologies TEXT[],
                contacts JSONB,
                signals JSONB,
                score INTEGER,
                status VARCHAR(50) DEFAULT 'new',
                source VARCHAR(255),
                notes TEXT,
                raw_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                enriched_at TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(status);
            CREATE INDEX IF NOT EXISTS idx_prospects_industry ON prospects(industry);
            CREATE INDEX IF NOT EXISTS idx_prospects_score ON prospects(score);
            """
        else:
            schema = """
            CREATE TABLE IF NOT EXISTS prospects (
                id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                website TEXT,
                industry TEXT,
                sub_industry TEXT,
                description TEXT,
                employee_count INTEGER,
                revenue_estimate_usd INTEGER,
                funding_stage TEXT,
                total_funding_usd INTEGER,
                headquarters TEXT,
                technologies TEXT,
                contacts TEXT,
                signals TEXT,
                score INTEGER,
                status TEXT DEFAULT 'new',
                source TEXT,
                notes TEXT,
                raw_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                enriched_at TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(status);
            CREATE INDEX IF NOT EXISTS idx_prospects_industry ON prospects(industry);
            """
        
        cursor = self.conn.cursor()
        for statement in schema.split(';'):
            if statement.strip():
                cursor.execute(statement)
        self.conn.commit()
    
    def store(self, prospect: Dict[str, Any]) -> Dict[str, Any]:
        """Store a prospect."""
        # Generate ID if missing
        if "id" not in prospect:
            prospect["id"] = f"prospect_{uuid.uuid4().hex[:12]}"
        
        now = datetime.utcnow().isoformat()
        prospect["updated_at"] = now
        if "created_at" not in prospect:
            prospect["created_at"] = now
        
        cursor = self.conn.cursor()
        
        if self.use_postgres:
            # PostgreSQL with JSONB
            cursor.execute("""
                INSERT INTO prospects (
                    id, company_name, website, industry, sub_industry, description,
                    employee_count, revenue_estimate_usd, funding_stage, total_funding_usd,
                    headquarters, technologies, contacts, signals, score, status,
                    source, notes, raw_data, created_at, updated_at, enriched_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    website = EXCLUDED.website,
                    industry = EXCLUDED.industry,
                    sub_industry = EXCLUDED.sub_industry,
                    description = EXCLUDED.description,
                    employee_count = EXCLUDED.employee_count,
                    revenue_estimate_usd = EXCLUDED.revenue_estimate_usd,
                    funding_stage = EXCLUDED.funding_stage,
                    total_funding_usd = EXCLUDED.total_funding_usd,
                    headquarters = EXCLUDED.headquarters,
                    technologies = EXCLUDED.technologies,
                    contacts = EXCLUDED.contacts,
                    signals = EXCLUDED.signals,
                    score = EXCLUDED.score,
                    status = EXCLUDED.status,
                    source = EXCLUDED.source,
                    notes = EXCLUDED.notes,
                    raw_data = EXCLUDED.raw_data,
                    updated_at = EXCLUDED.updated_at,
                    enriched_at = EXCLUDED.enriched_at
            """, (
                prospect.get("id"),
                prospect.get("company_name"),
                prospect.get("website"),
                prospect.get("industry"),
                prospect.get("sub_industry"),
                prospect.get("description"),
                prospect.get("employee_count"),
                prospect.get("revenue_estimate_usd"),
                prospect.get("funding_stage"),
                prospect.get("total_funding_usd"),
                Json(prospect.get("headquarters")),
                prospect.get("technologies"),
                Json(prospect.get("contacts")),
                Json(prospect.get("signals")),
                prospect.get("score"),
                prospect.get("status", "new"),
                prospect.get("source"),
                prospect.get("notes"),
                Json(prospect),
                prospect.get("created_at"),
                prospect.get("updated_at"),
                prospect.get("enriched_at")
            ))
        else:
            # SQLite with JSON as text
            cursor.execute("""
                INSERT OR REPLACE INTO prospects (
                    id, company_name, website, industry, sub_industry, description,
                    employee_count, revenue_estimate_usd, funding_stage, total_funding_usd,
                    headquarters, technologies, contacts, signals, score, status,
                    source, notes, raw_data, created_at, updated_at, enriched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prospect.get("id"),
                prospect.get("company_name"),
                prospect.get("website"),
                prospect.get("industry"),
                prospect.get("sub_industry"),
                prospect.get("description"),
                prospect.get("employee_count"),
                prospect.get("revenue_estimate_usd"),
                prospect.get("funding_stage"),
                prospect.get("total_funding_usd"),
                json.dumps(prospect.get("headquarters")),
                json.dumps(prospect.get("technologies")),
                json.dumps(prospect.get("contacts")),
                json.dumps(prospect.get("signals")),
                prospect.get("score"),
                prospect.get("status", "new"),
                prospect.get("source"),
                prospect.get("notes"),
                json.dumps(prospect),
                prospect.get("created_at"),
                prospect.get("updated_at"),
                prospect.get("enriched_at")
            ))
        
        self.conn.commit()
        
        return {
            "status": "success",
            "id": prospect["id"],
            "company_name": prospect.get("company_name"),
            "action": "stored"
        }
    
    def store_many(self, prospects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store multiple prospects."""
        results = []
        for prospect in prospects:
            result = self.store(prospect)
            results.append(result)
        
        return {
            "status": "success",
            "count": len(results),
            "results": results
        }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Store prospect data to database",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--file", "-f",
        help="Path to prospect JSON file (single prospect or array)"
    )
    input_group.add_argument(
        "--stdin",
        action="store_true",
        help="Read prospect(s) from stdin"
    )
    
    # Direct input
    parser.add_argument("--id", help="Prospect ID")
    parser.add_argument("--company", "-c", help="Company name")
    parser.add_argument("--website", "-w", help="Company website")
    parser.add_argument("--industry", "-i", help="Industry")
    parser.add_argument("--status", "-s", default="new", help="Status")
    parser.add_argument("--score", type=int, help="ICP fit score (0-100)")
    
    # Output
    parser.add_argument("--pretty", action="store_true", help="Pretty-print output")
    
    args = parser.parse_args()
    
    storage = ProspectStorage()
    
    try:
        prospects = []
        
        if args.file:
            with open(args.file, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    prospects = data
                else:
                    prospects = [data]
        elif args.stdin:
            data = json.load(sys.stdin)
            if isinstance(data, list):
                prospects = data
            else:
                prospects = [data]
        elif args.company:
            prospect = {
                "company_name": args.company,
                "status": args.status
            }
            if args.id:
                prospect["id"] = args.id
            if args.website:
                prospect["website"] = args.website
            if args.industry:
                prospect["industry"] = args.industry
            if args.score:
                prospect["score"] = args.score
            prospects = [prospect]
        else:
            print(json.dumps({"error": "No input provided"}))
            sys.exit(1)
        
        if len(prospects) == 1:
            result = storage.store(prospects[0])
        else:
            result = storage.store_many(prospects)
        
        print(json.dumps(result, indent=2 if args.pretty else None))
        
    finally:
        storage.close()


if __name__ == "__main__":
    main()
