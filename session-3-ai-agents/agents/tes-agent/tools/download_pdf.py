#!/usr/bin/env python3
"""
Download PDF Tool

Downloads a PDF from a URL and saves it locally.

Usage:
    python download_pdf.py --url "https://example.com/tes.pdf" --name "Example TES"
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

MEMORY_DIR = Path(__file__).parent.parent / "memory"
PDF_DIR = MEMORY_DIR / "data" / "pdfs"


def download_pdf(url: str, name: str) -> dict:
    """Download PDF from URL."""
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    
    safe_name = re.sub(r'[^\w\-_]', '_', name.lower())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_name}_{timestamp}.pdf"
    filepath = PDF_DIR / filename
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)
        response.raise_for_status()
        
        content_type = response.headers.get("Content-Type", "")
        is_pdf = (
            "pdf" in content_type.lower() or 
            url.lower().endswith(".pdf") or
            response.content[:4] == b'%PDF'
        )
        
        if not is_pdf:
            return {
                "error": "URL does not appear to be a PDF",
                "content_type": content_type,
                "url": url
            }
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        return {
            "status": "downloaded",
            "path": str(filepath),
            "size_bytes": len(response.content),
            "url": url,
            "name": name
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Download failed: {str(e)}",
            "url": url
        }


def main():
    parser = argparse.ArgumentParser(description="Download PDF Tool")
    parser.add_argument("--url", required=True, help="URL to download PDF from")
    parser.add_argument("--name", required=True, help="Name for the PDF file")
    
    args = parser.parse_args()
    
    result = download_pdf(args.url, args.name)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
