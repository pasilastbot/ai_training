#!/usr/bin/env python3

import argparse
import json
import chromadb
import os
import sys
from typing import List, Dict, Any, Optional
from google import genai
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv(".env.local")

def generate_query_embedding(query: str, embedding_model: str) -> List[float]:
    """Generate embedding for the search query using Gemini."""
    api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise Exception("Google API key not found. Please set GOOGLE_AI_STUDIO_KEY or GEMINI_API_KEY environment variable")
    
    print(f"🧮 Generating query embedding with model: {embedding_model}")
    
    client = genai.Client(api_key=api_key)
    
    try:
        result = client.models.embed_content(
            model=embedding_model,
            contents=[query]
        )
        
        embedding = result.embeddings[0].values
        print(f"✅ Generated query embedding with {len(embedding)} dimensions")
        return embedding
        
    except Exception as e:
        print(f"❌ Error generating query embedding: {e}")
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
    print(f"🔍 Searching ChromaDB collection: {collection_name}")
    
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
        
        print(f"✅ Found {len(results['documents'][0])} results")
        return results
        
    except Exception as e:
        print(f"❌ Error searching ChromaDB: {e}")
        raise e

def format_search_results(results: Dict[str, Any], format_type: str = "text") -> str:
    """Format search results for output."""
    if not results['documents'] or not results['documents'][0]:
        return "No results found."
    
    if format_type == "json":
        return json.dumps(results, indent=2)
    
    # Text format
    output = []
    documents = results['documents'][0]
    metadatas = results['metadatas'][0] if results['metadatas'] else []
    distances = results['distances'][0] if results['distances'] else []
    
    for i, doc in enumerate(documents):
        try:
            chunk_data = json.loads(doc)
            metadata = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else "N/A"
            
            output.append(f"🎯 **Result {i+1}** (Distance: {distance:.4f})" if isinstance(distance, float) else f"🎯 **Result {i+1}**")
            output.append(f"📋 **Topic**: {chunk_data.get('topic', 'N/A')}")
            output.append(f"❓ **Question**: {chunk_data.get('question', 'N/A')}")
            
            if chunk_data.get('keywords'):
                output.append(f"🏷️  **Keywords**: {', '.join(chunk_data['keywords'])}")
            
            content = chunk_data.get('content', '')
            if len(content) > 300:
                content = content[:300] + "..."
            output.append(f"📄 **Content**: {content}")
            
            if metadata.get('source_url'):
                output.append(f"🔗 **Source**: {metadata['source_url']}")
            
            if chunk_data.get('table'):
                table = chunk_data['table']
                output.append(f"📊 **Table**: {table.get('table_name', 'Unnamed Table')}")
            
            if chunk_data.get('image'):
                image = chunk_data['image']
                output.append(f"🖼️  **Image**: {image.get('image_title', 'Untitled Image')}")
            
            output.append("")  # Empty line between results
            
        except json.JSONDecodeError:
            output.append(f"🎯 **Result {i+1}**")
            output.append(f"📄 **Raw Content**: {doc[:300]}...")
            output.append("")
    
    return "\n".join(output)

def list_collections(chroma_host: str = "localhost", chroma_port: int = 8000) -> List[str]:
    """List available collections in ChromaDB."""
    try:
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        collections = client.list_collections()
        return [col.name for col in collections]
    except Exception as e:
        print(f"❌ Error listing collections: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Semantic search using Gemini embeddings and ChromaDB")
    parser.add_argument("query", type=str, nargs='?', help="Search query")
    parser.add_argument("-c", "--collection", type=str, default="gemini-docs", help="ChromaDB collection name")
    parser.add_argument("-n", "--n-results", type=int, default=5, help="Number of results to return")
    parser.add_argument("-e", "--embedding-model", type=str, default="gemini-embedding-001", help="Gemini model for embeddings")
    parser.add_argument("-f", "--format", type=str, choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--chroma-host", type=str, default="localhost", help="ChromaDB host")
    parser.add_argument("--chroma-port", type=int, default=8000, help="ChromaDB port")
    parser.add_argument("--list-collections", action="store_true", help="List available collections")
    parser.add_argument("--where", type=str, help="JSON filter for metadata (e.g., '{\"source_url\": \"https://example.com\"}')")
    parser.add_argument("--min-distance", type=float, help="Minimum distance threshold for results")
    parser.add_argument("--max-distance", type=float, help="Maximum distance threshold for results")
    
    args = parser.parse_args()
    
    try:
        # List collections if requested
        if args.list_collections:
            collections = list_collections(args.chroma_host, args.chroma_port)
            if collections:
                print("📚 Available collections:")
                for col in collections:
                    print(f"   - {col}")
            else:
                print("📚 No collections found or error accessing ChromaDB")
            return
        
        # Require query for search
        if not args.query:
            print("❌ Error: Query is required for search")
            parser.print_help()
            sys.exit(1)
        
        # Generate query embedding
        query_embedding = generate_query_embedding(args.query, args.embedding_model)
        
        # Parse where filter if provided
        where_filter = None
        if args.where:
            try:
                where_filter = json.loads(args.where)
            except json.JSONDecodeError:
                print(f"❌ Error: Invalid JSON in --where filter: {args.where}")
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
        
        # Filter by distance if specified
        if args.min_distance is not None or args.max_distance is not None:
            if results['distances'] and results['distances'][0]:
                filtered_indices = []
                for i, distance in enumerate(results['distances'][0]):
                    if args.min_distance is not None and distance < args.min_distance:
                        continue
                    if args.max_distance is not None and distance > args.max_distance:
                        continue
                    filtered_indices.append(i)
                
                # Filter all result arrays
                for key in ['documents', 'metadatas', 'distances', 'ids']:
                    if results[key] and results[key][0]:
                        results[key][0] = [results[key][0][i] for i in filtered_indices]
        
        # Format and output results
        formatted_results = format_search_results(results, args.format)
        print(formatted_results)
        
        # Summary
        result_count = len(results['documents'][0]) if results['documents'] and results['documents'][0] else 0
        print(f"\n🎯 Search completed: Found {result_count} results for query: '{args.query}'")
        
    except Exception as error:
        print(f"❌ Error during semantic search: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
