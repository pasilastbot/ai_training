import anthropic
from anthropic.types import TextBlock

import json
import argparse
import requests
import html2text
import ollama
import chromadb

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

def query_chunks(query):
    client = chromadb.HttpClient(host='localhost', port=8000)
    collection = client.get_collection("docs")
   # generate an embedding for the prompt and retrieve the most relevant doc
    response = ollama.embeddings(
        prompt=query,
        model="mxbai-embed-large"
    )
    results = collection.query(
        query_embeddings=[response["embedding"]],
        n_results=1
    )
    print(results)
    data = results['documents'][0][0]
    return data

def query_rag(content_chunks, question):
    client = anthropic.Anthropic(
        # defaults to os.environ.get("ANTHROPIC_API_KEY")
    )
    # Convert the list of content chunks to a JSON string
    content_chunks_json = json.dumps(content_chunks)
    system_prompt = "You're a helpful assistant. Please respond to the user's query in user's own language using the following documents: \n\n" \
               "<documents>" + content_chunks_json + "</documents>" \
               "Respond using the following chain of thought steps:\n" \
               "1. If the documents don't contain the answer, return a web search query with in json with key 'search' \n" \
               "2. Otherwise, respond with professional tone of voice \n" \
               "3. Respond with json format with no other text\n"

    print(system_prompt)
# Serialize the content to a JSON string
    content_json = json.dumps({
        "type": "text",
        "text": system_prompt + "\nQuestion is: " + question
    })

    message = ollama.chat(
        model='llama3.1',
        messages=[
            {
                "role": "user",
                "content": content_json
            }
        ]
    )

    final_response = message['message']['content']
    # final_response = next(
    #     (block.text for block in message.content if isinstance(block, TextBlock)),
    #     None,
    # )
    return final_response

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Search for a question in a webpage content")
    parser.add_argument("question", type=str, help="Question to ask about the webpage content")
    parser.add_argument("-o", "--output", type=str, help="Output file to save the markdown content")

    # Parse command-line arguments
    args = parser.parse_args()

    # Query semantic db
    json_response = query_chunks(args.question)

    rag_response = query_rag(json_response, args.question)

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
