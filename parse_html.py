import anthropic
from anthropic.types import TextBlock

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

def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Convert HTML from a URL to Markdown.")
    parser.add_argument("url", type=str, help="URL of the webpage to convert to markdown")
    parser.add_argument("-o", "--output", type=str, help="Output file to save the markdown content")

    # Parse command-line arguments
    args = parser.parse_args()

    # Convert URL to Markdown
    markdown_content = url_to_markdown(args.url)

    console = Console()
    markdown = Markdown(markdown_content)
    console.print(markdown)

    client = anthropic.Anthropic(
        # defaults to os.environ.get("ANTHROPIC_API_KEY")
        #api_key="my_api_key",
    )

    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=4000,
        temperature=0,
        system="You're an expert in web scraping and data extraction, known for your meticulous attention to detail and your proficiency in extracting complete structured data from unstructured sources. Use the chain of thought method with the following steps:\n\n" \
               "1. Read the given document and split it into chapters using headings and subheadings.\n" \
               "2. For each chapter, translate it to English, extract list format data, and convert it to a table.\n" \
               "3. Extract any images from the documentation and provide complete image URLs within the chapters.\n" \
               "4. If there are no tables or images, omit the 'table' or 'image' fields from the returned data. Do not provide empty or null values, and do not fabricate URLs.\n" \
               "5. Translate all data to English and return it in structured JSON format as follows:\n\n" \
               "{\n" \
               "  'topic': 'summary line of the whole text in English',\n" \
               "  'summary': 'short summary of the whole text in English',\n" \
               "  'language': 'original language of the whole text',\n" \
               "  'page_category': ['article', 'collection', 'category', 'product', 'news', 'service', 'other', 'faq', 'home'],\n" \
               "  'product': {'name': 'product title', 'price': 'product price', 'currency': 'product currency', 'description': 'product description'},\n" \
               "  'service': {'name': 'service name', 'price': 'service price', 'description': 'service description'},\n" \
               "  'chapters': [\n" \
               "    {\n" \
               "      'topic': 'topic of the chapter in English',\n" \
               "      'question': 'a question that this chapter answers in English',\n" \
               "      'keywords': ['max 3 keywords for the chapter'],\n" \
               "      'image': {'image_url': 'absolute, complete image URL, fix if incomplete', 'image_alt': 'image alt text', 'image_title': 'image title'},  // Omit if no image\n" \
               "      'table': {'table_name': 'table name', 'headers': ['header1', 'header2'], 'rows': [['row1col1', 'row1col2'], ['row2col1', 'row2col2']]},  // Omit if no table\n" \
               "      'content': 'chapter contents 150-500 words in English'\n" \
               "    }\n" \
               "  ]\n" \
               "}\n\n" \
               "Note: It is crucial not to lose any data or details. Ensure all data and complete tables are returned.\n" \
               "Ensure the returned data is in English. Only return plain JSON, with no additional text.\n",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": markdown_content
                    }
                ]
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "{"
                    }
                ]
            }
        ]
    )

    final_response = next(
        (block.text for block in message.content if isinstance(block, TextBlock)),
        None,
    )
    json_response = json.loads('{' + final_response)


    if args.output:
        # If an output file is specified, write the markdown content to the file
        with open(args.output, 'w', encoding='utf-8') as file:
            file.write(json_response)
            print(f"Markdown content has been saved to {args.output}")
    else:
        # Otherwise, print the markdown content to the standard output
        print(json.dumps(json_response, indent=2))

if __name__ == "__main__":
    main()

