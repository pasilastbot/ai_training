# Task List

## Legend
- ✅ Done
- ⏳ In Progress
- ❌ Not Started

---

## Documentation

- ✅ Create initial documentation structure
- ✅ Write description.md
- ✅ Write architecture.md
- ✅ Write datamodel.md
- ✅ Write frontend.md
- ✅ Write backend.md
- ✅ Create todo.md
- ✅ Create ai_changelog.md
- ✅ Create learnings.md
- ✅ Implement spec-driven development workflow
- ✅ Create specs folder structure (features/, apis/, components/)
- ✅ Create specification template (TEMPLATE.md)
- ✅ Create specs/README.md with workflow guide
- ✅ Create example specification (example-chat-feature.md)
- ✅ Mandate comprehensive testing in specs (unit + integration + E2E)
- ✅ Update template with detailed testing requirements
- ✅ Update example spec with comprehensive test plan (15+ unit, 7+ integration, 7+ E2E tests)
- ✅ Add testing validation step to <spec> workflow

---

## Infrastructure

- ❌ Add proper error handling to all CLI tools
- ❌ Implement unit tests with vitest (TypeScript)
- ❌ Implement unit tests with pytest (Python)
- ❌ Add Docker configuration for ChromaDB
- ❌ Create .env.example template
- ❌ Add CI/CD pipeline for testing

---

## Features

- ❌ Add conversation persistence for agents (save/load chat history)
- ❌ Implement streaming in Dr. Sigmund API
- ❌ Add rate limiting to Flask API
- ❌ Create a unified web dashboard for all tools
- ❌ Add image gallery view for generated images
- ❌ Implement tool result caching

---

## Multi-Persona Psychiatrist Feature

> Spec: `specs/features/multi-persona-psychiatrist.md`

### Phase 1: Configuration & Backend
- ✅ Create `config/personas.json` with 6 persona definitions
- ✅ Add persona loading to `psychiatrist_api.py`
- ✅ Add `/api/personas` endpoint
- ✅ Add `/api/personas/:id` endpoint
- ✅ Modify `/api/chat` to accept `persona_id`
- ✅ Modify `/api/reset` to be persona-aware
- ❌ Write backend unit tests

### Phase 2: Frontend Persona Selection
- ✅ Create persona selection screen HTML/CSS
- ✅ Fetch personas from API on load
- ✅ Implement persona card selection UI
- ✅ Store selected persona in session state

### Phase 3: Dynamic Theming
- ✅ Convert hardcoded CSS to CSS variables
- ✅ Apply theme from selected persona
- ✅ Update header title dynamically
- ✅ Update welcome message dynamically

### Phase 4: Sprite Integration
- ✅ Modify sprite-engine.js to accept dynamic path
- ❌ Generate sprites for Dr. Luna Cosmos
- ❌ Generate sprites for Dr. Pixel
- ❌ Generate sprites for remaining personas
- ❌ Create animations.json for each new persona

### Phase 5: UI Polish & Switching
- ✅ Add "Change Therapist" button
- ✅ Implement confirmation dialog
- ✅ Handle persona switch (clear history, reload)

### Phase 6: Testing & Documentation
- ✅ Write backend unit tests (13 tests)
- ✅ Write integration tests (21 tests)
- ✅ Perform manual E2E testing (5 scenarios via browser)
- ✅ Generate test coverage report (77% coverage)
- ✅ Create comprehensive test report (TEST_REPORT.md)
- ✅ Update README with persona feature

---

## Dr. Sigmund 2000 Sprite Integration

> Spec: `specs/features/psychiatrist-sprite-integration.md`

### Phase 1: Asset Generation
- ✅ Generate neutral/idle mood sprites (4 frames)
- ✅ Generate thinking mood sprites (4 frames)
- ✅ Generate amused mood sprites (4 frames)
- ✅ Generate concerned mood sprites (4 frames)
- ✅ Generate shocked mood sprites (4 frames)
- ✅ Create animations.json configuration file
- ✅ Organize sprites in `public/sprites/dr-sigmund/` folder

### Phase 2: Sprite Engine Development
- ✅ Create sprite-engine.js with config loading
- ✅ Implement canvas rendering and animation loop
- ✅ Add mood switching API function
- ✅ Implement image preloading

### Phase 3: Frontend Integration
- ✅ Add canvas element to index.html
- ✅ Replace/augment ASCII art display with sprites
- ✅ Connect API response mood to sprite engine
- ✅ Implement fallback to ASCII art on sprite load failure

### Phase 4: Testing & Polish
- ✅ Test all 5 mood transitions
- ❌ Cross-browser testing (Chrome, Firefox, Safari)
- ✅ Verify fallback behavior
- ❌ Performance optimization if needed

---

## RAG Pipeline

- ❌ Add support for more document types (DOCX, PPT)
- ❌ Implement document deduplication
- ❌ Add metadata filtering in semantic search
- ❌ Create batch indexing for multiple URLs
- ❌ Add incremental re-indexing support

---

## CLI Tools

- ❌ Add progress bars to long-running operations
- ❌ Implement --verbose flag for debug output
- ❌ Add --dry-run option where applicable
- ❌ Create tool aliases for common operations
- ❌ Add JSON output format to all tools

---

## Agents

- ❌ Add memory/context persistence across sessions
- ❌ Implement multi-turn planning with execution
- ❌ Add tool result visualization in chat
- ❌ Create agent testing framework
- ❌ Add support for more MCP servers

---

## Security

- ❌ Add input validation to all API endpoints
- ❌ Implement API key rotation support
- ❌ Add request logging and monitoring
- ❌ Create security audit checklist
- ❌ Add rate limiting per IP/user

---

## Performance

- ❌ Add response caching layer
- ❌ Implement connection pooling for ChromaDB
- ❌ Add embedding caching
- ❌ Profile and optimize slow operations
- ❌ Add async support to RAG queries

---

## Notes

- Update this file when completing tasks (change ❌ to ✅)
- Add new tasks as they arise
- Do not remove completed tasks (keep for history)
- Group related tasks under appropriate headers
