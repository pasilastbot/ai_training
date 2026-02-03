#!/usr/bin/env python3
"""
Semantic search tool using Gemini embeddings and ChromaDB.
Designed to work with documents indexed by index_site_gemini.py.

Uses RETRIEVAL_QUERY task type for search queries, which pairs with
RETRIEVAL_DOCUMENT task type used during indexing.
"""

import argparse
import json
import chromadb
import os
import sys
import numpy as np
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown

# Load environment variables from .env.local
load_dotenv(".env.local")

# Configuration
EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_DIMENSION = 768  # Must match the dimension used during indexing
DEFAULT_COLLECTION = "docs_gemini"

console = Console()


def get_api_key() -> str:
    """Get the Google API key from environment variables."""
    api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise Exception(
            "Google API key not found. Please set GOOGLE_AI_STUDIO_KEY or GEMINI_API_KEY environment variable"
        )
    return api_key


def generate_query_embedding(
    query: str, 
    dimension: int = DEFAULT_DIMENSION
) -> List[float]:
    """
    Generate embedding for the search query using Gemini.
    
    Uses RETRIEVAL_QUERY task type which is optimized for search queries,
    pairing with RETRIEVAL_DOCUMENT used during document indexing.
    """
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    
    console.print(f"[cyan]Generating query embedding with {EMBEDDING_MODEL} ({dimension}D)[/cyan]")
    
    try:
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=dimension
            )
        )
        
        embedding = result.embeddings[0].values
        
        # Normalize for non-3072 dimensions
        if dimension != 3072:
            embedding_array = np.array(embedding)
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                embedding = (embedding_array / norm).tolist()
        
        console.print(f"[green]✓ Generated embedding with {len(embedding)} dimensions[/green]")
        return embedding
        
    except Exception as e:
        console.print(f"[red]✗ Error generating query embedding: {e}[/red]")
        raise e


