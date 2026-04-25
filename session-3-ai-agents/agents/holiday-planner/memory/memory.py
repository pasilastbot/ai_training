#!/usr/bin/env python3
"""
Holiday Planner Memory Module

Provides persistent storage for family profiles, preferences, and trip plans.
Uses SQLite for structured data and ChromaDB for semantic search.

Usage:
    python memory.py --init                    # Initialize database
    python memory.py --family create "name"    # Create family profile
    python memory.py --family list             # List all families
    python memory.py --family get "id"         # Get family details
    python memory.py --trip list               # List all trips
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

AGENT_DIR = Path(__file__).parent.parent
DATA_DIR = AGENT_DIR / "memory" / "data"
DB_PATH = DATA_DIR / "holiday_planner.db"


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
        CREATE TABLE IF NOT EXISTS families (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS family_members (
            id TEXT PRIMARY KEY,
            family_id TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            age INTEGER,
            preferences_json TEXT,
            FOREIGN KEY (family_id) REFERENCES families(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id TEXT PRIMARY KEY,
            family_id TEXT,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'planning',
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (family_id) REFERENCES families(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wish_sessions (
            id TEXT PRIMARY KEY,
            family_id TEXT,
            member_id TEXT,
            wishes_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (family_id) REFERENCES families(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS destination_cache (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            country TEXT,
            data_json TEXT NOT NULL,
            cached_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS trips_fts USING fts5(
            id, name, destinations, content=trips
        )
    """)
    
    conn.commit()
    conn.close()
    
    return {"status": "initialized", "database": str(DB_PATH)}


# ============ Family Management ============

def create_family(name: str, members: list = None) -> dict:
    """Create a new family profile."""
    conn = get_connection()
    cursor = conn.cursor()
    
    family_id = str(uuid4())[:8]
    now = datetime.utcnow().isoformat()
    
    family_data = {
        "id": family_id,
        "name": name,
        "members": members or [],
        "shared_preferences": {},
        "constraints": {},
        "past_trips": [],
        "created_at": now,
        "updated_at": now
    }
    
    cursor.execute(
        "INSERT INTO families (id, name, data_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (family_id, name, json.dumps(family_data, ensure_ascii=False), now, now)
    )
    
    if members:
        for member in members:
            member_id = str(uuid4())[:8]
            cursor.execute(
                "INSERT INTO family_members (id, family_id, name, role, age, preferences_json) VALUES (?, ?, ?, ?, ?, ?)",
                (member_id, family_id, member.get("name", ""), member.get("role", "adult"),
                 member.get("age"), json.dumps(member.get("preferences", {}), ensure_ascii=False))
            )
    
    conn.commit()
    conn.close()
    
    return family_data


def get_family(family_id: str) -> Optional[dict]:
    """Get family profile by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT data_json FROM families WHERE id = ?", (family_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row["data_json"])
    return None


def list_families(limit: int = 20) -> list:
    """List all family profiles."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, name, created_at FROM families ORDER BY updated_at DESC LIMIT ?",
        (limit,)
    )
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results


def update_family(family_id: str, updates: dict) -> dict:
    """Update family profile."""
    conn = get_connection()
    cursor = conn.cursor()
    
    family = get_family(family_id)
    if not family:
        return {"error": f"Family not found: {family_id}"}
    
    family.update(updates)
    family["updated_at"] = datetime.utcnow().isoformat()
    
    cursor.execute(
        "UPDATE families SET data_json = ?, updated_at = ?, name = ? WHERE id = ?",
        (json.dumps(family, ensure_ascii=False), family["updated_at"], family.get("name", ""), family_id)
    )
    
    conn.commit()
    conn.close()
    
    return family


def add_family_member(family_id: str, member: dict) -> dict:
    """Add a member to a family."""
    family = get_family(family_id)
    if not family:
        return {"error": f"Family not found: {family_id}"}
    
    member_id = str(uuid4())[:8]
    member["id"] = member_id
    
    family["members"].append(member)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO family_members (id, family_id, name, role, age, preferences_json) VALUES (?, ?, ?, ?, ?, ?)",
        (member_id, family_id, member.get("name", ""), member.get("role", "adult"),
         member.get("age"), json.dumps(member.get("preferences", {}), ensure_ascii=False))
    )
    
    conn.commit()
    conn.close()
    
    return update_family(family_id, {"members": family["members"]})


def update_member_preferences(family_id: str, member_id: str, preferences: dict) -> dict:
    """Update preferences for a specific family member."""
    family = get_family(family_id)
    if not family:
        return {"error": f"Family not found: {family_id}"}
    
    member_found = False
    for member in family["members"]:
        if member.get("id") == member_id:
            member["preferences"] = {**member.get("preferences", {}), **preferences}
            member_found = True
            break
    
    if not member_found:
        return {"error": f"Member not found: {member_id}"}
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE family_members SET preferences_json = ? WHERE id = ?",
        (json.dumps(preferences, ensure_ascii=False), member_id)
    )
    
    conn.commit()
    conn.close()
    
    return update_family(family_id, {"members": family["members"]})


# ============ Trip Management ============

def create_trip(name: str, family_id: str = None, destinations: list = None) -> dict:
    """Create a new trip plan."""
    conn = get_connection()
    cursor = conn.cursor()
    
    trip_id = str(uuid4())[:8]
    now = datetime.utcnow().isoformat()
    
    trip_data = {
        "id": trip_id,
        "family_id": family_id,
        "name": name,
        "status": "planning",
        "destinations": destinations or [],
        "itinerary": [],
        "budget": {},
        "accommodation": [],
        "transportation": [],
        "created_at": now,
        "updated_at": now
    }
    
    cursor.execute(
        "INSERT INTO trips (id, family_id, name, status, data_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (trip_id, family_id, name, "planning", json.dumps(trip_data, ensure_ascii=False), now, now)
    )
    
    conn.commit()
    conn.close()
    
    return trip_data


