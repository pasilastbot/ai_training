#!/usr/bin/env python3
"""
Knowledge Search Subagent

Searches for energy-related information using multiple sources:
1. Leanheat Building RAG knowledge base (primary)
2. Google Search via Gemini grounding (fallback)

Returns comprehensive answers with sources.

Usage:
    python knowledge_search.py "How does demand response work?"
    python knowledge_search.py --query "energy savings" --fallback-to-google
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent_env import load_agent_environment
load_agent_environment()

from google import genai
from google.genai import types

AGENT_DIR = Path(__file__).parent.parent
PROJECT_ROOT = AGENT_DIR.parent.parent.parent


def get_client() -> genai.Client:
    """Get Gemini client."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_STUDIO_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY required")
    return genai.Client(api_key=api_key)


def search_leanheat_knowledge(query: str, n_results: int = 5) -> dict:
    """Search the Leanheat knowledge base."""
    cmd = [
        "npm", "run", "leanheat-memory", "--",
        "recall", query,
        "-n", str(n_results),
        "-f", "json"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=60
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            start = output.find('{')
            if start >= 0:
                try:
                    return json.loads(output[start:])
                except json.JSONDecodeError:
                    pass
            return {"results": [], "raw": output}
        else:
            return {"results": [], "error": result.stderr.strip()}
    
    except Exception as e:
        return {"results": [], "error": str(e)}


def search_google(query: str) -> dict:
    """Search Google using Gemini's search grounding."""
    cmd = [
        "npm", "run", "google-search", "--",
        query,
        "-s",
        "-f", "json"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=60
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            start = output.find('{')
            if start >= 0:
                try:
                    return json.loads(output[start:])
                except json.JSONDecodeError:
                    pass
            return {"answer": output, "sources": []}
        else:
            return {"error": result.stderr.strip()}
    
    except Exception as e:
        return {"error": str(e)}


def synthesize_answer(query: str, knowledge_results: dict, google_results: dict = None) -> dict:
    """Synthesize a comprehensive answer from multiple sources using Gemini."""
    client = get_client()
    
    context_parts = []
    
    if knowledge_results.get("results"):
        context_parts.append("## Leanheat Knowledge Base Results:")
        for i, result in enumerate(knowledge_results["results"], 1):
            topic = result.get("topic", "Unknown")
            fact = result.get("fact", "")
            relevance = result.get("relevance", 0)
            context_parts.append(f"""
{i}. **{topic}** (relevance: {relevance:.2%})
{fact}
""")
    
    if google_results and not google_results.get("error"):
        context_parts.append("\n## Google Search Results:")
        if google_results.get("answer"):
            context_parts.append(google_results["answer"])
        if google_results.get("sources"):
            context_parts.append("\nSources:")
            for source in google_results["sources"][:5]:
                context_parts.append(f"- {source.get('title', '')}: {source.get('url', '')}")
    
    if not context_parts:
        return {
            "query": query,
            "answer": "I couldn't find relevant information about this topic.",
            "sources": [],
            "confidence": "low"
        }
    
    prompt = f"""Based on the following information sources, provide a comprehensive answer to this question about energy optimization and Leanheat Building technology:

**Question:** {query}

{chr(10).join(context_parts)}

Instructions:
1. Synthesize information from all sources into a clear, helpful answer
2. Focus on practical information relevant to building energy optimization
3. If discussing Leanheat Building, mention specific features and benefits
4. Include relevant statistics and percentages when available
5. Keep the answer concise but informative (2-4 paragraphs)
6. If sources conflict or information is uncertain, acknowledge it

Provide your answer in JSON format:
{{
    "answer": "Your comprehensive answer here",
    "key_points": ["point1", "point2", "point3"],
    "sources_used": ["Leanheat KB", "Google Search"],
    "confidence": "high|medium|low",
    "follow_up_questions": ["question1", "question2"]
}}"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        result["query"] = query
        return result
    
    except Exception as e:
        return {
            "query": query,
            "answer": f"Error synthesizing answer: {str(e)}",
            "sources_used": [],
            "confidence": "low"
        }


def search_knowledge(
    query: str,
    use_google_fallback: bool = True,
    synthesize: bool = True
) -> dict:
    """
    Search for knowledge using Leanheat KB and optionally Google.
    
    Args:
        query: Search query
        use_google_fallback: Whether to use Google Search if KB results are insufficient
        synthesize: Whether to synthesize results using Gemini
    
    Returns:
        dict with answer, sources, and confidence
    """
    print(f"[KnowledgeSearch] Searching Leanheat KB: {query}", file=sys.stderr)
    
    kb_results = search_leanheat_knowledge(query)
    
    has_good_kb_results = (
        kb_results.get("results") and 
        len(kb_results["results"]) >= 2 and
        any(r.get("relevance", 0) > 0.7 for r in kb_results.get("results", []))
    )
    
    google_results = None
    if use_google_fallback and not has_good_kb_results:
        print(f"[KnowledgeSearch] KB results insufficient, searching Google...", file=sys.stderr)
        google_results = search_google(f"Leanheat Building energy optimization {query}")
    
    if synthesize:
        return synthesize_answer(query, kb_results, google_results)
    else:
        return {
            "query": query,
            "leanheat_results": kb_results,
            "google_results": google_results
        }


def main():
    parser = argparse.ArgumentParser(description="Knowledge Search Subagent")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--no-fallback", action="store_true", help="Don't use Google fallback")
    parser.add_argument("--raw", action="store_true", help="Return raw results without synthesis")
    
    args = parser.parse_args()
    
    if not args.query:
        parser.print_help()
        return
    
    result = search_knowledge(
        args.query,
        use_google_fallback=not args.no_fallback,
        synthesize=not args.raw
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
