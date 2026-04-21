#!/usr/bin/env python3
"""
Memory CLI — ChromaDB-based memory for the Prospecting Agent

Provides persistent storage for:
- ICP (Ideal Customer Profile) preferences
- Session state and conversation history
- Learned preferences from user interactions

Usage:
  python memory.py get-icp                     # Get current ICP
  python memory.py set-icp --file icp.json     # Set ICP from file
  python memory.py update-icp --key industries --value '["SaaS", "Fintech"]'
  python memory.py store --key session_id --value "abc123"
  python memory.py retrieve --key session_id
  python memory.py search --query "AI companies"
  python memory.py list                        # List all stored items
  python memory.py clear --collection icp      # Clear a collection
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try to import chromadb, fall back to file-based storage
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

# Try to import numpy for embeddings
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Try to import Gemini for embeddings
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# Configuration
MEMORY_DIR = Path(__file__).parent / "data"
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))
EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSION = 768


class MemoryStore:
    """ChromaDB-based memory store with file fallback."""
    
    def __init__(self, use_server: bool = False, use_chroma: bool = False):
        self.memory_dir = MEMORY_DIR
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = None
        self.collections: Dict[str, Any] = {}
        
        # Only use ChromaDB if explicitly requested and available
        if use_chroma and CHROMA_AVAILABLE:
            try:
                if use_server:
                    self.client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
                else:
                    chroma_path = self.memory_dir / "chroma"
                    chroma_path.mkdir(parents=True, exist_ok=True)
                    self.client = chromadb.PersistentClient(path=str(chroma_path))
                self._init_collections()
            except Exception as e:
                print(f"Warning: ChromaDB initialization failed: {e}", file=sys.stderr)
                print("Falling back to file-based storage", file=sys.stderr)
                self.client = None
    
    def _init_collections(self):
        """Initialize ChromaDB collections."""
        if not self.client:
            return
        
        collection_names = ["icp", "prospects", "sessions", "preferences"]
        for name in collection_names:
            try:
                self.collections[name] = self.client.get_or_create_collection(
                    name=f"prospecting_{name}",
                    metadata={"description": f"Prospecting agent {name} storage"}
                )
            except Exception as e:
                print(f"Warning: Failed to create collection {name}: {e}", file=sys.stderr)
    
    def _get_collection(self, name: str):
        """Get or create a collection by name."""
        if not self.client:
            return None
        
        if name not in self.collections:
            try:
                self.collections[name] = self.client.get_or_create_collection(
                    name=f"prospecting_{name}",
                    metadata={"description": f"Prospecting agent {name} storage"}
                )
            except Exception as e:
                print(f"Warning: Failed to create collection {name}: {e}", file=sys.stderr)
                return None
        
        return self.collections.get(name)
    
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini."""
        if not GEMINI_AVAILABLE:
            # Return zero vector if Gemini not available
            return [0.0] * EMBEDDING_DIMENSION
        
        try:
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY")
            if not api_key:
                return [0.0] * EMBEDDING_DIMENSION
            
            client = genai.Client(api_key=api_key)
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=EMBEDDING_DIMENSION
                )
            )
            
            values = result.embeddings[0].values
            
            # Normalize if using reduced dimensions
            if NUMPY_AVAILABLE and EMBEDDING_DIMENSION != 3072:
                arr = np.array(values)
                norm = np.linalg.norm(arr)
                if norm > 0:
                    values = (arr / norm).tolist()
            
            return values
        except Exception as e:
            print(f"Warning: Embedding generation failed: {e}", file=sys.stderr)
            return [0.0] * EMBEDDING_DIMENSION
    
    def _file_path(self, collection: str) -> Path:
        """Get file path for file-based storage."""
        return self.memory_dir / f"{collection}.json"
    
    def _load_file(self, collection: str) -> Dict[str, Any]:
        """Load data from file."""
        path = self._file_path(collection)
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return {}
    
    def _save_file(self, collection: str, data: Dict[str, Any]):
        """Save data to file."""
        path = self._file_path(collection)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    # ICP Operations
    
    def get_icp(self) -> Optional[Dict[str, Any]]:
        """Get current ICP profile."""
        if self.client and "icp" in self.collections:
            try:
                results = self.collections["icp"].get(ids=["current_icp"])
                if results["documents"]:
                    return json.loads(results["documents"][0])
            except Exception:
                pass
        
        # Fallback to file
        data = self._load_file("icp")
        return data.get("current_icp")
    
    def set_icp(self, icp: Dict[str, Any]) -> bool:
        """Set ICP profile."""
        icp["updated_at"] = datetime.utcnow().isoformat()
        if "created_at" not in icp:
            icp["created_at"] = icp["updated_at"]
        
        icp_json = json.dumps(icp)
        
        if self.client and "icp" in self.collections:
            try:
                # Generate embedding from ICP description
                embed_text = f"{icp.get('name', '')} {' '.join(icp.get('target_industries', []))} {' '.join(icp.get('keywords', []))}"
                embedding = self._get_embedding(embed_text)
                
                self.collections["icp"].upsert(
                    ids=["current_icp"],
                    documents=[icp_json],
                    embeddings=[embedding],
                    metadatas=[{"type": "icp", "name": icp.get("name", "default")}]
                )
                return True
            except Exception as e:
                print(f"Warning: ChromaDB upsert failed: {e}", file=sys.stderr)
        
        # Fallback to file
        data = self._load_file("icp")
        data["current_icp"] = icp
        self._save_file("icp", data)
        return True
    
    def update_icp(self, key: str, value: Any) -> bool:
        """Update a specific ICP field."""
        icp = self.get_icp() or {"name": "default", "target_industries": [], "geography": []}
        icp[key] = value
        return self.set_icp(icp)
    
    # Generic Key-Value Operations
    
    def store(self, collection: str, key: str, value: Any, metadata: Optional[Dict] = None) -> bool:
        """Store a key-value pair."""
        value_json = json.dumps(value) if not isinstance(value, str) else value
        
        coll = self._get_collection(collection)
        if coll:
            try:
                embedding = self._get_embedding(value_json[:1000])  # Limit for embedding
                coll.upsert(
                    ids=[key],
                    documents=[value_json],
                    embeddings=[embedding],
                    metadatas=[metadata or {"key": key}]
                )
                return True
            except Exception as e:
                print(f"Warning: ChromaDB store failed: {e}", file=sys.stderr)
        
        # Fallback to file
        data = self._load_file(collection)
        data[key] = {"value": value, "metadata": metadata, "updated_at": datetime.utcnow().isoformat()}
        self._save_file(collection, data)
        return True
    
    def retrieve(self, collection: str, key: str) -> Optional[Any]:
        """Retrieve a value by key."""
        coll = self._get_collection(collection)
        if coll:
            try:
                results = coll.get(ids=[key])
                if results["documents"]:
                    try:
                        return json.loads(results["documents"][0])
                    except json.JSONDecodeError:
                        return results["documents"][0]
            except Exception:
                pass
        
        # Fallback to file
        data = self._load_file(collection)
        item = data.get(key)
        return item.get("value") if item else None
    
    def search(self, collection: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Semantic search in a collection."""
        coll = self._get_collection(collection)
        if coll:
            try:
                query_embedding = self._get_embedding(query)
                results = coll.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results
                )
                
                items = []
                for i, doc in enumerate(results["documents"][0]):
                    try:
                        value = json.loads(doc)
                    except json.JSONDecodeError:
                        value = doc
                    
                    items.append({
                        "id": results["ids"][0][i],
                        "value": value,
                        "distance": results["distances"][0][i] if results.get("distances") else None,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else None
                    })
                return items
            except Exception as e:
                print(f"Warning: ChromaDB search failed: {e}", file=sys.stderr)
        
        # Fallback: simple keyword search in file
        data = self._load_file(collection)
        query_lower = query.lower()
        results = []
        for key, item in data.items():
            value_str = json.dumps(item.get("value", "")).lower()
            if query_lower in value_str:
                results.append({"id": key, "value": item.get("value"), "metadata": item.get("metadata")})
        return results[:n_results]
    
    def list_items(self, collection: str) -> List[Dict[str, Any]]:
        """List all items in a collection."""
        coll = self._get_collection(collection)
        if coll:
            try:
                results = coll.get()
                items = []
                for i, doc in enumerate(results["documents"]):
                    try:
                        value = json.loads(doc)
                    except json.JSONDecodeError:
                        value = doc
                    items.append({
                        "id": results["ids"][i],
                        "value": value,
                        "metadata": results["metadatas"][i] if results.get("metadatas") else None
                    })
                return items
            except Exception:
                pass
        
        # Fallback to file
        data = self._load_file(collection)
        return [{"id": k, "value": v.get("value"), "metadata": v.get("metadata")} for k, v in data.items()]
    
    def clear(self, collection: str) -> bool:
        """Clear all items in a collection."""
        if self.client and collection in self.collections:
            try:
                # Delete and recreate collection
                self.client.delete_collection(f"prospecting_{collection}")
                self.collections[collection] = self.client.create_collection(
                    name=f"prospecting_{collection}",
                    metadata={"description": f"Prospecting agent {collection} storage"}
                )
                return True
            except Exception as e:
                print(f"Warning: ChromaDB clear failed: {e}", file=sys.stderr)
        
        # Fallback to file
        self._save_file(collection, {})
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Memory CLI for Prospecting Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--server", action="store_true", help="Use ChromaDB server instead of local")
    parser.add_argument("--chroma", action="store_true", help="Use ChromaDB (default: file-based storage)")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # get-icp
    subparsers.add_parser("get-icp", help="Get current ICP profile")
    
    # set-icp
    set_icp = subparsers.add_parser("set-icp", help="Set ICP from JSON file")
    set_icp.add_argument("--file", "-f", required=True, help="Path to ICP JSON file")
    
    # update-icp
    update_icp = subparsers.add_parser("update-icp", help="Update a specific ICP field")
    update_icp.add_argument("--key", "-k", required=True, help="Field key to update")
    update_icp.add_argument("--value", "-v", required=True, help="New value (JSON)")
    
    # store
    store = subparsers.add_parser("store", help="Store a key-value pair")
    store.add_argument("--collection", "-c", default="sessions", help="Collection name")
    store.add_argument("--key", "-k", required=True, help="Key")
    store.add_argument("--value", "-v", required=True, help="Value (JSON or string)")
    
    # retrieve
    retrieve = subparsers.add_parser("retrieve", help="Retrieve a value by key")
    retrieve.add_argument("--collection", "-c", default="sessions", help="Collection name")
    retrieve.add_argument("--key", "-k", required=True, help="Key")
    
    # search
    search = subparsers.add_parser("search", help="Semantic search")
    search.add_argument("--collection", "-c", default="prospects", help="Collection name")
    search.add_argument("--query", "-q", required=True, help="Search query")
    search.add_argument("--n", "-n", type=int, default=5, help="Number of results")
    
    # list
    list_cmd = subparsers.add_parser("list", help="List all items in collection")
    list_cmd.add_argument("--collection", "-c", default="sessions", help="Collection name")
    
    # clear
    clear = subparsers.add_parser("clear", help="Clear a collection")
    clear.add_argument("--collection", "-c", required=True, help="Collection name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    memory = MemoryStore(use_server=args.server, use_chroma=args.chroma)
    
    if args.command == "get-icp":
        icp = memory.get_icp()
        if icp:
            print(json.dumps(icp, indent=2))
        else:
            print(json.dumps({"error": "No ICP found"}))
            sys.exit(1)
    
    elif args.command == "set-icp":
        with open(args.file, "r") as f:
            icp = json.load(f)
        if memory.set_icp(icp):
            print(json.dumps({"status": "success", "message": "ICP updated"}))
        else:
            print(json.dumps({"status": "error", "message": "Failed to update ICP"}))
            sys.exit(1)
    
    elif args.command == "update-icp":
        try:
            value = json.loads(args.value)
        except json.JSONDecodeError:
            value = args.value
        
        if memory.update_icp(args.key, value):
            print(json.dumps({"status": "success", "key": args.key}))
        else:
            print(json.dumps({"status": "error", "message": "Failed to update ICP"}))
            sys.exit(1)
    
    elif args.command == "store":
        try:
            value = json.loads(args.value)
        except json.JSONDecodeError:
            value = args.value
        
        if memory.store(args.collection, args.key, value):
            print(json.dumps({"status": "success", "collection": args.collection, "key": args.key}))
        else:
            print(json.dumps({"status": "error", "message": "Failed to store"}))
            sys.exit(1)
    
    elif args.command == "retrieve":
        value = memory.retrieve(args.collection, args.key)
        if value is not None:
            print(json.dumps({"key": args.key, "value": value}))
        else:
            print(json.dumps({"error": "Key not found"}))
            sys.exit(1)
    
    elif args.command == "search":
        results = memory.search(args.collection, args.query, args.n)
        print(json.dumps({"query": args.query, "results": results}, indent=2))
    
    elif args.command == "list":
        items = memory.list_items(args.collection)
        print(json.dumps({"collection": args.collection, "items": items}, indent=2))
    
    elif args.command == "clear":
        if memory.clear(args.collection):
            print(json.dumps({"status": "success", "collection": args.collection}))
        else:
            print(json.dumps({"status": "error", "message": "Failed to clear"}))
            sys.exit(1)


if __name__ == "__main__":
    main()
