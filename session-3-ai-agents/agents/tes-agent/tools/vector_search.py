#!/usr/bin/env python3
"""
Vector Search Module for TES Agent

Uses ChromaDB for semantic search across TES content.
Embeddings generated via Google Gemini text-embedding-004 model.
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from google import genai
from google.genai import types

MEMORY_PATH = Path(__file__).parent.parent / "memory"
VECTOR_DB_PATH = MEMORY_PATH / "data" / "vector_db"
DATA_PATH = MEMORY_PATH / "data" / "tes"

# Ensure directories exist
VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)

COLLECTION_NAME = "tes_documents"
EMBEDDING_MODEL = "gemini-embedding-2"


def get_client() -> genai.Client:
    """Get Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable required")
    return genai.Client(api_key=api_key)


def get_embedding(text: str, client: genai.Client) -> List[float]:
    """Generate embedding for text using Gemini."""
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text
    )
    return result.embeddings[0].values


def get_chroma_client() -> "chromadb.Client":
    """Get ChromaDB client."""
    if not CHROMADB_AVAILABLE:
        raise ImportError("chromadb not installed. Run: pip install chromadb")
    
    return chromadb.PersistentClient(
        path=str(VECTOR_DB_PATH),
        settings=Settings(anonymized_telemetry=False)
    )


def get_or_create_collection(chroma_client: "chromadb.Client") -> "chromadb.Collection":
    """Get or create the TES documents collection."""
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "TES document content for semantic search"}
    )


