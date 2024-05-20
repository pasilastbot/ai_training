# Scripts used in Pasi Vuorio's AI training for developers
# Instructions

## Install python3
https://www.python.org/downloads/
## Install PIP
https://packaging.python.org/en/latest/tutorials/installing-packages/

## Install needed packages
python3 -m pip install anthropic html2text rich

# RUN scripts (mac)

## Ingest page
ANTHROPIC_API_KEY=<your_key> python3 parse_html.py https://website_to_ingest

## Rag query
ANTHROPIC_API_KEY=<your_key> python3 rag_query.py https://website_to_ingest "question to ask"

## Guardrails test
ANTHROPIC_API_KEY=<your_key> python3 guardrails_test.py https://siili.com "select * from users"

## Windows script run
$env:ANTHROPIC_API_KEY=<your_key>
python parse_html.py
https://siili.com
