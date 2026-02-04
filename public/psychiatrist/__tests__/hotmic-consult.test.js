/**
 * Hot Mic consult frontend tests (jsdom + mocked fetch).
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

import { state, sendMessage } from '../app.js';

function createChatDOM() {
  document.body.innerHTML = `
    <div class="chat-container" id="chatContainer">
      <div class="welcome">Welcome</div>
    </div>
    <div class="loading" id="loading"></div>
    <input id="messageInput" />
    <div id="characterContainer"></div>
    <div id="asciiContainer" class="ascii-container active"></div>
    <pre id="asciiArt"></pre>
    <div id="spriteLabel"></div>
  `;
}

describe('Hot Mic consult (single mode)', () => {
  beforeEach(() => {
    createChatDOM();
    // @ts-expect-error - mocked in vitest.setup.ts
    global.fetch = vi.fn();

    state.mode = 'single';
    state.useSpriteMode = false;
    state.spriteEngine = null;
    state.selectedPersonaId = 'dr-rex-hardcastle';
    state.currentPersona = { id: 'dr-rex-hardcastle', name: 'Dr. Rex Hardcastle', asciiArt: { neutral: 'N' } };
    state.chatHistory = [];
  });

  it('renders consult transcript lines before final doctor reply', async () => {
    document.getElementById('messageInput').value = 'help me sleep';

    // @ts-expect-error - mocked in vitest.setup.ts
    fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        response: 'Final advice to user.',
        mood: 'thinking',
        ascii_art: 'ASCII',
        consult: {
          enabled: true,
          consulted_persona_id: 'dr-ada-sterling',
          consulted_persona_name: 'Dr. Ada Sterling',
          transcript: [
            {
              from_persona_name: 'Dr. Rex Hardcastle',
              to_persona_name: 'Dr. Ada Sterling',
              text: 'Rex -> Ada hot mic line',
            },
            {
              from_persona_name: 'Dr. Ada Sterling',
              to_persona_name: 'Dr. Rex Hardcastle',
              text: 'Ada -> Rex hot mic reply',
            },
          ],
        },
      }),
    });

    await sendMessage();

    // @ts-expect-error - mocked in vitest.setup.ts
    const [, options] = fetch.mock.calls[0];
    const payload = JSON.parse(options.body);
    expect(payload.consult).toBe(true);

    const internal = document.querySelectorAll('.message.internal');
    expect(internal.length).toBe(2);
    expect(internal[0].textContent).toContain('HOT MIC');
    expect(internal[0].textContent).toContain('Rex -> Ada hot mic line');
    expect(internal[1].textContent).toContain('Ada -> Rex hot mic reply');

    const bots = document.querySelectorAll('.message.bot');
    expect(bots.length).toBe(1);
    expect(bots[0].textContent).toContain('Final advice to user.');
  });
});

