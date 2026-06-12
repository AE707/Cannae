// Shared utilities for the Cannae frontend

class APIClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    async fetchJson(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers: headers,
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            throw new Error(`API request failed: ${error.message}`);
        }
    }
}

// Initialize API client
const api = new APIClient();

// Utility functions
function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoading(element) {
    element.innerHTML = '<div class="loading">Loading...</div>';
}

function showError(element, message) {
    element.innerHTML = `<div class="error">Error: ${escapeHtml(message)}</div>`;
}

function clearElement(element) {
    element.innerHTML = '';
}

// Export for use in other modules
window.APIClient = APIClient;
window.api = api;
window.formatTimestamp = formatTimestamp;
window.escapeHtml = escapeHtml;
window.showLoading = showLoading;
window.showError = showError;
window.clearElement = clearElement;