def search_chromadb(
    query_embedding: List[float],
    collection_name: str,
    n_results: int = 5,
    chroma_host: str = "localhost",
    chroma_port: int = 8000,
    where_filter: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Search ChromaDB using the query embedding."""
    console.print(f"[cyan]Searching collection: {collection_name}[/cyan]")
    
    try:
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        collection = client.get_collection(name=collection_name)
        
        # Perform the search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        result_count = len(results['documents'][0]) if results['documents'] else 0
        console.print(f"[green]✓ Found {result_count} results[/green]")
        return results
        
    except Exception as e:
        console.print(f"[red]✗ Error searching ChromaDB: {e}[/red]")
        raise e


def format_results_text(results: Dict[str, Any]) -> None:
    """Format and print search results in a readable text format."""
    if not results['documents'] or not results['documents'][0]:
        console.print("[yellow]No results found.[/yellow]")
        return
    
    documents = results['documents'][0]
    metadatas = results.get('metadatas', [[]])[0] if results.get('metadatas') else []
    distances = results.get('distances', [[]])[0] if results.get('distances') else []
    
    console.print("\n[bold]Search Results:[/bold]\n")
    
    for i, doc in enumerate(documents):
        try:
            chunk_data = json.loads(doc)
            distance = distances[i] if i < len(distances) else None
            similarity = 1 - distance if distance is not None else None
            
            # Result header
            if similarity is not None:
                console.print(f"[bold cyan]Result {i+1}[/bold cyan] (similarity: {similarity:.4f})")
            else:
                console.print(f"[bold cyan]Result {i+1}[/bold cyan]")
            
            # Topic and question
            console.print(f"  [bold]Topic:[/bold] {chunk_data.get('topic', 'N/A')}")
            console.print(f"  [bold]Question:[/bold] {chunk_data.get('question', 'N/A')}")
            
            # Keywords
            keywords = chunk_data.get('keywords', [])
            if keywords:
                console.print(f"  [bold]Keywords:[/bold] {', '.join(keywords)}")
            
            # Content preview
            content = chunk_data.get('content', '')
            if len(content) > 300:
                content = content[:300] + "..."
            console.print(f"  [bold]Content:[/bold] {content}")
            
            # Metadata
            metadata = metadatas[i] if i < len(metadatas) and metadatas else {}
            if metadata:
                if metadata.get('source_url'):
                    console.print(f"  [bold]Source:[/bold] {metadata['source_url']}")
            
            # Table info
            if chunk_data.get('table'):
                table = chunk_data['table']
                console.print(f"  [bold]Table:[/bold] {table.get('table_name', 'Unnamed')}")
            
            # Image info
            if chunk_data.get('image'):
                image = chunk_data['image']
                if image.get('image_url'):
                    console.print(f"  [bold]Image:[/bold] {image.get('image_title', 'Untitled')}")
            
            console.print()  # Empty line between results
            
        except json.JSONDecodeError:
            console.print(f"[bold cyan]Result {i+1}[/bold cyan]")
            console.print(f"  [bold]Raw Content:[/bold] {doc[:300]}...")
            console.print()


def format_results_json(results: Dict[str, Any]) -> str:
    """Format search results as JSON."""
    if not results['documents'] or not results['documents'][0]:
        return json.dumps({"results": []}, indent=2)
    
    formatted = []
    documents = results['documents'][0]
    metadatas = results.get('metadatas', [[]])[0] if results.get('metadatas') else []
    distances = results.get('distances', [[]])[0] if results.get('distances') else []
    
    for i, doc in enumerate(documents):
        try:
            chunk_data = json.loads(doc)
            distance = distances[i] if i < len(distances) else None
            similarity = 1 - distance if distance is not None else None
            metadata = metadatas[i] if i < len(metadatas) and metadatas else {}
            
            formatted.append({
                "rank": i + 1,
                "similarity": similarity,
                "distance": distance,
                "topic": chunk_data.get('topic'),
                "question": chunk_data.get('question'),
                "keywords": chunk_data.get('keywords', []),
                "content": chunk_data.get('content'),
                "table": chunk_data.get('table'),
                "image": chunk_data.get('image'),
                "metadata": metadata
            })
        except json.JSONDecodeError:
            formatted.append({
                "rank": i + 1,
                "raw_content": doc
            })
    
    return json.dumps({"results": formatted}, indent=2)


def format_results_table(results: Dict[str, Any]) -> None:
    """Format search results as a rich table."""
    if not results['documents'] or not results['documents'][0]:
        console.print("[yellow]No results found.[/yellow]")
        return
    
    table = Table(title="Search Results")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Similarity", style="green", width=10)
    table.add_column("Topic", style="bold", width=30)
    table.add_column("Content Preview", width=50)
    
    documents = results['documents'][0]
    distances = results.get('distances', [[]])[0] if results.get('distances') else []
    
    for i, doc in enumerate(documents):
        try:
            chunk_data = json.loads(doc)
            distance = distances[i] if i < len(distances) else None
            similarity = f"{1 - distance:.4f}" if distance is not None else "N/A"
            topic = chunk_data.get('topic', 'N/A')[:30]
            content = chunk_data.get('content', '')[:50] + "..." if len(chunk_data.get('content', '')) > 50 else chunk_data.get('content', '')
            
            table.add_row(str(i + 1), similarity, topic, content)
        except json.JSONDecodeError:
            table.add_row(str(i + 1), "N/A", "Parse Error", doc[:50])
    
    console.print(table)


def list_collections(chroma_host: str = "localhost", chroma_port: int = 8000) -> List[str]:
    """List available collections in ChromaDB."""
    try:
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        collections = client.list_collections()
        return [col.name for col in collections]
    except Exception as e:
        console.print(f"[red]✗ Error listing collections: {e}[/red]")
        return []


def get_collection_info(
    collection_name: str,
    chroma_host: str = "localhost", 
    chroma_port: int = 8000
) -> Dict[str, Any]:
    """Get information about a specific collection."""
    try:
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        collection = client.get_collection(name=collection_name)
        return {
            "name": collection.name,
            "count": collection.count(),
            "metadata": collection.metadata
        }
    except Exception as e:
        console.print(f"[red]✗ Error getting collection info: {e}[/red]")
        return {}


def main():
    parser = argparse.ArgumentParser(
        description="Semantic search using Gemini embeddings and ChromaDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "What is machine learning?"
  %(prog)s "How to bake a cake?" -n 10 --format json
  %(prog)s --list-collections
  %(prog)s --collection-info docs_gemini
  %(prog)s "search query" --dimension 1536 -c my_collection
        """
    )
    
    # Query argument
    parser.add_argument("query", type=str, nargs='?', help="Search query")
    
    # Collection options
    parser.add_argument(
        "-c", "--collection", 
        type=str, 
        default=DEFAULT_COLLECTION, 
        help=f"ChromaDB collection name (default: {DEFAULT_COLLECTION})"
    )
    
    # Result options
    parser.add_argument(
        "-n", "--n-results", 
        type=int, 
        default=5, 
        help="Number of results to return (default: 5)"
    )
    parser.add_argument(
        "-f", "--format", 
        type=str, 
        choices=["text", "json", "table"], 
        default="text", 
        help="Output format (default: text)"
    )
    
    # Embedding options
    parser.add_argument(
        "--dimension", 
        type=int, 
        choices=[768, 1536, 3072], 
        default=DEFAULT_DIMENSION,
        help=f"Embedding dimension - must match indexed data (default: {DEFAULT_DIMENSION})"
    )
    
    # ChromaDB connection
    parser.add_argument(
        "--chroma-host", 
        type=str, 
        default="localhost", 
        help="ChromaDB host (default: localhost)"
    )
    parser.add_argument(
        "--chroma-port", 
        type=int, 
        default=8000, 
        help="ChromaDB port (default: 8000)"
    )
    
    # Filtering options
    parser.add_argument(
        "--where", 
        type=str, 
        help="JSON filter for metadata (e.g., '{\"topic\": \"example\"}')"
    )
    parser.add_argument(
        "--min-similarity", 
        type=float, 
        help="Minimum similarity threshold (0-1)"
    )
    parser.add_argument(
        "--max-similarity", 
        type=float, 
        help="Maximum similarity threshold (0-1)"
    )
    
    # Info commands
    parser.add_argument(
        "--list-collections", 
        action="store_true", 
        help="List available collections"
    )
    parser.add_argument(
        "--collection-info", 
        type=str, 
        metavar="NAME",
        help="Show info about a specific collection"
    )
    
    args = parser.parse_args()
    
    try:
        # List collections
        if args.list_collections:
            collections = list_collections(args.chroma_host, args.chroma_port)
            if collections:
                console.print("[bold]Available collections:[/bold]")
                for col in collections:
                    info = get_collection_info(col, args.chroma_host, args.chroma_port)
                    count = info.get('count', '?')
                    console.print(f"  • {col} ({count} documents)")
            else:
                console.print("[yellow]No collections found[/yellow]")
            return
        
        # Collection info
        if args.collection_info:
            info = get_collection_info(args.collection_info, args.chroma_host, args.chroma_port)
            if info:
                console.print(f"[bold]Collection: {info['name']}[/bold]")
                console.print(f"  Documents: {info['count']}")
                if info.get('metadata'):
                    console.print(f"  Metadata: {json.dumps(info['metadata'], indent=2)}")
            return
        
        # Require query for search
        if not args.query:
            console.print("[red]✗ Error: Query is required for search[/red]")
            parser.print_help()
            sys.exit(1)
        
        # Generate query embedding
        query_embedding = generate_query_embedding(args.query, args.dimension)
        
        # Parse where filter if provided
        where_filter = None
        if args.where:
            try:
                where_filter = json.loads(args.where)
            except json.JSONDecodeError:
                console.print(f"[red]✗ Error: Invalid JSON in --where filter: {args.where}[/red]")
                sys.exit(1)
        
        # Search ChromaDB
        results = search_chromadb(
            query_embedding,
            args.collection,
            args.n_results,
            args.chroma_host,
            args.chroma_port,
            where_filter
        )
        
        # Filter by similarity if specified
        if args.min_similarity is not None or args.max_similarity is not None:
            if results['distances'] and results['distances'][0]:
                filtered_indices = []
                for i, distance in enumerate(results['distances'][0]):
                    similarity = 1 - distance
                    if args.min_similarity is not None and similarity < args.min_similarity:
                        continue
                    if args.max_similarity is not None and similarity > args.max_similarity:
                        continue
                    filtered_indices.append(i)
                
                # Filter all result arrays
                for key in ['documents', 'metadatas', 'distances', 'ids']:
                    if key in results and results[key] and results[key][0]:
                        results[key][0] = [results[key][0][i] for i in filtered_indices]
        
        # Format and output results
        if args.format == "json":
            print(format_results_json(results))
        elif args.format == "table":
            format_results_table(results)
        else:
            format_results_text(results)
        
        # Summary
        result_count = len(results['documents'][0]) if results['documents'] and results['documents'][0] else 0
        console.print(f"\n[bold]Search completed:[/bold] {result_count} results for '[italic]{args.query}[/italic]'")
        
    except Exception as error:
        console.print(f"[red]✗ Error during semantic search: {error}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
