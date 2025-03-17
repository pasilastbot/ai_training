import google.genai as genai
from google.genai import types

import json
import argparse
import requests
import html2text
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
    client = genai.Client()

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
        print(parsed_response)
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

def query_rag(content_chunks, question):
    client = genai.Client()
    
    # Convert the list of content chunks to a JSON string
    content_chunks_json = json.dumps(content_chunks)
    system_prompt = "You're a helpful assistant. Please respond to the user's query in user's own language using the following documents: \n\n" \
               "<documents>" + content_chunks_json + "</documents>" \
               "Answer the question in humoristic way." \
               "If the documents don't contain the answer, return a web search query with prefix: [Google]\n"

    response = client.models.generate_content(
        model='gemini-2.0-flash-001',
        contents=[system_prompt, question],
        config=types.GenerateContentConfig(
            temperature=0,
            max_output_tokens=4000
        )
    )
    console = Console()
    console.print(response.text, style="red")
    # Check if response contains [Google] indicating web search needed
    if "[Google]" in response.text:
        # Extract the search query after [Google] prefix
        search_query = response.text.split("[Google]")[1].strip()
        
        # Run query with Google Search tool enabled
        search_response = client.models.generate_content(
            model='gemini-2.0-flash-001',
            contents=search_query,
            config=types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=4000,
                tools=[
                    types.Tool(google_search=types.GoogleSearch())
                ]
            )
        )
        response = search_response

    return response.text

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Convert HTML from a URL to Markdown.")
    parser.add_argument("url", type=str, help="URL of the webpage to convert to markdown")
    parser.add_argument("question", type=str, help="Question to ask about the webpage content")
    parser.add_argument("-o", "--output", type=str, help="Output file to save the markdown content")

    # Parse command-line arguments
    args = parser.parse_args()

    # Convert URL to Markdown
    markdown_content = url_to_markdown(args.url)

    # Query Gemini API
    json_response = query_chunks(markdown_content)
    
    # Ensure we have chapters to process
    if not json_response.get('chapters'):
        json_response['chapters'] = [{"topic": "Main Content", "content": markdown_content}]

    rag_response = query_rag(json_response['chapters'], args.question)

    if args.output:
        # If an output file is specified, write the markdown content to the file
        with open(args.output, 'w', encoding='utf-8') as file:
            file.write(rag_response)
            print(f"Markdown content has been saved to {args.output}")
    else:
        # Otherwise, print the markdown content to the standard output
        print(rag_response)

if __name__ == "__main__":
    main()
