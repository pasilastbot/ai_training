## Hot Mic Consult (Spicy Backchannel)

> **Status:** 📝 Draft - Implement immediately
> **Created:** 2026-02-04
> **Author:** AI Agent
> **Context:** Dr. Sigmund 2000 demo app (Flask + vanilla JS)

### Overview
Add a “hot mic” feature to single-doctor chat where the active doctor consults **one random colleague per user message** and the UI shows the **doctor-to-doctor backchannel transcript** to the user for comedic “movie scene” roasting, followed by the doctor’s normal user-facing response.

### Goals
- Preserve **single-doctor** feel while adding an entertaining “behind the scenes” cutaway.
- Exactly **one consult per user message**.
- **Random** colleague selection (excluding current doctor).
- Consult transcript is **visible** in UI (no collapse by default).

### Non-Goals
- Multi-doctor panel mode (already covered by `multi-persona-panel-discussion.md`)
- Persistent storage (sessions remain in-memory for panel mode only)

---

## Requirements

### Functional
- **FR-HM-1:** When enabled, `/api/chat` MUST perform **one colleague consult** per user message.
- **FR-HM-2:** The consulted colleague MUST be chosen **randomly** from available personas excluding the current one.
- **FR-HM-3:** The API MUST return a **consult transcript** that includes:
  - doctor → colleague message (internal)
  - colleague → doctor message (internal)
- **FR-HM-4:** The UI MUST render the consult transcript in the chat log in a visually distinct “internal” style.
- **FR-HM-5:** The final doctor response MUST still be returned as `{response, mood, ascii_art}`.

### Tone / Humor
- “Spicy” roasting is allowed and encouraged, but should avoid hate/discrimination and slurs.
- Roasts should target behaviors/situations and the *other doctor’s methods*, not protected traits.

---

## API Contract

### POST `/api/chat`

**Request**
```json
{
  "message": "what should I do to sleep better?",
  "history": [],
  "persona_id": "dr-rex-hardcastle",
  "consult": true
}
```

**Response**
```json
{
  "response": "User-facing doctor reply…",
  "mood": "thinking",
  "ascii_art": "...",
  "consult": {
    "enabled": true,
    "consulted_persona_id": "dr-ada-sterling",
    "consulted_persona_name": "Dr. Ada Sterling",
    "transcript": [
      {
        "from_persona_id": "dr-rex-hardcastle",
        "from_persona_name": "Dr. Rex Hardcastle",
        "to_persona_id": "dr-ada-sterling",
        "to_persona_name": "Dr. Ada Sterling",
        "text": "…"
      },
      {
        "from_persona_id": "dr-ada-sterling",
        "from_persona_name": "Dr. Ada Sterling",
        "to_persona_id": "dr-rex-hardcastle",
        "to_persona_name": "Dr. Rex Hardcastle",
        "text": "…"
      }
    ]
  }
}
```

---

## Frontend UX
- Single mode `sendMessage()` sends `consult: true` by default.
- Chat log renders internal consult lines with:
  - distinct style (terminal-ish dashed border)
  - explicit label: `>> [HOT MIC] DR. X → DR. Y:`

---

## Testing Strategy

### Backend (pytest)
- `/api/chat` with `consult: true` returns `consult.transcript` with 2 items and correct IDs.
- Random selection is patchable/deterministic in tests (patch `random.choice`).
- Existing `/api/chat` tests remain green when consult is omitted.

### Frontend (vitest + jsdom)
- When `/api/chat` response includes `consult.transcript`, UI renders two internal messages before final reply.

