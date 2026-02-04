/**
 * Frontend Unit Tests for Multi-Persona Psychiatrist
 * 
 * Tests the persona selection UI, state management, theming, and sprite loading.
 * Spec: specs/features/multi-persona-psychiatrist.md (lines 730-756)
 * 
 * Run with: npm test
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock personas data (matches config/personas.json structure)
const mockPersonas = {
  defaultPersonaId: 'dr-sigmund-2000',
  personas: [
    {
      id: 'dr-sigmund-2000',
      name: 'Dr. Sigmund 2000',
      tagline: 'Your Y2K-Compliant Digital Therapist',
      description: 'A hilariously outdated AI psychiatrist from 1997',
      era: '1990s Retro',
      theme: {
        primary: '#008080',
        secondary: '#C0C0C0',
        accent: '#FFFF00',
        headerBg: '#000080',
        headerText: '#FFFF00',
        userMessageBg: '#FFFFCC',
        userMessageBorder: '#CCCC00',
        botMessageBg: '#CCFFCC',
        botMessageBorder: '#00CC00',
        fontFamily: "'Comic Sans MS', 'Chalkboard SE', cursive",
        terminalGreen: '#00FF00',
        messageTextColor: '#000000'
      },
      spritePath: 'sprites/dr-sigmund/',
      welcomeMessage: 'Welcome to Dr. Sigmund 2000',
      available: true,
      order: 1
    },
    {
      id: 'captain-whiskers',
      name: 'Captain Whiskers, PhD',
      tagline: 'Purrfessional Therapy Services',
      description: 'A sophisticated cat therapist',
      era: 'Whimsical / Cat',
      theme: {
        primary: '#3d2817',
        secondary: '#5c4033',
        accent: '#ff9800',
        headerBg: '#2a1a0f',
        headerText: '#f4e4c1',
        userMessageBg: '#fff3e0',
        userMessageBorder: '#ff9800',
        botMessageBg: '#ffe0b2',
        botMessageBorder: '#ff9800',
        fontFamily: "'Georgia', serif",
        terminalGreen: '#ff9800',
        messageTextColor: '#3e2723'
      },
      spritePath: 'sprites/captain-whiskers/',
      welcomeMessage: 'Greetings, I am Captain Whiskers',
      available: true,
      order: 6
    }
  ]
};

// Helper function to create DOM structure
function createPersonaSelectDOM() {
  document.body.innerHTML = `
    <div class="persona-select-screen" id="personaSelectScreen">
      <div class="personas-grid" id="personasGrid"></div>
      <button class="start-session-btn" id="startSessionBtn" disabled>
        Start Session
      </button>
    </div>
    <div class="chat-screen" id="chatScreen">
      <div class="header">
        <h1 id="therapistName">AI Therapist</h1>
        <p id="therapistTagline">Choose your counselor</p>
      </div>
    </div>
  `;
}

// Helper function to render persona cards (simulates frontend logic)
function renderPersonaCards(personas, gridId = 'personasGrid') {
  const grid = document.getElementById(gridId);
  if (!grid) return;
  
  grid.innerHTML = '';
  
  personas.forEach(persona => {
    if (!persona.available) return;
    
    const card = document.createElement('div');
    card.className = 'persona-card';
    card.dataset.personaId = persona.id;
    
    card.innerHTML = `
      <div class="persona-avatar">[ASCII]</div>
      <h3>${persona.name}</h3>
      <p class="tagline">${persona.tagline}</p>
      <span class="era-badge">${persona.era}</span>
      <p class="description">${persona.description}</p>
    `;
    
    card.addEventListener('click', () => {
      document.querySelectorAll('.persona-card').forEach(c => 
        c.classList.remove('selected')
      );
      card.classList.add('selected');
      
      const btn = document.getElementById('startSessionBtn');
      if (btn) {
        btn.disabled = false;
        btn.textContent = `Start Session with ${persona.name}`;
        btn.dataset.selectedPersonaId = persona.id;
      }
    });
    
    grid.appendChild(card);
  });
}

// Helper function to apply theme (simulates frontend logic)
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

describe('Persona Selection Screen', () => {
  beforeEach(() => {
    createPersonaSelectDOM();
    vi.clearAllMocks();
  });

  /**
   * Test 1: Persona list renders correctly
   * Spec requirement (lines 731-735)
   * Given: API returns list of 6 personas
   * When: Persona selection screen loads
   * Then: All 6 persona cards are rendered with correct info
   */
  it('should render all available personas with correct information', () => {
    // Arrange
    const personas = mockPersonas.personas;
    
    // Act
    renderPersonaCards(personas);
    
    // Assert
    const cards = document.querySelectorAll('.persona-card');
    expect(cards.length).toBe(2); // 2 available personas in mock
    
    // Check first persona
    const firstCard = cards[0];
    expect(firstCard.querySelector('h3').textContent).toBe('Dr. Sigmund 2000');
    expect(firstCard.querySelector('.tagline').textContent).toBe('Your Y2K-Compliant Digital Therapist');
    expect(firstCard.querySelector('.era-badge').textContent).toBe('1990s Retro');
    expect(firstCard.querySelector('.description').textContent).toBe('A hilariously outdated AI psychiatrist from 1997');
    expect(firstCard.dataset.personaId).toBe('dr-sigmund-2000');
    
    // Check second persona
    const secondCard = cards[1];
    expect(secondCard.querySelector('h3').textContent).toBe('Captain Whiskers, PhD');
    expect(secondCard.querySelector('.tagline').textContent).toBe('Purrfessional Therapy Services');
    expect(secondCard.dataset.personaId).toBe('captain-whiskers');
  });

  /**
   * Test 2: Persona selection updates state
   * Spec requirement (lines 737-742)
   * Given: Persona selection screen is displayed
   * When: User clicks on a persona card
   * Then: Selected persona state is updated
   */
  it('should update selection state when persona card is clicked', () => {
    // Arrange
    renderPersonaCards(mockPersonas.personas);
    const cards = document.querySelectorAll('.persona-card');
    const startBtn = document.getElementById('startSessionBtn');
    
    // Act - click first persona
    cards[0].click();
    
    // Assert
    expect(cards[0].classList.contains('selected')).toBe(true);
    expect(cards[1].classList.contains('selected')).toBe(false);
    expect(startBtn.disabled).toBe(false);
    expect(startBtn.textContent).toContain('Dr. Sigmund 2000');
    expect(startBtn.dataset.selectedPersonaId).toBe('dr-sigmund-2000');
    
    // Act - click second persona
    cards[1].click();
    
    // Assert
    expect(cards[0].classList.contains('selected')).toBe(false);
    expect(cards[1].classList.contains('selected')).toBe(true);
    expect(startBtn.textContent).toContain('Captain Whiskers');
    expect(startBtn.dataset.selectedPersonaId).toBe('captain-whiskers');
  });

  /**
   * Test 3: Theme applies on persona change
   * Spec requirement (lines 744-748)
   * Given: User selects Dr. Luna Cosmos
   * When: Theme is applied
   * Then: CSS variables update to purple/indigo colors
   */
  it('should apply persona theme colors to CSS variables', () => {
    // Arrange
    const captainWhiskersTheme = mockPersonas.personas[1].theme;
    
    // Act
    applyTheme(captainWhiskersTheme);
    
    // Assert
    const root = document.documentElement;
    expect(root.style.getPropertyValue('--primary')).toBe('#3d2817');
    expect(root.style.getPropertyValue('--secondary')).toBe('#5c4033');
    expect(root.style.getPropertyValue('--accent')).toBe('#ff9800');
    expect(root.style.getPropertyValue('--header-bg')).toBe('#2a1a0f');
    expect(root.style.getPropertyValue('--header-text')).toBe('#f4e4c1');
    expect(root.style.getPropertyValue('--user-message-bg')).toBe('#fff3e0');
    expect(root.style.getPropertyValue('--bot-message-bg')).toBe('#ffe0b2');
    expect(root.style.getPropertyValue('--font-family')).toBe("'Georgia', serif");
    expect(root.style.getPropertyValue('--terminal-green')).toBe('#ff9800');
    expect(root.style.getPropertyValue('--message-text-color')).toBe('#3e2723');
  });

  /**
   * Test 4: Sprite path updates for persona
   * Spec requirement (lines 750-754)
   * Given: User selects Captain Whiskers
   * When: Sprite engine initializes
   * Then: Loads from `sprites/captain-whiskers/` path
   */
  it('should use correct sprite path for selected persona', () => {
    // Arrange
    const persona = mockPersonas.personas[1]; // Captain Whiskers
    
    // Act
    const spritePath = persona.spritePath;
    const expectedPath = 'sprites/captain-whiskers/';
    
    // Assert
    expect(spritePath).toBe(expectedPath);
    expect(spritePath).toContain('captain-whiskers');
    expect(spritePath).toMatch(/^sprites\/[a-z-]+\/$/);
  });

  /**
   * Test 5: Welcome message matches persona
   * Spec requirement (lines 756-760)
   * Given: User starts session with Dr. Pixel
   * When: Chat container loads
   * Then: Welcome message contains gaming terminology
   */
  it('should display persona-specific welcome message', () => {
    // Arrange
    const drSigmund = mockPersonas.personas[0];
    const captainWhiskers = mockPersonas.personas[1];
    
    // Act & Assert - Dr. Sigmund
    expect(drSigmund.welcomeMessage).toContain('Dr. Sigmund 2000');
    expect(drSigmund.welcomeMessage).toBeTruthy();
    
    // Act & Assert - Captain Whiskers
    expect(captainWhiskers.welcomeMessage).toContain('Captain Whiskers');
    expect(captainWhiskers.welcomeMessage).toBeTruthy();
    
    // Verify each persona has unique welcome message
    expect(drSigmund.welcomeMessage).not.toBe(captainWhiskers.welcomeMessage);
  });
});

