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
import google.genai as genai
from google.genai import types
import os
import sys

# NOTE: To use the Google search functionality, you need to:
# 1. Set up Google Gemini API access (https://ai.google.dev/)
# 2. Set the GOOGLE_API_KEY environment variable with your API key:
#    export GOOGLE_API_KEY=your_api_key_here
#
# If the API key is not set, the search will fall back to simulated results.

# Initialize console for rich output
console = Console()

# Check if Google API key is available
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_SEARCH_AVAILABLE = False
gemini_client = None

# Try to initialize Google API client
try:
    if GOOGLE_API_KEY:
        # Create a client instance with the API key instead of using configure
        gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
        GOOGLE_SEARCH_AVAILABLE = True
        console.print("[green]Google Gemini API initialized successfully[/green]")
    else:
        console.print("[yellow]Google API key not found. Search will use fallback mode.[/yellow]")
except Exception as e:
    console.print(f"[red]Error initializing Google Gemini API: {e}[/red]")

def debug_log(message, level="info"):
    """Log debug messages with color coding based on level"""
    colors = {
        "info": "blue",
        "warning": "yellow",
        "error": "red",
        "success": "green"
    }
    color = colors.get(level, "white")
    console.print(f"[{color}]{message}[/{color}]")

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

# Real action functions
def search_web(query):
    """
    Search the web using Google via Gemini API.
    
    This function attempts to get real search results using the Google Gemini API.
    If the API key is not available or there's an error, it falls back to simulated results.
    
    Args:
        query (str): The search query
        
    Returns:
        str: Formatted search results
    """
    try:
        # Use Google Gemini for web search if API key is available
        if GOOGLE_SEARCH_AVAILABLE and gemini_client:
            try:
                debug_log(f"Searching Google for: {query}", "info")
                
                # Clean up the query
                query = query.strip()
                
                # Add specific terms if needed to improve search quality
                if not any(term in query.lower() for term in ["recent", "latest", "news", "current"]) and \
                   not query.endswith("?"):
                    # For non-news queries without a question mark, focus on facts
                    enhanced_query = f"{query} facts information"
                else:
                    enhanced_query = query
                
                debug_log(f"Enhanced query: {enhanced_query}", "info")
                
                # Execute the search
                search_response = gemini_client.models.generate_content(
                    model='gemini-2.0-flash-001',
                    contents=enhanced_query,
                    config=types.GenerateContentConfig(
                        temperature=0,
                        max_output_tokens=4000,
                        tools=[
                            types.Tool(google_search=types.GoogleSearch())
                        ]
                    )
                )
                
                # Process the search response
                response_text = search_response.text
                
                # Format the search results in a readable way
                search_results = "Google Search Results:\n\n"
                
                # Check if the response contains search results in a specific format
                try:
                    parts = search_response.candidates[0].content.parts
                    if hasattr(parts[0], 'function_call') and hasattr(parts[0].function_call, 'args'):
                        # Extract structured search results
                        args = parts[0].function_call.args
                        if "search_results" in args:
                            for i, result in enumerate(args["search_results"]):
                                search_results += f"{i+1}. {result.get('title', 'No title')}\n"
                                search_results += f"   URL: {result.get('link', 'No link')}\n"
                                search_results += f"   {result.get('snippet', 'No snippet')}\n\n"
                            
                            # Add a summary if available
                            if len(parts) > 1 and hasattr(parts[1], 'text'):
                                search_results += "\nSummary:\n" + parts[1].text
                        else:
                            search_results += response_text
                    else:
                        search_results += response_text
                except (AttributeError, KeyError, TypeError, IndexError) as e:
                    # If extraction fails, return the raw text
                    debug_log(f"Failed to parse structured search results: {e}", "warning")
                    search_results += response_text
                    
                debug_log("Search completed successfully", "success")
                return search_results
            except Exception as gemini_error:
                debug_log(f"Gemini API error: {gemini_error}", "error")
                debug_log("Falling back to simulated search results", "warning")
        else:
            if not GOOGLE_API_KEY:
                debug_log("Google API key not found. Set GOOGLE_API_KEY environment variable.", "warning")
            elif not gemini_client:
                debug_log("Google client initialization failed.", "warning")
            else:
                debug_log("Google search is disabled for unknown reason.", "warning")
            
        # Fallback to simulated search if API key is not set or other error
        return f"Simulated web search results for: {query}\n\n1. Sample result 1\n   URL: https://example.com/result1\n   This is a simulated search result about {query}.\n\n2. Sample result 2\n   URL: https://example.com/result2\n   This is another simulated search result related to {query}."
    except Exception as e:
        debug_log(f"Error searching the web: {e}", "error")
        return f"Error searching the web: {str(e)}"


