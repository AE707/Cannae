// Council UI logic for Cannae AI Command Center

document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const agentSelect = document.getElementById('agent-choice');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const messagesContainer = document.getElementById('messages');
    const memoryContainer = document.getElementById('memory-content');

    // State
    let userId = 'user_' + Math.random().toString(36).substr(2, 9);
    let conversationHistory = [];
    let currentAgent = 'ceo'; // Default to CEO

    // Initialize UI
    initializeUI();

    // Event listeners
    agentSelect.addEventListener('change', (e) => {
        currentAgent = e.target.value;
        // Clear input when switching agents
        messageInput.value = '';
        messageInput.placeholder = `Ask the ${currentAgent.toUpperCase()} agent...`;
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await sendMessage();
    });

    // Allow Enter key to send message (Shift+Enter for new line)
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Focus input on load
    messageInput.focus();
});

async function initializeUI() {
    // Load initial memory context
    await loadMemoryContext();

    // Add welcome message
    addMessage(
        'agent',
        `Welcome to Cannae AI Command Center. I'm your ${currentAgent.toUpperCase()} agent. How can I assist you today?`
    );
}

async function sendMessage() {
    const messageText = messageInput.value.trim();
    if (!messageText) return;

    // Disable form during processing
    chatForm.disabled = true;
    messageInput.disabled = true;

    try {
        // Add user message to chat
        addMessage('user', messageText);

        // Clear input
        messageInput.value = '';

        // Show loading indicator
        showLoading(messagesContainer);

        // Call API
        const response = await api.fetchJson('/chat/', {
            method: 'POST',
            body: JSON.stringify({
                user_id: userId,
                message: messageText,
                history: conversationHistory,
                agent_type: currentAgent,
            })
        });

        // Add agent response
        addMessage('agent', response.response);

        // Update conversation history
        conversationHistory = [
            ...conversationHistory,
            { role: 'user', content: messageText },
            { role: 'assistant', content: response.response }
        ];

        // Keep history manageable (last 10 exchanges)
        if (conversationHistory.length > 20) {
            conversationHistory = conversationHistory.slice(-20);
        }

        // Update memory context
        await loadMemoryContext();

    } catch (error) {
        showError(messagesContainer, error.message);
    } finally {
        // Re-enable form
        chatForm.disabled = false;
        messageInput.disabled = false;
        messageInput.focus();

        // Remove loading indicator
        clearElement(messagesContainer);
    }
}

function addMessage(type, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `
        <div class="message-content">${content}</div>
        <div class="message-meta">${type === 'user' ? 'You' : 'Agent'} • ${formatTimestamp(new Date())}</div>
    `;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function loadMemoryContext() {
    try {
        showLoading(memoryContainer);
        const response = await api.fetchJson(`/memory/${userId}?`);

        // Format memory data for display
        let memoryHtml = '<div class="memory-item"><span class="memory-label">Semantic Memories:</span>';
        if (response.semantic && response.semantic.length > 0) {
            memoryHtml += '<ul>';
            response.semantic.slice(0, 5).forEach(item => {
                memoryHtml += `<li>${escapeHtml(item.content || '')}</li>`;
            });
            memoryHtml += '</ul>';
        } else {
            memoryHtml += '<p>No semantic memories found.</p>';
        }
        memoryHtml += '</div>';

        memoryHtml += '<div class="memory-item"><span class="memory-label">Graph Memories:</span>';
        if (response.graph && response.graph.length > 0) {
            memoryHtml += '<ul>';
            response.graph.slice(0, 5).forEach(item => {
                memoryHtml += `<li>${escapeHtml(item.content || '')}</li>`;
            });
            memoryHtml += '</ul>';
        } else {
            memoryHtml += '<p>No graph memories found.</p>';
        }
        memoryHtml += '</div>';

        memoryContainer.innerHTML = memoryHtml;
    } catch (error) {
        showError(memoryContainer, `Failed to load memory: ${error.message}`);
    }
}

// Make functions globally accessible for debugging
window.sendMessage = sendMessage;
window.loadMemoryContext = loadMemoryContext;