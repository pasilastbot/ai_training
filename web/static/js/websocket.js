/**
 * WebSocket Client for Chat Communication
 */

export class WebSocketClient {
    constructor(url, options = {}) {
        this.url = url;
        this.ws = null;
        this.sessionId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 2000;
        this.listeners = {
            open: [],
            close: [],
            error: [],
            message: [],
            session_created: [],
            user_message_echo: [],
            assistant_message: [],
            function_call: [],
            function_result: [],
            grounding: [],
            typing: [],
            error_message: []
        };
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        try {
            this.ws = new WebSocket(this.url);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.emit('open');

                // Request new session
                this.send({
                    type: 'new_session',
                    timestamp: Date.now()
                });
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                this.emit('close', event);

                // Attempt reconnection
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
                    setTimeout(() => this.connect(), this.reconnectDelay);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('error', error);
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (error) {
                    console.error('Failed to parse message:', error);
                }
            };

        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.emit('error', error);
        }
    }

    /**
     * Handle incoming message
     */
    handleMessage(message) {
        const type = message.type;

        // Store session ID when created
        if (type === 'session_created') {
            this.sessionId = message.session_id;
        }

        // Emit specific event
        this.emit(type, message);

        // Emit general message event
        this.emit('message', message);
    }

    /**
     * Send message to server
     */
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
            return true;
        } else {
            console.error('WebSocket not open. State:', this.ws?.readyState);
            return false;
        }
    }

    /**
     * Send user message
     */
    sendUserMessage(content) {
        if (!this.sessionId) {
            console.error('No session ID available');
            return false;
        }

        return this.send({
            type: 'user_message',
            session_id: this.sessionId,
            content: content,
            timestamp: Date.now()
        });
    }

    /**
     * Clear chat history
     */
    clearHistory() {
        if (!this.sessionId) {
            console.error('No session ID available');
            return false;
        }

        return this.send({
            type: 'clear_history',
            session_id: this.sessionId,
            timestamp: Date.now()
        });
    }

    /**
     * Register event listener
     */
    on(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        } else {
            console.warn(`Unknown event type: ${event}`);
        }
    }

    /**
     * Remove event listener
     */
    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    /**
     * Emit event to all listeners
     */
    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} listener:`, error);
                }
            });
        }
    }

    /**
     * Close connection
     */
    close() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    /**
     * Get connection state
     */
    getState() {
        if (!this.ws) return 'CLOSED';

        switch (this.ws.readyState) {
            case WebSocket.CONNECTING: return 'CONNECTING';
            case WebSocket.OPEN: return 'OPEN';
            case WebSocket.CLOSING: return 'CLOSING';
            case WebSocket.CLOSED: return 'CLOSED';
            default: return 'UNKNOWN';
        }
    }

    /**
     * Check if connected
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}
