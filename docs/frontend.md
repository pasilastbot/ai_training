# Frontend Documentation

## Overview

This project is primarily a CLI-based system with one demo web application. The frontend components are minimal but demonstrate integration patterns for Gemini-powered applications.

---

## Web Applications

### Dr. Sigmund 2000 - Virtual Psychiatrist

**Location:** `public/psychiatrist/index.html`

A retro-themed AI psychiatrist chatbot demonstrating:
- Flask API integration
- Gemini-powered chat responses
- 90s-style web aesthetics

#### Design Philosophy

The application intentionally uses a nostalgic 1990s web design as part of the humorous theme:
- Windows 95/98 era visual elements
- Beveled buttons and inset borders
- Comic Sans and monospace fonts
- Teal backgrounds with checkerboard patterns
- Blinking text animations
- Scrolling marquee banner
- ASCII art for dynamic mood display

#### UI Components

| Component | Purpose |
|-----------|---------|
| **Header** | Title with retro gradient and neon text effects |
| **Marquee** | Scrolling welcome message ("Best viewed in Netscape Navigator 3.0") |
| **ASCII Display** | Dynamic ASCII art face showing psychiatrist's mood |
| **Chat Container** | Message history with styled user/bot bubbles |
| **Input Area** | Text input with Send and Reset buttons |
| **Footer** | Fake visitor counter and copyright notice |

#### Styling Details

**Color Palette:**
- Primary Background: `#008080` (Teal)
- Panel Background: `#C0C0C0` (Silver)
- Header: `#000080` (Navy Blue)
- User Messages: `#FFFFCC` (Light Yellow)
- Bot Messages: `#CCFFCC` (Light Green)
- Accent: `#FFFF00` (Yellow), `#FF00FF` (Magenta), `#00FF00` (Lime)

**Typography:**
- Primary Font: Comic Sans MS (intentionally)
- Code/ASCII: Courier New (monospace)

**Visual Effects:**
- Beveled borders (`border: 4px outset/inset`)
- Gradient backgrounds
- Blinking animations (`@keyframes blink`)
- Scrolling marquee (`@keyframes marquee`)

#### Responsive Behavior

The application uses a fixed-width layout (700px max-width) centered on screen, appropriate for the retro aesthetic. Not mobile-optimized (authentic to 90s web design).

---

#### Panel Mode (Multi-Persona Panel Discussion)

Panel Mode adds a **Single Therapist / Panel Discussion** toggle on the selection screen:
- **Preconfigured panels**: loaded from `GET /api/panel/configs`
- **Custom panels**: select **2–4** therapists directly from the persona grid

**How it works:**
- The UI does **not** start a backend panel session until the **first user message**
- First message uses `POST /api/panel/start` (returns `session_id` + moderator intro + persona responses)
- Subsequent messages use `POST /api/panel/continue` with `session_id`
- Reset ends the panel via `POST /api/panel/end`

**Implementation:**
- Frontend logic lives in `public/psychiatrist/app.js` (ES module)
- `index.html` includes the new Panel Mode UI and loads `app.js`

---

#### Hot Mic Consult (Spicy Backchannel)

Single-doctor mode can also request a **1:1 consult** with a random colleague and show the **doctor-to-doctor transcript** inline in the chat log for comedic effect.

**How it works:**
- Frontend sends `consult: true` in `POST /api/chat`
- Backend picks a random colleague, generates a “hot mic” exchange, and returns a `consult.transcript[]`
- UI renders transcript lines using a distinct “internal” message style before the final doctor reply

**Implementation:**
- Backend: `psychiatrist_api.py` (`/api/chat` consult mode)
- Frontend: `public/psychiatrist/app.js` + CSS `.message.internal`

## UI/UX Patterns

### Message Bubble Pattern

```html
<div class="message user">
    <div class="message-label">>> YOU:</div>
    <div class="message-text">Message content here</div>
</div>

<div class="message bot">
    <div class="message-label">>> DR. SIGMUND 2000:</div>
    <div class="message-text">Response content here</div>
</div>
```

### Loading State Pattern

```html
<div class="loading" id="loading">
    <span class="blink">*** PROCESSING YOUR THOUGHTS... PLEASE WAIT ***</span>
</div>
```

JavaScript toggles the `active` class to show/hide loading state.

### ASCII Art Mood Display

The backend returns ASCII art representing the psychiatrist's current mood:

```
thinking   amused     concerned  shocked    neutral
.---.      .---.      .---.      .---.      .---.
/ o o \    / ^ ^ \    / o o \    / O O \    / - - \
|  ~  |    |  v  |    |  n  |    |  O  |    |  _  |
\ === /    \ === /    \ === /    \ === /    \ === /
 '---'      '---'      '---'      '---'      '---'
```

---

## JavaScript Patterns

### API Communication

```javascript
async function sendMessage() {
    const response = await fetch('http://localhost:5001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: userMessage,
            history: chatHistory.slice(-10) // Keep last 10 for context
        })
    });
    const data = await response.json();
    // Handle response...
}
```

### State Management

Simple client-side state:
```javascript
let chatHistory = [];  // Array of {role, content} objects
```

### Event Handling

```javascript
// Enter key submission
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// Button click
<button onclick="sendMessage()">SEND</button>
```

---

## CLI-Based Interaction

While most of the project is CLI-based, the tools provide good output formatting:

### Rich Console Output (Python)

Uses the `rich` library for formatted terminal output:
- Markdown rendering
- Colored text
- Progress indicators

### CLI Progress Feedback (TypeScript)

Uses `ora` for spinner animations during async operations:
```typescript
import ora from 'ora';
const spinner = ora('Processing...').start();
// ...work...
spinner.succeed('Done!');
```

---

## Future Frontend Considerations

If building a more complete web frontend, consider:

### Recommended Stack
- **Framework:** React or Vue.js
- **Styling:** Tailwind CSS
- **State:** React Query for API state
- **Components:** shadcn/ui or Radix UI

### Key Features to Implement
1. **Chat Interface** - Real-time messaging with streaming support
2. **Tool Results Display** - Show images, code, structured data
3. **File Upload** - For image editing and document analysis
4. **History Management** - Persistent conversation history
5. **Settings Panel** - Model selection, temperature controls

### API Integration Patterns

```typescript
// Example React Query hook for chat
const useChat = () => {
  return useMutation({
    mutationFn: (message: string) => 
      fetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message })
      }).then(r => r.json()),
    onSuccess: (data) => {
      // Add to message history
    }
  });
};
```

---

## Asset Management

### Generated Images
Default output location: `public/images/`

### Generated Audio
Default output location: `public/audio/`

### Generated Videos
Default output location: `public/videos/`

These directories are created automatically by the CLI tools when generating media.
