// LangAI Frontend - Static Version
let currentFeature = 'grammar';

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    setupEventListeners();
});

// ============ THEME ============
function initializeTheme() {
    const savedTheme = localStorage.getItem('langai-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

document.getElementById('themeToggle')?.addEventListener('click', function() {
    const current = document.documentElement.getAttribute('data-theme');
    const newTheme = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('langai-theme', newTheme);
    
    const icon = this.querySelector('i');
    if (newTheme === 'dark') {
        icon.classList.remove('bi-moon-fill');
        icon.classList.add('bi-sun-fill');
    } else {
        icon.classList.remove('bi-sun-fill');
        icon.classList.add('bi-moon-fill');
    }
});

// ============ PAGE NAVIGATION ============
function showPage(pageName) {
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(page => {
        page.style.display = 'none';
    });
    
    // Show selected page
    const page = document.getElementById(pageName + 'Page');
    if (page) {
        page.style.display = 'block';
        window.scrollTo(0, 0);
    }
}

// ============ EVENT LISTENERS ============
function setupEventListeners() {
    // Character counter
    const editorInput = document.getElementById('editorInput');
    if (editorInput) {
        editorInput.addEventListener('input', function() {
            const count = this.value.length;
            document.getElementById('charCount').textContent = count;
            
            if (count > 10000) {
                this.value = this.value.substring(0, 10000);
            }
        });
    }
}

// ============ EDITOR FUNCTIONS ============
function setFeature(feature, btn) {
    currentFeature = feature;
    
    // Update button states
    document.querySelectorAll('[data-feature]').forEach(b => {
        b.classList.remove('active');
    });
    btn.classList.add('active');
}

function processText() {
    const text = document.getElementById('editorInput').value.trim();
    
    if (!text) {
        showNotification('Please enter some text', 'warning');
        return;
    }
    
    // Simulate processing
    showNotification('Processing...', 'info');
    
    setTimeout(() => {
        let result = '';
        
        switch(currentFeature) {
            case 'grammar':
                result = generateGrammarResult(text);
                break;
            case 'translate':
                result = generateTranslateResult(text);
                break;
            case 'plagiarism':
                result = generatePlagiarismResult(text);
                break;
            case 'summarize':
                result = generateSummaryResult(text);
                break;
        }
        
        displayResults(result);
        showNotification('Processing complete!', 'success');
    }, 800);
}

function displayResults(result) {
    document.getElementById('resultsPanel').innerHTML = result;
}

function generateGrammarResult(text) {
    const corrected = text
        .replace(/thier/gi, 'their')
        .replace(/recieve/gi, 'receive')
        .replace(/occured/gi, 'occurred')
        .replace(/basicly/gi, 'basically');
    
    return `
        <div class="mb-3">
            <h6><i class="bi bi-check-lg text-success me-2"></i>Grammar Check</h6>
            <hr class="my-2">
            <p class="mb-2"><strong>Corrected:</strong></p>
            <div class="alert alert-success py-2 px-3" style="font-size: 0.9rem;">
                ${escapeHtml(corrected)}
            </div>
            <p class="small text-muted"><i class="bi bi-info-circle me-1"></i>3 grammar issues found and corrected.</p>
        </div>
    `;
}

function generateTranslateResult(text) {
    const languages = {
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'pt': 'Portuguese',
        'it': 'Italian',
        'ja': 'Japanese',
        'zh': 'Chinese',
        'ar': 'Arabic',
        'ru': 'Russian',
        'hi': 'Hindi',
        'ur': 'Urdu'
    };
    
    const langList = Object.keys(languages).slice(0, 5)
        .map(lang => `<span class="badge bg-light text-dark me-2 mb-2">${languages[lang]}</span>`)
        .join('');
    
    return `
        <div class="mb-3">
            <h6><i class="bi bi-translate text-info me-2"></i>Translation</h6>
            <hr class="my-2">
            <p class="small mb-2"><strong>Available Languages:</strong></p>
            <div class="mb-3">
                ${langList}
            </div>
            <div class="alert alert-info py-2 px-3" style="font-size: 0.85rem;">
                <strong>Spanish:</strong> [Translated text would appear here]
            </div>
            <p class="small text-muted"><i class="bi bi-info-circle me-1"></i>Select a language to translate</p>
        </div>
    `;
}

function generatePlagiarismResult(text) {
    const similarity = Math.random() * 0.3;
    const percentage = (similarity * 100).toFixed(1);
    const riskLevel = similarity > 0.2 ? 'warning' : 'success';
    
    return `
        <div class="mb-3">
            <h6><i class="bi bi-search text-warning me-2"></i>Plagiarism Check</h6>
            <hr class="my-2">
            <div class="alert alert-${riskLevel} py-3 px-3 text-center">
                <div class="fs-4 fw-bold">${percentage}%</div>
                <small>Similarity Detected</small>
            </div>
            <div class="progress mb-3" style="height: 8px;">
                <div class="progress-bar bg-${riskLevel}" style="width: ${percentage}%"></div>
            </div>
            <p class="small text-muted"><i class="bi bi-info-circle me-1"></i>${similarity > 0.2 ? 'Please review matched sources' : 'Low plagiarism risk - Content is unique'}</p>
        </div>
    `;
}

function generateSummaryResult(text) {
    const sentences = text.split('.').filter(s => s.trim().length > 0);
    const summaryLength = Math.max(1, Math.ceil(sentences.length * 0.4));
    const summary = sentences.slice(0, summaryLength).join('. ') + '.';
    const compressionRatio = ((1 - summary.length / text.length) * 100).toFixed(1);
    
    return `
        <div class="mb-3">
            <h6><i class="bi bi-file-text text-primary me-2"></i>Summary</h6>
            <hr class="my-2">
            <div class="alert alert-primary py-2 px-3" style="font-size: 0.9rem;">
                ${escapeHtml(summary)}
            </div>
            <p class="small text-muted">
                <i class="bi bi-info-circle me-1"></i>Compression: <strong>${compressionRatio}%</strong>
            </p>
        </div>
    `;
}

function downloadText() {
    const text = document.getElementById('editorInput').value;
    
    if (!text) {
        showNotification('Nothing to download', 'warning');
        return;
    }
    
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
    element.setAttribute('download', 'document.txt');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    
    showNotification('Downloaded successfully!', 'success');
}

// ============ UTILITIES ============
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 100px; right: 20px; z-index: 1000; max-width: 400px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => alertDiv.remove(), 3000);
}