def get_trip(trip_id: str) -> Optional[dict]:
    """Get trip by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT data_json FROM trips WHERE id = ?", (trip_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row["data_json"])
    return None


def list_trips(family_id: str = None, status: str = None, limit: int = 20) -> list:
    """List trips, optionally filtered by family or status."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, name, status, family_id, created_at FROM trips"
    params = []
    conditions = []
    
    if family_id:
        conditions.append("family_id = ?")
        params.append(family_id)
    if status:
        conditions.append("status = ?")
        params.append(status)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return results


def update_trip(trip_id: str, updates: dict) -> dict:
    """Update trip data."""
    conn = get_connection()
    cursor = conn.cursor()
    
    trip = get_trip(trip_id)
    if not trip:
        return {"error": f"Trip not found: {trip_id}"}
    
    trip.update(updates)
    trip["updated_at"] = datetime.utcnow().isoformat()
    
    cursor.execute(
        "UPDATE trips SET data_json = ?, updated_at = ?, status = ?, name = ? WHERE id = ?",
        (json.dumps(trip, ensure_ascii=False), trip["updated_at"], trip.get("status", "planning"), trip.get("name", ""), trip_id)
    )
    
    conn.commit()
    conn.close()
    
    return trip


def delete_trip(trip_id: str) -> dict:
    """Delete a trip."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return {"deleted": deleted, "trip_id": trip_id}


# ============ Wish Sessions ============

def store_wishes(family_id: str, member_id: str, wishes: dict) -> dict:
    """Store wishes from a family member for a trip planning session."""
    conn = get_connection()
    cursor = conn.cursor()
    
    wish_id = str(uuid4())[:8]
    now = datetime.utcnow().isoformat()
    
    cursor.execute(
        "INSERT INTO wish_sessions (id, family_id, member_id, wishes_json, created_at) VALUES (?, ?, ?, ?, ?)",
        (wish_id, family_id, member_id, json.dumps(wishes, ensure_ascii=False), now)
    )
    
    conn.commit()
    conn.close()
    
    return {"id": wish_id, "stored": True}


def get_family_wishes(family_id: str) -> list:
    """Get all wishes for a family."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, member_id, wishes_json, created_at FROM wish_sessions WHERE family_id = ? ORDER BY created_at DESC",
        (family_id,)
    )
    
    results = []
    for row in cursor.fetchall():
        results.append({
            "id": row["id"],
            "member_id": row["member_id"],
            "wishes": json.loads(row["wishes_json"]),
            "created_at": row["created_at"]
        })
    
    conn.close()
    return results


# ============ Destination Cache ============

def cache_destination(name: str, country: str, data: dict) -> dict:
    """Cache destination information."""
    conn = get_connection()
    cursor = conn.cursor()
    
    dest_id = f"{name.lower().replace(' ', '_')}_{country.lower()}"
    now = datetime.utcnow().isoformat()
    
    cursor.execute(
        "INSERT OR REPLACE INTO destination_cache (id, name, country, data_json, cached_at) VALUES (?, ?, ?, ?, ?)",
        (dest_id, name, country, json.dumps(data, ensure_ascii=False), now)
    )
    
    conn.commit()
    conn.close()
    
    return {"id": dest_id, "cached": True}


def get_cached_destination(name: str, country: str = None) -> Optional[dict]:
    """Get cached destination info."""
    conn = get_connection()
    cursor = conn.cursor()
    
    if country:
        dest_id = f"{name.lower().replace(' ', '_')}_{country.lower()}"
        cursor.execute("SELECT data_json FROM destination_cache WHERE id = ?", (dest_id,))
    else:
        cursor.execute("SELECT data_json FROM destination_cache WHERE name LIKE ?", (f"%{name}%",))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row["data_json"])
    return None


# ============ Statistics ============

def get_stats() -> dict:
    """Get database statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute("SELECT COUNT(*) FROM families")
    stats["total_families"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM family_members")
    stats["total_members"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trips")
    stats["total_trips"] = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, COUNT(*) FROM trips GROUP BY status")
    stats["trips_by_status"] = {row[0]: row[1] for row in cursor.fetchall()}
    
    cursor.execute("SELECT COUNT(*) FROM destination_cache")
    stats["cached_destinations"] = cursor.fetchone()[0]
    
    conn.close()
    return stats


# ============ CLI ============

def main():
    parser = argparse.ArgumentParser(description="Holiday Planner Memory CLI")
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--family", nargs="+", help="Family operations: create <name> | list | get <id>")
    parser.add_argument("--trip", nargs="+", help="Trip operations: create <name> | list | get <id>")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    
    args = parser.parse_args()
    
    if args.init:
        result = init_database()
        print(json.dumps(result, indent=2))
    
    elif args.family:
        action = args.family[0]
        if action == "create" and len(args.family) > 1:
            result = create_family(args.family[1])
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif action == "list":
            result = list_families()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif action == "get" and len(args.family) > 1:
            result = get_family(args.family[1])
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Usage: --family create <name> | list | get <id>")
    
    elif args.trip:
        action = args.trip[0]
        if action == "create" and len(args.trip) > 1:
            result = create_trip(args.trip[1])
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif action == "list":
            result = list_trips()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif action == "get" and len(args.trip) > 1:
            result = get_trip(args.trip[1])
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Usage: --trip create <name> | list | get <id>")
    
    elif args.stats:
        result = get_stats()
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
