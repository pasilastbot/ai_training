#!/usr/bin/env python3

import argparse
import json
import requests
import html2text
import chromadb
import uuid
import os
import sys
import signal
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Timeout handler
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

def with_timeout(seconds):
    def decorator(func):
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wrapper
    return decorator

# Load environment variables from .env.local
load_dotenv(".env.local")

def url_to_markdown(url: str) -> str:
    """Convert URL content to markdown format."""
    try:
        print(f"🌐 Fetching content from: {url}")
        response = requests.get(url)
        
        if response.status_code == 200:
            html_converter = html2text.HTML2Text()
            html_converter.ignore_links = False
            html_converter.ignore_images = True
            html_converter.ignore_emphasis = False
            
            markdown = html_converter.handle(response.text)
            print(f"✅ Successfully converted {len(markdown)} characters to markdown")
            return markdown
        else:
            raise Exception(f"HTTP {response.status_code}: {response.reason}")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching URL: {e}")

def read_file_content(file_path: str) -> str:
    """Read content from local file."""
    try:
        print(f"📄 Reading file: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        print(f"✅ Successfully read {len(content)} characters from file")
        return content
    except Exception as e:
        raise Exception(f"Error reading file {file_path}: {e}")

def create_simple_chunks(content: str) -> Dict[str, Any]:
    """Create simple chunks when Gemini processing fails."""
    print("📦 Creating simple text chunks")
    
    # Split content into chunks of ~1000 characters
    chunk_size = 1000
    chunks = []
    
    for i in range(0, len(content), chunk_size):
        chunk_content = content[i:i + chunk_size]
        if chunk_content.strip():  # Only add non-empty chunks
            chunks.append({
                "topic": f"Content Chunk {len(chunks) + 1}",
                "question": f"What information is in chunk {len(chunks) + 1}?",
                "keywords": ["content", "text"],
                "content": chunk_content.strip()
            })
    
    return {
        "topic": "Document Content",
        "summary": "Document processed with simple chunking",
        "language": "unknown",
        "page_category": "other",
        "chapters": chunks
    }

@with_timeout(60)  # 60 second timeout
def chunk_content_with_gemini(content: str, model: str) -> Dict[str, Any]:
    """Process content with Gemini to create structured chunks."""
    api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise Exception("Google API key not found. Please set GOOGLE_AI_STUDIO_KEY or GEMINI_API_KEY environment variable")

    # Limit content size to prevent timeouts - be very conservative
    max_content_length = 10000  # ~10KB limit for stability
    if len(content) > max_content_length:
        print(f"⚠️  Content too large ({len(content)} chars), truncating to {max_content_length} chars")
        content = content[:max_content_length] + "\n\n[Content truncated due to size limit]"

    print(f"🤖 Processing {len(content)} characters with Gemini model: {model}")
    
    client = genai.Client(api_key=api_key)
    
    system_prompt = f"""You're an expert in web scraping and data extraction, known for your attention to detail and ability to extract complete structured data from unstructured sources.

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

{{
  "topic": "summary line of whole text in english",
  "summary": "short summary of whole text in english",
  "language": "original language of the whole text",
  "page_category": "(article, collection, category, product, news, service, other, faq, home)",
  "product": {{"name": "product title", "price": "product price", "currency": "product currency", "description": "product description"}},
  "service": {{"name": "service name", "price": "service price", "description": "service description"}},
  "chapters": [{{
    "topic": "topic of the chapter in English",
    "question": "a question that this chapter answers to in English",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "image": {{"image_url": "absolute, complete image url, fix if incomplete", "image_alt": "image alt text", "image_title": "image title"}},
    "table": {{"table_name": "table name", "headers": ["header1", "header2"], "rows": [["row1col1", "row1col2"], ["row2col1", "row2col2"]]}},
    "content": "chapter contents 100-500 words in English"
  }}]
}}

Make sure you return data in English. Return proper and valid JSON starting and ending with {{ and }}, no other text, backticks or code blocks.

Document to process:
{content}"""
    
    try:
        print("⏳ Sending request to Gemini...")
        response = client.models.generate_content(
            model=model,
            contents=system_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=4000,
                candidate_count=1
            )
        )
        print("✅ Received response from Gemini")
        
        response_text = response.text
        if response_text is None:
            raise Exception("Gemini returned empty response")
        
        print(f"📝 Received {len(response_text)} characters from Gemini")
        
        # Extract JSON from response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            parsed_response = json.loads(json_str)
            print(f"✅ Successfully parsed {len(parsed_response['chapters'])} chapters")
            return parsed_response
        else:
            raise Exception("No valid JSON found in Gemini response")
            
    except Exception as e:
        print(f"❌ Error processing content with Gemini: {e}")
        print("🔄 Using simple chunking fallback")
        # Return a simple chunking fallback
        return create_simple_chunks(content)

@with_timeout(30)  # 30 second timeout
def generate_embeddings(chunks: List[Dict[str, Any]], embedding_model: str) -> List[List[float]]:
    """Generate embeddings for chunks using Gemini."""
    api_key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise Exception("Google API key not found. Please set GOOGLE_AI_STUDIO_KEY or GEMINI_API_KEY environment variable")
    
    print(f"🧮 Generating embeddings with model: {embedding_model}")
    
    client = genai.Client(api_key=api_key)
    
    # Prepare content for embedding - combine relevant fields
    contents = []
    for chunk in chunks:
        embedding_text = f"{chunk['topic']}\n{chunk['question']}\n{chunk['content']}"
        if chunk.get('keywords'):
            embedding_text += f"\nKeywords: {', '.join(chunk['keywords'])}"
        if chunk.get('table'):
            embedding_text += f"\nTable: {chunk['table']['table_name']} - {json.dumps(chunk['table'])}"
        contents.append(embedding_text)
    
    try:
        result = client.models.embed_content(
            model=embedding_model,
            contents=contents
        )
        
        embeddings = [embedding.values for embedding in result.embeddings]
        print(f"✅ Generated {len(embeddings)} embeddings")
        return embeddings
        
    except Exception as e:
        print(f"❌ Error generating embeddings: {e}")
        raise e

