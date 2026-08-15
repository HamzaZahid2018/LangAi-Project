// LangAI Frontend - Main JavaScript

const BACKEND_URL = 'http://localhost:8000';
const API_ENDPOINTS = {
    grammar: '/editor/check-grammar/',
    translate: '/editor/translate/',
    plagiarism: '/editor/check-plagiarism/',
    summarize: '/editor/summarize/',
};

let currentFeature = 'grammar';
let backendConnected = false;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    initializeEventListeners();
    checkBackendStatus();
    setInterval(checkBackendStatus, 5000); // Check every 5 seconds
});

// Theme Management
function initializeTheme() {
    const savedTheme = localStorage.getItem('langai-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeButton(savedTheme);
}

function updateThemeButton(theme) {
    const btn = document.getElementById('themeToggle');
    const icon = btn.querySelector('i');
    const label = btn.querySelector('.theme-label');
    
    if (theme === 'dark') {
        icon.classList.remove('bi-moon-fill');
        icon.classList.add('bi-sun-fill');
        label.textContent = 'Light';
    } else {
        icon.classList.remove('bi-sun-fill');
        icon.classList.add('bi-moon-fill');
        label.textContent = 'Night';
    }
}

document.getElementById('themeToggle')?.addEventListener('click', function() {
    const current = document.documentElement.getAttribute('data-theme');
    const newTheme = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('langai-theme', newTheme);
    updateThemeButton(newTheme);
});

// Event Listeners
function initializeEventListeners() {
    // Feature buttons
    document.querySelectorAll('[data-feature]').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('[data-feature]').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentFeature = this.dataset.feature;
        });
    });

    // Process button
    document.getElementById('processBtn')?.addEventListener('click', processText);

    // Login button
    document.getElementById('loginBtn')?.addEventListener('click', function() {
        const modal = new bootstrap.Modal(document.getElementById('loginModal'));
        modal.show();
    });

    // Character counter
    document.getElementById('inputText')?.addEventListener('input', function() {
        const count = this.value.length;
        document.getElementById('charCount').textContent = count;
        if (count > 10000) {
            this.value = this.value.substring(0, 10000);
        }
    });
}

// Backend Status Check
async function checkBackendStatus() {
    try {
        const response = await fetch(`${BACKEND_URL}/editor/check-grammar/`, {
            method: 'OPTIONS',
            headers: {
                'Content-Type': 'application/json',
            },
        });
        
        backendConnected = true;
        updateBackendStatus(true);
    } catch (error) {
        backendConnected = false;
        updateBackendStatus(false);
    }
}

function updateBackendStatus(connected) {
    const statusText = document.getElementById('statusText');
    const modalStatus = document.getElementById('modalStatus');
    
    if (connected) {
        statusText.innerHTML = '<span class="status-badge connected">✓ Connected</span> - Backend running on localhost:8000';
        if (modalStatus) modalStatus.innerHTML = '<span class="status-badge connected">✓ Connected</span> Backend is ready!';
    } else {
        statusText.innerHTML = '<span class="status-badge disconnected">✗ Disconnected</span> - Make sure backend is running on localhost:8000';
        if (modalStatus) modalStatus.innerHTML = '<span class="status-badge disconnected">✗ Not Connected</span> Start Django server first';
    }
}

// Process Text
async function processText() {
    const inputText = document.getElementById('inputText').value.trim();
    
    if (!inputText) {
        showAlert('Please enter some text', 'warning');
        return;
    }

    if (!backendConnected) {
        showAlert('Backend not connected. Make sure Django server is running on localhost:8000', 'danger');
        return;
    }

    const endpoint = API_ENDPOINTS[currentFeature];
    if (!endpoint) {
        showAlert('Invalid feature selected', 'danger');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${BACKEND_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                text: inputText,
                language: currentFeature === 'translate' ? 'es' : undefined,
            }),
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error('Error:', error);
        showAlert(`Error: ${error.message}`, 'danger');
    } finally {
        hideLoading();
    }
}

