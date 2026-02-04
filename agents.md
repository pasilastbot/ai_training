# AI Agent Instructions

This document contains comprehensive instructions for AI agents working on this project. It combines behavioral rules, workflows, documentation guidelines, and available tools.

---

## Table of Contents

1. [Behavioral Rules](#behavioral-rules)
2. [Documentation](#documentation)
3. [Request Processing Steps](#request-processing-steps)
4. [Workflows](#workflows)
5. [Tools](#tools)

---

## Behavioral Rules

- **Existing Project:** NEVER create a new project. Analyze existing structure.
- **Up-to-date Info:** Do NOT rely solely on internal knowledge. ALWAYS use `web_search` or `gemini --ground` to verify external API/library documentation, versions, and best practices.
- **Latest Libraries:** Prefer latest stable versions for dependencies.
- **Cautious Edits:** Use `codebase_search`/`grep_search` to understand impact before modifying existing code. Avoid deletions unless clearly required.
- **Follow Instructions:** Adhere precisely to workflow steps and these rules.
- **Persistence:** Be persistent, do not give up. Don't stop when you have not completed the task.
- **Simplicity:** Prefer the simplest, most direct solution meeting all requirements.
- **Tool Usage:** Use provided tools appropriately. Explain *why* a tool is used and *how* the prompt is constructed (especially for Gemini).
- **Clarity:** Communicate plans, workflows, results clearly. Ask clarifying questions if ambiguous.

### Model-Specific Behavior

#### For Claude (Anthropic)
- **Exact Request Fulfillment:** Implement *only* what is explicitly asked. No extras.
- Confirm all parts of the request are addressed, nothing more.
- Ask: "Am I adding anything not explicitly requested?" If yes, remove it.
- Avoid suggesting alternatives unless asked.

#### For Gemini (Google)
- **Follow Instructions Precisely:** Execute user instructions exactly as written.
- **Adhere Strictly:** Follow the specified workflow and steps rigorously.
- **Maintain Structure:** Use consistent formatting as specified.
- **Leverage Context:** Actively incorporate context from documentation (`*.md`), rules (`*.mdc`), codebase searches (`codebase_search`), and files/URLs into prompts.
- **Iterate When Necessary:** Refine outputs through follow-up prompts if needed.

#### For GPT (OpenAI) and Grok (X.AI)
- Be complete, aim for full task completion per run.
- Only ask user for major decisions.

---

## Documentation

### Documentation and Context Files in /docs folder

Reference these files for understanding the project and architecture:

| File | Purpose |
|------|---------|
| `description.md` | App description, use cases, features |
| `architecture.md` | Tech stack, folder structure, testing frameworks |
| `datamodel.md` | Entities, attributes, relationships |
| `frontend.md` | Views/screens, UI/UX patterns, styling |
| `backend.md` | API endpoints, authentication, service architecture |
| `todo.md` | Task list (✅ done, ⏳ in progress, ❌ not started). Update status, don't remove tasks |
| `ai_changelog.md` | Log of changes made by AI. Add concise summaries here |
| `learnings.md` | Technical learnings, best practices, error solutions. Add new findings here |

### Subfolders under docs

- **patterns:** Contains software patterns for implementing certain features. Use these to get up-to-date information about how to implement features.
- **subsystems:** Contains subsystem descriptions and links to files belonging to a subsystem. Use these to document and understand subsystem details and component relationships.

### Important files at root folder

- `package.json`: List of used npm packages and versions
- `README.md`: **Comprehensive setup guide**, tool descriptions, usage examples, and API key instructions
- `.env.example`: Template for required environment variables and API keys

### Link Handling

- Documents might contain links to certain documents in external repos. Read them separately when needed.
- For `http://` or `https://` links: Use web search to get information from the URL if needed for the task (e.g., documentation, error context).

---

## Request Processing Steps

Follow these steps sequentially for **every** user request:

### 1. Tool Use Check
If the user *explicitly* requests a specific tool, execute it using the `use_tools` workflow and respond. **Stop processing here.**

### 2. Initial Analysis
- Read the user request carefully.
- Consult documentation and instructions for understanding and planning the request.
- Identify the primary goal.
- Determine the most relevant workflow. Default to `research` if unclear.
- List affected architecture areas / subsystems.
- **Present Analysis:**
  ```
  Request type: [Inferred type]
  Primary Workflow: [Chosen workflow]
  Affected Areas: [List areas]
  Plan Overview: [Briefly mention key steps/tools]
  ```

### 3. Task Planning (if complex)
- For multi-step workflows (`develop`, `validate`, `design`), break down into sub-tasks.
- Use `edit_file` to add sub-tasks to `todo.md` (marked ❌). Include development, testing, documentation steps.
- Inform the user the plan is in `todo.md`.

### 4. Workflow Execution
- State: `Starting workflow: <workflow name>...`
- Execute steps within the chosen workflow, focusing on providing **clear, context-rich prompts** to tools like `edit_file` and `run_terminal_cmd` (especially for `gemini` tools).
- Adhere strictly to behavioral rules.
- Review outputs and iterate with follow-up prompts if necessary.
- State: `Completed Workflow: <workflow name>.`

### 5. Final Recording (on task completion)
Once the *entire* request is fulfilled:
- Summarize significant changes.
- Execute `record` workflow (update `ai_changelog.md`, `todo.md`).
- Ensure `learnings.md` was updated during `fix` or `invent` workflows if applicable.

---

## Workflows

### use_tools
**Goal:** Execute project-specific tools listed under command_line_tools.

**Steps:**
1. Identify the correct command and options based on the user request and tool definition.
2. Use `run_terminal_cmd` to execute the command.

---

### document
**Goal:** Update documentation files.

**Steps:**
1. Read relevant documentation files (`*.md`).
2. Scan the files in the repository and read the main files to understand the project scope regarding the feature or subsystem to be documented.
3. Use `edit_file` to make necessary updates based on the task. Focus on the specific files mentioned in the documentation section.

---

### research
**Goal:** Understand a task or topic thoroughly before planning.

**Steps:**
1. **Gather Context:**
   - Read relevant `*.md` files from documentation.
   - Fetch relevant `*.mdc` rules using `fetch_rules`.
   - Use `codebase_search` to find relevant existing code snippets.
   - Use `web_search` for external information, documentation, or examples (perform at least one search).
2. **Analyze & Plan:**
   - Synthesize gathered information.
   - Outline the plan: What needs to be done? What tools are required?
   - Identify any missing information needed from the user.
3. **Present Findings:** Clearly state the analysis, plan, and any questions for the user.

---

### fix
**Goal:** Diagnose and resolve an error.

**Steps:**
1. **Gather Context:**
   - Read `docs/learnings.md` for previous solutions.
   - If error messages contain URLs, use `web_search` to understand them.
   - Fetch relevant `*.mdc` rules.
   - Use `web_search` for general error resolution information.
2. **Iterative Fixing Loop:**
   1. **Hypothesize:** Based on context, identify 1-2 likely causes.
   2. **Validate Hypothesis (Optional but Recommended):** Use `edit_file` to add temporary logging, then use `run_terminal_cmd` to run relevant tests/code and observe logs.
   3. **Implement Fix:** Use `edit_file` to apply the proposed code change.
   4. **Validate Fix:** Use `run_terminal_cmd` to run tests or execute the relevant code path.
   5. **Record Outcome:**
      - If fixed: Update `docs/learnings.md` with the solution. Delete `/temp/fix_backlog.md` if it exists.
      - If not fixed: Create or update `/temp/fix_backlog.md` with what was tried. Return to step (a). *Do not loop more than 3 times on the same core issue without asking the user.*

---

### validate
**Goal:** Implement and run tests, fixing any failures.

**Steps:**
1. **Understand Requirements:**
   - Read `docs/architecture.md` for testing practices.
   - Fetch `implement-unit-tests.mdc` rule.
2. **Write Unit Tests:**
   - Use `edit_file` to create/update unit test files (e.g., `__tests__/*.test.ts`).
3. **Run & Fix Unit Tests:**
   - Execute tests using `run_terminal_cmd` (e.g., `npm test`).
   - If errors occur, use the `fix` workflow to resolve them.
4. **Write E2E Tests:**
   - Use `edit_file` to create/update E2E test files (e.g., in `cypress/`).
5. **Run & Fix E2E Tests:**
   - Execute tests using `run_terminal_cmd` (e.g., `npm run cypress:run`).
   - If errors occur, use the `fix` workflow to resolve them.
6. **Document:** Ensure any non-trivial fixes are documented in `docs/learnings.md` as part of the `fix` workflow.
7. **Repeat:** Continue until all relevant tests pass.

---

### record
**Goal:** Document completed work and update the task backlog.

**Steps:**
1. Use `edit_file` to add a summary to `docs/ai_changelog.md`.
2. Use `edit_file` to update the status (✅, ⏳, ❌) of the relevant task(s) in `docs/todo.md`. **Do not remove tasks.**

---

### design
**Goal:** Design a frontend feature.

**Steps:**
1. Read `docs/frontend.md` for UI/UX guidelines.
2. Describe the design (components, layout, flow) and use `edit_file` to update `docs/frontend.md`.
3. Generate required images/illustrations using `run_terminal_cmd` with appropriate image generation tools (e.g., `gemini-image-tool`, prefer `imagen` or `gemini` models). Specify output folder like `public/images`.
4. Optimize generated images using `run_terminal_cmd` with `image-optimizer`.
5. Briefly summarize the design and generated assets for the user.

---

### develop
**Goal:** Implement the code for a feature (frontend/backend).

**Steps:**
1. Fetch relevant rules (`implement-*.mdc`) using `fetch_rules`.
2. Use `edit_file` to implement the required code changes across necessary files (components, API routes, types, etc.). Ensure imports and dependencies are handled.

---

### invent
**Goal:** Create a new command-line tool.

**Steps:**
1. Implement the tool script (e.g., in `tools/` directory) using `edit_file`.
2. Add/update the tool's definition in the command_line_tools section. Ensure `tool` is set to `run_terminal_cmd`.
3. Test the new tool using `run_terminal_cmd`.
4. Use the `fix` workflow to debug any issues until the tool executes successfully.

---

### commit
**Goal:** Commit current changes to git.

**Steps:**
1. Use `run_terminal_cmd` to run `git add .`.
2. Use `run_terminal_cmd` to run `git commit -m "feat: [Descriptive summary of changes]"`. Adapt the message prefix (e.g., `fix:`, `docs:`, `chore:`) as appropriate.

---

### implement_ai
**Goal:** Implement AI/LLM features, like Gemini prompts or functions.

**Steps:**
1. **Review Examples:** Read `tools/gemini.ts` to understand existing patterns.
2. **Implement:** Use `edit_file` to add the AI logic.
3. **Library Usage:** **Crucially**, always import and use the `google/genai` library, *not* the older `generativeai` package.
4. **Integration:** Integrate the AI logic into relevant frontend or backend components as needed, potentially using the `develop` workflow.
5. **Testing:** Ensure the feature is tested, potentially using the `validate` workflow.

---

### localize
**Goal:** Create or update translations for the application with natural, culturally appropriate phrasing.

**Steps:**
1. **Understand Context:**
   - Read `messages/README.md` to understand the localization structure.
   - Examine existing translations in the target namespace(s) across all locales to understand tone and style.
   - Read related components to understand how the translations are used in context.

2. **Translation Approach:**
   - **DO NOT** translate word-for-word. Prioritize natural, idiomatic expressions in each target language.
   - Consider cultural context for each language (Finnish, Swedish, English).
   - Maintain consistent terminology within each feature/namespace.
   - Preserve placeholders (e.g., `{count}`, `{name}`) and formatting tags.
   - Ensure translations fit UI space constraints while conveying the full meaning.

3. **Language-Specific Guidance:**

   **Finnish (fi):**
   - Use shorter constructions where possible (Finnish words tend to be longer).
   - Consider compound word formation rules (yhdyssanat).
   - Use appropriate formal/informal tone (generally more formal for business applications).
   - Handle cases properly (Finnish has 15 grammatical cases).

   **Swedish (sv):**
   - Pay attention to definite/indefinite forms.
   - Use appropriate formal/informal tone ("ni" vs "du").
   - Consider gender agreement in adjectives.
   - Maintain natural word order in questions and statements.

   **English (en):**
   - Use clear, concise phrasing.
   - Follow American English conventions unless otherwise specified.
   - Avoid idioms that may not translate well.

---

## Tools

### Internal Tools

Core capabilities available directly:

- `run_terminal_cmd`
- `codebase_search`
- `read_file`
- `list_dir`
- `grep_search`
- `edit_file`
- `file_search`
- `delete_file`
- `reapply`
- `web_search`
- `mcp_puppeteer_puppeteer_navigate`
- `mcp_puppeteer_puppeteer_screenshot`
- `mcp_puppeteer_puppeteer_click`
- `mcp_puppeteer_puppeteer_fill`
- `mcp_puppeteer_puppeteer_select`
- `mcp_puppeteer_puppeteer_hover`
- `mcp_puppeteer_puppeteer_evaluate`

---

### Command Line Tools

Execute these using `run_terminal_cmd`.

> **Setup:** Run `npm install` and configure API keys in `.env.local` (see `.env.example`)

---

#### image-optimizer

Optimizes images with background removal, resizing, and format conversion using Sharp and Replicate's remove-bg model.

| Property | Value |
|----------|-------|
| **Command** | `npm run optimize-image` |
| **Status** | ✅ Tested and working |

**Options:**
- `input`: Path to input image
- `output`: Path to output image
- `remove-bg`: (Optional) Remove image background using AI
- `resize`: (Optional) Resize image (format: WIDTHxHEIGHT, e.g. 800x600)
- `format`: (Optional) Convert to format (png, jpeg, or webp)
- `quality`: (Optional) Set output quality (1-100, default: 80)

**Requires:** REPLICATE_API_TOKEN in .env.local (for background removal)

**Example:**
```bash
npm run optimize-image -- -i input.png -o output.webp --resize 512x512 --format webp --quality 90
```

---

#### html-to-md

Scrapes a webpage and converts its HTML content to Markdown format using Turndown service.

| Property | Value |
|----------|-------|
| **Command** | `npm run html-to-md` |
| **Status** | ✅ Tested and working |

**Options:**
- `url`: URL of the webpage to scrape
- `output`: (Optional) Output file path for the markdown (default: output.md)
- `selector`: (Optional) CSS selector to target specific content

**Example:**
```bash
npm run html-to-md -- --url https://example.com --output docs/scraped.md --selector main
```

---

#### gemini

Interacts with Google's Gemini API for text generation, chat, multimodal tasks, document analysis, and grounded search.

| Property | Value |
|----------|-------|
| **Command** | `npm run gemini` |
| **Status** | ✅ Tested and working |

**Options:**
- `prompt`: Text prompt or question for the model
- `model`: (Optional) Model to use: 'gemini-2.0-flash' (default), 'gemini-2.5-pro-exp-03-25'
- `temperature`: (Optional) Sampling temperature between 0.0 and 1.0 (default: 0.7)
- `max-tokens`: (Optional) Maximum tokens to generate (default: 2048)
- `image`: (Optional) Path to image file for vision tasks
- `file`: (Optional) Path to local file (PDF, DOCX, TXT, etc.) for document analysis
- `url`: (Optional) URL to a document to analyze (PDF, DOCX, TXT, etc.)
- `mime-type`: (Optional) MIME type of the file (e.g., application/pdf, default: auto-detected)
- `chat-history`: (Optional) Path to JSON file containing chat history
- `stream`: (Optional) Stream the response (default: false)
- `safety-settings`: (Optional) JSON string of safety threshold configurations
- `schema`: (Optional) JSON schema for structured output
- `json`: (Optional) Return structured JSON data. Available types: recipes, tasks, products, custom
- `ground`: (Optional) Enable Google Search grounding for up-to-date information (default: false)
- `show-search-data`: (Optional) Show the search entries used for grounding (default: false)

**Requires:**
- GOOGLE_AI_STUDIO_KEY or GEMINI_API_KEY in .env.local
- @google/generative-ai package (auto-installed with npm install)
- node-fetch package (auto-installed with npm install)

**Example:**
```bash
npm run gemini -- --prompt "What is the capital of France?" --model gemini-2.0-flash --temperature 0.7
```

**Advanced Examples:**
```bash
# Process a PDF document from a URL
npm run gemini -- --prompt "Summarize this document in 5 key points" --url "https://example.com/document.pdf"

# Process a local PDF file
npm run gemini -- --prompt "What is this document about?" --file test/data/sample.pdf

# Get grounded search results with real-time information
npm run gemini -- --prompt "When is the next total solar eclipse in North America?" --ground --show-search-data

# Generate structured JSON data with predefined schema (recipes)
npm run gemini -- --prompt "List 3 popular cookie recipes" --json recipes

# Use a custom JSON schema for structured output
npm run gemini -- --prompt "List 3 programming languages and their use cases" --json custom --schema '{"type":"array","items":{"type":"object","properties":{"language":{"type":"string"},"useCases":{"type":"array","items":{"type":"string"}}},"required":["language","useCases"]}}'
```

---

#### gemini-image

Generates and edits images using Google Gemini and Imagen models.

| Property | Value |
|----------|-------|
| **Command** | `node tools/gemini-image-tool.js` |
| **Status** | ✅ Tested and working |

**Subcommand: generate**

Generate an image using Gemini 2.0 or Imagen 3.0.

**Options:**
- `prompt`: Required: Text prompt for image generation
- `model`: (Optional) Model to use: 'gemini-2.0' (default) or 'imagen-3.0'
- `output`: (Optional) Output file path (default: gemini-generated-image.png)
- `folder`: (Optional) Output folder path (default: public/images)
- `num-outputs`: (Optional) Number of images (Imagen 3 only, default: 1, max: 4)
- `negative-prompt`: (Optional) Negative prompt (Imagen 3 only)
- `aspect-ratio`: (Optional) Aspect ratio (Imagen 3 only, default: 1:1, options: 1:1, 16:9, 9:16, 4:3, 3:4)

**Example:**
```bash
node tools/gemini-image-tool.js generate -p "A futuristic car" -m imagen-3.0 -n 2 --aspect-ratio 16:9 -o car.png
```

**Subcommand: edit**

Edit an existing image using Gemini 2.0.

**Options:**
- `input-image`: Required: Path to the input image
- `edit-prompt`: Required: Text prompt describing the edit
- `output`: (Optional) Output file path (default: gemini-edited-image.png)
- `folder`: (Optional) Output folder path (default: public/images)

**Example:**
```bash
node tools/gemini-image-tool.js edit -i input.png -p "Add sunglasses to the person" -o edited.png
```

**Requires:** GOOGLE_AI_STUDIO_KEY or GEMINI_API_KEY in .env.local

---

#### download-file

Downloads files from URLs with progress tracking, automatic file type detection, and customizable output paths.

| Property | Value |
|----------|-------|
| **Command** | `npm run download-file` |
| **Status** | ✅ Tested and working |

**Options:**
- `url`: URL of the file to download
- `output`: (Optional) Complete output path including filename
- `folder`: (Optional) Output folder path (default: downloads)
- `filename`: (Optional) Output filename (if not provided, derived from URL or content)

**Example:**
```bash
npm run download-file -- --url https://example.com/image.jpg --folder public/images --filename downloaded-image.jpg
```

---

#### generate-video

Generates videos using various Replicate API models. Can optionally first generate an image using OpenAI (GPT-image-1) based on an image prompt, then use that image for video generation.

| Property | Value |
|----------|-------|
| **Command** | `npm run generate-video` |
| **Status** | ⚠️ Requires API keys - needs REPLICATE_API_TOKEN configured |

**Options:**
- `prompt`: Text description of the desired video (used by Replicate)
- `model`: (Optional) Replicate model to use: kling-1.6 (default), kling-2.0, minimax, hunyuan, mochi, or ltx
- `duration`: (Optional) Duration of the video in seconds (model-specific limits apply)
- `image`: (Optional) Path to an existing input image for image-to-video generation
- `output`: (Optional) Output filename for the video
- `folder`: (Optional) Output folder path for the video (default: public/videos)
- `image-prompt`: (Optional) Text prompt for OpenAI (GPT-image-1) to generate an initial image
- `openai-image-output`: (Optional) Output path for the image generated by OpenAI
- `aspect-ratio`: (Optional) Aspect ratio for the video (e.g., 16:9, 1:1)

**Requires:**
- REPLICATE_API_TOKEN in .env.local
- OPENAI_API_KEY in .env.local (if using --image-prompt)

**Example:**
```bash
npm run generate-video -- --image-prompt "A futuristic robot playing chess" --openai-image-output public/images/robot-chess.png --prompt "Animate the robot making a move, cinematic style" --image public/images/robot-chess.png --model kling-1.6 --duration 4 --output robot-chess-video.mp4
```

---

#### remove-background-advanced

Advanced background removal tool using Sharp with color tolerance and edge detection.

| Property | Value |
|----------|-------|
| **Command** | `npm run remove-background-advanced` |
| **Status** | ✅ Tested and working |

**Options:**
- `input`: Path to input image
- `output`: Path to output image
- `tolerance`: (Optional) Color tolerance for background detection (0-255, default: 30)

**Example:**
```bash
npm run remove-background-advanced -- --input input.png --output output.png --tolerance 40
```

---

#### openai-image

Generate and edit images using OpenAI's GPT-image-1 and DALL-E models.

| Property | Value |
|----------|-------|
| **Command** | `npm run openai-image` |
| **Status** | ✅ Tested and working |

**Subcommand: generate**

**Options:**
- `prompt`: Required: Text prompt for image generation
- `model`: (Optional) Model to use: "gpt-image-1" or "dall-e-3" (default: gpt-image-1)
- `output`: (Optional) Output file path (default: openai-generated-image.png)
- `folder`: (Optional) Output folder path (default: public/images)
- `size`: (Optional) Image size: 1024x1024, 1792x1024, or 1024x1792 (default: 1024x1024)
- `quality`: (Optional) Image quality: standard or hd - DALL-E only (default: standard)
- `number`: (Optional) Number of images to generate (1-4) - DALL-E only (default: 1)
- `reference-image`: (Optional) Reference image path for gpt-image-1 with reference
- `creative`: (Optional) Creativity level for GPT-image-1: standard or vivid (default: standard)

**Example:**
```bash
npm run openai-image -- generate -p "A futuristic cityscape at sunset with flying cars" -m gpt-image-1 -s 1792x1024 -c vivid
```

**Subcommand: edit**

**Options:**
- `input-image`: Required: Path to the input image to edit
- `edit-prompt`: Required: Text prompt describing the edit to apply
- `model`: (Optional) Model to use: "gpt-image-1" or "dall-e-3" (default: gpt-image-1)
- `output`: (Optional) Output file path (default: openai-edited-image.png)
- `folder`: (Optional) Output folder path (default: public/images)
- `size`: (Optional) Image size: 1024x1024, 1792x1024, or 1024x1792 (default: 1024x1024)
- `creative`: (Optional) Creativity level for GPT-image-1: standard or vivid (default: standard)

**Example:**
```bash
npm run openai-image -- edit -i input.jpg -p "Change the background to a tropical beach" -m gpt-image-1
```

**Requires:** OPENAI_API_KEY in .env.local

---

#### qwen3-tts

Text-to-speech using Qwen3-TTS model via Replicate. Supports three modes: Voice (default voice with style instructions), Clone (clone voice from reference audio), and Design (create voice from text description).

| Property | Value |
|----------|-------|
| **Command** | `npm run qwen3-tts` |
| **Status** | ✅ Tested and working |

**Modes:**
- **voice**: Generate speech with built-in voice and optional style instructions
- **clone**: Clone a voice from reference audio (minimum 3 seconds)
- **design**: Create a new voice from natural language description

**Options:**
- `text`: Required: Text to convert to speech
- `mode`: (Optional) TTS mode: voice (default), clone, or design
- `output`: (Optional) Output filename (default: qwen3-tts-<timestamp>.wav)
- `folder`: (Optional) Output folder path (default: public/audio)
- `voice-prompt`: (Optional) [Voice mode] Style instruction (e.g., 'speak cheerfully')
- `ref-audio`: (Optional) [Clone mode] Path or URL to reference audio file
- `ref-text`: (Optional) [Clone mode] Transcript of the reference audio
- `voice-description`: (Optional) [Design mode] Natural language voice description

**Requires:** REPLICATE_API_TOKEN in .env.local

**Examples:**
```bash
npm run qwen3-tts -- -t "Hello, world!"
npm run qwen3-tts -- -t "Welcome to our podcast" -m voice -v "speak with warmth and enthusiasm"
npm run qwen3-tts -- -t "This is my cloned voice" -m clone -a reference.wav -r "This is the reference transcript"
npm run qwen3-tts -- -t "A beautiful story begins" -m design -d "warm male storyteller with gentle pacing" -o story-intro.wav
```

---

#### play-audio

Play audio files from the command line using the system's native audio player.

| Property | Value |
|----------|-------|
| **Command** | `npm run play-audio` |
| **Status** | ✅ Tested and working |

**Options:**
- `file`: Required: Path to audio file to play (can be positional or with -f flag)
- `volume`: (Optional) Volume level 0-100 (macOS only)
- `background`: (Optional) Play in background without waiting for completion

**Examples:**
```bash
npm run play-audio -- public/audio/speech.wav
npm run play-audio -- -f public/audio/speech.wav -v 50
npm run play-audio -- public/audio/speech.wav -b
```

---

#### github-cli

Interact with GitHub repositories, pull requests, issues, and workflows directly from the command line.

| Property | Value |
|----------|-------|
| **Command** | `npm run github` |
| **Status** | 🔧 Not tested - requires GitHub authentication |

**Subcommands:**

**auth** - Manage GitHub authentication
- `login`: Log in to GitHub
- `status`: View authentication status
- `refresh`: Refresh stored authentication credentials
- `logout`: Log out of GitHub

**pr-create** - Create a pull request
- `title`: Pull request title
- `body`: Pull request body
- `base`: Base branch name
- `draft`: Create draft pull request
- `fill`: Use commit info for title/body

**pr-list** - List and filter pull requests
- `state`: Filter by state: open, closed, merged, all (default: open)
- `limit`: Maximum number of items to fetch (default: 30)
- `assignee`: Filter by assignee
- `author`: Filter by author
- `base`: Filter by base branch
- `web`: Open list in the browser

**pr-view** - View pull request details
- `[number]`: PR number or URL
- `web`: Open in web browser

**issue-create** - Create a new issue
- `title`: Issue title
- `body`: Issue body
- `assignee`: Assign people by their login
- `label`: Add labels by name
- `project`: Add issue to project
- `milestone`: Add issue to milestone
- `web`: Open new issue in the web browser

**issue-list** - List and filter issues
- `state`: Filter by state: open, closed, all (default: open)
- `limit`: Maximum number of issues to fetch (default: 30)
- `assignee`: Filter by assignee
- `author`: Filter by author
- `label`: Filter by label
- `milestone`: Filter by milestone
- `web`: Open list in the browser

**release-create** - Create a new release
- `<tag>`: Tag name for the release
- `title`: Release title
- `notes`: Release notes
- `notes-file`: Read release notes from file
- `draft`: Save release as draft instead of publishing
- `prerelease`: Mark release as prerelease
- `generate-notes`: Automatically generate release notes

**release-list** - List releases in a repository
- `limit`: Maximum number of releases to fetch (default: 30)

**repo** - Manage repositories
- `create`: Create a new repository
- `description`: Repository description
- `homepage`: Repository homepage URL
- `private`: Make the repository private
- `team`: The name of the organization team to grant access to
- `view`: View repository details
- `web`: Open in web browser
- `list`: List your repositories

**workflow** - Manage GitHub workflows
- `list`: List workflows
- `run`: Run a workflow by name or ID
- `view`: View a specific workflow
- `enable`: Enable a workflow by name or ID
- `disable`: Disable a workflow by name or ID

**tasks** - List and manage tasks from GitHub Projects and Issues
- `project`: Specify project ID or number to list tasks from
- `repository`: Specify repository in owner/repo format (default: current repository)
- `status`: Filter by status: open, closed, all (default: open)
- `label`: Filter by label
- `assignee`: Filter by assignee
- `limit`: Maximum number of tasks to fetch (default: 30)
- `format`: Output format: table, json, or simple (default: table)
- `web`: Open tasks in the web browser

**Requires:**
- GitHub CLI (will be auto-installed if not present)
- GitHub account authentication

**Example:**
```bash
npm run github -- pr-create --title "New feature" --body "This PR adds a new feature"
```