def check_weather(location):
    try:
        # Try to geocode the location to get coordinates
        # In a real-world scenario, you should use a proper geocoding API
        # For now, we'll use a simple dictionary for common locations
        geocode_map = {
            "new york": {"lat": 40.71, "lon": -74.01},
            "london": {"lat": 51.51, "lon": -0.13},
            "paris": {"lat": 48.85, "lon": 2.35},
            "tokyo": {"lat": 35.68, "lon": 139.76},
            "berlin": {"lat": 52.52, "lon": 13.41},
            "sydney": {"lat": -33.87, "lon": 151.21},
            "san francisco": {"lat": 37.77, "lon": -122.42},
            "los angeles": {"lat": 34.05, "lon": -118.24},
            "chicago": {"lat": 41.88, "lon": -87.63},
            "seattle": {"lat": 47.61, "lon": -122.33},
        }
        
        # Convert location to lowercase for case-insensitive matching
        location_lower = location.lower()
        
        # Get coordinates for the location
        if location_lower in geocode_map:
            coords = geocode_map[location_lower]
        else:
            # Default to Berlin if location not found
            coords = {"lat": 52.52, "lon": 13.41}
            
        # Make request to Open-Meteo API
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=temperature_2m,wind_speed_10m,precipitation,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract current weather information
            current = data.get('current', {})
            temperature = current.get('temperature_2m', 'N/A')
            wind_speed = current.get('wind_speed_10m', 'N/A')
            precipitation = current.get('precipitation', 'N/A')
            
            # Weather code interpretation
            weather_codes = {
                0: "Clear sky",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Overcast",
                45: "Fog",
                48: "Depositing rime fog",
                51: "Light drizzle",
                53: "Moderate drizzle",
                55: "Dense drizzle",
                56: "Light freezing drizzle",
                57: "Dense freezing drizzle",
                61: "Slight rain",
                63: "Moderate rain",
                65: "Heavy rain",
                66: "Light freezing rain",
                67: "Heavy freezing rain",
                71: "Slight snow fall",
                73: "Moderate snow fall",
                75: "Heavy snow fall",
                77: "Snow grains",
                80: "Slight rain showers",
                81: "Moderate rain showers",
                82: "Violent rain showers",
                85: "Slight snow showers",
                86: "Heavy snow showers",
                95: "Thunderstorm",
                96: "Thunderstorm with slight hail",
                99: "Thunderstorm with heavy hail"
            }
            
            weather_code = current.get('weather_code', 0)
            weather_description = weather_codes.get(weather_code, "Unknown")
            
            # Format the response
            weather_info = f"Current weather in {location}:\n"
            weather_info += f"- Condition: {weather_description}\n"
            weather_info += f"- Temperature: {temperature}°C\n"
            weather_info += f"- Wind Speed: {wind_speed} km/h\n"
            weather_info += f"- Precipitation: {precipitation} mm\n"
            
            # Add forecast information if available
            if 'daily' in data:
                daily = data['daily']
                if 'temperature_2m_max' in daily and len(daily['temperature_2m_max']) > 0:
                    weather_info += f"\nToday's Forecast:\n"
                    weather_info += f"- High: {daily['temperature_2m_max'][0]}°C\n"
                    weather_info += f"- Low: {daily['temperature_2m_min'][0]}°C\n"
                    
                    if 'precipitation_sum' in daily:
                        weather_info += f"- Precipitation Sum: {daily['precipitation_sum'][0]} mm\n"
            
            return weather_info
        else:
            return f"Error: Unable to get weather data. Status code: {response.status_code}"
    
    except Exception as e:
        return f"Error checking weather: {str(e)}"

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
1. search_web(query): Search the web using Google for additional information. Returns up-to-date search results from the web including titles, URLs, and snippets. Use this when:
   - The information needed is not in your documents
   - You need current or real-time information 
   - You need to verify facts from external sources
   - The user asks about trending topics, news, or recent events
   - You need specific information like product details, reviews, or comparative information

2. check_weather(location): Check the weather in a given location. Returns the current weather conditions and forecast for the specified location.

