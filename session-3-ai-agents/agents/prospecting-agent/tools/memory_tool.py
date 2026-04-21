#!/usr/bin/env python3
"""
Memory Tool

Wrapper around the memory system for use by the main agent.
Provides simplified CLI access to ICP and session management.

Usage:
  python memory_tool.py icp get
  python memory_tool.py icp set --file icp.json
  python memory_tool.py icp update --key keywords --value '["AI", "ML"]'
  python memory_tool.py session get --key last_search
  python memory_tool.py session set --key last_search --value '{"query": "..."}'
  python memory_tool.py preference get --key default_model
  python memory_tool.py preference set --key default_model --value "gemini-2.5-flash"
"""

import argparse
import json
import sys
from pathlib import Path

# Add memory module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "memory"))
from memory import MemoryStore


def main():
    parser = argparse.ArgumentParser(
        description="Memory tool for the prospecting agent",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--server", action="store_true", help="Use ChromaDB server")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    
    subparsers = parser.add_subparsers(dest="category", help="Memory category")
    
    # ICP commands
    icp_parser = subparsers.add_parser("icp", help="ICP management")
    icp_sub = icp_parser.add_subparsers(dest="action")
    
    icp_sub.add_parser("get", help="Get current ICP")
    
    icp_set = icp_sub.add_parser("set", help="Set ICP from file")
    icp_set.add_argument("--file", "-f", required=True, help="ICP JSON file")
    
    icp_update = icp_sub.add_parser("update", help="Update ICP field")
    icp_update.add_argument("--key", "-k", required=True, help="Field to update")
    icp_update.add_argument("--value", "-v", required=True, help="New value (JSON)")
    
    # Session commands
    session_parser = subparsers.add_parser("session", help="Session management")
    session_sub = session_parser.add_subparsers(dest="action")
    
    session_get = session_sub.add_parser("get", help="Get session value")
    session_get.add_argument("--key", "-k", required=True, help="Key to retrieve")
    
    session_set = session_sub.add_parser("set", help="Set session value")
    session_set.add_argument("--key", "-k", required=True, help="Key")
    session_set.add_argument("--value", "-v", required=True, help="Value (JSON)")
    
    session_sub.add_parser("list", help="List session items")
    session_sub.add_parser("clear", help="Clear session")
    
    # Preference commands
    pref_parser = subparsers.add_parser("preference", help="User preferences")
    pref_sub = pref_parser.add_subparsers(dest="action")
    
    pref_get = pref_sub.add_parser("get", help="Get preference")
    pref_get.add_argument("--key", "-k", required=True, help="Preference key")
    
    pref_set = pref_sub.add_parser("set", help="Set preference")
    pref_set.add_argument("--key", "-k", required=True, help="Preference key")
    pref_set.add_argument("--value", "-v", required=True, help="Value")
    
    pref_sub.add_parser("list", help="List preferences")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search memory")
    search_parser.add_argument("--collection", "-c", default="prospects", help="Collection")
    search_parser.add_argument("--query", "-q", required=True, help="Search query")
    search_parser.add_argument("--n", type=int, default=5, help="Number of results")
    
    args = parser.parse_args()
    
    if not args.category:
        parser.print_help()
        sys.exit(1)
    
    memory = MemoryStore(use_server=args.server)
    indent = 2 if args.pretty else None
    
    try:
        if args.category == "icp":
            if args.action == "get":
                icp = memory.get_icp()
                if icp:
                    print(json.dumps(icp, indent=indent))
                else:
                    print(json.dumps({"error": "No ICP found"}))
                    sys.exit(1)
            
            elif args.action == "set":
                with open(args.file, "r") as f:
                    icp = json.load(f)
                if memory.set_icp(icp):
                    print(json.dumps({"status": "success", "action": "icp_set"}))
                else:
                    print(json.dumps({"status": "error"}))
                    sys.exit(1)
            
            elif args.action == "update":
                try:
                    value = json.loads(args.value)
                except json.JSONDecodeError:
                    value = args.value
                
                if memory.update_icp(args.key, value):
                    print(json.dumps({"status": "success", "key": args.key}))
                else:
                    print(json.dumps({"status": "error"}))
                    sys.exit(1)
        
        elif args.category == "session":
            if args.action == "get":
                value = memory.retrieve("sessions", args.key)
                if value is not None:
                    print(json.dumps({"key": args.key, "value": value}, indent=indent))
                else:
                    print(json.dumps({"error": "Key not found", "key": args.key}))
                    sys.exit(1)
            
            elif args.action == "set":
                try:
                    value = json.loads(args.value)
                except json.JSONDecodeError:
                    value = args.value
                
                if memory.store("sessions", args.key, value):
                    print(json.dumps({"status": "success", "key": args.key}))
                else:
                    print(json.dumps({"status": "error"}))
                    sys.exit(1)
            
            elif args.action == "list":
                items = memory.list_items("sessions")
                print(json.dumps({"items": items}, indent=indent))
            
            elif args.action == "clear":
                if memory.clear("sessions"):
                    print(json.dumps({"status": "success", "action": "session_cleared"}))
                else:
                    print(json.dumps({"status": "error"}))
                    sys.exit(1)
        
        elif args.category == "preference":
            if args.action == "get":
                value = memory.retrieve("preferences", args.key)
                if value is not None:
                    print(json.dumps({"key": args.key, "value": value}, indent=indent))
                else:
                    print(json.dumps({"error": "Preference not found", "key": args.key}))
                    sys.exit(1)
            
            elif args.action == "set":
                try:
                    value = json.loads(args.value)
                except json.JSONDecodeError:
                    value = args.value
                
                if memory.store("preferences", args.key, value):
                    print(json.dumps({"status": "success", "key": args.key}))
                else:
                    print(json.dumps({"status": "error"}))
                    sys.exit(1)
            
            elif args.action == "list":
                items = memory.list_items("preferences")
                print(json.dumps({"items": items}, indent=indent))
        
        elif args.category == "search":
            results = memory.search(args.collection, args.query, args.n)
            print(json.dumps({"query": args.query, "results": results}, indent=indent))
    
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