def store_in_chromadb(
    chunks: List[Dict[str, Any]], 
    embeddings: List[List[float]], 
    collection_name: str,
    chroma_host: str = "localhost",
    chroma_port: int = 8000,
    source_url: Optional[str] = None
) -> None:
    """Store chunks and embeddings in ChromaDB."""
    print(f"💾 Storing {len(chunks)} chunks in ChromaDB collection: {collection_name}")
    
    try:
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        
        # Create or get collection
        try:
            collection = client.create_collection(
                name=collection_name,
                metadata={
                    "description": "Gemini-indexed document chunks",
                    "created_at": str(uuid.uuid4()),
                    "source_url": source_url or "local_file"
                }
            )
            print(f"✅ Created new collection: {collection_name}")
        except Exception:
            # Collection might already exist, get it instead
            collection = client.get_collection(name=collection_name)
            print(f"ℹ️  Using existing collection: {collection_name}")
        
        # Prepare data for insertion
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"chunk_{uuid.uuid4()}"
            
            ids.append(chunk_id)
            documents.append(json.dumps(chunk))
            metadatas.append({
                "topic": chunk['topic'],
                "question": chunk['question'],
                "keywords": ', '.join(chunk.get('keywords', [])),
                "source_url": source_url or "local_file",
                "chunk_index": i,
                "has_table": 'table' in chunk,
                "has_image": 'image' in chunk,
                "created_at": str(uuid.uuid4())
            })
        
        # Add documents to collection
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✅ Successfully stored {len(chunks)} chunks in ChromaDB")
        
    except Exception as e:
        print(f"❌ Error storing in ChromaDB: {e}")
        raise e

def main():
    parser = argparse.ArgumentParser(description="Index web content or files using Gemini for chunking and embeddings")
    parser.add_argument("-u", "--url", type=str, help="URL of webpage to index")
    parser.add_argument("-f", "--file", type=str, help="Path to local file to index")
    parser.add_argument("-o", "--output", type=str, help="Output file to save processed document JSON")
    parser.add_argument("-c", "--collection", type=str, default="gemini-docs", help="ChromaDB collection name")
    parser.add_argument("-m", "--model", type=str, default="gemini-2.5-flash", help="Gemini model for content processing")
    parser.add_argument("-e", "--embedding-model", type=str, default="gemini-embedding-001", help="Gemini model for embeddings")
    parser.add_argument("--chroma-host", type=str, default="localhost", help="ChromaDB host")
    parser.add_argument("--chroma-port", type=int, default=8000, help="ChromaDB port")
    
    args = parser.parse_args()
    
    try:
        # Get content from URL or file
        if args.url:
            content = url_to_markdown(args.url)
            source_url = args.url
        elif args.file:
            content = read_file_content(args.file)
            source_url = None
        else:
            print("❌ Error: Either --url or --file must be provided")
            parser.print_help()
            sys.exit(1)
        
        # Process content with Gemini to create structured chunks
        try:
            processed_doc = chunk_content_with_gemini(content, args.model)
        except TimeoutException:
            print("⏰ Gemini processing timed out, using fallback chunking")
            processed_doc = {
                "topic": "Content Processing Timeout",
                "summary": "Content was too large or complex to process",
                "language": "unknown",
                "page_category": "other",
                "chapters": [{
                    "topic": "Raw Content",
                    "question": "What is the content about?",
                    "keywords": ["content"],
                    "content": content[:1000] + "..." if len(content) > 1000 else content
                }]
            }
        
        # Generate embeddings for all chunks
        try:
            embeddings = generate_embeddings(processed_doc['chapters'], args.embedding_model)
        except TimeoutException:
            print("⏰ Embedding generation timed out")
            raise Exception("Embedding generation timed out - content may be too complex")
        
        # Store in ChromaDB
        store_in_chromadb(
            processed_doc['chapters'],
            embeddings,
            args.collection,
            args.chroma_host,
            args.chroma_port,
            source_url
        )
        
        # Save processed document if output specified
        if args.output:
            output_data = {
                **processed_doc,
                "indexed_at": str(uuid.uuid4()),
                "source_url": source_url,
                "embedding_model": args.embedding_model,
                "processing_model": args.model
            }
            
            with open(args.output, 'w', encoding='utf-8') as file:
                json.dump(output_data, file, indent=2)
            print(f"📁 Processed document saved to: {args.output}")
        
        print(f"🎉 Indexing completed successfully!")
        print(f"📊 Summary:")
        print(f"   - Document: {processed_doc['topic']}")
        print(f"   - Language: {processed_doc['language']}")
        print(f"   - Category: {processed_doc['page_category']}")
        print(f"   - Chapters: {len(processed_doc['chapters'])}")
        print(f"   - Collection: {args.collection}")
        print(f"   - Embeddings: {len(embeddings)}")
        
    except Exception as error:
        print(f"❌ Error during indexing: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
