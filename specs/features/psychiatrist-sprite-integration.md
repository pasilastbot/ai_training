# Psychiatrist Game Sprite Integration

> **Status:** Draft
> **Created:** 2026-02-04
> **Last Updated:** 2026-02-04
> **Author:** AI Agent

## Overview

### Purpose
Replace the static ASCII art mood display in Dr. Sigmund 2000 with animated pixel art sprites, utilizing the existing `sprite-animator` tool to generate character animations and adding a browser-based sprite animation system.

### User Story
As a player of the Dr. Sigmund 2000 game, I want to see an animated pixel art psychiatrist character that reacts to the conversation so that the game feels more visually engaging and retains its charming retro aesthetic.

### Scope

**Included:**
- Generate Dr. Sigmund 2000 character sprites using the sprite-animator tool
- Create animation sets for each mood state (thinking, amused, concerned, shocked, neutral)
- Implement a JavaScript sprite animation engine in the game frontend
- Replace ASCII art display with animated sprite canvas
- Maintain the 90s aesthetic with pixel art style

**Not Included:**
- Patient character sprites (future enhancement)
- Sound effects for animations
- Multiple psychiatrist character skins
- Mobile-responsive sprite scaling (game is intentionally desktop-focused)

---

## Requirements

### Functional Requirements
- **FR-1:** The game MUST display an animated sprite character instead of/alongside ASCII art
- **FR-2:** The sprite MUST animate continuously using the appropriate mood animation
- **FR-3:** The sprite MUST change animation when the psychiatrist's mood changes (based on API response)
- **FR-4:** Each mood (thinking, amused, concerned, shocked, neutral) MUST have its own animation set
- **FR-5:** Animations MUST loop smoothly without visible jitter
- **FR-6:** The sprite display MUST fit within the existing UI layout (replace the ASCII container)
- **FR-7:** A fallback to ASCII art SHOULD be available if sprites fail to load

### Non-Functional Requirements
- **Performance:** Animations must run at 8-12 FPS minimum, using requestAnimationFrame for smooth playback
- **Asset Size:** Total sprite assets should be under 2MB to maintain fast page load
- **Style Consistency:** Sprites must use pixel art style matching the 90s/retro game aesthetic
- **Compatibility:** Must work in modern browsers (Chrome, Firefox, Safari, Edge)
- **Accessibility:** ASCII art fallback ensures text-based accessibility is preserved

---

## API Contract

### Modified API Response

The existing `/api/chat` endpoint already returns a `mood` field. No changes needed to the backend API.

**Current Response:**
```json
{
  "response": "The psychiatrist's response text",
  "mood": "thinking | amused | concerned | shocked | neutral",
  "ascii_art": "ASCII art representation (kept for fallback)"
}
```

### New Frontend Sprite Configuration

```typescript
interface SpriteAnimation {
  mood: string;
  frames: string[];      // Array of frame image paths
  frameDuration: number; // Milliseconds per frame
  loop: boolean;
}

interface SpriteConfig {
  character: string;
  basePath: string;              // e.g., "sprites/dr-sigmund/"
  frameSize: { width: number; height: number };
  animations: Record<string, SpriteAnimation>;
}
```

### Animation Metadata File

Located at `public/sprites/dr-sigmund/animations.json`:

```json
{
  "character": "Dr. Sigmund 2000",
  "frameSize": { "width": 128, "height": 128 },
  "animations": {
    "neutral": {
      "frames": ["neutral_000.png", "neutral_001.png", "neutral_002.png", "neutral_003.png"],
      "frameDuration": 200,
      "loop": true
    },
    "thinking": {
      "frames": ["thinking_000.png", "thinking_001.png", "thinking_002.png", "thinking_003.png"],
      "frameDuration": 300,
      "loop": true
    },
    "amused": {
      "frames": ["amused_000.png", "amused_001.png", "amused_002.png", "amused_003.png"],
      "frameDuration": 150,
      "loop": true
    },
    "concerned": {
      "frames": ["concerned_000.png", "concerned_001.png", "concerned_002.png", "concerned_003.png"],
      "frameDuration": 250,
      "loop": true
    },
    "shocked": {
      "frames": ["shocked_000.png", "shocked_001.png", "shocked_002.png", "shocked_003.png"],
      "frameDuration": 100,
      "loop": true
    }
  }
}
```

---

## Data Model

### New Entities

**SpriteAnimationMetadata** - Stored as JSON files in `public/sprites/dr-sigmund/`:

