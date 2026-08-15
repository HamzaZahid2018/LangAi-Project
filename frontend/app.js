// LangAI Frontend App - Complete Integration

const BACKEND_URL = 'http://localhost:8000';
let currentUser = null;
let currentFeature = 'grammar';
let backendConnected = false;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    checkBackendStatus();
    setInterval(checkBackendStatus, 5000);
    checkAuthStatus();
});

// ============ THEME MANAGEMENT ============
function initializeTheme() {
    const savedTheme = localStorage.getItem('langai-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeButton(savedTheme);
}

document.getElementById('themeToggle')?.addEventListener('click', function() {
    const current = document.documentElement.getAttribute('data-theme');
    const newTheme = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('langai-theme', newTheme);
    updateThemeButton(newTheme);
});

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

// ============ BACKEND STATUS CHECK ============
async function checkBackendStatus() {
    try {
        const response = await fetch(`${BACKEND_URL}/editor/check-grammar/`, {
            method: 'OPTIONS',
            headers: { 'Content-Type': 'application/json' },
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
    if (connected) {
        statusText.innerHTML = '<span class="status-badge connected">✓ Connected</span>';
    } else {
        statusText.innerHTML = '<span class="status-badge disconnected">✗ Disconnected</span>';
    }
}

// ============ AUTHENTICATION ============
async function checkAuthStatus() {
    const token = localStorage.getItem('langai-token');
    const user = localStorage.getItem('langai-user');
    
    if (token && user) {
        currentUser = JSON.parse(user);
        updateUIForLoggedIn();
    } else {
        updateUIForLoggedOut();
    }
}

function updateUIForLoggedIn() {
    document.getElementById('authButtons').style.display = 'none';
    document.getElementById('userDropdown').style.display = 'block';
    document.getElementById('navEditor').style.display = 'block';
    document.getElementById('navDashboard').style.display = 'block';
    document.getElementById('navHistory').style.display = 'block';
    document.getElementById('userName').textContent = currentUser.username;
}

function updateUIForLoggedOut() {
    document.getElementById('authButtons').style.display = 'block';
    document.getElementById('userDropdown').style.display = 'none';
    document.getElementById('navEditor').style.display = 'none';
    document.getElementById('navDashboard').style.display = 'none';
    document.getElementById('navHistory').style.display = 'none';
    goHome();
}

// ============ AUTH FUNCTIONS ============
async function login() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showMessage('loginMessage', 'Please enter username and password', 'danger');
        return;
    }

    if (!backendConnected) {
        showMessage('loginMessage', 'Backend not connected', 'danger');
        return;
    }

    try {
        const response = await fetch(`${BACKEND_URL}/accounts/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('langai-token', data.token || 'authenticated');
            localStorage.setItem('langai-user', JSON.stringify(data.user || { username }));
            currentUser = data.user || { username };
            updateUIForLoggedIn();
            showEditor();
        } else {
            showMessage('loginMessage', 'Invalid username or password', 'danger');
        }
    } catch (error) {
        showMessage('loginMessage', 'Connection error: ' + error.message, 'danger');
    }
}

async function register() {
    const firstName = document.getElementById('regFirstName').value.trim();
    const lastName = document.getElementById('regLastName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const username = document.getElementById('regUsername').value.trim();
    const password = document.getElementById('regPassword').value;

    if (!firstName || !email || !username || !password) {
        showMessage('registerMessage', 'Please fill all fields', 'danger');
        return;
    }

    if (password.length < 8) {
        showMessage('registerMessage', 'Password must be at least 8 characters', 'danger');
        return;
    }

    if (!backendConnected) {
        showMessage('registerMessage', 'Backend not connected', 'danger');
        return;
    }

    try {
        const response = await fetch(`${BACKEND_URL}/accounts/register/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                first_name: firstName,
                last_name: lastName,
                email,
                username,
                password
            }),
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('langai-token', data.token || 'authenticated');
            localStorage.setItem('langai-user', JSON.stringify(data.user || { username }));
            currentUser = data.user || { username };
            updateUIForLoggedIn();
            showEditor();
        } else {
            const error = await response.json();
            showMessage('registerMessage', error.message || 'Registration failed', 'danger');
        }
    } catch (error) {
        showMessage('registerMessage', 'Connection error: ' + error.message, 'danger');
    }
}

function logout() {
    localStorage.removeItem('langai-token');
    localStorage.removeItem('langai-user');
    currentUser = null;
    updateUIForLoggedOut();
}

// ============ PAGE NAVIGATION ============
function hideAllPages() {
    document.querySelectorAll('.page-content').forEach(page => {
        page.style.display = 'none';
    });
}

function goHome() {
    hideAllPages();
    document.getElementById('homePage').style.display = 'block';
}

function showLogin() {
    hideAllPages();
    document.getElementById('loginPage').style.display = 'block';
    document.getElementById('loginUsername').focus();
}

