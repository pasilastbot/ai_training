#!/bin/bash

# Startup script for Gemini Chatbot

echo "🤖 Starting Gemini Chatbot Application..."
echo ""

# Check if GEMINI_API_KEY is set
if [ -z "$GOOGLE_AI_STUDIO_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  Warning: GOOGLE_AI_STUDIO_KEY or GOOGLE_API_KEY not set"
    echo "   Please set your API key:"
    echo "   export GEMINI_API_KEY=your_key_here"
    echo ""
fi

# Check if Python dependencies are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Start the application
echo "🚀 Starting server..."
echo "   Web interface: http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 api/app.py