```typescript
interface SpriteAnimationMetadata {
  character: string;
  frameSize: {
    width: number;
    height: number;
  };
  animations: Record<MoodType, {
    frames: string[];
    frameDuration: number;
    loop: boolean;
  }>;
}

type MoodType = 'thinking' | 'amused' | 'concerned' | 'shocked' | 'neutral';
```

### Modified Entities
- No database changes required
- Existing ASCII_FACES dictionary in `psychiatrist_api.py` remains for fallback

### Relationships
- HTML Frontend → Sprite Animation Engine → Animation Metadata JSON → PNG Frame Files

---

## Component Structure

### Files to Create

| File Path | Purpose | Dependencies |
|-----------|---------|--------------|
| `public/sprites/dr-sigmund/animations.json` | Animation configuration | None |
| `public/sprites/dr-sigmund/*.png` | Animation frame images | Generated by sprite-animator |
| `public/psychiatrist/sprite-engine.js` | JavaScript sprite animation engine | None (vanilla JS) |

### Files to Modify

| File Path | Changes | Reason |
|-----------|---------|--------|
| `public/psychiatrist/index.html` | Add canvas element, load sprite engine, replace ASCII with sprite | Enable sprite display |
| `tools/sprite-animator.ts` (optional) | Add preset for "psychiatrist" character style | Convenience for regenerating sprites |

### Asset Folder Structure

```
public/sprites/dr-sigmund/
├── animations.json           # Animation configuration
├── neutral_000.png          # Neutral mood frames
├── neutral_001.png
├── neutral_002.png
├── neutral_003.png
├── thinking_000.png         # Thinking mood frames
├── thinking_001.png
├── thinking_002.png
├── thinking_003.png
├── amused_000.png           # Amused mood frames
├── amused_001.png
├── amused_002.png
├── amused_003.png
├── concerned_000.png        # Concerned mood frames
├── concerned_001.png
├── concerned_002.png
├── concerned_003.png
├── shocked_000.png          # Shocked mood frames
├── shocked_001.png
├── shocked_002.png
└── shocked_003.png
```

---

## Dependencies

### External Libraries
| Package | Version | Purpose |
|---------|---------|---------|
| None | - | Using vanilla JavaScript for browser compatibility and simplicity |

### API Keys / Environment Variables
- `REPLICATE_API_TOKEN`: Required for generating sprites via sprite-animator tool (already configured)

### System Requirements
- No additional system requirements
- Sprites generated once, then served as static assets

---

## Sprite Generation Plan

### Character Design Specification

**Dr. Sigmund 2000 Character:**
- Style: 90s pixel art, 32x32 or 64x64 upscaled to 128x128
- Appearance: Cartoon psychiatrist/doctor, possibly with:
  - White coat or formal attire
  - Glasses or monocle (Freudian aesthetic)
  - Simple, expressive face
  - Retro computer/terminal aesthetic elements
- Color palette: Limited colors matching the teal/green 90s UI

### Generation Commands

```bash
# Neutral/Idle animation (listening pose)
npm run sprite-animator -- \
  -c "retro pixel art psychiatrist doctor character, white coat, glasses, sitting at desk, 90s computer game style" \
  -a idle \
  -n 4 \
  -s "32x32 pixel art, limited color palette, teal green accent, clean lines, centered" \
  --transparent \
  -f public/sprites/dr-sigmund

# Thinking animation
npm run sprite-animator -- \
  -c "retro pixel art psychiatrist doctor thinking, hand on chin, pondering, 90s computer game style" \
  -a idle \
  -n 4 \
  -s "32x32 pixel art, limited color palette, teal green accent, thoughtful expression" \
  --transparent \
  -f public/sprites/dr-sigmund

# Amused animation (slight laugh/smile)
npm run sprite-animator -- \
  -c "retro pixel art psychiatrist doctor amused, slight smile, chuckling, 90s computer game style" \
  -a idle \
  -n 4 \
  -s "32x32 pixel art, limited color palette, teal green accent, happy expression" \
  --transparent \
  -f public/sprites/dr-sigmund

# Concerned animation
npm run sprite-animator -- \
  -c "retro pixel art psychiatrist doctor concerned, worried expression, furrowed brow, 90s computer game style" \
  -a idle \
  -n 4 \
  -s "32x32 pixel art, limited color palette, teal green accent, worried expression" \
  --transparent \
  -f public/sprites/dr-sigmund

# Shocked animation
npm run sprite-animator -- \
  -c "retro pixel art psychiatrist doctor shocked, surprised expression, wide eyes, 90s computer game style" \
  -a idle \
  -n 4 \
  -s "32x32 pixel art, limited color palette, teal green accent, surprised expression" \
  --transparent \
  -f public/sprites/dr-sigmund
```

