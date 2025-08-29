# Gemini Agent CLI example: task plan

- **status legend**: ✅ done, ⏳ in progress, ❌ not started

## Tasks

1) Research Gemini SDK tools and confirm Python types
- status: ✅ done
- notes: Using `from google import genai` and `from google.genai import types`; tools are `types.Tool(google_search=types.GoogleSearch())`, `types.Tool(code_execution=types.ToolCodeExecution())`, `types.Tool(url_context=types.UrlContext())`
  - refs: https://ai.google.dev/gemini-api/docs/google-search, https://ai.google.dev/gemini-api/docs/code-execution, https://ai.google.dev/gemini-api/docs/url-context

2) Implement `gemini_agent.py` CLI with optional tools
- status: ❌ not started
- scope:
  - flags: `--google-search`, `--code-execution`, `--url-context`, `--model` (default: `gemini-2.5-flash`)
  - input: positional `prompt`
  - behavior: print `response.text`; if present also print generated code and execution output

3) Provide minimal usage examples
- status: ❌ not started
- examples:
  - code execution: sum of first 50 primes
  - google search: Euro 2024 winner
  - url context: compare two recipe URLs

4) Manual validate locally (non-interactive)
- status: ❌ not started
- run: `python gemini_agent.py "..." --code-execution` etc.

5) Record work and update docs
- status: ❌ not started
- update: `docs/ai_changelog.md`, mark this plan items accordingly in `docs/todo.md`

6) Commit changes
- status: ❌ not started
- message: "add gemini_agent.py CLI example using search, code-exec, url-context"

---

## MCP integration plan

7) Add MCP dependency and CLI flags
- status: ⏳ in progress
- actions:
  - add `mcp` to requirements
  - add flags: `--mcp-stdio`, `--mcp-args`, `--mcp-env KEY=VALUE`, `--no-mcp-autocall`
  - when enabled, create `StdioServerParameters` and `ClientSession` via `mcp.client.stdio`

8) Implement MCP tool execution in single-turn and chat
- status: ❌ not started
- actions:
  - build `tools` as: `[session]` to enable automatic function calling
  - support disabling with `automatic_function_calling=...disable=True`

9) Smoke test with weather MCP
- status: ❌ not started
- actions:
  - install `npx`/node if needed, run with `npx -y @philschmid/weather-mcp`
  - prompt example: "What is the weather in London in YYYY-MM-DD?"

Refs:
- MCP in Gemini SDKs (Python): use `ClientSession` in tools; automatic calls loop until done.
- Supported models for function calling: Gemini 2.5 Flash/Pro per docs.

- Tools validation (2025-08-29):
  - download-file: ✅ passed (downloaded httpbin PNG to public/images)
  - remove-background-advanced: ✅ passed (processed sample image)
  - gemini.ts CLI: ✅ passed (responded with output)
  - gemini-image-tool.js: ✅ fixed (uses Imagen 3 endpoint; avoids key leak)
  - gemini-image wrapper: ✅ updated to call Node tool; validated
  - generate-video: ❌ skipped per request (partial updates in place)
  - tools/gemini.py: ✅ rewritten to proxy to npm run gemini
