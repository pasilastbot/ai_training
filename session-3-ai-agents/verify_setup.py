#!/usr/bin/env python3
"""
Verify Session 3 Setup

Run this to check all dependencies and configurations are ready.
"""

import sys
import os

def check_python_version():
    """Check Python version >= 3.10"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor} (need 3.10+)")
        return False

def check_api_key():
    """Check Gemini API key is set"""
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    
    key = os.environ.get("GOOGLE_AI_STUDIO_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        print(f"✓ Gemini API key found ({key[:8]}...)")
        return True
    else:
        print("✗ No Gemini API key (set GEMINI_API_KEY or GOOGLE_AI_STUDIO_KEY)")
        return False

def check_dependencies():
    """Check required packages are installed"""
    packages = [
        ("google.genai", "google-genai"),
        ("chromadb", "chromadb"),
        ("rich", "rich"),
        ("requests", "requests"),
        ("numpy", "numpy"),
    ]
    
    all_ok = True
    for module, package in packages:
        try:
            __import__(module)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (pip install {package})")
            all_ok = False
    
    return all_ok

def check_chromadb():
    """Check if ChromaDB is accessible"""
    try:
        import chromadb
        client = chromadb.HttpClient(host='localhost', port=8000)
        client.heartbeat()
        print("✓ ChromaDB running on localhost:8000")
        return True
    except Exception as e:
        print(f"⚠ ChromaDB not running (run: chroma run --path ./chroma-data)")
        return False  # Warning, not error - only needed for Exercise 2-3

def check_agent():
    """Check gemini_agent.py is importable"""
    try:
        # Just check the file exists and has key functions
        with open("gemini_agent.py", "r") as f:
            content = f.read()
            if "build_cli_function_declarations" in content and "execute_cli_function" in content:
                print("✓ gemini_agent.py ready")
                return True
            else:
                print("✗ gemini_agent.py missing key functions")
                return False
    except FileNotFoundError:
        print("✗ gemini_agent.py not found")
        return False

def main():
    print("=" * 50)
    print("Session 3: Setup Verification")
    print("=" * 50)
    print()
    
    results = []
    
    print("Python:")
    results.append(check_python_version())
    print()
    
    print("API Key:")
    results.append(check_api_key())
    print()
    
    print("Dependencies:")
    results.append(check_dependencies())
    print()
    
    print("ChromaDB:")
    check_chromadb()  # Don't add to results - it's optional for some exercises
    print()
    
    print("Agent:")
    results.append(check_agent())
    print()
    
    print("=" * 50)
    if all(results):
        print("✓ All checks passed! Ready for Session 3.")
        print()
        print("Quick test:")
        print("  python gemini_agent.py --chat")
        print()
        print("Then try:")
        print("  > What time is it?")
        print("  > Search for latest AI news")
    else:
        print("✗ Some checks failed. Fix issues above before starting.")
        sys.exit(1)

if __name__ == "__main__":
    main()
