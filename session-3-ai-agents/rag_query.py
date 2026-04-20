#!/usr/bin/env python3
"""
RAG Query

Query indexed content using retrieval-augmented generation.
Retrieves relevant chunks from ChromaDB and uses Gemini to generate grounded answers.

Usage:
    python rag_query.py "What services do they offer?"
    python rag_query.py "Tell me about pricing" -n 3
"""

import google.genai as genai
from google.genai import types

import json
import argparse
import os
import numpy as np
import chromadb

from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv

load_dotenv('.env.local')

API_KEY = os.getenv('GOOGLE_AI_STUDIO_KEY') or os.getenv('GEMINI_API_KEY')
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSION = 768

console = Console()


def get_query_embedding(query: str) -> list:
    """Generate embedding for a query using Gemini."""
    client = genai.Client(api_key=API_KEY)
    
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIMENSION
        )
    )
    
    values = result.embeddings[0].values
    
    if EMBEDDING_DIMENSION != 3072:
        arr = np.array(values)
        norm = np.linalg.norm(arr)
        if norm > 0:
            values = (arr / norm).tolist()
    
    return values


def retrieve_chunks(query: str, n_results: int = 5) -> list:
    """Retrieve relevant chunks from ChromaDB."""
    embedding = get_query_embedding(query)
    
    chroma = chromadb.HttpClient(host='localhost', port=8000)
    collection = chroma.get_collection("docs")
    
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results
    )
    
    chunks = []
    for doc, dist in zip(results['documents'][0], results['distances'][0]):
        chunk = json.loads(doc)
        chunk['_similarity'] = 1 - dist
        chunks.append(chunk)
    
    return chunks


def generate_answer(question: str, chunks: list) -> str:
    """Generate answer using Gemini with retrieved context."""
    client = genai.Client(api_key=API_KEY)
    
    context = "\n\n".join([
        f"[Source: {c.get('topic', 'Unknown')}]\n{c.get('content', '')}"
        for c in chunks
    ])
    
    prompt = f"""Answer the following question using ONLY the provided context.
If the context doesn't contain enough information, say so.
Cite which sources you used.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=1000
        )
    )
    
    return response.text


def main():
    parser = argparse.ArgumentParser(description="RAG Query with Gemini")
    parser.add_argument("question", type=str, help="Question to ask")
    parser.add_argument("-n", "--num-chunks", type=int, default=5, help="Chunks to retrieve")
    parser.add_argument("--show-sources", action="store_true", help="Show retrieved sources")

    args = parser.parse_args()
    
    console.print(f"\n[bold]Question:[/bold] {args.question}\n")
    
    # Retrieve
    console.print("[dim]Retrieving relevant content...[/dim]")
    chunks = retrieve_chunks(args.question, args.num_chunks)
    
    if args.show_sources:
        console.print("\n[bold]Sources:[/bold]")
        for i, c in enumerate(chunks):
            console.print(f"  {i+1}. {c.get('topic', 'N/A')} (sim: {c['_similarity']:.3f})")
        console.print()
    
    # Generate
    console.print("[dim]Generating answer...[/dim]\n")
    answer = generate_answer(args.question, chunks)
    
    console.print("[bold]Answer:[/bold]")
    console.print(Markdown(answer))


if __name__ == "__main__":
    main()
