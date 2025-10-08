/**
 * Main Application Entry Point
 */

import { WebSocketClient } from './websocket.js';
import { ChatUI } from './chat.js';

// Configuration
const WS_URL = `ws://${window.location.host}/ws/chat`;

// Initialize components
let wsClient;
let chatUI;

/**
 * Initialize application
 */
function init() {
    // Get DOM elements
    const messageList = document.getElementById('messageList');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const statusIndicator = document.getElementById('status');
    const statusText = document.getElementById('statusText');
    const clearButton = document.getElementById('clearButton');

    // Initialize Chat UI
    chatUI = new ChatUI(messageList, messageInput, sendButton, {
        onSend: (content) => {
            if (wsClient && wsClient.isConnected()) {
                wsClient.sendUserMessage(content);
            } else {
                chatUI.addError('Not connected to server. Please refresh the page.');
            }
        }
    });

    // Initialize WebSocket Client
    wsClient = new WebSocketClient(WS_URL);

    // WebSocket event handlers
    wsClient.on('open', () => {
        console.log('Connected to server');
        updateStatus('connected', 'Connected');
        chatUI.setInputEnabled(true);
    });

    wsClient.on('close', () => {
        console.log('Disconnected from server');
        updateStatus('disconnected', 'Disconnected');
        chatUI.setInputEnabled(false);
    });

    wsClient.on('error', (error) => {
        console.error('Connection error:', error);
        updateStatus('disconnected', 'Connection Error');
        chatUI.addError('Connection error occurred');
    });

    wsClient.on('session_created', (data) => {
        console.log('Session created:', data.session_id);
    });

    wsClient.on('user_message_echo', (data) => {
        chatUI.addUserMessage(data.content, data.timestamp);
    });

    wsClient.on('typing', () => {
        chatUI.setTyping(true);
    });

    wsClient.on('assistant_message', (data) => {
        if (data.content && !data.complete) {
            // Start or append to assistant message
            if (!chatUI.currentAssistantMessage) {
                chatUI.startAssistantMessage(data.timestamp);
            }
            chatUI.appendToAssistantMessage(data.content);
        } else if (data.complete) {
            // Complete assistant message
            chatUI.setTyping(false);
            chatUI.completeAssistantMessage();
        }
    });

    wsClient.on('function_call', (data) => {
        chatUI.setTyping(false);
        chatUI.addFunctionCall({
            name: data.function_name,
            args: data.function_args,
            status: data.status
        });
    });

    wsClient.on('function_result', (data) => {
        chatUI.addFunctionResult({
            name: data.function_name,
            success: data.success,
            output: data.output,
            error: data.error
        });
        chatUI.setTyping(true);
    });

    wsClient.on('grounding', (data) => {
        if (data.sources && data.sources.length > 0) {
            chatUI.addGrounding(data.sources);
        }
    });

    wsClient.on('error_message', (data) => {
        chatUI.setTyping(false);
        chatUI.addError(data.error);
    });

    wsClient.on('history_cleared', () => {
        chatUI.clearMessages();
        chatUI.addError('Chat history cleared');
    });

    // Clear button handler
    clearButton.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear the chat history?')) {
            if (wsClient && wsClient.isConnected()) {
                wsClient.clearHistory();
            } else {
                chatUI.clearMessages();
            }
        }
    });

    // Connect to WebSocket
    wsClient.connect();

    /**
     * Update connection status indicator
     */
    function updateStatus(state, text) {
        statusIndicator.className = `status-indicator ${state}`;
        statusText.textContent = text;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
