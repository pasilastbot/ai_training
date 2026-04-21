#!/usr/bin/env python3
"""
Retrieve Prospects Tool

Query and retrieve prospects from the database.

Usage:
  python retrieve_prospects.py --all
  python retrieve_prospects.py --id prospect_123
  python retrieve_prospects.py --status enriched --industry SaaS
  python retrieve_prospects.py --min-score 70 --limit 20
  python retrieve_prospects.py --search "AI company"
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try PostgreSQL
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "")
SQLITE_PATH = Path(__file__).parent.parent / "memory" / "data" / "prospects.db"


class ProspectRetrieval:
    """Prospect retrieval with PostgreSQL and SQLite support."""
    
    def __init__(self):
        self.use_postgres = bool(DATABASE_URL) and POSTGRES_AVAILABLE
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Connect to database."""
        if self.use_postgres:
            self.conn = psycopg2.connect(DATABASE_URL)
        else:
            if not SQLITE_PATH.exists():
                raise FileNotFoundError(f"Database not found: {SQLITE_PATH}")
            self.conn = sqlite3.connect(str(SQLITE_PATH))
            self.conn.row_factory = sqlite3.Row
    
    def _parse_row(self, row: Any) -> Dict[str, Any]:
        """Parse a database row into a prospect dict."""
        if self.use_postgres:
            return dict(row)
        else:
            prospect = dict(row)
            # Parse JSON fields
            for field in ["headquarters", "technologies", "contacts", "signals", "raw_data"]:
                if prospect.get(field):
                    try:
                        prospect[field] = json.loads(prospect[field])
                    except (json.JSONDecodeError, TypeError):
                        pass
            return prospect
    
    def _get_cursor(self):
        """Get a cursor appropriate for the database type."""
        if self.use_postgres:
            return self.conn.cursor(cursor_factory=RealDictCursor)
        return self.conn.cursor()
    
    def get_by_id(self, prospect_id: str) -> Optional[Dict[str, Any]]:
        """Get a prospect by ID."""
        cursor = self._get_cursor()
        cursor.execute("SELECT * FROM prospects WHERE id = %s" if self.use_postgres else "SELECT * FROM prospects WHERE id = ?", (prospect_id,))
        row = cursor.fetchone()
        return self._parse_row(row) if row else None
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all prospects with pagination."""
        cursor = self._get_cursor()
        if self.use_postgres:
            cursor.execute("SELECT * FROM prospects ORDER BY updated_at DESC LIMIT %s OFFSET %s", (limit, offset))
        else:
            cursor.execute("SELECT * FROM prospects ORDER BY updated_at DESC LIMIT ? OFFSET ?", (limit, offset))
        return [self._parse_row(row) for row in cursor.fetchall()]
    
    def query(
        self,
        status: Optional[str] = None,
        industry: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        funding_stage: Optional[str] = None,
        min_employees: Optional[int] = None,
        max_employees: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query prospects with filters."""
        conditions = []
        params = []
        
        if status:
            conditions.append("status = %s" if self.use_postgres else "status = ?")
            params.append(status)
        
        if industry:
            conditions.append("industry ILIKE %s" if self.use_postgres else "industry LIKE ?")
            params.append(f"%{industry}%")
        
        if min_score is not None:
            conditions.append("score >= %s" if self.use_postgres else "score >= ?")
            params.append(min_score)
        
        if max_score is not None:
            conditions.append("score <= %s" if self.use_postgres else "score <= ?")
            params.append(max_score)
        
        if funding_stage:
            conditions.append("funding_stage = %s" if self.use_postgres else "funding_stage = ?")
            params.append(funding_stage)
        
        if min_employees is not None:
            conditions.append("employee_count >= %s" if self.use_postgres else "employee_count >= ?")
            params.append(min_employees)
        
        if max_employees is not None:
            conditions.append("employee_count <= %s" if self.use_postgres else "employee_count <= ?")
            params.append(max_employees)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"SELECT * FROM prospects WHERE {where_clause} ORDER BY score DESC NULLS LAST, updated_at DESC"
        
        if self.use_postgres:
            query += " LIMIT %s OFFSET %s"
        else:
            query = query.replace("NULLS LAST", "")
            query += " LIMIT ? OFFSET ?"
        
        params.extend([limit, offset])
        
        cursor = self._get_cursor()
        cursor.execute(query, tuple(params))
        return [self._parse_row(row) for row in cursor.fetchall()]
    
    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Full-text search in prospects."""
        cursor = self._get_cursor()
        
        if self.use_postgres:
            cursor.execute("""
                SELECT * FROM prospects 
                WHERE company_name ILIKE %s 
                   OR description ILIKE %s 
                   OR industry ILIKE %s
                ORDER BY score DESC NULLS LAST
                LIMIT %s
            """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
        else:
            cursor.execute("""
                SELECT * FROM prospects 
                WHERE company_name LIKE ? 
                   OR description LIKE ? 
                   OR industry LIKE ?
                ORDER BY score DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
        
        return [self._parse_row(row) for row in cursor.fetchall()]
    
    def count(self, status: Optional[str] = None) -> int:
        """Count prospects."""
        cursor = self.conn.cursor()
        if status:
            if self.use_postgres:
                cursor.execute("SELECT COUNT(*) FROM prospects WHERE status = %s", (status,))
            else:
                cursor.execute("SELECT COUNT(*) FROM prospects WHERE status = ?", (status,))
        else:
            cursor.execute("SELECT COUNT(*) FROM prospects")
        return cursor.fetchone()[0]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get prospect statistics."""
        cursor = self._get_cursor()
        
        stats = {
            "total": self.count(),
            "by_status": {},
            "by_industry": {},
            "avg_score": None
        }
        
        # By status
        cursor.execute("SELECT status, COUNT(*) as count FROM prospects GROUP BY status")
        for row in cursor.fetchall():
            status_val = row["status"] if self.use_postgres else row[0]
            count_val = row["count"] if self.use_postgres else row[1]
            stats["by_status"][status_val or "unknown"] = count_val
        
        # By industry
        cursor.execute("SELECT industry, COUNT(*) as count FROM prospects WHERE industry IS NOT NULL GROUP BY industry ORDER BY count DESC LIMIT 10")
        for row in cursor.fetchall():
            if self.use_postgres:
                stats["by_industry"][row["industry"]] = row["count"]
            else:
                stats["by_industry"][row["industry"]] = row["count"]
        
        # Average score
        cursor.execute("SELECT AVG(score) as avg FROM prospects WHERE score IS NOT NULL")
        row = cursor.fetchone()
        if row:
            stats["avg_score"] = round(float(row[0] if isinstance(row, tuple) else row["avg"]), 1) if row[0] else None
        
        return stats
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve prospects from database",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Query modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--all", action="store_true", help="Get all prospects")
    mode_group.add_argument("--id", help="Get prospect by ID")
    mode_group.add_argument("--search", "-q", help="Search prospects")
    mode_group.add_argument("--stats", action="store_true", help="Get statistics")
    
    # Filters
    parser.add_argument("--status", "-s", help="Filter by status")
    parser.add_argument("--industry", "-i", help="Filter by industry")
    parser.add_argument("--min-score", type=int, help="Minimum score")
    parser.add_argument("--max-score", type=int, help="Maximum score")
    parser.add_argument("--funding-stage", help="Filter by funding stage")
    parser.add_argument("--min-employees", type=int, help="Minimum employees")
    parser.add_argument("--max-employees", type=int, help="Maximum employees")
    
    # Pagination
    parser.add_argument("--limit", "-l", type=int, default=100, help="Max results")
    parser.add_argument("--offset", "-o", type=int, default=0, help="Offset")
    
    # Output
    parser.add_argument("--pretty", action="store_true", help="Pretty-print output")
    parser.add_argument("--compact", action="store_true", help="Compact output (id, name, score only)")
    
    args = parser.parse_args()
    
    try:
        retrieval = ProspectRetrieval()
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e), "prospects": []}))
        sys.exit(1)
    
    try:
        if args.stats:
            result = retrieval.get_stats()
        elif args.id:
            prospect = retrieval.get_by_id(args.id)
            if prospect:
                result = {"prospect": prospect}
            else:
                result = {"error": "Prospect not found", "id": args.id}
                print(json.dumps(result))
                sys.exit(1)
        elif args.search:
            prospects = retrieval.search(args.search, args.limit)
            result = {"query": args.search, "count": len(prospects), "prospects": prospects}
        elif args.all or args.status or args.industry or args.min_score:
            prospects = retrieval.query(
                status=args.status,
                industry=args.industry,
                min_score=args.min_score,
                max_score=args.max_score,
                funding_stage=args.funding_stage,
                min_employees=args.min_employees,
                max_employees=args.max_employees,
                limit=args.limit,
                offset=args.offset
            )
            result = {"count": len(prospects), "prospects": prospects}
        else:
            # Default: get all
            prospects = retrieval.get_all(args.limit, args.offset)
            result = {"count": len(prospects), "prospects": prospects}
        
        # Compact output
        if args.compact and "prospects" in result:
            result["prospects"] = [
                {"id": p.get("id"), "company_name": p.get("company_name"), "score": p.get("score"), "status": p.get("status")}
                for p in result["prospects"]
            ]
        
        print(json.dumps(result, indent=2 if args.pretty else None, default=str))
        
    finally:
        retrieval.close()


if __name__ == "__main__":
    main()