function showRegister() {
    hideAllPages();
    document.getElementById('registerPage').style.display = 'block';
    document.getElementById('regFirstName').focus();
}

function showEditor() {
    if (!currentUser) {
        showLogin();
        return;
    }
    hideAllPages();
    document.getElementById('editorPage').style.display = 'block';
}

function showDashboard() {
    if (!currentUser) {
        showLogin();
        return;
    }
    hideAllPages();
    document.getElementById('dashboardPage').style.display = 'block';
    loadDashboard();
}

function showHistory() {
    if (!currentUser) {
        showLogin();
        return;
    }
    hideAllPages();
    document.getElementById('historyPage').style.display = 'block';
    loadHistory();
}

// ============ EDITOR FUNCTIONS ============
function setFeature(btn) {
    document.querySelectorAll('[data-feature]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFeature = btn.dataset.feature;
}

document.getElementById('inputText')?.addEventListener('input', updateCharCount);

function updateCharCount() {
    const count = document.getElementById('inputText').value.length;
    document.getElementById('charCount').textContent = count;
}

async function processText() {
    const text = document.getElementById('inputText').value.trim();

    if (!text) {
        showAlert('Please enter some text', 'warning');
        return;
    }

    if (!backendConnected) {
        showAlert('Backend not connected', 'danger');
        return;
    }

    if (!currentUser) {
        showLogin();
        return;
    }

    const endpoints = {
        grammar: '/editor/check-grammar/',
        translate: '/editor/translate/',
        plagiarism: '/editor/check-plagiarism/',
        summarize: '/editor/summarize/',
    };

    const endpoint = endpoints[currentFeature];
    if (!endpoint) return;

    showLoading();

    try {
        const response = await fetch(`${BACKEND_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ text }),
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            displayResults(data);
        } else {
            showAlert('Error processing text', 'danger');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    let html = '';

    if (data.error) {
        html = `<div class="alert alert-danger">${data.error}</div>`;
    } else {
        html = '<div class="result-item">';

        switch (currentFeature) {
            case 'grammar':
                html += '<h6><i class="bi bi-check-lg me-2"></i>Grammar Check</h6>';
                html += `<div class="result-text">${escapeHtml(data.corrected || data.output_text || 'No corrections needed')}</div>`;
                break;
            case 'translate':
                html += '<h6><i class="bi bi-translate me-2"></i>Translation</h6>';
                html += `<div class="result-text">${escapeHtml(data.translated || data.output_text || 'Translation failed')}</div>`;
                break;
            case 'plagiarism':
                const score = (data.similarity_score * 100).toFixed(2);
                html += '<h6><i class="bi bi-search me-2"></i>Plagiarism Check</h6>';
                html += `<div class="alert alert-info">${score}% Similarity Detected</div>`;
                break;
            case 'summarize':
                html += '<h6><i class="bi bi-file-earmark-text me-2"></i>Summary</h6>';
                html += `<div class="result-text">${escapeHtml(data.summary || data.output_text || 'Summary generation failed')}</div>`;
                break;
        }

        html += '</div>';
    }

    resultsDiv.innerHTML = html;
}

async function saveDocument() {
    if (!currentUser) {
        showLogin();
        return;
    }

    const title = prompt('Enter document title:');
    if (!title) return;

    const text = document.getElementById('inputText').value;

    try {
        const response = await fetch(`${BACKEND_URL}/editor/save-document/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({ title, content: text }),
            credentials: 'include'
        });

        if (response.ok) {
            showAlert('Document saved successfully!', 'success');
            document.getElementById('inputText').value = '';
            updateCharCount();
        } else {
            showAlert('Failed to save document', 'danger');
        }
    } catch (error) {
        showAlert('Error: ' + error.message, 'danger');
    }
}

// ============ DASHBOARD ============
async function loadDashboard() {
    try {
        const response = await fetch(`${BACKEND_URL}/editor/dashboard/`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById('totalDocs').textContent = data.total_docs || 0;
            document.getElementById('totalOps').textContent = data.total_operations || 0;
            document.getElementById('grammarCount').textContent = data.grammar_count || 0;
            document.getElementById('translateCount').textContent = data.translate_count || 0;
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// ============ HISTORY ============
async function loadHistory() {
    try {
        const response = await fetch(`${BACKEND_URL}/editor/history/`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            const historyList = document.getElementById('historyList');
            
            if (data.history && data.history.length > 0) {
                historyList.innerHTML = data.history.map(item => `
                    <div class="result-item">
                        <h6>${item.operation}</h6>
                        <small class="text-muted">${item.timestamp}</small>
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// ============ UTILITIES ============
function showLoading() {
    document.getElementById('results').innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary mb-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="text-muted">Processing...</p>
        </div>
    `;
}

function hideLoading() {
    // Results will be displayed by displayResults()
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 80px; right: 20px; z-index: 1000; max-width: 400px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 4000);
}

function showMessage(elementId, message, type) {
    const div = document.getElementById(elementId);
    div.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
