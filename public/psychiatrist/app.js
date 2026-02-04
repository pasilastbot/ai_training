// Frontend logic for the Dr. Sigmund 2000 demo app.
// Extended with Panel Mode support (multi-persona discussions).

/* global SpriteEngine */

export const state = {
  // Data
  personas: [],
  panelConfigs: [],

  // Mode
  mode: 'single', // 'single' | 'panel'

  // Single mode selection
  selectedPersonaId: null,
  currentPersona: null,
  chatHistory: [],

  // Panel mode selection + session
  selectedPanelConfigId: null,
  selectedPanelPersonaIds: new Set(),
  panelSessionId: null,
  includeModerator: true,

  // UI/engine
  spriteEngine: null,
  useSpriteMode: true,
};

const MOOD_LABELS = {
  neutral: '*listening*',
  thinking: '*pondering*',
  amused: '*chuckling*',
  concerned: '*worried*',
  shocked: '*surprised*',
};

function el(id) {
  return document.getElementById(id);
}

function safeJsonParse(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

// ============================================
// INITIALIZATION
// ============================================

export async function initApp() {
  await loadPersonas();
  await loadPanelConfigs();

  // Default to single mode
  setMode('single');

  // Random session count
  const visitor = el('visitorCount');
  if (visitor) {
    visitor.textContent = String(Math.floor(Math.random() * 9000) + 1000).padStart(6, '0');
  }
}

if (typeof window !== 'undefined') {
  window.addEventListener('load', async () => {
    // Only auto-init when the app DOM exists
    if (!el('personaSelectScreen')) return;
    await initApp();
  });
}

// ============================================
// MODE TOGGLING
// ============================================

export function setMode(mode) {
  state.mode = mode === 'panel' ? 'panel' : 'single';

  const singleBtn = el('modeSingleBtn');
  const panelBtn = el('modePanelBtn');
  const panelSection = el('panelConfigSection');

  if (singleBtn && panelBtn) {
    singleBtn.classList.toggle('active', state.mode === 'single');
    panelBtn.classList.toggle('active', state.mode === 'panel');
  }

  if (panelSection) {
    panelSection.classList.toggle('hidden', state.mode !== 'panel');
  }

  // Reset selection state when switching modes
  if (state.mode === 'single') {
    state.selectedPanelConfigId = null;
    state.selectedPanelPersonaIds = new Set();
    state.panelSessionId = null;
    state.selectedPersonaId = state.selectedPersonaId || getDefaultPersonaId();
  } else {
    state.selectedPersonaId = null;
    state.currentPersona = null;
    state.chatHistory = [];
  }

  renderPersonaCards();
  renderPanelConfigCards();
  updateStartButton();
}

function getDefaultPersonaId() {
  // defaultPersonaId is returned by /api/personas; we store it in selectedPersonaId initially.
  const fromList = state.personas.find((p) => p.id === 'dr-sigmund-2000');
  return fromList?.id || state.personas[0]?.id || null;
}

// Expose for HTML onclick
if (typeof window !== 'undefined') {
  window.setMode = setMode;
}

// ============================================
// PERSONA LOADING
// ============================================

export async function loadPersonas() {
  try {
    const response = await fetch('/api/personas');
    const data = await response.json();
    state.personas = data.personas || [];
    state.selectedPersonaId = data.defaultPersonaId || getDefaultPersonaId();
    renderPersonaCards();
    updateStartButton();
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Failed to load personas:', error);
    const grid = el('personasGrid');
    if (grid) {
      grid.innerHTML =
        '<p style="color: red; text-align: center;">Failed to load therapists. Please refresh the page.</p>';
    }
  }
}

export function renderPersonaCards() {
  const grid = el('personasGrid');
  if (!grid) return;

  grid.innerHTML = '';

  state.personas.forEach((persona) => {
    const card = document.createElement('div');
    card.className = 'persona-card';

    const isSelected =
      state.mode === 'single'
        ? persona.id === state.selectedPersonaId
        : state.selectedPanelPersonaIds.has(persona.id);

    if (isSelected) card.classList.add('selected');

    card.onclick = () => {
      if (state.mode === 'single') {
        selectPersona(persona.id);
      } else {
        togglePanelPersona(persona.id);
      }
    };

    const asciiPreview = getAsciiPreview(persona);
    card.innerHTML = `
      <div class="persona-avatar" style="color: ${persona.theme?.terminalGreen || '#00FF00'}; border-color: ${persona.theme?.terminalGreen || '#00FF00'};">${asciiPreview}</div>
      <h3>${persona.name}</h3>
      <p class="tagline">"${persona.tagline}"</p>
      <span class="era-badge" style="background: ${persona.theme?.accent || '#e94560'};">${persona.era}</span>
      <p class="description">${persona.description}</p>
    `;

    grid.appendChild(card);
  });
}

function getAsciiPreview(persona) {
  const previewMap = {
    'dr-sigmund-2000': " .---.\n/ o o \\\n|  ~  |\n\\ === /\n '---'",
    'dr-luna-cosmos': "  *  *\n  ◐  \n \\ _ /\n  | |\n *' '*",
    'dr-rex-hardcastle': ' _____\n/     \\\n| -  - |\n|  _  |\n\\_===_/',
    'dr-pixel': ' ╔═══╗\n ║●  ●║\n ║  ▽ ║\n ╚═▀═╝\n  ◄►◄►',
    'dr-ada-sterling': ' ┌───┐\n │◦ ◦│\n │ ‿ │\n └─┬─┘\n  ═══',
    'captain-whiskers': ' /\\_/\\\n( o.o )\n > ^ <\n/|   |\\\n(_|_|_)',
  };
  return previewMap[persona.id] || ' (?)\n (?)\n (?)';
}

function selectPersona(personaId) {
  state.selectedPersonaId = personaId;
  renderPersonaCards();
  updateStartButton();
}

function togglePanelPersona(personaId) {
  // Panel mode supports 2-4 personas
  if (state.selectedPanelPersonaIds.has(personaId)) {
    state.selectedPanelPersonaIds.delete(personaId);
  } else {
    if (state.selectedPanelPersonaIds.size >= 4) return;
    state.selectedPanelPersonaIds.add(personaId);
  }

  // If user manually toggles, clear config selection (custom panel)
  state.selectedPanelConfigId = null;

  renderPersonaCards();
  updateStartButton();
}

function updateStartButton() {
  const btn = el('startSessionBtn');
  if (!btn) return;

  if (state.mode === 'single') {
    if (state.selectedPersonaId) {
      btn.disabled = false;
      const persona = state.personas.find((p) => p.id === state.selectedPersonaId);
      btn.textContent = `Start Session with ${persona?.name || 'Therapist'}`;
    } else {
      btn.disabled = true;
      btn.textContent = 'Select a Therapist';
    }
    return;
  }

  // Panel mode
  const count = state.selectedPanelPersonaIds.size;
  const ok = count >= 2 && count <= 4;
  btn.disabled = !ok;

  if (state.selectedPanelConfigId) {
    const cfg = state.panelConfigs.find((c) => c.id === state.selectedPanelConfigId);
    btn.textContent = ok ? `Start Panel: ${cfg?.name || 'Panel'}` : 'Select 2–4 Therapists';
  } else {
    btn.textContent = ok ? `Start Custom Panel (${count})` : 'Select 2–4 Therapists';
  }
}

// ============================================
// PANEL CONFIG LOADING
// ============================================

export async function loadPanelConfigs() {
  try {
    const response = await fetch('/api/panel/configs');
    const data = await response.json();
    state.panelConfigs = data.configs || [];
    renderPanelConfigCards();
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Failed to load panel configs:', error);
    const grid = el('panelConfigsGrid');
    if (grid) {
      grid.innerHTML =
        '<p style="color: red; text-align: center;">Failed to load panel configs.</p>';
    }
  }
}

export function renderPanelConfigCards() {
  const grid = el('panelConfigsGrid');
  if (!grid) return;

  if (state.mode !== 'panel') {
    grid.innerHTML = '';
    return;
  }

  grid.innerHTML = '';
  if (!state.panelConfigs.length) {
    grid.innerHTML = '<div class="loading-personas">Loading available panels...</div>';
    return;
  }

  state.panelConfigs.forEach((cfg) => {
    const card = document.createElement('div');
    card.className = 'panel-config-card';
    if (cfg.id === state.selectedPanelConfigId) card.classList.add('selected');

    card.onclick = () => selectPanelConfig(cfg.id);

    const members = (cfg.persona_ids || []).length;
    card.innerHTML = `
      <div class="panel-config-title">
        <span class="panel-config-icon">${cfg.icon || '👥'}</span>
        <span class="panel-config-name">${cfg.name}</span>
      </div>
      <div class="panel-config-desc">${cfg.description || ''}</div>
      <div class="panel-config-meta">${members} therapists • ${cfg.best_for || ''}</div>
    `;

    grid.appendChild(card);
  });
}

function selectPanelConfig(configId) {
  state.selectedPanelConfigId = configId;

  const cfg = state.panelConfigs.find((c) => c.id === configId);
  const personaIds = (cfg?.persona_ids || []).slice(0, 4);
  state.selectedPanelPersonaIds = new Set(personaIds);

  renderPanelConfigCards();
  renderPersonaCards();
  updateStartButton();
}

// ============================================
// SESSION START
// ============================================

export async function startSession() {
  if (state.mode === 'panel') {
    return startPanelMode();
  }
  return startSingleMode();
}

async function startSingleMode() {
  if (!state.selectedPersonaId) return;

  // Get full persona details
  try {
    const response = await fetch(`/api/personas/${state.selectedPersonaId}`);
    state.currentPersona = await response.json();
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Failed to load persona details:', error);
    state.currentPersona = state.personas.find((p) => p.id === state.selectedPersonaId);
  }

  applyTheme(state.currentPersona.theme);

  el('therapistName').textContent = state.currentPersona.name;
  el('therapistTagline').innerHTML =
    `~ ${state.currentPersona.tagline} ~ <span class="blink">ONLINE</span>`;
  el('currentPersonaId').textContent = state.currentPersona.id;

  const welcomeHtml = `
    <p><b>Welcome!</b></p>
    <p>${state.currentPersona.welcomeMessage || 'How can I help you today?'}</p>
  `;
  el('welcomeMessage').innerHTML = welcomeHtml;

  if (state.currentPersona.asciiArt && state.currentPersona.asciiArt.neutral) {
    el('asciiArt').textContent = state.currentPersona.asciiArt.neutral;
  }

  document.title = `${state.currentPersona.name} - AI Therapist`;

  el('personaSelectScreen').classList.add('hidden');
  el('chatScreen').classList.add('active');

  await initSpriteEngine(state.currentPersona.spritePath);
  el('messageInput').focus();
}

async function startPanelMode() {
  // Panel mode does not create a backend session until first message.
  const count = state.selectedPanelPersonaIds.size;
  if (count < 2 || count > 4) return;

  state.panelSessionId = null;
  state.chatHistory = [];
  state.currentPersona = null;

  // include moderator checkbox (defaults to true)
  const includeModeratorEl = el('includeModerator');
  state.includeModerator = includeModeratorEl ? includeModeratorEl.checked : true;

  // Reset theme to default (retro)
  applyTheme({
    primary: '#008080',
    secondary: '#C0C0C0',
    accent: '#FFFF00',
    headerBg: '#000080',
    headerText: '#FFFF00',
    fontFamily: "'Comic Sans MS', cursive",
    terminalGreen: '#00FF00',
    messageTextColor: '#000000',
  });

  el('therapistName').textContent = 'Panel Discussion';
  el('therapistTagline').innerHTML = `~ Multi-Persona Panel ~ <span class="blink">ONLINE</span>`;
  el('currentPersonaId').textContent = `panel(${count})`;

  const welcomeHtml = `
    <p><b>Welcome to Panel Mode!</b></p>
    <p>Send your first message to hear multiple perspectives. You can reset to end the panel session.</p>
  `;
  el('welcomeMessage').innerHTML = welcomeHtml;

  // Force ASCII mode (multiple personas)
  switchToAsciiMode();
  el('asciiArt').textContent = '*** PANEL READY ***';

  document.title = `Panel Discussion - AI Therapist`;

  el('personaSelectScreen').classList.add('hidden');
  el('chatScreen').classList.add('active');

  el('messageInput').focus();
}

// Expose for HTML onclick
if (typeof window !== 'undefined') {
  window.startSession = startSession;
}

// ============================================
// THEMING
// ============================================

function applyTheme(theme) {
  if (!theme) return;

  const root = document.documentElement;

  if (theme.primary) root.style.setProperty('--primary', theme.primary);
  if (theme.secondary) root.style.setProperty('--secondary', theme.secondary);
  if (theme.accent) root.style.setProperty('--accent', theme.accent);
  if (theme.headerBg) root.style.setProperty('--header-bg', theme.headerBg);
  if (theme.headerText) root.style.setProperty('--header-text', theme.headerText);
  if (theme.userMessageBg) root.style.setProperty('--user-message-bg', theme.userMessageBg);
  if (theme.userMessageBorder) root.style.setProperty('--user-message-border', theme.userMessageBorder);
  if (theme.botMessageBg) root.style.setProperty('--bot-message-bg', theme.botMessageBg);
  if (theme.botMessageBorder) root.style.setProperty('--bot-message-border', theme.botMessageBorder);
  if (theme.fontFamily) root.style.setProperty('--font-family', theme.fontFamily);
  if (theme.terminalGreen) root.style.setProperty('--terminal-green', theme.terminalGreen);
  if (theme.messageTextColor) root.style.setProperty('--message-text-color', theme.messageTextColor);
}

// ============================================
// SPRITE ENGINE
// ============================================

async function initSpriteEngine(spritePath) {
  state.useSpriteMode = true;
  el('characterContainer').style.display = 'flex';
  el('asciiContainer').classList.remove('active');

  const configPath = `../${spritePath}animations.json`;

  try {
    state.spriteEngine = new SpriteEngine('spriteCanvas', configPath);

    state.spriteEngine.onLoad(() => {
      // eslint-disable-next-line no-console
      console.log('[Game] Sprite engine loaded for', state.currentPersona?.name);
      state.spriteEngine.setMood('neutral');
      state.spriteEngine.play();
      updateSpriteLabel('neutral');
    });

    state.spriteEngine.onError((error) => {
      // eslint-disable-next-line no-console
      console.warn('[Game] Sprite engine failed, using ASCII:', error);
      switchToAsciiMode();
    });

    const success = await state.spriteEngine.init();
    if (!success) switchToAsciiMode();
  } catch (error) {
    // eslint-disable-next-line no-console
    console.warn('[Game] Failed to initialize sprite engine:', error);
    switchToAsciiMode();
  }
}

function switchToAsciiMode() {
  state.useSpriteMode = false;
  el('characterContainer').style.display = 'none';
  el('asciiContainer').classList.add('active');
}

function updateSpriteLabel(mood) {
  const label = el('spriteLabel');
  if (label) label.textContent = MOOD_LABELS[mood] || '*listening*';
}

function updateMood(mood, asciiArt) {
  if (state.useSpriteMode && state.spriteEngine && state.spriteEngine.isReady()) {
    state.spriteEngine.setMood(mood);
    updateSpriteLabel(mood);
  } else {
    updateAsciiArt(asciiArt);
  }
}

function updateAsciiArt(asciiArt) {
  el('asciiArt').textContent = asciiArt;
}

// ============================================
// CHAT FUNCTIONS
// ============================================

export function addMessage(text, isUser, labelOverride = null, variant = null) {
  const container = el('chatContainer');
  const welcome = container.querySelector('.welcome');
  if (welcome) welcome.remove();

  const messageDiv = document.createElement('div');
  if (variant === 'internal') {
    messageDiv.className = 'message internal';
  } else {
    messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
  }

  const labelDiv = document.createElement('div');
  labelDiv.className = 'message-label';

  if (variant === 'internal') {
    const label = labelOverride || 'HOT MIC';
    labelDiv.textContent = `>> [HOT MIC] ${String(label).toUpperCase()}:`;
  } else if (isUser) {
    labelDiv.textContent = '>> YOU:';
  } else {
    const name = labelOverride || state.currentPersona?.name || 'THERAPIST';
    labelDiv.textContent = `>> ${String(name).toUpperCase()}:`;
  }

  const textDiv = document.createElement('div');
  textDiv.className = 'message-text';
  textDiv.textContent = text;

  messageDiv.appendChild(labelDiv);
  messageDiv.appendChild(textDiv);
  container.appendChild(messageDiv);

  container.scrollTop = container.scrollHeight;
}

function setLoading(isLoading) {
  const loading = el('loading');
  const input = el('messageInput');

  if (isLoading) {
    loading.classList.add('active');
    input.disabled = true;
    if (state.useSpriteMode && state.spriteEngine && state.spriteEngine.isReady()) {
      state.spriteEngine.setMood('thinking');
      updateSpriteLabel('thinking');
    }
  } else {
    loading.classList.remove('active');
    input.disabled = false;
    input.focus();
  }
}

function buildPanelStartPayload(message) {
  const payload = {
    message,
    include_moderator: !!state.includeModerator,
  };

  // If a panel config is selected and matches the selected personas exactly, omit persona_ids.
  const cfg = state.panelConfigs.find((c) => c.id === state.selectedPanelConfigId);
  const cfgIds = (cfg?.persona_ids || []).slice(0, 4);
  const selected = Array.from(state.selectedPanelPersonaIds);

  const sameAsCfg =
    cfg &&
    selected.length === cfgIds.length &&
    selected.every((id) => cfgIds.includes(id));

  if (state.selectedPanelConfigId) payload.panel_config = state.selectedPanelConfigId;

  if (!sameAsCfg) {
    payload.persona_ids = selected;
  }

  return payload;
}

export async function sendMessage() {
  const input = el('messageInput');
  const message = input.value.trim();

  if (!message) return;

  addMessage(message, true);
  input.value = '';
  setLoading(true);

  try {
    if (state.mode !== 'panel') {
      // Single persona chat (existing API)
      state.chatHistory.push({ role: 'user', content: message });

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          history: state.chatHistory.slice(-10),
          persona_id: state.selectedPersonaId,
          consult: true,
        }),
      });

      const data = await response.json();

      // Render hot-mic consult transcript if present
      const transcript = data?.consult?.transcript;
      if (Array.isArray(transcript) && transcript.length) {
        for (const line of transcript) {
          const from = line?.from_persona_name || line?.from_persona_id || 'Doctor';
          const to = line?.to_persona_name || line?.to_persona_id || 'Doctor';
          const label = `${from} → ${to}`;
          addMessage(line?.text || '', false, label, 'internal');
        }
      }

      if (data.mood) updateMood(data.mood, data.ascii_art);
      addMessage(data.response, false);
      state.chatHistory.push({ role: 'assistant', content: data.response });
    } else {
      // Panel mode
      const first = !state.panelSessionId;
      const endpoint = first ? '/api/panel/start' : '/api/panel/continue';
      const payload = first
        ? buildPanelStartPayload(message)
        : { session_id: state.panelSessionId, message, skip_personas: [] };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data?.error || `Panel request failed (${response.status})`);
      }

      if (first) state.panelSessionId = data.session_id;

      if (data.moderator_intro?.response) {
        addMessage(data.moderator_intro.response, false, 'Dr. Panel');
      }

      const responses = data.panel_responses || [];
      for (const r of responses) {
        addMessage(r.response, false, r.persona_name);
        if (r.mood || r.ascii_art) {
          updateMood(r.mood || 'neutral', r.ascii_art || '');
        }
      }

      // Optional: auto-summarize when server signals it
      const shouldSummarize = data.panel_state?.should_summarize;
      if (shouldSummarize && state.panelSessionId) {
        await showPanelSummary();
      }
    }
  } catch (error) {
    // eslint-disable-next-line no-console
    console.error('Error:', error);
    addMessage('*CONNECTION ERROR* Please try again.', false, state.mode === 'panel' ? 'SYSTEM' : null);

    if (state.useSpriteMode && state.spriteEngine && state.spriteEngine.isReady()) {
      state.spriteEngine.setMood('shocked');
      updateSpriteLabel('shocked');
    }
  } finally {
    setLoading(false);
  }
}

