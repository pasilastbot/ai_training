#!/usr/bin/env python3
"""Store and retrieve personal coding preferences in SQLite (skill-local DB)."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / ".agents" / "skills" / "coding-preferences" / "preferences.db"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS preferences (
            key TEXT PRIMARY KEY,
            category TEXT,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_preferences_category ON preferences(category)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_preferences_updated ON preferences(updated_at)"
    )
    conn.commit()


def cmd_set(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    if args.stdin:
        value = sys.stdin.read()
    elif args.value is not None:
        value = args.value
    else:
        print("error: provide --value or --stdin", file=sys.stderr)
        return 1
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO preferences (key, category, value, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            category = COALESCE(excluded.category, preferences.category),
            value = excluded.value,
            updated_at = excluded.updated_at
        """,
        (args.key, args.category, value.rstrip("\n"), now),
    )
    conn.commit()
    print(f"saved: {args.key}")
    return 0


def cmd_get(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    row = conn.execute(
        "SELECT key, category, value, updated_at FROM preferences WHERE key = ?",
        (args.key,),
    ).fetchone()
    if not row:
        print(f"error: no preference for key {args.key!r}", file=sys.stderr)
        return 1
    if args.json:
        import json

        print(
            json.dumps(
                {
                    "key": row["key"],
                    "category": row["category"],
                    "value": row["value"],
                    "updated_at": row["updated_at"],
                },
                indent=2,
            )
        )
    else:
        cat = row["category"] or ""
        prefix = f"[{cat}] " if cat else ""
        print(f"{prefix}{row['key']}\n---\n{row['value']}\n---\nupdated: {row['updated_at']}")
    return 0


def cmd_list(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    params: list[str] = []
    where = "1=1"
    if args.category:
        where += " AND category = ?"
        params.append(args.category)
    rows = conn.execute(
        f"SELECT key, category, updated_at FROM preferences WHERE {where} "
        "ORDER BY COALESCE(category, ''), key",
        params,
    ).fetchall()
    if not rows:
        print("(no preferences stored)")
        return 0
    for r in rows:
        cat = f" [{r['category']}]" if r["category"] else ""
        print(f"{r['key']}{cat}  ({r['updated_at']})")
    return 0


def cmd_delete(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    cur = conn.execute("DELETE FROM preferences WHERE key = ?", (args.key,))
    conn.commit()
    if cur.rowcount == 0:
        print(f"error: no preference for key {args.key!r}", file=sys.stderr)
        return 1
    print(f"deleted: {args.key}")
    return 0


def cmd_search(conn: sqlite3.Connection, args: argparse.Namespace) -> int:
    term = f"%{args.term}%"
    rows = conn.execute(
        """
        SELECT key, category, substr(value, 1, 200) AS preview, updated_at
        FROM preferences
        WHERE key LIKE ? OR value LIKE ?
        ORDER BY key
        """,
        (term, term),
    ).fetchall()
    if not rows:
        print("(no matches)")
        return 0
    for r in rows:
        cat = f" [{r['category']}]" if r["category"] else ""
        prev = r["preview"].replace("\n", " ")
        if len(r["preview"]) == 200:
            prev += "…"
        print(f"{r['key']}{cat}\n  {prev}\n  ({r['updated_at']})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_set = sub.add_parser("set", help="Create or replace a preference")
    p_set.add_argument("key", help="Dot-separated key, e.g. typescript.style")
    p_set.add_argument("--category", "-c", help="Optional group, e.g. style, git, tests")
    p_set.add_argument("--value", "-v", help="Preference text")
    p_set.add_argument(
        "--stdin",
        action="store_true",
        help="Read preference body from stdin (multiline)",
    )
    p_set.set_defaults(func=cmd_set)

    p_get = sub.add_parser("get", help="Print one preference")
    p_get.add_argument("key")
    p_get.add_argument("--json", action="store_true", help="Machine-readable output")
    p_get.set_defaults(func=cmd_get)

    p_list = sub.add_parser("list", help="List all keys (optional filter)")
    p_list.add_argument("--category", "-c", help="Only this category")
    p_list.set_defaults(func=cmd_list)

    p_del = sub.add_parser("delete", help="Remove a preference")
    p_del.add_argument("key")
    p_del.set_defaults(func=cmd_delete)

    p_search = sub.add_parser("search", help="Search keys and values (SQL LIKE)")
    p_search.add_argument("term", help="Substring to match")
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args()
    conn = connect()
    try:
        init_db(conn)
        return int(args.func(conn, args))
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
