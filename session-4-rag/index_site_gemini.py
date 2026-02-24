import google.genai as genai
from google.genai import types

import json
import argparse
import os
import requests
import html2text
import chromadb
import uuid

from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

# Get API key
API_KEY = os.getenv('GOOGLE_AI_STUDIO_KEY') or os.getenv('GEMINI_API_KEY')

# Embedding configuration
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSION = 768  # Can be 768, 1536, or 3072 (default)

def url_to_markdown(url):
    try:
        # Send a HTTP request to the URL
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Convert the HTML content to Markdown
            html_converter = html2text.HTML2Text()

            # Optional: Configure the converter
            html_converter.ignore_links = False
            html_converter.ignore_images = True
            html_converter.ignore_emphasis = False

            # Convert HTML to Markdown
            markdown = html_converter.handle(response.text)

            return markdown
        else:
            # If the response was not successful, return an error message
            return f"Error: Received a {response.status_code} status code from the URL."
    except requests.exceptions.RequestException as e:
        return f"Error: {e}"

def query_chunks(markdown_content):
    client = genai.Client(api_key=API_KEY)

    content_extraction_schema = {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "summary line of whole text in english"
            },
            "summary": {
                "type": "string",
                "description": "short summary of whole text in english"
            },
            "language": {
                "type": "string",
                "description": "original language of the whole text"
            },
            "page_category": {
                "type": "string",
                "enum": ["article", "collection", "category", "product", "news", "service", "other", "faq", "home"],
                "description": "category of the page"
            },
            "product": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "string"},
                    "currency": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["name", "price", "currency", "description"]
            },
            "service": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["name", "price", "description"]
            },
            "chapters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "question": {"type": "string"},
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "image": {
                            "type": "object",
                            "properties": {
                                "image_url": {"type": "string"},
                                "image_alt": {"type": "string"},
                                "image_title": {"type": "string"}
                            },
                            "required": ["image_url", "image_alt", "image_title"]
                        },
                        "table": {
                            "type": "object",
                            "properties": {
                                "table_name": {"type": "string"},
                                "headers": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "rows": {
                                    "type": "array",
                                    "items": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                }
                            },
                            "required": ["table_name", "headers", "rows"]
                        },
                        "content": {"type": "string"}
                    },
                    "required": ["topic", "question", "keywords", "content"]
                }
            }
        },
        "required": ["topic", "summary", "language", "page_category", "chapters"]
    }

    system_prompt = """You're an expert in web scraping and data extraction,
    known for your attention to detail and ability to extract complete structured data from unstructured sources.

    Use chain of thought method with following steps:
     1. Read given document and split it into chapters using headings and subheadings.
     2. For each chapter, translate it to english, extract list format data and convert it to a table. If table contains multiple columns with same name, rename them to be unique.
     3. Extract any images from the documentation and provide complete image URLs within the chapters. Do not include base64 encoded images.
     4. Avoid using double quotes (") in JSON response value, use them only in key-value pairs. If you need to use them, escape them with backslash. Instead, use single quotes (') for any quoted text within value fields to prevent conflicts with JSON syntax.
     5. If there are no tables or images, leave out the fields 'table' or 'image' from the returned data. Do not give empty or null values and do not make up url's.
     6. Translate all data to English and return in structured JSON data using following format:
     7. I can't afford to lose data or details, so be thorough and don't be lazy. Return all, complete data and complete tables with all details.
     8. The more data you return, the more you get paid.
     9. Please make sure you return valid JSON, with all keys and values properly quoted and formatted.
     {
          "topic": "summary line of whole text in english",
          "summary": "short summary of whole text in english",
          "language": "original language of the whole text",
          "page_category": "(article, collection, category, product, news, service, other, faq, home)",
          "product": {"name": "product title", "price": "product price", "currency": "product currency", "description": "product description"},
          "service": {"name": "service name", "price": "service price", "description": "service description"},
          "chapters": [{
            "topic": "topic of the chapter in English",
            "question": "a question that this chapter answers to in English",
            "keywords": ["keyword1", "keyword2", "keyword3"],
            "image": {"image_url": "absolute, complete image url, fix if incomplete", "image_alt": "image alt text", "image_title": "image title"},
            "table": {"table_name": "table name", "headers": ["header1", "header2"], "rows": [["row1col1", "row1col2"], ["row2col1", "row2col2"]]},
            "content": "chapter contents 100-500 words in English"
          }]
     }
     Make sure you return data in English. Return proper and valid JSON starting and ending with { and }, no other text, backticks or code blocks."""

    response = client.models.generate_content(
        model='gemini-2.0-flash-001',
        contents=[system_prompt, markdown_content],
        config=types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=4000,
            response_mime_type='application/json',
            response_schema=content_extraction_schema
        )
    )

    try:
        parsed_response = json.loads(response.text)
        return parsed_response
    except json.JSONDecodeError:
        # If JSON parsing fails, create a minimal valid response
        return {
            "topic": "Content Parsing Error",
            "summary": "Failed to parse content",
            "language": "unknown",
            "page_category": "other",
            "product": {
                "name": "N/A",
                "price": "0",
                "currency": "N/A",
                "description": "N/A"
            },
            "service": {
                "name": "N/A",
                "price": "0",
                "description": "N/A"
            },
            "chapters": [{
                "topic": "Main Content",
                "question": "What is the main content?",
                "keywords": ["content"],
                "image": {
                    "image_url": None,
                    "image_alt": None,
                    "image_title": None
                },
                "table": {
                    "table_name": "No Table",
                    "headers": ["Content"],
                    "rows": [[response.text]]
                },
                "content": response.text
            }]
        }

