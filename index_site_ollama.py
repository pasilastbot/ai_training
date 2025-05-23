import json
import argparse
import requests
import html2text
import ollama
import chromadb
import uuid

from rich.console import Console
from rich.markdown import Markdown

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

    # Serialize the content to a JSON string
    content_json = json.dumps({
        "type": "text",
        "text": system_prompt + "\n\nDocument to process:\n" + markdown_content
    })

    message = ollama.chat(
        model='gemma3:12b',
        messages=[
            {
                "role": "user",
                "content": content_json
            }
        ]
    )

    response_text = message['message']['content']

    try:
        # Try to extract JSON from the response
        # First, find the first { and the last }
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            parsed_response = json.loads(json_str)
            return parsed_response
        else:
            raise json.JSONDecodeError("No JSON found", response_text, 0)
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
                "content": response_text
            }]
        }

def index_chunks(content_chunks):
    # Convert the list of content chunks to a JSON string
    content_chunks_json = json.dumps(content_chunks)

    client = chromadb.HttpClient(host='localhost', port=8000)
    collection = client.get_or_create_collection("docs")

    # store each document in a vector embedding database
    for i, chunk in enumerate(content_chunks):
        print(chunk)
        table_content = json.dumps(chunk['table']) if chunk.get('table') is not None else ''
        response = ollama.embeddings(model="mxbai-embed-large", prompt=table_content + json.dumps(chunk['content']))
        embedding = response["embedding"]
        collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[embedding],
            documents=[json.dumps(chunk)]
        )

    return content_chunks_json

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Convert HTML from a URL to Markdown.")
    parser.add_argument("url", type=str, help="URL of the webpage to convert to markdown")
    parser.add_argument("-o", "--output", type=str, help="Output file to save the markdown content")

    # Parse command-line arguments
    args = parser.parse_args()

    # Convert URL to Markdown
    markdown_content = url_to_markdown(args.url)

    # Query using Ollama
    json_response = query_chunks(markdown_content)

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