def chunk_tes_content(tes_data: dict, tes_name: str) -> List[Dict]:
    """Break TES content into searchable chunks with metadata."""
    chunks = []
    
    def add_chunk(content: str, section: str, metadata: dict = None):
        if content and len(content.strip()) > 20:
            chunk_id = hashlib.md5(f"{tes_name}:{section}:{content[:100]}".encode()).hexdigest()
            chunk = {
                "id": chunk_id,
                "content": content.strip(),
                "section": section,
                "tes_name": tes_name,
                "metadata": metadata or {}
            }
            chunks.append(chunk)
    
    # Basic info
    if tes_data.get("name"):
        add_chunk(f"TES: {tes_data['name']}", "name")
    
    if tes_data.get("validity_period"):
        vp = tes_data["validity_period"]
        add_chunk(
            f"Voimassaolo: {vp.get('start_date', '')} - {vp.get('end_date', '')}",
            "validity_period"
        )
    
    # Scope
    if tes_data.get("scope"):
        scope = tes_data["scope"]
        scope_text = []
        if scope.get("industries"):
            scope_text.append(f"Toimialat: {', '.join(scope['industries'])}")
        if scope.get("employee_groups"):
            scope_text.append(f"Työntekijäryhmät: {', '.join(scope['employee_groups'])}")
        if scope.get("geographical_scope"):
            scope_text.append(f"Alue: {scope['geographical_scope']}")
        if scope.get("exclusions"):
            scope_text.append(f"Poissuljetut: {', '.join(scope['exclusions'])}")
        if scope_text:
            add_chunk("\n".join(scope_text), "scope")
    
    # Working hours
    if tes_data.get("working_hours"):
        wh = tes_data["working_hours"]
        wh_text = []
        if wh.get("weekly_hours"):
            wh_text.append(f"Viikkotyöaika: {wh['weekly_hours']} tuntia")
        if wh.get("daily_hours"):
            wh_text.append(f"Päivittäinen työaika: {wh['daily_hours']} tuntia")
        if wh.get("averaging_period"):
            wh_text.append(f"Tasoittumisjakso: {wh['averaging_period']}")
        if wh_text:
            add_chunk("\n".join(wh_text), "working_hours")
    
    # Salary tables - each table as separate chunk
    if tes_data.get("salary_tables"):
        for i, table in enumerate(tes_data["salary_tables"]):
            table_text = f"Palkkataulukko: {table.get('name', f'Taulukko {i+1}')}\n"
            if table.get("effective_date"):
                table_text += f"Voimassa: {table['effective_date']}\n"
            if table.get("levels"):
                table_text += "Tasot:\n"
                for level in table["levels"]:
                    table_text += f"  - {level.get('name', 'N/A')}: {level.get('monthly_salary', level.get('hourly_rate', 'N/A'))} €\n"
            add_chunk(table_text, f"salary_table_{i}", {"table_name": table.get("name", "")})
    
    # Job classification
    if tes_data.get("job_classification"):
        jc = tes_data["job_classification"]
        jc_text = f"Palkkaryhmittely: {jc.get('system', 'N/A')}\n"
        if jc.get("groups"):
            for group in jc["groups"]:
                jc_text += f"  - {group.get('name', 'N/A')}: {group.get('description', '')}\n"
        add_chunk(jc_text, "job_classification")
    
    # Overtime
    if tes_data.get("overtime"):
        ot = tes_data["overtime"]
        ot_text = "Ylityökorvaukset:\n"
        if ot.get("daily_first_hours"):
            ot_text += f"  Vuorokautinen ylityö (1-2h): {ot['daily_first_hours']}%\n"
        if ot.get("daily_additional"):
            ot_text += f"  Vuorokautinen ylityö (jatkuva): {ot['daily_additional']}%\n"
        if ot.get("weekly_first_hours"):
            ot_text += f"  Viikottainen ylityö (1-8h): {ot['weekly_first_hours']}%\n"
        if ot.get("weekly_additional"):
            ot_text += f"  Viikottainen ylityö (jatkuva): {ot['weekly_additional']}%\n"
        add_chunk(ot_text, "overtime")
    
    # Shift work
    if tes_data.get("shift_work"):
        sw = tes_data["shift_work"]
        sw_text = "Vuorotyölisät:\n"
        if sw.get("evening_compensation"):
            sw_text += f"  Iltalisa: {sw['evening_compensation']}\n"
        if sw.get("night_compensation"):
            sw_text += f"  Yölisä: {sw['night_compensation']}\n"
        add_chunk(sw_text, "shift_work")
    
    # Weekend/holiday
    if tes_data.get("weekend_and_holiday_work"):
        wh = tes_data["weekend_and_holiday_work"]
        wh_text = "Viikonloppu- ja pyhätyö:\n"
        if wh.get("saturday_compensation"):
            wh_text += f"  Lauantailisä: {wh['saturday_compensation']}\n"
        if wh.get("sunday_compensation"):
            wh_text += f"  Sunnuntaityö: {wh['sunday_compensation']}\n"
        if wh.get("holiday_compensation"):
            wh_text += f"  Pyhätyö: {wh['holiday_compensation']}\n"
        add_chunk(wh_text, "weekend_holiday")
    
    # Vacation
    if tes_data.get("vacation"):
        vac = tes_data["vacation"]
        vac_text = "Vuosiloma:\n"
        if vac.get("days_first_year"):
            vac_text += f"  Ensimmäinen vuosi: {vac['days_first_year']} pv\n"
        if vac.get("days_standard"):
            vac_text += f"  Normaali: {vac['days_standard']} pv\n"
        if vac.get("days_senior"):
            vac_text += f"  Pitkä työsuhde: {vac['days_senior']} pv\n"
        if vac.get("vacation_bonus"):
            vac_text += f"  Lomaraha: {vac['vacation_bonus']}\n"
        add_chunk(vac_text, "vacation")
    
    # Sick leave
    if tes_data.get("sick_leave"):
        sl = tes_data["sick_leave"]
        sl_text = "Sairausloma:\n"
        if sl.get("paid_days_standard"):
            sl_text += f"  Palkallinen jakso: {sl['paid_days_standard']} pv\n"
        if sl.get("salary_percentage"):
            sl_text += f"  Palkan osuus: {sl['salary_percentage']}%\n"
        add_chunk(sl_text, "sick_leave")
    
    # Notice periods
    if tes_data.get("notice_periods"):
        np = tes_data["notice_periods"]
        np_text = "Irtisanomisajat:\n"
        if np.get("employee_periods"):
            np_text += "  Työntekijä:\n"
            for period in np["employee_periods"]:
                np_text += f"    - {period.get('tenure', 'N/A')}: {period.get('notice_period', 'N/A')}\n"
        if np.get("employer_periods"):
            np_text += "  Työnantaja:\n"
            for period in np["employer_periods"]:
                np_text += f"    - {period.get('tenure', 'N/A')}: {period.get('notice_period', 'N/A')}\n"
        add_chunk(np_text, "notice_periods")
    
    # Allowances
    if tes_data.get("allowances"):
        allow = tes_data["allowances"]
        allow_text = "Lisät ja korvaukset:\n"
        for key, value in allow.items():
            if isinstance(value, dict) and value.get("amount"):
                allow_text += f"  {key}: {value['amount']} €\n"
            elif isinstance(value, (int, float)):
                allow_text += f"  {key}: {value} €\n"
        if len(allow_text) > 30:
            add_chunk(allow_text, "allowances")
    
    # Other terms - include if present
    if tes_data.get("other_terms"):
        for key, value in tes_data["other_terms"].items():
            if isinstance(value, str) and len(value) > 20:
                add_chunk(f"{key}: {value}", f"other_{key}")
            elif isinstance(value, dict):
                add_chunk(f"{key}: {json.dumps(value, ensure_ascii=False)}", f"other_{key}")
    
    return chunks