// Display Results
function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    let html = '';

    switch (currentFeature) {
        case 'grammar':
            html = formatGrammarResults(data);
            break;
        case 'translate':
            html = formatTranslateResults(data);
            break;
        case 'plagiarism':
            html = formatPlagiarismResults(data);
            break;
        case 'summarize':
            html = formatSummarizeResults(data);
            break;
    }

    resultsDiv.innerHTML = html;
}

function formatGrammarResults(data) {
    if (data.error) {
        return `<div class="alert alert-danger">${data.error}</div>`;
    }

    let html = '<div class="result-item">';
    html += '<h6><i class="bi bi-check-lg me-2"></i>Grammar Check Results</h6>';
    
    if (data.corrected) {
        html += `<div class="result-text"><strong>Corrected:</strong><br>${escapeHtml(data.corrected)}</div>`;
    }
    
    if (data.errors && data.errors.length > 0) {
        html += '<div class="mt-2"><strong>Issues Found:</strong><ul class="small">';
        data.errors.forEach(err => {
            html += `<li>${escapeHtml(err)}</li>`;
        });
        html += '</ul></div>';
    } else {
        html += '<p class="text-success small">✓ No grammar issues found!</p>';
    }
    
    html += '</div>';
    return html;
}

function formatTranslateResults(data) {
    if (data.error) {
        return `<div class="alert alert-danger">${data.error}</div>`;
    }

    let html = '<div class="result-item">';
    html += '<h6><i class="bi bi-translate me-2"></i>Translation Results</h6>';
    
    if (data.translated) {
        html += `<div class="result-text">${escapeHtml(data.translated)}</div>`;
    }
    
    html += '</div>';
    return html;
}

function formatPlagiarismResults(data) {
    if (data.error) {
        return `<div class="alert alert-danger">${data.error}</div>`;
    }

    const similarity = data.similarity_score || 0;
    const percentage = (similarity * 100).toFixed(2);
    const riskLevel = similarity > 0.7 ? 'danger' : similarity > 0.4 ? 'warning' : 'success';

    let html = '<div class="result-item">';
    html += '<h6><i class="bi bi-search me-2"></i>Plagiarism Detection</h6>';
    html += `<div class="alert alert-${riskLevel}">
        <strong>Similarity Score:</strong> ${percentage}%
        <div class="progress mt-2">
            <div class="progress-bar bg-${riskLevel}" style="width: ${percentage}%"></div>
        </div>
    </div>`;
    
    if (data.detected_sources && data.detected_sources.length > 0) {
        html += '<strong class="small">Detected Sources:</strong><ul class="small">';
        data.detected_sources.forEach(source => {
            html += `<li>${escapeHtml(source)}</li>`;
        });
        html += '</ul>';
    }
    
    html += '</div>';
    return html;
}

function formatSummarizeResults(data) {
    if (data.error) {
        return `<div class="alert alert-danger">${data.error}</div>`;
    }

    let html = '<div class="result-item">';
    html += '<h6><i class="bi bi-file-earmark-text me-2"></i>Summary</h6>';
    
    if (data.summary) {
        html += `<div class="result-text">${escapeHtml(data.summary)}</div>`;
    }
    
    if (data.compression_ratio) {
        html += `<p class="small text-muted mt-2">Compression: ${data.compression_ratio}</p>`;
    }
    
    html += '</div>';
    return html;
}

// Utilities
function showLoading() {
    document.getElementById('results').innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary mb-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-muted">Processing your text...</p>
        </div>
    `;
    document.getElementById('processBtn').disabled = true;
}

function hideLoading() {
    document.getElementById('processBtn').disabled = false;
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.insertBefore(alertDiv, document.body.firstChild);
    
    setTimeout(() => alertDiv.remove(), 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Copy to clipboard utility
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Copied to clipboard!', 'success');
    }).catch(() => {
        showAlert('Failed to copy', 'danger');
    });
}
