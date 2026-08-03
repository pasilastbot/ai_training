#!/usr/bin/env python3
"""
Energy Advisor Memory Module

Provides persistent storage for customer apartment details and conversation history.
Uses SQLite for structured data storage.

Usage:
    python memory.py --init                           # Initialize database
    python memory.py --apartment create               # Create apartment (interactive)
    python memory.py --apartment list                 # List all apartments
    python memory.py --apartment get "id"             # Get apartment details
    python memory.py --apartment search "query"       # Search apartments
    python memory.py --stats                          # Show statistics
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import uuid4

AGENT_DIR = Path(__file__).parent.parent
DATA_DIR = AGENT_DIR / "memory" / "data"
DB_PATH = DATA_DIR / "energy_advisor.db"


def get_connection() -> sqlite3.Connection:
    """Get SQLite connection."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> dict:
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apartments (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            customer_name TEXT,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_apartments_customer 
        ON apartments(customer_id)
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            customer_id TEXT,
            apartment_id TEXT,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            summary TEXT,
            data_json TEXT,
            FOREIGN KEY (apartment_id) REFERENCES apartments(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id TEXT PRIMARY KEY,
            apartment_id TEXT NOT NULL,
            recommendation_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            estimated_savings_eur REAL,
            estimated_savings_percent REAL,
            priority TEXT,
            status TEXT DEFAULT 'suggested',
            created_at TEXT NOT NULL,
            FOREIGN KEY (apartment_id) REFERENCES apartments(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_responses (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            video_path TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)
    
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS apartments_fts USING fts5(
            id, customer_name, city, building_type, heating_type,
            content=apartments
        )
    """)
    
    conn.commit()
    conn.close()
    
    return {"status": "initialized", "database": str(DB_PATH)}


# ============ Apartment Management ============

def create_apartment(
    customer_id: str,
    customer_name: str = None,
    address: dict = None,
    building_info: dict = None,
    apartment_details: dict = None,
    heating_system: dict = None,
    energy_consumption: dict = None,
    occupancy: dict = None,
    preferences: dict = None,
    notes: str = None
) -> dict:
    """Create a new apartment record."""
    conn = get_connection()
    cursor = conn.cursor()
    
    apartment_id = str(uuid4())[:8]
    now = datetime.utcnow().isoformat()
    
    apartment_data = {
        "id": apartment_id,
        "customer_id": customer_id,
        "customer_name": customer_name or "",
        "address": address or {},
        "building_info": building_info or {},
        "apartment_details": apartment_details or {},
        "heating_system": heating_system or {},
        "energy_consumption": energy_consumption or {},
        "occupancy": occupancy or {},
        "preferences": preferences or {},
        "notes": notes or "",
        "created_at": now,
        "updated_at": now
    }
    
    cursor.execute(
        """INSERT INTO apartments (id, customer_id, customer_name, data_json, created_at, updated_at) 
           VALUES (?, ?, ?, ?, ?, ?)""",
        (apartment_id, customer_id, customer_name or "", 
         json.dumps(apartment_data, ensure_ascii=False), now, now)
    )
    
    conn.commit()
    conn.close()
    
    return apartment_data


def get_apartment(apartment_id: str) -> Optional[dict]:
    """Get apartment by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT data_json FROM apartments WHERE id = ?", (apartment_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row["data_json"])
    return None


def get_apartment_by_customer(customer_id: str) -> Optional[dict]:
    """Get apartment by customer ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT data_json FROM apartments WHERE customer_id = ? ORDER BY updated_at DESC LIMIT 1", 
        (customer_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row["data_json"])
    return None


def list_apartments(limit: int = 50) -> list:
    """List all apartments."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT id, customer_id, customer_name, 
                  json_extract(data_json, '$.address.city') as city,
                  json_extract(data_json, '$.building_info.building_type') as building_type,
                  json_extract(data_json, '$.heating_system.type') as heating_type,
                  json_extract(data_json, '$.apartment_details.size_sqm') as size_sqm,
                  created_at 
           FROM apartments 
           ORDER BY updated_at DESC 
           LIMIT ?""",
        (limit,)
    )
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results


def update_apartment(apartment_id: str, updates: dict) -> dict:
    """Update apartment data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    apartment = get_apartment(apartment_id)
    if not apartment:
        return {"error": f"Apartment not found: {apartment_id}"}
    
    for key, value in updates.items():
        if isinstance(value, dict) and key in apartment:
            apartment[key].update(value)
        else:
            apartment[key] = value
    
    apartment["updated_at"] = datetime.utcnow().isoformat()
    
    cursor.execute(
        """UPDATE apartments 
           SET data_json = ?, updated_at = ?, customer_name = ? 
           WHERE id = ?""",
        (json.dumps(apartment, ensure_ascii=False), apartment["updated_at"], 
         apartment.get("customer_name", ""), apartment_id)
    )
    
    conn.commit()
    conn.close()
    
    return apartment


def delete_apartment(apartment_id: str) -> dict:
    """Delete an apartment."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM apartments WHERE id = ?", (apartment_id,))
    
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return {"deleted": deleted, "apartment_id": apartment_id}


def search_apartments(query: str, limit: int = 20) -> list:
    """Search apartments by customer name, city, or building type."""
    conn = get_connection()
    cursor = conn.cursor()
    
    search_pattern = f"%{query}%"
    
    cursor.execute(
        """SELECT id, customer_id, customer_name, 
                  json_extract(data_json, '$.address.city') as city,
                  json_extract(data_json, '$.building_info.building_type') as building_type,
                  json_extract(data_json, '$.heating_system.type') as heating_type,
                  json_extract(data_json, '$.apartment_details.size_sqm') as size_sqm
           FROM apartments 
           WHERE customer_name LIKE ? 
              OR json_extract(data_json, '$.address.city') LIKE ?
              OR json_extract(data_json, '$.building_info.building_type') LIKE ?
              OR json_extract(data_json, '$.heating_system.type') LIKE ?
           ORDER BY updated_at DESC 
           LIMIT ?""",
        (search_pattern, search_pattern, search_pattern, search_pattern, limit)
    )
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results


def get_apartments_by_heating_type(heating_type: str) -> list:
    """Get all apartments with a specific heating type."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT data_json FROM apartments 
           WHERE json_extract(data_json, '$.heating_system.type') = ?""",
        (heating_type,)
    )
    
    results = [json.loads(row["data_json"]) for row in cursor.fetchall()]
    conn.close()
    
    return results


def get_apartments_by_city(city: str) -> list:
    """Get all apartments in a specific city."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT data_json FROM apartments 
           WHERE json_extract(data_json, '$.address.city') LIKE ?""",
        (f"%{city}%",)
    )
    
    results = [json.loads(row["data_json"]) for row in cursor.fetchall()]
    conn.close()
    
    return results


# ============ Recommendations ============

def create_recommendation(
    apartment_id: str,
    recommendation_type: str,
    title: str,
    description: str = None,
    estimated_savings_eur: float = None,
    estimated_savings_percent: float = None,
    priority: str = "medium"
) -> dict:
    """Create a new recommendation for an apartment."""
    conn = get_connection()
    cursor = conn.cursor()
    
    rec_id = str(uuid4())[:8]
    now = datetime.utcnow().isoformat()
    
    cursor.execute(
        """INSERT INTO recommendations 
           (id, apartment_id, recommendation_type, title, description, 
            estimated_savings_eur, estimated_savings_percent, priority, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (rec_id, apartment_id, recommendation_type, title, description,
         estimated_savings_eur, estimated_savings_percent, priority, now)
    )
    
    conn.commit()
    conn.close()
    
    return {
        "id": rec_id,
        "apartment_id": apartment_id,
        "type": recommendation_type,
        "title": title,
        "description": description,
        "estimated_savings_eur": estimated_savings_eur,
        "estimated_savings_percent": estimated_savings_percent,
        "priority": priority,
        "status": "suggested",
        "created_at": now
    }


def get_recommendations(apartment_id: str) -> list:
    """Get all recommendations for an apartment."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT * FROM recommendations WHERE apartment_id = ? ORDER BY created_at DESC""",
        (apartment_id,)
    )
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results


# ============ Video Responses ============

def store_video_response(
    question: str,
    answer: str,
    video_path: str = None,
    conversation_id: str = None
) -> dict:
    """Store a video response."""
    conn = get_connection()
    cursor = conn.cursor()
    
    response_id = str(uuid4())[:8]
    now = datetime.utcnow().isoformat()
    
    cursor.execute(
        """INSERT INTO video_responses 
           (id, conversation_id, question, answer, video_path, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (response_id, conversation_id, question, answer, video_path, now)
    )
    
    conn.commit()
    conn.close()
    
    return {
        "id": response_id,
        "question": question,
        "answer": answer,
        "video_path": video_path,
        "created_at": now
    }


def get_recent_video_responses(limit: int = 10) -> list:
    """Get recent video responses."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT * FROM video_responses ORDER BY created_at DESC LIMIT ?""",
        (limit,)
    )
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results


# ============ Statistics ============

def get_stats() -> dict:
    """Get database statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute("SELECT COUNT(*) FROM apartments")
    stats["total_apartments"] = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT json_extract(data_json, '$.heating_system.type') as heating_type, COUNT(*) 
        FROM apartments 
        GROUP BY heating_type
    """)
    stats["by_heating_type"] = {row[0] or "unknown": row[1] for row in cursor.fetchall()}
    
    cursor.execute("""
        SELECT json_extract(data_json, '$.building_info.building_type') as building_type, COUNT(*) 
        FROM apartments 
        GROUP BY building_type
    """)
    stats["by_building_type"] = {row[0] or "unknown": row[1] for row in cursor.fetchall()}
    
    cursor.execute("""
        SELECT json_extract(data_json, '$.address.city') as city, COUNT(*) 
        FROM apartments 
        GROUP BY city
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)
    stats["top_cities"] = {row[0] or "unknown": row[1] for row in cursor.fetchall()}
    
    cursor.execute("SELECT COUNT(*) FROM recommendations")
    stats["total_recommendations"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM video_responses")
    stats["total_video_responses"] = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT AVG(CAST(json_extract(data_json, '$.apartment_details.size_sqm') AS REAL))
        FROM apartments 
        WHERE json_extract(data_json, '$.apartment_details.size_sqm') IS NOT NULL
    """)
    avg_size = cursor.fetchone()[0]
    stats["average_apartment_size_sqm"] = round(avg_size, 1) if avg_size else None
    
    conn.close()
    return stats


def get_apartment_summary(apartment_id: str) -> dict:
    """Get a summary of an apartment for the AI agent."""
    apartment = get_apartment(apartment_id)
    if not apartment:
        return {"error": f"Apartment not found: {apartment_id}"}
    
    summary = {
        "customer": apartment.get("customer_name", "Unknown"),
        "location": apartment.get("address", {}).get("city", "Unknown"),
        "building_type": apartment.get("building_info", {}).get("building_type", "Unknown"),
        "size_sqm": apartment.get("apartment_details", {}).get("size_sqm"),
        "heating_type": apartment.get("heating_system", {}).get("type", "Unknown"),
        "has_smart_controls": apartment.get("heating_system", {}).get("has_smart_controls", False),
        "annual_heating_kwh": apartment.get("energy_consumption", {}).get("annual_heating_kwh"),
        "annual_cost_eur": apartment.get("energy_consumption", {}).get("annual_cost_eur"),
        "energy_class": apartment.get("energy_consumption", {}).get("energy_class"),
        "residents": apartment.get("occupancy", {}).get("residents_count"),
        "preferred_temp": apartment.get("preferences", {}).get("preferred_temp_c"),
        "comfort_priority": apartment.get("preferences", {}).get("comfort_priority", "balanced")
    }
    
    return summary


# ============ CLI ============

def main():
    parser = argparse.ArgumentParser(description="Energy Advisor Memory CLI")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--apartment", nargs="+", help="Apartment ops: create | list | get <id> | search <query>")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    
    args = parser.parse_args()
    
    if args.init:
        result = init_database()
        print(json.dumps(result, indent=2))
    
    elif args.apartment:
        action = args.apartment[0]
        if action == "create":
            customer_id = input("Customer ID: ").strip() or str(uuid4())[:8]
            customer_name = input("Customer Name: ").strip()
            city = input("City: ").strip()
            building_type = input("Building Type (apartment/house/townhouse): ").strip() or "apartment"
            size_sqm = input("Size (sqm): ").strip()
            heating_type = input("Heating Type (district_heating/electric/heat_pump): ").strip() or "district_heating"
            
            result = create_apartment(
                customer_id=customer_id,
                customer_name=customer_name,
                address={"city": city} if city else None,
                building_info={"building_type": building_type} if building_type else None,
                apartment_details={"size_sqm": float(size_sqm)} if size_sqm else None,
                heating_system={"type": heating_type} if heating_type else None
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif action == "list":
            result = list_apartments()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif action == "get" and len(args.apartment) > 1:
            result = get_apartment(args.apartment[1])
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif action == "search" and len(args.apartment) > 1:
            result = search_apartments(args.apartment[1])
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Usage: --apartment create | list | get <id> | search <query>")
    
    elif args.stats:
        result = get_stats()
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