def index_tes(tes_name: str, tes_data: dict, client: genai.Client = None) -> Dict:
    """Index a TES document for vector search."""
    if client is None:
        client = get_client()
    
    chroma_client = get_chroma_client()
    collection = get_or_create_collection(chroma_client)
    
    # Generate chunks
    chunks = chunk_tes_content(tes_data, tes_name)
    
    if not chunks:
        return {"status": "error", "message": "No content to index"}
    
    # Delete existing chunks for this TES
    try:
        existing = collection.get(where={"tes_name": tes_name})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass  # Collection might be empty
    
    # Generate embeddings and add to collection
    ids = []
    embeddings = []
    documents = []
    metadatas = []
    
    for chunk in chunks:
        try:
            embedding = get_embedding(chunk["content"], client)
            
            ids.append(chunk["id"])
            embeddings.append(embedding)
            documents.append(chunk["content"])
            metadatas.append({
                "tes_name": tes_name,
                "section": chunk["section"],
                **chunk.get("metadata", {})
            })
        except Exception as e:
            print(f"Warning: Failed to embed chunk {chunk['section']}: {e}", file=sys.stderr)
            continue
    
    if ids:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
    
    return {
        "status": "success",
        "tes_name": tes_name,
        "chunks_indexed": len(ids),
        "total_chunks": len(chunks)
    }


def search(query: str, n_results: int = 5, tes_filter: str = None, client: genai.Client = None) -> List[Dict]:
    """
    Semantic search across TES documents.
    
    Args:
        query: Search query in Finnish or English
        n_results: Number of results to return
        tes_filter: Optional TES name to filter by
        client: Gemini client (will create if not provided)
    
    Returns:
        List of matching chunks with scores
    """
    if client is None:
        client = get_client()
    
    chroma_client = get_chroma_client()
    collection = get_or_create_collection(chroma_client)
    
    # Generate query embedding
    query_embedding = get_embedding(query, client)
    
    # Build search params
    search_params = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"]
    }
    
    if tes_filter:
        search_params["where"] = {"tes_name": tes_filter}
    
    # Search
    results = collection.query(**search_params)
    
    # Format results
    formatted = []
    for i, doc in enumerate(results["documents"][0]):
        formatted.append({
            "content": doc,
            "tes_name": results["metadatas"][0][i].get("tes_name", "unknown"),
            "section": results["metadatas"][0][i].get("section", "unknown"),
            "score": 1 - results["distances"][0][i],  # Convert distance to similarity
            "metadata": results["metadatas"][0][i]
        })
    
    return formatted


def reindex_all(client: genai.Client = None) -> Dict:
    """Reindex all TES documents from the data folder."""
    if client is None:
        client = get_client()
    
    results = {"indexed": [], "errors": []}
    
    # Find all TES JSON files
    for json_file in DATA_PATH.glob("*.json"):
        if json_file.name in ["icp.json", "schema.json"]:
            continue
        
        try:
            with open(json_file) as f:
                tes_data = json.load(f)
            
            tes_name = tes_data.get("name", json_file.stem)
            result = index_tes(tes_name, tes_data, client)
            results["indexed"].append({
                "name": tes_name,
                "file": json_file.name,
                "chunks": result.get("chunks_indexed", 0)
            })
        except Exception as e:
            results["errors"].append({
                "file": json_file.name,
                "error": str(e)
            })
    
    return results


def get_stats() -> Dict:
    """Get vector database statistics."""
    if not CHROMADB_AVAILABLE:
        return {"error": "chromadb not available"}
    
    try:
        chroma_client = get_chroma_client()
        collection = get_or_create_collection(chroma_client)
        
        count = collection.count()
        
        # Get unique TES names
        if count > 0:
            sample = collection.get(limit=count, include=["metadatas"])
            tes_names = list(set(m.get("tes_name", "unknown") for m in sample["metadatas"]))
        else:
            tes_names = []
        
        return {
            "total_chunks": count,
            "indexed_tes": tes_names,
            "num_tes": len(tes_names),
            "db_path": str(VECTOR_DB_PATH)
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TES Vector Search")
    subparsers = parser.add_subparsers(dest="command")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search TES content")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-n", "--num-results", type=int, default=5, help="Number of results")
    search_parser.add_argument("--tes", help="Filter by TES name")
    
    # Index command  
    index_parser = subparsers.add_parser("index", help="Index a TES document")
    index_parser.add_argument("--file", help="TES JSON file to index")
    index_parser.add_argument("--all", action="store_true", help="Reindex all TES documents")
    
    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")
    
    args = parser.parse_args()
    
    if args.command == "search":
        results = search(args.query, n_results=args.num_results, tes_filter=args.tes)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    
    elif args.command == "index":
        if args.all:
            results = reindex_all()
            print(json.dumps(results, ensure_ascii=False, indent=2))
        elif args.file:
            with open(args.file) as f:
                tes_data = json.load(f)
            tes_name = tes_data.get("name", Path(args.file).stem)
            result = index_tes(tes_name, tes_data)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("Specify --file or --all")
    
    elif args.command == "stats":
        stats = get_stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()