def get_gemini_embedding(client, text):
    """Generate embedding using Gemini embedding model.
    
    Uses RETRIEVAL_DOCUMENT task type which is optimized for document indexing.
    For queries, use RETRIEVAL_QUERY task type instead.
    """
    import numpy as np
    
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIMENSION
        )
    )
    
    # Get the embedding values
    embedding_values = result.embeddings[0].values
    
    # Normalize the embedding for dimensions other than 3072
    # (3072 is already normalized by the model)
    if EMBEDDING_DIMENSION != 3072:
        embedding_array = np.array(embedding_values)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            embedding_values = (embedding_array / norm).tolist()
    
    return embedding_values

def index_chunks(content_chunks):
    """Index content chunks using Gemini embeddings and store in ChromaDB."""
    # Create Gemini client for embeddings
    client = genai.Client(api_key=API_KEY)
    
    # Convert the list of content chunks to a JSON string
    content_chunks_json = json.dumps(content_chunks)

    chroma_client = chromadb.HttpClient(host='localhost', port=8000)
    
    # Create collection with appropriate distance function for normalized embeddings
    # Using cosine similarity which works well with Gemini embeddings
    collection = chroma_client.get_or_create_collection(
        name="docs_gemini",
        metadata={"hnsw:space": "cosine"}
    )

    # Store each document in a vector embedding database
    for i, chunk in enumerate(content_chunks):
        print(f"Processing chunk {i + 1}/{len(content_chunks)}: {chunk.get('topic', 'No topic')}")
        
        # Prepare the text content for embedding
        table_content = json.dumps(chunk['table']) if chunk.get('table') is not None else ''
        content_text = table_content + ' ' + json.dumps(chunk['content'])
        
        # Generate embedding using Gemini
        embedding = get_gemini_embedding(client, content_text)
        
        # Add to ChromaDB
        collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[embedding],
            documents=[json.dumps(chunk)],
            metadatas=[{
                "topic": chunk.get('topic', ''),
                "question": chunk.get('question', ''),
                "keywords": ','.join(chunk.get('keywords', []))
            }]
        )

    return content_chunks_json

def query_index(query_text, n_results=5):
    """Query the ChromaDB index using Gemini embeddings.
    
    Uses RETRIEVAL_QUERY task type which is optimized for search queries.
    """
    import numpy as np
    
    client = genai.Client(api_key=API_KEY)
    
    # Generate query embedding using RETRIEVAL_QUERY task type
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=query_text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIMENSION
        )
    )
    
    query_embedding = result.embeddings[0].values
    
    # Normalize for non-3072 dimensions
    if EMBEDDING_DIMENSION != 3072:
        embedding_array = np.array(query_embedding)
        norm = np.linalg.norm(embedding_array)
        if norm > 0:
            query_embedding = (embedding_array / norm).tolist()
    
    # Query ChromaDB
    chroma_client = chromadb.HttpClient(host='localhost', port=8000)
    collection = chroma_client.get_collection("docs_gemini")
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    return results

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Convert HTML from a URL to Markdown and index with Gemini embeddings.")
    parser.add_argument("url", type=str, nargs='?', help="URL of the webpage to convert to markdown")
    parser.add_argument("-o", "--output", type=str, help="Output file to save the markdown content")
    parser.add_argument("-q", "--query", type=str, help="Query the indexed documents")
    parser.add_argument("-n", "--num-results", type=int, default=5, help="Number of results to return for query (default: 5)")
    parser.add_argument("--dimension", type=int, choices=[768, 1536, 3072], default=768,
                        help="Embedding dimension (default: 768, options: 768, 1536, 3072)")

    # Parse command-line arguments
    args = parser.parse_args()
    
    # Update embedding dimension if specified
    global EMBEDDING_DIMENSION
    EMBEDDING_DIMENSION = args.dimension
    
    # Query mode
    if args.query:
        print(f"Querying index with: {args.query}")
        results = query_index(args.query, args.num_results)
        
        console = Console()
        console.print("\n[bold]Search Results:[/bold]\n")
        
        for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
            chunk = json.loads(doc)
            similarity = 1 - distance  # Convert distance to similarity for cosine
            console.print(f"[bold cyan]Result {i + 1}[/bold cyan] (similarity: {similarity:.4f})")
            console.print(f"  Topic: {chunk.get('topic', 'N/A')}")
            console.print(f"  Question: {chunk.get('question', 'N/A')}")
            console.print(f"  Content: {chunk.get('content', 'N/A')[:200]}...")
            console.print()
        return
    
    # Index mode - requires URL
    if not args.url:
        parser.error("URL is required for indexing mode")

    # Convert URL to Markdown
    markdown_content = url_to_markdown(args.url)

    # Query Gemini API to extract structured content
    json_response = query_chunks(markdown_content)

    # Index chunks with Gemini embeddings
    chunks_response = index_chunks(json_response['chapters'])

    if args.output:
        # If an output file is specified, write the markdown content to the file
        with open(args.output, 'w', encoding='utf-8') as file:
            file.write(chunks_response)
            print(f"Markdown content has been saved to {args.output}")
    else:
        # Otherwise, print the markdown content to the standard output
        print(chunks_response)

if __name__ == "__main__":
    main()