async function showPanelSummary() {
  const response = await fetch('/api/panel/summarize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: state.panelSessionId }),
  });
  const data = await response.json();
  if (!response.ok) return;

  const summaryText = data?.moderator_summary?.response;
  if (summaryText) addMessage(summaryText, false, 'Dr. Panel');
}

export async function resetChat() {
  // Single mode: local reset + optional backend reset
  if (state.mode !== 'panel') {
    state.chatHistory = [];

    const container = el('chatContainer');
    container.innerHTML = `
      <div class="welcome">
        <p><b>*** SESSION RESET ***</b></p>
        <p>${state.currentPersona?.resetMessage || 'Starting fresh. What would you like to discuss?'}</p>
      </div>
    `;

    if (state.useSpriteMode && state.spriteEngine && state.spriteEngine.isReady()) {
      state.spriteEngine.setMood('neutral');
      updateSpriteLabel('neutral');
    } else if (state.currentPersona?.asciiArt?.neutral) {
      updateAsciiArt(state.currentPersona.asciiArt.neutral);
    }

    try {
      await fetch('/api/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ persona_id: state.selectedPersonaId }),
      });
    } catch {
      // ignore
    }

    return;
  }

  // Panel mode: end the panel session if active, then clear UI
  if (state.panelSessionId) {
    try {
      await fetch('/api/panel/end', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: state.panelSessionId }),
      });
    } catch {
      // ignore
    }
  }

  state.panelSessionId = null;
  const container = el('chatContainer');
  container.innerHTML = `
    <div class="welcome">
      <p><b>*** PANEL SESSION ENDED ***</b></p>
      <p>Send a message to start a new panel discussion.</p>
    </div>
  `;
  updateAsciiArt('*** PANEL READY ***');
}

