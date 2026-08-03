#!/usr/bin/env python3
"""
Recall Knowledge Tool

Retrieves Leanheat Building knowledge from the RAG-backed memory.
Uses semantic search to find relevant facts about energy optimization.

Usage:
    python recall_knowledge.py "How does Leanheat reduce energy costs?"
    python recall_knowledge.py "demand response" --category statistic --format json
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

AGENT_DIR = Path(__file__).parent.parent
PROJECT_ROOT = AGENT_DIR.parent.parent.parent


def recall_leanheat_knowledge(
    query: str,
    n_results: int = 5,
    category: str = None,
    format_type: str = "json"
) -> dict:
    """
    Recall knowledge from the Leanheat memory database.
    
    Args:
        query: Search query
        n_results: Number of results to return
        category: Optional category filter (feature, benefit, technology, etc.)
        format_type: Output format (json or text)
    
    Returns:
        dict with search results
    """
    cmd = [
        "npm", "run", "leanheat-memory", "--",
        "recall", query,
        "-n", str(n_results),
        "-f", format_type
    ]
    
    if category:
        cmd.extend(["-c", category])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=60
        )
        
        if result.returncode == 0:
            if format_type == "json":
                try:
                    output = result.stdout.strip()
                    start = output.find('{')
                    if start >= 0:
                        return json.loads(output[start:])
                except json.JSONDecodeError:
                    pass
            
            return {
                "status": "success",
                "query": query,
                "raw_output": result.stdout.strip()
            }
        else:
            return {
                "status": "error",
                "query": query,
                "error": result.stderr.strip() or "Command failed"
            }
    
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "query": query,
            "error": "Search timed out"
        }
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "error": str(e)
        }


def list_knowledge_stats() -> dict:
    """Get statistics about the knowledge base."""
    cmd = ["npm", "run", "leanheat-memory", "--", "list"]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=30
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "output": result.stdout.strip()
            }
        else:
            return {
                "status": "error",
                "error": result.stderr.strip() or "Command failed"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def store_knowledge(
    fact: str,
    topic: str,
    category: str = "general",
    keywords: list = None
) -> dict:
    """Store a new fact in the knowledge base."""
    cmd = [
        "npm", "run", "leanheat-memory", "--",
        "store",
        "-f", fact,
        "-t", topic,
        "-c", category
    ]
    
    if keywords:
        cmd.extend(["-k"] + keywords)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=60
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "topic": topic,
                "message": "Fact stored successfully"
            }
        else:
            return {
                "status": "error",
                "error": result.stderr.strip() or "Command failed"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(description="Recall Leanheat Knowledge")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("-n", "--n-results", type=int, default=5, help="Number of results")
    parser.add_argument("-c", "--category", help="Filter by category")
    parser.add_argument("-f", "--format", choices=["json", "text"], default="json", help="Output format")
    parser.add_argument("--stats", action="store_true", help="Show knowledge base stats")
    parser.add_argument("--store", action="store_true", help="Store a new fact")
    parser.add_argument("--topic", help="Topic for storing fact")
    
    args = parser.parse_args()
    
    if args.stats:
        result = list_knowledge_stats()
        print(json.dumps(result, indent=2))
    elif args.store and args.query and args.topic:
        result = store_knowledge(args.query, args.topic, args.category or "general")
        print(json.dumps(result, indent=2))
    elif args.query:
        result = recall_leanheat_knowledge(
            args.query,
            args.n_results,
            args.category,
            args.format
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
