/**
 * Panel Mode "E2E-style" frontend tests (jsdom + mocked fetch).
 *
 * These tests exercise the real browser code in `public/psychiatrist/app.js`
 * by wiring minimal DOM and asserting API calls + rendered output.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

import {
  state,
  setMode,
  renderPanelConfigCards,
  renderPersonaCards,
  startSession,
  sendMessage,
  resetChat,
} from '../app.js';

function createAppDOM() {
  document.body.innerHTML = `
    <div class="persona-select-screen" id="personaSelectScreen">
      <button id="modeSingleBtn" class="mode-btn"></button>
      <button id="modePanelBtn" class="mode-btn"></button>
      <div id="panelConfigSection" class="panel-config-section hidden">
        <div id="panelConfigsGrid"></div>
        <input type="checkbox" id="includeModerator" checked />
      </div>
      <div id="personasGrid"></div>
      <button id="startSessionBtn" disabled>Start Session</button>
    </div>

    <div class="chat-screen" id="chatScreen">
      <div class="header">
        <h1 id="therapistName"></h1>
        <p id="therapistTagline"></p>
      </div>

      <div id="characterContainer"></div>
      <div id="asciiContainer" class="ascii-container"></div>
      <pre id="asciiArt"></pre>

      <div class="chat-container" id="chatContainer">
        <div class="welcome" id="welcomeMessage"></div>
      </div>

      <div class="loading" id="loading"></div>
      <input id="messageInput" />
      <span id="currentPersonaId"></span>
      <span id="visitorCount"></span>
    </div>

    <div id="confirmModal"></div>
  `;
}

function seedPersonas() {
  state.personas = [
    { id: 'dr-sigmund-2000', name: 'Dr. Sigmund 2000', tagline: 'Retro', description: 'A', era: '90s', theme: {} },
    { id: 'dr-ada-sterling', name: 'Dr. Ada Sterling', tagline: 'CBT', description: 'B', era: 'Modern', theme: {} },
    { id: 'captain-whiskers', name: 'Captain Whiskers, PhD', tagline: 'Cat', description: 'C', era: 'Cat', theme: {} },
    { id: 'dr-pixel', name: 'Dr. Pixel', tagline: 'Game', description: 'D', era: 'Gamer', theme: {} },
  ];
}

function seedPanelConfigs() {
  state.panelConfigs = [
    {
      id: 'balanced',
      name: 'The Balanced Panel',
      description: 'Mix',
      persona_ids: ['dr-sigmund-2000', 'dr-ada-sterling', 'captain-whiskers'],
      best_for: 'General',
      icon: '⚖️',
      order: 1,
    },
  ];
}

describe('Panel Mode UI (Phase 8)', () => {
  beforeEach(() => {
    createAppDOM();
    seedPersonas();
    seedPanelConfigs();
    state.selectedPanelConfigId = null;
    state.selectedPanelPersonaIds = new Set();
    state.panelSessionId = null;
    // @ts-expect-error - mocked in vitest.setup.ts
    global.fetch = vi.fn();
  });

  it('shows panel configuration section when switching to panel mode', () => {
    setMode('panel');
    renderPanelConfigCards();

    expect(document.getElementById('panelConfigSection').classList.contains('hidden')).toBe(false);
    expect(document.querySelectorAll('.panel-config-card').length).toBe(1);
  });

  it('selecting a panel config auto-selects personas and enables start button', () => {
    setMode('panel');
    renderPanelConfigCards();
    renderPersonaCards();

    // Click the panel config card
    document.querySelector('.panel-config-card').click();

    expect(document.querySelectorAll('.persona-card.selected').length).toBe(3);
    const btn = document.getElementById('startSessionBtn');
    expect(btn.disabled).toBe(false);
    expect(btn.textContent).toContain('Start Panel');
  });

  it('first panel message calls /api/panel/start and renders moderator + persona responses', async () => {
    setMode('panel');
    renderPanelConfigCards();
    renderPersonaCards();

    // Select panel config
    document.querySelector('.panel-config-card').click();

    // Enter panel chat screen (no API call yet)
    await startSession();

    const input = document.getElementById('messageInput');
    input.value = 'Hello panel';

    // Mock /api/panel/start response
    // @ts-expect-error - mocked in vitest.setup.ts
    fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        session_id: 'panel-abc123',
        moderator_intro: { persona: 'moderator-dr-panel', response: 'Welcome everyone!', mood: 'neutral' },
        panel_responses: [
          { persona_id: 'dr-sigmund-2000', persona_name: 'Dr. Sigmund 2000', response: 'Sigmund here.', mood: 'neutral', references: [], ascii_art: 'S' },
          { persona_id: 'dr-ada-sterling', persona_name: 'Dr. Ada Sterling', response: 'Ada here.', mood: 'thinking', references: [], ascii_art: 'A' },
        ],
        panel_state: { active: true, exchange_count: 1, total_personas: 3, has_moderator: true },
      }),
    });

    await sendMessage();

    // API called correctly
    // @ts-expect-error - mocked in vitest.setup.ts
    expect(fetch).toHaveBeenCalled();
    // @ts-expect-error - mocked in vitest.setup.ts
    const [url, options] = fetch.mock.calls[0];
    expect(url).toBe('/api/panel/start');
    const payload = JSON.parse(options.body);
    expect(payload.message).toBe('Hello panel');
    expect(payload.include_moderator).toBe(true);

    // Rendered messages include moderator + personas
    const labels = Array.from(document.querySelectorAll('.message.bot .message-label')).map((n) => n.textContent);
    expect(labels.some((t) => t.includes('DR. PANEL'))).toBe(true);
    expect(labels.some((t) => t.includes('DR. SIGMUND 2000'))).toBe(true);
    expect(labels.some((t) => t.includes('DR. ADA STERLING'))).toBe(true);

    expect(state.panelSessionId).toBe('panel-abc123');
  });

  it('second panel message calls /api/panel/continue and reset ends panel session', async () => {
    setMode('panel');
    renderPanelConfigCards();
    renderPersonaCards();

    document.querySelector('.panel-config-card').click();
    await startSession();

    const input = document.getElementById('messageInput');

    // First message: start
    input.value = 'Start';
    // @ts-expect-error - mocked in vitest.setup.ts
    fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        session_id: 'panel-xyz789',
        moderator_intro: { persona: 'moderator-dr-panel', response: 'Intro', mood: 'neutral' },
        panel_responses: [
          { persona_id: 'dr-sigmund-2000', persona_name: 'Dr. Sigmund 2000', response: 'One', mood: 'neutral', references: [], ascii_art: 'S' },
          { persona_id: 'dr-ada-sterling', persona_name: 'Dr. Ada Sterling', response: 'Two', mood: 'thinking', references: [], ascii_art: 'A' },
        ],
        panel_state: { active: true, exchange_count: 1, total_personas: 3, has_moderator: true },
      }),
    });

    await sendMessage();
    expect(state.panelSessionId).toBe('panel-xyz789');

    // Second message: continue
    input.value = 'Continue';
    // @ts-expect-error - mocked in vitest.setup.ts
    fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        session_id: 'panel-xyz789',
        panel_responses: [
          { persona_id: 'dr-sigmund-2000', persona_name: 'Dr. Sigmund 2000', response: 'Again', mood: 'amused', references: [], ascii_art: 'S2' },
        ],
        panel_state: { active: true, exchange_count: 2, total_personas: 3, has_moderator: true, should_summarize: false },
      }),
    });

    await sendMessage();

    // Verify continue endpoint call
    // @ts-expect-error - mocked in vitest.setup.ts
    const [url2, options2] = fetch.mock.calls[1];
    expect(url2).toBe('/api/panel/continue');
    const payload2 = JSON.parse(options2.body);
    expect(payload2.session_id).toBe('panel-xyz789');
    expect(payload2.message).toBe('Continue');

    // Reset ends session
    // @ts-expect-error - mocked in vitest.setup.ts
    fetch.mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ success: true }) });
    await resetChat();

    // End endpoint called
    // @ts-expect-error - mocked in vitest.setup.ts
    const [url3] = fetch.mock.calls[2];
    expect(url3).toBe('/api/panel/end');
    expect(state.panelSessionId).toBe(null);

    expect(document.getElementById('chatContainer').textContent).toContain('PANEL SESSION ENDED');
  });
});

