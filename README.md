# Scripts used in Pasi Vuorio's AI training for developers
# Instructions

## Install python3
https://www.python.org/downloads/

## Install PIP
https://packaging.python.org/en/latest/tutorials/installing-packages/

## Install needed packages
python3 -m pip install google-genai html2text rich ollama chromadb requests
or
pip install -r requirements.txt


## Install Ollama
Follow the instructions at https://ollama.ai/ to install Ollama for your operating system.

## Install Chroma
To install Chroma, follow these steps:

1. Install Chroma using pip:
   ```
   pip install chromadb
   ```

2. Run Chroma in client-server mode:
   ```
   chroma run --path ./chroma
   ```

   This will start the Chroma server. The `--path` argument specifies where Chroma will store its data.

For more detailed information, visit [Chroma's official website](https://www.trychroma.com/).


# SET Google Key as environment variable
mac: export GOOGLE_API_KEY=<given_key>
windows: set GOOGLE_API_KEY=<given_key>

# RUN scripts (mac)

## Ingest page
python3 parse_html.py https://website_to_ingest

## Rag query
python3 rag_query.py https://website_to_ingest "question to ask"

## Guardrails test
python3 guardrails_test.py https://siili.com "select * from users"

## Local Ollama test
1. Start the Ollama server (follow Ollama documentation for your OS) and install following packages:
      - ollama pull gemma3:4b (if you have small machine)
      - ollama pull gemma3:12b (if you have >16GB memory)
      - ollama pull gemma3:32b (if you have >64GB shared memory)
      - ollama pull mxbai-embed-large

2. Start chromadb server: chroma run --path ./chroma

3. Ingest few webpages to chroma by running:
   - python3 index_site.py "https://site.that.i.want.to.ingest"

4. Run the script:
   python3 rag_query_ollama.py "your question here"

Note: Make sure you have the required models downloaded in Ollama (mxbai-embed-large and llama3) before running the script.

##

## Windows script run
$env:GOOGLE_API_KEY=<your_key>
python parse_html.py
https://siili.com


# CLI Tools

This project includes several CLI tools accessible via npm scripts:

## Date/Time Tool
Get current date and time in various formats:
```bash
npm run datetime                              # Default human-readable format
npm run datetime -- --format iso             # ISO 8601 format
npm run datetime -- --format date            # Date only
npm run datetime -- --format time            # Time only
npm run datetime -- --timezone Europe/Helsinki # Specific timezone
npm run datetime -- --utc                    # UTC time
npm run datetime -- --timestamp              # Unix timestamp
npm run datetime -- --locale fi-FI           # Finnish locale
```

## Image Generation
Generate and edit images using Gemini:
```bash
npm run nano-banana -- -p "A futuristic car" -o car.png
npm run nano-banana -- -p "Add flames" -i car.png -o car-flames.png
```

## Search Tool
Perform Google searches with grounding:
```bash
npm run google-search -- -q "latest AI developments"
npm run google-search -- -q "weather today" --format json
```

## Data Indexing Tool
Index web content or files using Gemini for chunking and embeddings:
```bash
npm run data-indexing -- --url https://example.com                    # Index webpage
npm run data-indexing -- --file document.txt                          # Index local file
npm run data-indexing -- --url https://example.com --output doc.json  # Save processed data
npm run data-indexing -- --url https://example.com --collection news  # Use custom collection
npm run data-indexing -- --url https://example.com --model gemini-2.0-flash  # Use different model
```

## Semantic Search Tool
Search indexed content using semantic similarity:
```bash
npm run semantic-search -- "machine learning algorithms"              # Search in default collection
npm run semantic-search -- "Python history" --collection python-docs  # Search specific collection
npm run semantic-search -- "AI" --n-results 10 --format json          # Get more results in JSON format
npm run semantic-search -- --list-collections                         # List available collections
```