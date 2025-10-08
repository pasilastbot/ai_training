/**
 * Chat UI Logic
 */

import { renderMessage, renderFunctionCall, renderFunctionResult, renderGrounding } from './renderer.js';

export class ChatUI {
    constructor(messageListElement, inputElement, sendButtonElement, options = {}) {
        this.messageList = messageListElement;
        this.input = inputElement;
        this.sendButton = sendButtonElement;
        this.options = options;

        this.currentAssistantMessage = null;
        this.assistantMessageBuffer = [];

        this.setupInputHandlers();
    }

    /**
     * Setup input event handlers
     */
    setupInputHandlers() {
        // Auto-resize textarea
        this.input.addEventListener('input', () => {
            this.autoResize();
            this.updateCharCount();
        });

        // Handle Enter key (send) vs Shift+Enter (new line)
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Send button click
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
    }

    /**
     * Auto-resize textarea based on content
     */
    autoResize() {
        this.input.style.height = 'auto';
        this.input.style.height = Math.min(this.input.scrollHeight, 120) + 'px';
    }

    /**
     * Update character count
     */
    updateCharCount() {
        const charCountEl = document.getElementById('charCount');
        if (charCountEl) {
            const count = this.input.value.length;
            charCountEl.textContent = `${count} / 10000`;

            if (count > 9000) {
                charCountEl.style.color = '#EA4335';
            } else {
                charCountEl.style.color = '';
            }
        }
    }

    /**
     * Send message (to be overridden or set via callback)
     */
    sendMessage() {
        const content = this.input.value.trim();
        if (!content) return;

        // Call send callback if provided
        if (this.options.onSend) {
            this.options.onSend(content);
        }

        // Clear input
        this.input.value = '';
        this.autoResize();
        this.updateCharCount();
    }

    /**
     * Add user message to UI
     */
    addUserMessage(content, timestamp = Date.now()) {
        const messageEl = renderMessage({
            role: 'user',
            content: content,
            timestamp: timestamp
        });

        this.appendMessage(messageEl);
        return messageEl;
    }

    /**
     * Start new assistant message
     */
    startAssistantMessage(timestamp = Date.now()) {
        this.assistantMessageBuffer = [];
        this.currentAssistantMessage = renderMessage({
            role: 'assistant',
            content: '',
            timestamp: timestamp
        });

        this.appendMessage(this.currentAssistantMessage);
        return this.currentAssistantMessage;
    }

    /**
     * Append text to current assistant message
     */
    appendToAssistantMessage(text) {
        if (!this.currentAssistantMessage) {
            this.startAssistantMessage();
        }

        this.assistantMessageBuffer.push(text);

        const bubble = this.currentAssistantMessage.querySelector('.message-bubble');
        if (bubble) {
            const fullText = this.assistantMessageBuffer.join('');
            bubble.textContent = fullText;
        }
    }

    /**
     * Complete current assistant message
     */
    completeAssistantMessage() {
        this.currentAssistantMessage = null;
        this.assistantMessageBuffer = [];
    }

    /**
     * Add function call notification
     */
    addFunctionCall(data) {
        const functionCallEl = renderFunctionCall(data);
        this.appendMessage(functionCallEl);
        return functionCallEl;
    }

    /**
     * Add function result
     */
    addFunctionResult(data) {
        const functionResultEl = renderFunctionResult(data);
        this.appendMessage(functionResultEl);
        return functionResultEl;
    }

    /**
     * Add grounding sources
     */
    addGrounding(sources) {
        const groundingEl = renderGrounding(sources);
        this.appendMessage(groundingEl);
        return groundingEl;
    }

    /**
     * Add error message
     */
    addError(message) {
        const errorEl = document.createElement('div');
        errorEl.className = 'error-message';
        errorEl.textContent = `⚠️ ${message}`;
        this.appendMessage(errorEl);
        return errorEl;
    }

    /**
     * Append message element to list
     */
    appendMessage(element) {
        // Remove welcome message if it exists
        const welcome = this.messageList.querySelector('.welcome-message');
        if (welcome) {
            welcome.remove();
        }

        this.messageList.appendChild(element);
        this.scrollToBottom();
    }

    /**
     * Clear all messages
     */
    clearMessages() {
        this.messageList.innerHTML = '';
        this.currentAssistantMessage = null;
        this.assistantMessageBuffer = [];

        // Add welcome message back
        const welcome = document.createElement('div');
        welcome.className = 'welcome-message';
        welcome.innerHTML = `
            <h2>Welcome to Gemini AI Assistant! 👋</h2>
            <p>I'm powered by Google Gemini with access to powerful tools:</p>
            <ul>
                <li>🔍 Web search with grounding</li>
                <li>🎨 Image generation and editing</li>
                <li>🎬 Video generation</li>
                <li>📊 Data indexing and semantic search</li>
                <li>🌐 Web scraping and HTML conversion</li>
                <li>⏰ Date/time utilities</li>
                <li>And more!</li>
            </ul>
            <p><strong>How can I help you today?</strong></p>
        `;
        this.messageList.appendChild(welcome);
    }

    /**
     * Scroll to bottom of message list
     */
    scrollToBottom() {
        setTimeout(() => {
            this.messageList.scrollTop = this.messageList.scrollHeight;
        }, 100);
    }

    /**
     * Show/hide typing indicator
     */
    setTyping(isTyping) {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.style.display = isTyping ? 'flex' : 'none';
        }
    }

    /**
     * Enable/disable input
     */
    setInputEnabled(enabled) {
        this.input.disabled = !enabled;
        this.sendButton.disabled = !enabled;
    }

    /**
     * Format timestamp to readable time
     */
    static formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}