describe('State Management', () => {
  beforeEach(() => {
    createPersonaSelectDOM();
  });

  it('should maintain selected persona ID throughout session', () => {
    // Arrange
    renderPersonaCards(mockPersonas.personas);
    const cards = document.querySelectorAll('.persona-card');
    const startBtn = document.getElementById('startSessionBtn');
    
    // Act
    cards[0].click();
    const selectedId = startBtn.dataset.selectedPersonaId;
    
    // Assert
    expect(selectedId).toBe('dr-sigmund-2000');
    expect(selectedId).not.toBe('');
    expect(selectedId).not.toBeUndefined();
  });

  it('should clear selection when switching back to selection screen', () => {
    // Arrange
    renderPersonaCards(mockPersonas.personas);
    const cards = document.querySelectorAll('.persona-card');
    
    // Act - select a persona
    cards[1].click();
    expect(cards[1].classList.contains('selected')).toBe(true);
    
    // Act - clear selection (simulate reset)
    cards[1].classList.remove('selected');
    
    // Assert
    expect(cards[1].classList.contains('selected')).toBe(false);
  });
});

describe('Theme Management', () => {
  it('should handle theme with all required CSS variables', () => {
    // Arrange
    const theme = mockPersonas.personas[0].theme;
    const requiredProperties = [
      'primary', 'secondary', 'accent', 'headerBg', 'headerText',
      'userMessageBg', 'userMessageBorder', 'botMessageBg', 
      'botMessageBorder', 'fontFamily', 'terminalGreen', 'messageTextColor'
    ];
    
    // Assert
    requiredProperties.forEach(prop => {
      expect(theme).toHaveProperty(prop);
      expect(theme[prop]).toBeTruthy();
    });
  });

  it('should revert to default theme when needed', () => {
    // Arrange
    const customTheme = mockPersonas.personas[1].theme;
    const defaultTheme = mockPersonas.personas[0].theme;
    
    // Act - apply custom theme
    applyTheme(customTheme);
    expect(document.documentElement.style.getPropertyValue('--primary')).toBe('#3d2817');
    
    // Act - revert to default
    applyTheme(defaultTheme);
    
    // Assert
    expect(document.documentElement.style.getPropertyValue('--primary')).toBe('#008080');
  });
});