How to decide which action to use:
- First check if you can answer from the documents provided
- If the documents don't have the information, use search_web for factual information
- Use check_weather only for weather-related queries about specific locations

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

    # Interactive chat with real function execution
    while True:
        message = ollama.chat(
            model='gemma3:27b',
            messages=messages
        )

        response_content = message['message']['content']
        messages.append({"role": "assistant", "content": response_content})

        print("Assistant:", response_content)

        if "PAUSE" in response_content:
            # Parse the action and input
            action_lines = response_content.split('PAUSE')[0].strip().split('\n')
            action = None
            action_input = None
            
            for line in action_lines:
                if line.startswith('Action:'):
                    action = line.replace('Action:', '').strip()
                elif line.startswith('Action Input:'):
                    action_input = line.replace('Action Input:', '').strip()
            
            # Execute the function based on the action
            if action == 'search_web' and action_input:
                result = search_web(action_input)
            elif action == 'check_weather' and action_input:
                result = check_weather(action_input)
            else:
                result = "Error: Invalid action or missing input."
            
            # Add the observation to the conversation
            observation = f"Observation: {result}"
            messages.append({"role": "user", "content": observation})
            print(observation)
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
        
        # Don't print the assistant response here since it's already printed in query_rag
        conversation_history.append({"role": "user", "content": question})
        conversation_history.append({"role": "assistant", "content": rag_response})

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Search for a question using RAG and react pattern with Google search capability")
    parser.add_argument("question", type=str, nargs='?', help="Question to ask about the webpage content")
    parser.add_argument("-o", "--output", type=str, help="Output file to save the markdown content")
    parser.add_argument("-i", "--interactive", action="store_true", help="Start an interactive shell")
    parser.add_argument("--google", action="store_true", help="Force use of Google search (requires API key)")
    parser.add_argument("--setup", action="store_true", help="Show setup instructions for Google API")

    # Parse command-line arguments
    args = parser.parse_args()

    # Display setup instructions if requested
    if args.setup:
        console.print("\n[bold blue]====================================[/bold blue]")
        console.print("[bold green]Google Gemini API Setup Instructions[/bold green]")
        console.print("[bold blue]====================================[/bold blue]\n")
        
        console.print("To use Google search functionality, follow these steps:")
        console.print("[bold]1.[/bold] Sign up for Google AI Studio at [link]https://ai.google.dev/[/link]")
        console.print("[bold]2.[/bold] Create an API key in the Google AI Studio console")
        console.print("[bold]3.[/bold] Set the API key as an environment variable:")
        console.print("   - [bold yellow]export GOOGLE_API_KEY=your_api_key_here[/bold yellow] (Linux/macOS)")
        console.print("   - [bold yellow]set GOOGLE_API_KEY=your_api_key_here[/bold yellow] (Windows cmd)")
        console.print("   - [bold yellow]$env:GOOGLE_API_KEY=\"your_api_key_here\"[/bold yellow] (Windows PowerShell)")
        console.print("\nMake sure to keep your API key secure and never commit it to version control.")
        sys.exit(0)

    # Display banner
    console.print("\n[bold blue]====================================[/bold blue]")
    console.print("[bold green]React Pattern RAG with Google Search[/bold green]")
    console.print("[bold blue]====================================[/bold blue]\n")
    
    # Check and display search status
    if GOOGLE_SEARCH_AVAILABLE and gemini_client:
        console.print("[green]✓ Google search is enabled[/green]")
    else:
        console.print("[yellow]⚠ Google search is disabled (fallback mode active)[/yellow]")
        console.print("[italic]Run with --setup flag to see setup instructions[/italic]")
        if args.google:
            console.print("[red]Error: --google flag requires GOOGLE_API_KEY to be set[/red]")
            console.print("Set it with: export GOOGLE_API_KEY=your_api_key_here")
            sys.exit(1)
    
    console.print("[blue]Using model: gemma3:27b for reasoning[/blue]")
    console.print()

    # Query semantic db
    json_response = query_chunks(args.question if args.question else "")

    if args.interactive:
        console.print("[bold]Starting interactive mode. Type 'exit' to quit.[/bold]")
        interactive_shell(json_response)
    elif args.question:
        rag_response = query_rag(json_response, args.question)

        if args.output:
            # If an output file is specified, write the markdown content to the file
            with open(args.output, 'w', encoding='utf-8') as file:
                file.write(rag_response)
                console.print(f"[green]Response has been saved to {args.output}[/green]")
        else:
            # Otherwise, print the markdown content to the standard output
            print(rag_response)
    else:
        console.print("[yellow]Please provide a question or use the -i flag for interactive mode.[/yellow]")
        parser.print_help()

if __name__ == "__main__":
    main()
