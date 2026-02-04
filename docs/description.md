# AI Training System - Project Description

## Overview

This project is a comprehensive AI training and agent system designed for developers. It provides multi-platform AI integration with various LLM providers (Google Gemini, Ollama, OpenAI, Replicate), a rich set of CLI tools, interactive AI agents, and a complete RAG (Retrieval-Augmented Generation) pipeline using ChromaDB for vector storage.

## Purpose

The system serves as:

1. **A learning platform** for AI/LLM development techniques
2. **A toolkit** of reusable CLI tools for common AI tasks
3. **An agent framework** for building intelligent assistants
4. **A RAG pipeline** for semantic search and knowledge retrieval

## Key Features

### 1. Interactive AI Agents

- **Gemini Agent** (`gemini_agent.py`) - Full-featured agent with:
  - CLI tool integration (image generation, search, TTS, etc.)
  - Optional MCP (Model Context Protocol) support
  - Plan mode for step-by-step task planning
  - Interactive chat with conversation history
- **Ollama Agent** (`ollama_agent.py`) - Local LLM agent with:
  - Support for local models (glm-4.7-flash, gemma3, etc.)
  - CLI tool integration
  - No API key required (runs locally)

### 2. CLI Tools Suite

A comprehensive set of command-line tools accessible via npm scripts:


| Category    | Tools                                                                   |
| ----------- | ----------------------------------------------------------------------- |
| **AI/LLM**  | gemini, google-search, nano-banana                                      |
| **Image**   | gemini-image, openai-image, image-optimizer, remove-background-advanced |
| **Video**   | generate-video                                                          |
| **Audio**   | qwen3-tts, play-audio                                                   |
| **Data**    | data-indexing, semantic-search, html-to-md                              |
| **Utility** | datetime, download-file, github-cli                                     |


### 3. RAG Pipeline

Complete semantic search system:

- **Content Ingestion** - Process web pages and documents
- **AI-Powered Chunking** - Use Gemini to intelligently segment content
- **Vector Storage** - Store embeddings in ChromaDB
- **Semantic Search** - Query using natural language

### 4. Demo Application

- **Dr. Sigmund 2000** - A retro-themed AI psychiatrist game demonstrating:
  - Flask API backend
  - Gemini-powered chat responses
  - 90s-style web UI with ASCII art

## Use Cases

### For Learning

- Understand how to integrate multiple AI APIs
- Learn RAG pipeline implementation patterns
- Study agent architecture and tool calling
- Practice with function/tool calling patterns

### For Development

- Quick AI prototyping with ready-to-use tools
- Content processing and indexing workflows
- Image/video/audio generation pipelines
- Building custom AI agents

### For Production

- Semantic search over knowledge bases
- Automated content extraction and processing
- Multi-model AI workflows
- GitHub integration and automation

## Target Audience

- **Developers** learning AI/LLM integration
- **Data Engineers** building RAG systems
- **Full-stack Developers** adding AI features to applications
- **AI Researchers** prototyping new ideas

## Technology Stack Summary

- **Languages**: Python 3.9+, TypeScript
- **AI Providers**: Google Gemini, Ollama, OpenAI, Replicate
- **Vector DB**: ChromaDB
- **Runtime**: Node.js (tsx), Python
- **Web Framework**: Flask (for demo apps)

## Getting Started

See `README.md` for detailed setup instructions including:

- Python and Node.js dependency installation
- API key configuration
- ChromaDB setup for RAG features
- Running tools and agents