---

## Testing Strategy

### Unit Tests
- **Test:** Sprite engine loads animation config correctly
  - **Given:** A valid animations.json file
  - **When:** SpriteEngine.loadConfig() is called
  - **Then:** All animation definitions are parsed and frame paths are valid

- **Test:** Sprite engine handles missing frames gracefully
  - **Given:** An animation with a missing frame file
  - **When:** Attempting to play the animation
  - **Then:** Falls back to ASCII art display without crashing

### Integration Tests
- **Test:** Mood change triggers correct animation
  - **Setup:** Game loaded with sprites, chat sent
  - **Steps:** Send message that triggers "amused" mood
  - **Expected:** Sprite changes from neutral to amused animation

### E2E Tests (Manual)
- **Scenario:** Complete chat session with sprite animations
  - **Steps:**
    1. Open game in browser
    2. Verify neutral/idle sprite is animating
    3. Send message that triggers thinking response
    4. Verify sprite changes to thinking animation
    5. Continue conversation through all moods
  - **Expected:** Smooth animation transitions, no visual glitches

---

## Acceptance Criteria

- [ ] **AC-1:** Dr. Sigmund character sprites are generated for all 5 moods (20 total frames minimum)
- [ ] **AC-2:** Sprite animation engine plays continuous idle animation on page load
- [ ] **AC-3:** Animation changes within 100ms of receiving API response with new mood
- [ ] **AC-4:** Animations loop smoothly without visible stuttering
- [ ] **AC-5:** ASCII art fallback displays if sprite loading fails
- [ ] **AC-6:** Sprite display fits within existing UI without layout breakage
- [ ] **AC-7:** Page load time increases by no more than 500ms with sprites
- [ ] **AC-8:** Works correctly in Chrome, Firefox, and Safari
- [ ] All manual E2E tests pass
- [ ] Documentation updated (README mentions sprite feature)

---

## Implementation Notes

### Design Decisions

1. **Vanilla JavaScript over framework:** The game is a simple single-page app. Adding React or similar would be overkill and break the retro simplicity.

2. **Canvas-based rendering over CSS animations:** Canvas provides more control over frame timing and allows for potential future enhancements (particles, effects).

3. **4 frames per animation:** Balance between smooth animation and asset size. More frames can be added later if needed.

4. **128x128 display size:** Large enough to be visually impactful while maintaining pixel art aesthetic. Actual sprites may be 32x32 or 64x64, scaled up.

5. **Keep ASCII art fallback:** Maintains accessibility and provides graceful degradation.

### Known Limitations

1. **AI-generated sprite consistency:** Different frames may have slight variations in character appearance. May require manual touch-up or multiple generation attempts.

2. **No sprite sheet optimization:** Using individual frame files for simplicity. Could be optimized to sprite sheets later for fewer HTTP requests.

3. **Fixed frame rate per animation:** Different moods have different frame durations but no dynamic timing.

### Future Enhancements

- **Patient character sprite:** Add an animated patient character on the other side of the "couch"
- **Sprite sheets:** Combine frames into single sprite sheets for better performance
- **Animation transitions:** Smooth morphing between mood states instead of instant switch
- **Interactive elements:** Click on Dr. Sigmund for Easter egg animations
- **Multiple character skins:** Different psychiatrist appearances (serious, casual, robot version)
- **Sound effects:** Add retro sound effects for mood changes

---

## Implementation Sequence

### Phase 1: Asset Generation
1. Run sprite-animator commands to generate all mood animations
2. Rename/organize files into the `dr-sigmund/` folder structure
3. Create `animations.json` configuration file
4. Manually verify/touch-up sprites if needed

### Phase 2: Sprite Engine Development
1. Create `sprite-engine.js` with:
   - Config loading from JSON
   - Image preloading
   - Canvas rendering
   - Animation loop with requestAnimationFrame
   - Mood switching API

### Phase 3: Frontend Integration
1. Modify `index.html`:
   - Add canvas element in place of/alongside ASCII container
   - Include sprite-engine.js
   - Initialize sprite engine on page load
   - Connect API response mood to sprite engine

### Phase 4: Testing & Polish
1. Test all mood transitions
2. Verify fallback behavior
3. Cross-browser testing
4. Performance optimization if needed

---

## References

- Existing sprite tool: `tools/sprite-animator.ts`, `tools/sprite-animator.README.md`
- Game frontend: `public/psychiatrist/index.html`
- Game backend: `psychiatrist_api.py`
- Related docs: `docs/frontend.md`, `docs/architecture.md`
- Existing sprite examples: `public/sprites/idle_animation.json`