export function handleKeyPress(event) {
  if (event.key === 'Enter') sendMessage();
}

// Expose for HTML onclick
if (typeof window !== 'undefined') {
  window.sendMessage = sendMessage;
  window.resetChat = resetChat;
  window.handleKeyPress = handleKeyPress;
}

// ============================================
// CHANGE THERAPIST MODAL
// ============================================

export function showChangeConfirmation() {
  el('confirmModal').classList.add('active');
}

export function hideModal() {
  el('confirmModal').classList.remove('active');
}

export async function confirmChangeTherapist() {
  hideModal();

  // End panel session if active
  if (state.mode === 'panel' && state.panelSessionId) {
    try {
      await fetch('/api/panel/end', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: state.panelSessionId }),
      });
    } catch {
      // ignore
    }
  }

  // Reset state
  state.chatHistory = [];
  state.currentPersona = null;
  state.panelSessionId = null;

  if (state.spriteEngine) {
    state.spriteEngine.stop();
    state.spriteEngine = null;
  }

  // Switch screens
  el('chatScreen').classList.remove('active');
  el('personaSelectScreen').classList.remove('hidden');

  // Re-render
  renderPersonaCards();
  renderPanelConfigCards();
  updateStartButton();
}

if (typeof window !== 'undefined') {
  window.showChangeConfirmation = showChangeConfirmation;
  window.confirmChangeTherapist = confirmChangeTherapist;
  window.hideModal = hideModal;
}

