/**
 * Message Rendering Functions
 */

/**
 * Render a chat message
 */
export function renderMessage(data) {
    const { role, content, timestamp } = data;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    // Avatar
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';

    // Content container
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    // Message bubble
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = content;

    // Timestamp
    const time = document.createElement('div');
    time.className = 'message-time';
    time.textContent = formatTime(timestamp);

    contentDiv.appendChild(bubble);
    contentDiv.appendChild(time);

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);

    return messageDiv;
}

/**
 * Render function call notification
 */
export function renderFunctionCall(data) {
    const { name, args, status } = data;

    const div = document.createElement('div');
    div.className = 'function-call';

    const nameDiv = document.createElement('div');
    nameDiv.className = 'function-call-name';
    nameDiv.innerHTML = `🔧 Executing: <strong>${name}</strong>`;

    div.appendChild(nameDiv);

    if (args && Object.keys(args).length > 0) {
        const argsDiv = document.createElement('div');
        argsDiv.className = 'function-call-args';
        argsDiv.textContent = `Arguments: ${JSON.stringify(args, null, 2)}`;
        div.appendChild(argsDiv);
    }

    return div;
}

/**
 * Render function result
 */
export function renderFunctionResult(data) {
    const { name, success, output, error } = data;

    const div = document.createElement('div');
    div.className = success ? 'function-result' : 'function-result error';

    const nameDiv = document.createElement('div');
    nameDiv.className = 'function-call-name';
    nameDiv.innerHTML = success
        ? `✅ <strong>${name}</strong> completed`
        : `❌ <strong>${name}</strong> failed`;

    div.appendChild(nameDiv);

    if (output) {
        const outputDiv = document.createElement('div');
        outputDiv.className = 'function-call-args';
        outputDiv.textContent = output.substring(0, 500) + (output.length > 500 ? '...' : '');
        div.appendChild(outputDiv);
    }

    if (error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'function-call-args';
        errorDiv.style.color = '#dc3545';
        errorDiv.textContent = `Error: ${error}`;
        div.appendChild(errorDiv);
    }

    return div;
}

/**
 * Render grounding sources
 */
export function renderGrounding(sources) {
    if (!sources || sources.length === 0) {
        return document.createElement('div');
    }

    const div = document.createElement('div');
    div.className = 'grounding-sources';

    const title = document.createElement('h4');
    title.textContent = '📚 Sources:';
    div.appendChild(title);

    sources.forEach((source, index) => {
        const link = document.createElement('a');
        link.className = 'source-link';
        link.href = source.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = `[${index + 1}] ${source.title}`;
        div.appendChild(link);
    });

    return div;
}

/**
 * Format timestamp to readable time
 */
function formatTime(timestamp) {
    if (!timestamp) return '';

    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Parse and render markdown (basic support)
 */
export function parseMarkdown(text) {
    // Basic markdown parsing
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}
