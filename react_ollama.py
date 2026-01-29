import anthropic
from anthropic.types import TextBlock
import json
import argparse
import os
import requests
import html2text
import ollama
import chromadb
from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv('.env.local')

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
    if not query:
        return ""  # Return an empty string if the query is empty

    client = chromadb.HttpClient(host='localhost', port=8000)
    collection = client.get_collection("docs")
    # generate an embedding for the prompt and retrieve the most relevant doc
    response = ollama.embeddings(
        prompt=query,
        model="mxbai-embed-large"
    )

    if not response["embedding"]:
        return ""  # Return an empty string if the embedding is empty

    results = collection.query(
        query_embeddings=[response["embedding"]],
        n_results=1
    )
    print(results)
    if results['documents'] and results['documents'][0]:
        data = results['documents'][0][0]
        return data
    return ""  # Return an empty string if no documents are found

def query_rag(content_chunks, question, conversation_history=[]):
    client = anthropic.Anthropic(
        # defaults to os.environ.get("ANTHROPIC_API_KEY")
    )
    # Convert the list of content chunks to a JSON string
    content_chunks_json = json.dumps(content_chunks)
    system_prompt = """You're a helpful assistant. Please respond to the user's query using the following documents and the React pattern:
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE. If no action is required, respond with "No action required"
Observation will be the result of running those actions.

Your available documents are:
<documents>{}</documents>

Your available actions are:
1. search_web(query): Search the web for additional information if needed. Returns a summary of search results.
2. check_facts(text): Analyze the text given to evaluate is it fact or not. Returns positive, negative, or neutral.
3. check_weather(location): Check the weather in a given location. Returns the weather in the location.

Respond using the following format:
Thought: [Your thoughts about the question]
Action: [Action name if available]
Action Input: [Input for the action if available]
After each Action, wait for an Observation before continuing.
End your response with an Answer when you have sufficient information.
Remember to end the response with PAUSE if you entered an Action.

Question is: {}"""

    content_json = json.dumps({
        "type": "text",
        "text": system_prompt.format(content_chunks_json, question)
    })

    messages = [
        {
            "role": "system",
            "content": system_prompt.format(content_chunks_json, "")
        }
    ] + conversation_history + [
        {
            "role": "user",
            "content": question
        }
    ]

    while True:
        message = ollama.chat(
            model='gemma3:12b',
            messages=messages
        )

        response_content = message['message']['content']
        messages.append({"role": "assistant", "content": response_content})

        print("Assistant:", response_content)

        if "PAUSE" in response_content:
            user_input = input("Simulated response: ")
            messages.append({"role": "user", "content": user_input})
            print(messages)
        else:
            break

    return response_content

def interactive_shell(json_response):
    conversation_history = []
    while True:
        question = input("You: ")
        if question.lower() in ['exit', 'quit', 'bye']:
            break

        rag_response = query_rag(json_response, question, conversation_history)
        print("Assistant:", rag_response)

        conversation_history.append({"role": "user", "content": question})
        conversation_history.append({"role": "assistant", "content": rag_response})

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Search for a question in a webpage content")
    parser.add_argument("question", type=str, nargs='?', help="Question to ask about the webpage content")
    parser.add_argument("-o", "--output", type=str, help="Output file to save the markdown content")
    parser.add_argument("-i", "--interactive", action="store_true", help="Start an interactive shell")

    # Parse command-line arguments
    args = parser.parse_args()

    # Query semantic db
    json_response = query_chunks(args.question if args.question else "")

    if args.interactive:
        interactive_shell(json_response)
    elif args.question:
        rag_response = query_rag(json_response, args.question)

        if args.output:
            # If an output file is specified, write the markdown content to the file
            with open(args.output, 'w', encoding='utf-8') as file:
                file.write(rag_response)
                print(f"Markdown content has been saved to {args.output}")
        else:
            # Otherwise, print the markdown content to the standard output
            print(rag_response)
    else:
        print("Please provide a question or use the -i flag for interactive mode.")

if __name__ == "__main__":
    main()
