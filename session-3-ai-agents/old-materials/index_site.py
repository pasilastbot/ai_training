#!/usr/bin/env python3
"""
Index Website Content

Scrapes a webpage, extracts structured content using Gemini, 
generates embeddings, and stores in ChromaDB for RAG.

Usage:
    python index_site.py "https://example.com"
    python index_site.py "https://example.com" -o output.json
    python index_site.py -q "What is this about?" -n 5
"""

import google.genai as genai
from google.genai import types

import json
import argparse
import os
import requests
import html2text
import chromadb
import uuid
import numpy as np

from rich.console import Console
from dotenv import load_dotenv

load_dotenv('.env.local')

API_KEY = os.getenv('GOOGLE_AI_STUDIO_KEY') or os.getenv('GEMINI_API_KEY')
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSION = 768

console = Console()


def url_to_markdown(url: str) -> str:
    """Fetch URL and convert HTML to Markdown."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = True
        converter.ignore_emphasis = False
        
        return converter.handle(response.text)
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"


def extract_chunks(markdown_content: str) -> dict:
    """Use Gemini to extract structured chunks from markdown."""
    client = genai.Client(api_key=API_KEY)

    schema = {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "summary": {"type": "string"},
            "chapters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "question": {"type": "string"},
                        "keywords": {"type": "array", "items": {"type": "string"}},
                        "content": {"type": "string"}
                    },
                    "required": ["topic", "question", "keywords", "content"]
                }
            }
        },
        "required": ["topic", "summary", "chapters"]
    }

    system_prompt = """Extract structured content from this document.
    
    For each logical section, create a chapter with:
    - topic: section heading or theme
    - question: what question does this section answer?
    - keywords: 3-5 relevant keywords
    - content: the section content (100-500 words)
    
    Return valid JSON only."""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[system_prompt, markdown_content],
        config=types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=4000,
            response_mime_type='application/json',
            response_schema=schema
        )
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {
            "topic": "Parse Error",
            "summary": "Failed to parse content",
            "chapters": [{
                "topic": "Raw Content",
                "question": "What is the content?",
                "keywords": ["content"],
                "content": markdown_content[:2000]
            }]
        }


def get_embedding(client, text: str) -> list:
    """Generate embedding using Gemini."""
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIMENSION
        )
    )
    
    values = result.embeddings[0].values
    
    # Normalize for non-3072 dimensions
    if EMBEDDING_DIMENSION != 3072:
        arr = np.array(values)
        norm = np.linalg.norm(arr)
        if norm > 0:
            values = (arr / norm).tolist()
    
    return values


def index_chunks(chapters: list) -> str:
    """Index chapters into ChromaDB with Gemini embeddings."""
    client = genai.Client(api_key=API_KEY)
    chroma = chromadb.HttpClient(host='localhost', port=8000)
    
    collection = chroma.get_or_create_collection(
        name="docs",
        metadata={"hnsw:space": "cosine"}
    )

    for i, chapter in enumerate(chapters):
        console.print(f"[dim]Indexing {i + 1}/{len(chapters)}: {chapter.get('topic', 'N/A')}[/dim]")
        
        content = json.dumps(chapter.get('content', ''))
        embedding = get_embedding(client, content)
        
        collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[embedding],
            documents=[json.dumps(chapter)],
            metadatas=[{
                "topic": chapter.get('topic', ''),
                "question": chapter.get('question', ''),
                "keywords": ','.join(chapter.get('keywords', []))
            }]
        )

    return json.dumps(chapters, indent=2)


def query_index(query: str, n_results: int = 5) -> dict:
    """Query ChromaDB using Gemini embeddings."""
    client = genai.Client(api_key=API_KEY)
    
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIMENSION
        )
    )
    
    query_embedding = result.embeddings[0].values
    
    if EMBEDDING_DIMENSION != 3072:
        arr = np.array(query_embedding)
        norm = np.linalg.norm(arr)
        if norm > 0:
            query_embedding = (arr / norm).tolist()
    
    chroma = chromadb.HttpClient(host='localhost', port=8000)
    collection = chroma.get_collection("docs")
    
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )


def main():
    parser = argparse.ArgumentParser(description="Index website content for RAG")
    parser.add_argument("url", type=str, nargs='?', help="URL to index")
    parser.add_argument("-o", "--output", type=str, help="Save output to file")
    parser.add_argument("-q", "--query", type=str, help="Query the index")
    parser.add_argument("-n", "--num-results", type=int, default=5, help="Results to return")

    args = parser.parse_args()
    
    # Query mode
    if args.query:
        console.print(f"\n[bold]Searching:[/bold] {args.query}\n")
        results = query_index(args.query, args.num_results)
        
        for i, (doc, dist) in enumerate(zip(results['documents'][0], results['distances'][0])):
            chunk = json.loads(doc)
            similarity = 1 - dist
            console.print(f"[cyan]#{i + 1}[/cyan] (sim: {similarity:.3f}) {chunk.get('topic', 'N/A')}")
            console.print(f"   {chunk.get('content', 'N/A')[:150]}...\n")
        return
    
    # Index mode
    if not args.url:
        parser.error("URL required for indexing")

    console.print(f"[bold]Indexing:[/bold] {args.url}")
    
    markdown = url_to_markdown(args.url)
    chunks = extract_chunks(markdown)
    output = index_chunks(chunks.get('chapters', []))
    
    console.print(f"[green]✓ Indexed {len(chunks.get('chapters', []))} chunks[/green]")
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        console.print(f"[dim]Saved to {args.output}[/dim]")


if __name__ == "__main__":
    main()
