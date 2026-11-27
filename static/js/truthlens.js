/**
 * TRUTHLENS AI — NEON EDITORIAL INTELLIGENCE
 * Gen-Z Futuristic Editorial Client Controller
 */

// Application State
const state = {
    currentTab: 'dashboard',
    currentUser: { username: 'TruthLens User', role: 'guest' },
    currentReport: null,
    currentResultKind: null,
    currentResultFileName: '',
    currentArticleReport: null,
    currentArticleText: '',
    currentHistoryRecord: null,
    inputType: 'text',
    fileType: '',
    ocrText: '',
    ocrLanguage: 'eng',
    imageAuthenticity: {},
    weeklyChart: null,
    categoryChart: null,
    inputMode: 'text' // 'text', 'url', 'image'
};
let activeNavigationTab = 'dashboard';
let articleUploadFile = null;
let articleUploadHeadline = '';
let selectedPostScreenshot = null;
let selectedFakeImage = null;

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initLanguage();
    setupNavigation();
    setupInputModes();
    setupDropZone();
    setupArticleUploader();
    setupMouseSpotlight();
    setupMagneticButtons();
    initIntersectionObservers();
    
    // Initial data hydration
    loadDashboard();

    // Check URL parameters for direct view or record id
    const urlParams = new URLSearchParams(window.location.search);
    const viewParam = urlParams.get('tab');
    if (viewParam) {
        switchTab(viewParam);
    }
});

/* ==========================================================================
   Interactive Background Spotlight & Micro-Interactions
   ========================================================================== */

function setupMouseSpotlight() {
    const spotlight = document.querySelector('.mouse-spotlight');
    if (!spotlight) return;

    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let currentX = mouseX;
    let currentY = mouseY;

    window.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    function renderSpotlight() {
        currentX += (mouseX - currentX) * 0.1;
        currentY += (mouseY - currentY) * 0.1;
        spotlight.style.left = `${currentX}px`;
        spotlight.style.top = `${currentY}px`;
        requestAnimationFrame(renderSpotlight);
    }
    requestAnimationFrame(renderSpotlight);
}

function setupMagneticButtons() {
    document.querySelectorAll('.btn-cta-lime, .btn-primary-analyze').forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            btn.style.transform = `translate(${x * 0.15}px, ${y * 0.15}px) scale(1.02)`;
        });

        btn.addEventListener('mouseleave', () => {
            btn.style.transform = '';
        });
    });
}

/* Number Count-Up Animation */
function animateValue(element, start, end, duration = 1200, suffix = '') {
    if (!element) return;
    const isDecimal = end.toString().includes('.');
    const decimalPlaces = isDecimal ? end.toString().split('.')[1].length : 0;
    const range = end - start;
    let startTime = null;

    function step(timestamp) {
        if (!startTime) startTime = timestamp;
        const progress = Math.min((timestamp - startTime) / duration, 1);
        const easeOutProgress = 1 - Math.pow(1 - progress, 3); // Cubic ease out
        const current = start + range * easeOutProgress;

        element.textContent = (isDecimal ? current.toFixed(decimalPlaces) : Math.floor(current).toLocaleString()) + suffix;

        if (progress < 1) {
            requestAnimationFrame(step);
        } else {
            element.textContent = (isDecimal ? end.toFixed(decimalPlaces) : end.toLocaleString()) + suffix;
        }
    }
    requestAnimationFrame(step);
}

function initIntersectionObservers() {
    if (!('IntersectionObserver' in window)) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const targetVal = parseFloat(el.getAttribute('data-count-target'));
                const suffix = el.getAttribute('data-count-suffix') || '';
                if (!isNaN(targetVal)) {
                    animateValue(el, 0, targetVal, 1400, suffix);
                    observer.unobserve(el);
                }
            }
        });
    }, { threshold: 0.2 });

    document.querySelectorAll('[data-count-target]').forEach(el => observer.observe(el));
}

/* ==========================================================================
   Theme & Navigation Controls
   ========================================================================== */

function initTheme() {
    const storedTheme = localStorage.getItem('eon_theme') || localStorage.getItem('truthlens_theme');
    const savedTheme = storedTheme === 'light' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeButtonText(savedTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('eon_theme', next);
    localStorage.setItem('truthlens_theme', next);
    updateThemeButtonText(next);
}

function updateThemeButtonText(theme) {
    const btn = document.getElementById('themeToggleBtn');
    const label = document.getElementById('themeToggleLabel');
    const key = theme === 'dark' ? 'themeLight' : 'themeDark';
    if (label) label.textContent = t(key);
    if (btn) btn.setAttribute('aria-label', t(key));
}

function currentLanguage() {
    return document.documentElement.getAttribute('lang') || 'en';
}

function t(key) {
    const language = currentLanguage();
    const translations = window.EON_TRANSLATIONS || {};
    return (translations[language] && translations[language][key])
        || (translations.en && translations.en[key])
        || key;
}

function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (key) element.textContent = t(key);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        if (key) element.setAttribute('placeholder', t(key));
    });
    document.querySelectorAll('[data-i18n-title]').forEach(element => {
        const key = element.getAttribute('data-i18n-title');
        if (key) element.setAttribute('title', t(key));
    });
    updateThemeButtonText(document.documentElement.getAttribute('data-theme') || 'dark');
    if (state.currentReport && state.currentResultKind) {
        renderSimpleScanResult(state.currentResultKind, state.currentReport, state.currentResultFileName, false);
    }
    if (state.currentArticleReport && state.currentResultKind !== 'article') {
        renderArticleAnalysisEnhancements(state.currentArticleReport, state.currentArticleText);
    }
    if (state.currentHistoryRecord) renderHistoryDetail(state.currentHistoryRecord);
}

function initLanguage() {
    const available = window.EON_TRANSLATIONS || {};
    const saved = localStorage.getItem('eon_language') || 'en';
    const language = Object.prototype.hasOwnProperty.call(available, saved) ? saved : 'en';
    document.documentElement.setAttribute('lang', language);
    document.documentElement.setAttribute('dir', language === 'ar' ? 'rtl' : 'ltr');
    const selector = document.getElementById('languageSelector');
    if (selector) {
        selector.value = language;
        selector.addEventListener('change', () => {
            const selected = Object.prototype.hasOwnProperty.call(available, selector.value) ? selector.value : 'en';
            document.documentElement.setAttribute('lang', selected);
            document.documentElement.setAttribute('dir', selected === 'ar' ? 'rtl' : 'ltr');
            localStorage.setItem('eon_language', selected);
            applyTranslations();
            loadDashboard();
            if (state.currentTab === 'history') loadHistoryPage();
        });
    }
    applyTranslations();
}

function setupNavigation() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabTarget = btn.getAttribute('data-tab');
            switchTab(tabTarget);
            closeMobileSidebar();
        });
    });

    const mobileBtn = document.getElementById('mobileMenuBtn');
    if (mobileBtn) {
        mobileBtn.addEventListener('click', toggleMobileSidebar);
    }
}

function toggleMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.toggle('mobile-open');
}

function closeMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.remove('mobile-open');
}

function switchTab(tabId) {
    const availableTabs = ['dashboard', 'articles', 'fake-posts', 'fake-images', 'history'];
    if (!availableTabs.includes(tabId)) tabId = 'dashboard';
    state.currentTab = tabId;
    activeNavigationTab = tabId;

    document.querySelectorAll('.nav-item').forEach(item => {
        const btn = item.querySelector('.nav-btn');
        if (btn && btn.getAttribute('data-tab') === activeNavigationTab) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    document.querySelectorAll('.tab-content').forEach(content => {
        if (content.id === `tab-${tabId}`) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });

    if (tabId === 'history') loadHistoryPage();
}

async function loadDashboard() {
    try {
        const [statsResponse, historyResponse] = await Promise.all([
            fetch('/api/dashboard/stats'),
            fetch('/api/history?limit=6')
        ]);
        if (!statsResponse.ok || !historyResponse.ok) throw new Error('Dashboard data could not be loaded.');
        const statsData = await statsResponse.json();
        const historyData = await historyResponse.json();
        const stats = statsData.stats || {};
        const setText = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        };
        setText('dashTotal', stats.total_analyzed || 0);
        setText('dashFake', stats.likely_fake || 0);
        setText('dashReal', stats.likely_real || 0);
        setText('dashUnverified', stats.needs_verification || 0);
        renderScanDistribution(stats);
        const recent = document.getElementById('dashRecentTable');
        if (recent) recent.innerHTML = renderHistoryTable(historyData.history || []);
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function renderScanDistribution(stats) {
    const chart = document.getElementById('scanDistributionChart');
    if (!chart) return;

    const entries = [
        { key: 'likelyFake', count: Number(stats.likely_fake) || 0, className: 'fake' },
        { key: 'likelyReal', count: Number(stats.likely_real) || 0, className: 'real' },
        { key: 'unverified', count: Number(stats.needs_verification) || 0, className: 'unverified' }
    ];
    const total = entries.reduce((sum, entry) => sum + Math.max(0, entry.count), 0);
    chart.innerHTML = entries.map(entry => {
        const count = Math.max(0, Math.floor(entry.count));
        const percentage = total ? (count / total) * 100 : 0;
        const label = escapeHTML(t(entry.key));
        return `<div class="scan-distribution-row" role="listitem" aria-label="${label}: ${count}">
            <div class="scan-distribution-label"><span>${label}</span><strong>${count.toLocaleString(currentLanguage())}</strong></div>
            <div class="scan-distribution-track" aria-hidden="true"><span class="scan-distribution-bar ${entry.className}" style="width:${percentage.toFixed(2)}%"></span></div>
        </div>`;
    }).join('');
}

function escapeHTML(value) {
    return String(value || '').replace(/[&<>"']/g, character => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[character]));
}

async function loadHistoryPage() {
    const container = document.getElementById('historyRecords');
    if (!container) return;
    try {
        const response = await fetch('/api/history?limit=100');
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || 'History could not be loaded.');
        container.innerHTML = renderHistoryTable(data.history || []);
    } catch (error) {
        container.innerHTML = `<tr><td colspan="5">${escapeHTML(error.message)}</td></tr>`;
    }
}

function renderHistoryTable(records) {
    if (!records.length) return `<tr><td colspan="5">${escapeHTML(t('emptyHistory'))}</td></tr>`;
    return records.map(item => {
        const verdictKey = predictionKey(item);
        const inputKeys = {
            text: 'typeText',
            url: 'typeUrl',
            document: 'typeDocument',
            image: 'typeImage',
            social_post: 'typePost'
        };
        const fileName = item.file_type || item.title || t('untitledScan');
        const contentType = t(inputKeys[item.input_type] || 'typeText');
        const scanDate = item.scan_datetime || item.created_at || '';
        return `<tr>
            <td>${escapeHTML(fileName)}</td>
            <td>${escapeHTML(contentType)}</td>
            <td>${escapeHTML(scanDate)}</td>
            <td><span class="simple-table-verdict ${verdictKey}">${escapeHTML(t(verdictKey))}</span></td>
            <td><button class="btn-secondary simple-view-button" type="button" onclick="viewHistoryItem(${Number(item.id)})">${escapeHTML(t('viewResult'))}</button></td>
        </tr>`;
    }).join('');
}

function predictionKey(report) {
    const prediction = String(report.prediction || report.classification || '').toUpperCase();
    if (prediction === 'FAKE' || prediction.includes('LIKELY FAKE')) return 'likelyFake';
    if (prediction === 'REAL' || prediction.includes('LIKELY REAL')) return 'likelyReal';
    return 'unverified';
}

function explanationForPrediction(report) {
    if (report.fact_check_summary) return report.fact_check_summary;
    if (report.image_authenticity?.model_available === false) return t('imageUnavailable');
    const key = predictionKey(report);
    if (key === 'likelyFake') return t('fakeExplanation');
    if (key === 'likelyReal') return t('realExplanation');
    return t('unverifiedExplanation');
}

async function viewHistoryItem(recordId) {
    try {
        const response = await fetch(`/api/history/${recordId}`);
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || 'Analysis record not found.');
        const item = data.record;
        state.currentHistoryRecord = item;
        renderHistoryDetail(item);
        switchTab('history');
        document.getElementById('historyResultDetails')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function renderHistoryDetail(item) {
    const verdictKey = predictionKey(item);
    const fileName = document.getElementById('historyDetailFileName');
    const verdict = document.getElementById('historyDetailVerdict');
    const explanation = document.getElementById('historyDetailExplanation');
    const details = document.getElementById('historyResultDetails');
    if (fileName) fileName.textContent = item.file_type || item.title || t('untitledScan');
    if (verdict) {
        verdict.textContent = t(verdictKey);
        verdict.className = `simple-result-verdict ${verdictKey}`;
    }
    if (explanation) explanation.textContent = explanationForPrediction(item);
    if (details) details.hidden = false;
}

function closeHistoryDetail() {
    const details = document.getElementById('historyResultDetails');
    if (details) details.hidden = true;
    state.currentHistoryRecord = null;
}

async function deleteHistoryRecord(recordId) {
    if (!window.confirm(t('delete') + ' this analysis from your history?')) return;
    try {
        const response = await fetch(`/api/history/${recordId}`, { method: 'DELETE' });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || 'Could not delete the record.');
        await loadHistoryPage();
        await loadDashboard();
        showToast(t('delete') + ' — ' + t('history'), 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

/* Scroll directly to the News Ingestion Box from Hero CTA */
function scrollToVerification() {
    const box = document.getElementById('newsVerificationBox');
    if (box) {
        box.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Pulse effect
        box.style.boxShadow = '0 0 50px rgba(213, 255, 85, 0.4)';
        setTimeout(() => box.style.boxShadow = '', 1500);
    }
}

/* ==========================================================================
   Input Modes & Article Ingestion
   ========================================================================== */

function setupInputModes() {
    document.querySelectorAll('.input-mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.input-mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const mode = btn.getAttribute('data-mode');
            state.inputMode = mode;
            state.inputType = mode === 'image' ? 'image' : mode;

            document.querySelectorAll('.input-mode-view').forEach(view => {
                view.classList.remove('active');
            });

            const targetView = document.getElementById(`mode-view-${mode}`);
            if (targetView) targetView.classList.add('active');
        });
    });
}

function setupDropZone() {
    const dropZone = document.getElementById('imageDropZone');
    const fileInput = document.getElementById('imageFileInput');
    if (dropZone && fileInput) {
        dropZone.addEventListener('click', event => {
            if (event.target !== fileInput) fileInput.click();
        });
        dropZone.addEventListener('dragover', e => {
            e.preventDefault();
            dropZone.style.borderColor = 'var(--accent-lime)';
        });
        dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = ''; });
        dropZone.addEventListener('drop', e => {
            e.preventDefault();
            dropZone.style.borderColor = '';
            if (e.dataTransfer.files && e.dataTransfer.files[0]) handleImageUpload(e.dataTransfer.files[0]);
        });
        fileInput.addEventListener('change', e => {
            if (e.target.files && e.target.files[0]) handleImageUpload(e.target.files[0]);
        });
    }

    const scannerZone = document.getElementById('imageScannerDropZone');
    const scannerInput = document.getElementById('imageScannerFileInput');
    if (scannerZone && scannerInput) {
        scannerZone.addEventListener('dragover', e => {
            e.preventDefault();
            scannerZone.style.borderColor = 'var(--accent-lime)';
        });
        scannerZone.addEventListener('dragleave', () => { scannerZone.style.borderColor = ''; });
        scannerZone.addEventListener('drop', e => {
            e.preventDefault();
            scannerZone.style.borderColor = '';
            if (e.dataTransfer.files && e.dataTransfer.files[0]) handleDedicatedImageUpload(e.dataTransfer.files[0]);
        });
        scannerZone.addEventListener('click', e => {
            if (!e.target.closest('button')) scannerInput.click();
        });
    }
}

function setupArticleUploader() {
    const dropZone = document.getElementById('articleFileDropZone');
    const fileInput = document.getElementById('articleFileInput');
    const pastedArticleText = document.getElementById('pastedArticleText');
    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', event => {
        if (event.target === fileInput || event.target.closest('button')) return;
        fileInput.click();
    });
    dropZone.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            fileInput.click();
        }
    });
    dropZone.addEventListener('dragover', event => {
        event.preventDefault();
        dropZone.classList.add('drag-over');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', event => {
        event.preventDefault();
        dropZone.classList.remove('drag-over');
        const [file] = event.dataTransfer.files || [];
        if (file) selectArticleFile(file);
    });
    fileInput.addEventListener('change', () => {
        const [file] = fileInput.files || [];
        if (file) selectArticleFile(file);
    });
    if (pastedArticleText) {
        pastedArticleText.addEventListener('input', () => {
            const analyzeButton = document.getElementById('analyzePastedArticleBtn');
            if (analyzeButton) analyzeButton.disabled = !pastedArticleText.value.trim();
        });
        pastedArticleText.dispatchEvent(new Event('input'));
    }
}

function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function setArticleFileStatus(message) {
    const status = document.getElementById('articleFileStatus');
    if (status) status.textContent = message;
}

function selectArticleFile(file) {
    const extension = file.name.toLowerCase().match(/\.[^.]+$/)?.[0] || '';
    const allowed = ['.txt', '.html', '.htm', '.pdf', '.doc', '.docx'];
    if (!allowed.includes(extension)) {
        removeArticleFile();
        showToast(t('invalidArticleFile'), 'error');
        return;
    }
    if (file.size > 20 * 1024 * 1024) {
        removeArticleFile();
        showToast(t('articleFileTooLarge'), 'error');
        return;
    }

    articleUploadFile = file;
    articleUploadHeadline = '';
    const headlineInput = document.getElementById('headlineInput');
    if (headlineInput) headlineInput.value = '';
    state.fileType = file.name;
    state.inputType = 'document';
    const details = document.getElementById('articleFileDetails');
    const name = document.getElementById('articleFileName');
    const size = document.getElementById('articleFileSize');
    const text = document.getElementById('uploadedArticleText');
    const analyzeButton = document.getElementById('analyzeUploadedArticleBtn');
    if (details) details.hidden = false;
    if (name) name.textContent = file.name;
    if (size) size.textContent = formatFileSize(file.size);
    if (text) {
        text.value = '';
        text.disabled = true;
    }
    if (analyzeButton) analyzeButton.disabled = true;
    setArticleFileStatus(t('extractingText'));
    extractUploadedArticle(file);
}

function removeArticleFile() {
    articleUploadFile = null;
    articleUploadHeadline = '';
    state.fileType = '';
    state.inputType = 'text';
    const input = document.getElementById('articleFileInput');
    const details = document.getElementById('articleFileDetails');
    const name = document.getElementById('articleFileName');
    const size = document.getElementById('articleFileSize');
    const text = document.getElementById('uploadedArticleText');
    const analyzeButton = document.getElementById('analyzeUploadedArticleBtn');
    if (input) input.value = '';
    if (details) details.hidden = true;
    if (name) name.textContent = '';
    if (size) size.textContent = '';
    if (text) {
        text.value = '';
        text.disabled = true;
    }
    if (analyzeButton) analyzeButton.disabled = true;
    const headlineInput = document.getElementById('headlineInput');
    if (headlineInput) headlineInput.value = '';
    setArticleFileStatus('');
}

async function pasteArticleText() {
    try {
        const text = await navigator.clipboard.readText();
        const articleInput = document.getElementById('newsTextInput');
        if (!articleInput) return;
        articleInput.value = text;
        articleInput.dispatchEvent(new Event('input', { bubbles: true }));
        articleInput.focus();
    } catch (error) {
        showToast(t('clipboardDenied'), 'error');
    }
}

function clearArticleText() {
    const articleInput = document.getElementById('newsTextInput');
    if (articleInput) {
        articleInput.value = '';
        articleInput.dispatchEvent(new Event('input', { bubbles: true }));
        articleInput.focus();
    }
}

function handleImageUpload(file) {
    const validTypes = ['image/png', 'image/jpeg', 'image/webp', 'image/bmp', 'image/tiff'];
    const validExtension = /\.(png|jpe?g|webp|bmp|tiff?)$/i.test(file.name);
    if (!validTypes.includes(file.type) && !validExtension) {
        showToast('Please upload a valid image file (PNG, JPG, WEBP, BMP, or TIFF).', 'error');
        return;
    }
    if (file.size > 20 * 1024 * 1024) {
        showToast('The image is too large. Maximum size is 20 MB.', 'error');
        return;
    }

    const previewArea = document.getElementById('ocrStatusMessage');
    if (previewArea) {
        previewArea.innerHTML = `
            <div style="margin-top:14px; color:var(--accent-lime); font-family:var(--font-mono); font-weight:700; display:flex; align-items:center; justify-content:center; gap:8px;">
                <span>⚡ Preparing ${file.name} for OCR...</span>
            </div>
        `;
    }
    extractUploadedArticle(file);
}

async function extractUploadedArticle(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/extract-file', { method: 'POST', body: formData });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Could not extract text from the uploaded file.');
        }

        let extractedText = data.text || '';
        if ((data.requires_ocr || data.scanned_pages > 0) && file.name.toLowerCase().endsWith('.pdf')) {
            setArticleFileStatus(t('scannedPdfDetected'));
            extractedText = await extractScannedPdfText(file);
        }
        if (!extractedText.trim()) {
            throw new Error('No readable text was extracted. Check the file or try a clearer scan.');
        }

        const uploadedText = document.getElementById('uploadedArticleText');
        const analyzeButton = document.getElementById('analyzeUploadedArticleBtn');
        articleUploadHeadline = data.headline || '';
        if (uploadedText) {
            uploadedText.value = extractedText;
            uploadedText.disabled = false;
        }
        if (analyzeButton) analyzeButton.disabled = false;
        state.fileType = data.filename || file.name;
        setArticleFileStatus(t('extractionComplete'));
        showToast(`Article text extracted from ${data.filename || file.name}.`, 'success');
    } catch (error) {
        setArticleFileStatus(error.message);
        showToast(error.message, 'error');
    }
}

async function loadArticleOcrLibraries() {
    if (!window.pdfjsLib) {
        await new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
            script.onload = resolve;
            script.onerror = () => reject(new Error('PDF OCR support could not be loaded.'));
            document.head.appendChild(script);
        });
    }
    await loadTesseractLibrary();
    window.pdfjsLib.GlobalWorkerOptions.workerSrc =
        'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}

async function extractScannedPdfText(file) {
    await loadArticleOcrLibraries();
    const pdf = await window.pdfjsLib.getDocument({ data: await file.arrayBuffer() }).promise;
    const pages = [];
    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
        setArticleFileStatus(t('readingScannedPdf').replace('{current}', pageNumber).replace('{total}', pdf.numPages));
        const page = await pdf.getPage(pageNumber);
        const pageText = (await page.getTextContent()).items
            .map(item => item.str || '')
            .join(' ')
            .trim();
        if (pageText) {
            pages.push(pageText);
            continue;
        }
        const viewport = page.getViewport({ scale: 1.5 });
        const canvas = document.createElement('canvas');
        canvas.width = Math.ceil(viewport.width);
        canvas.height = Math.ceil(viewport.height);
        await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise;
        const result = await window.Tesseract.recognize(canvas, state.ocrLanguage || 'eng');
        const text = (result.data.text || '').trim();
        if (text) pages.push(text);
    }
    await pdf.destroy();
    const extracted = pages.join('\n\n').trim();
    if (!extracted) throw new Error(t('scannedPdfOcrFailed'));
    return extracted;
}

async function runBrowserOCR(file) {
    const previewArea = document.getElementById('ocrStatusMessage');
    try {
        if (!window.Tesseract) {
            await new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js';
                script.async = true;
                script.onload = resolve;
                script.onerror = () => reject(new Error('OCR library could not be loaded.'));
                document.head.appendChild(script);
            });
        }

        if (previewArea) {
            const previewUrl = URL.createObjectURL(file);
            previewArea.innerHTML = `
                <img src="${previewUrl}" alt="Uploaded newspaper or article" style="max-width:220px;max-height:150px;margin:14px auto 8px;display:block;border-radius:10px;object-fit:contain;">
                <div style="color:var(--accent-lime);font-family:var(--font-mono);font-weight:700;">⚡ Initializing OCR engine...</div>
            `;
        }
        const ocrLanguage = state.ocrLanguage || 'eng';
        const result = await Tesseract.recognize(file, ocrLanguage, {
            logger: progress => {
                if (!previewArea || !progress.status) return;
                const percent = typeof progress.progress === 'number'
                    ? ` ${Math.round(progress.progress * 100)}%`
                    : '';
                const label = progress.status === 'recognizing text'
                    ? 'Reading text'
                    : progress.status.replace(/_/g, ' ');
                previewArea.querySelector('div')?.replaceChildren(document.createTextNode(`⚡ ${label}${percent}`));
            }
        });
        const text = (result.data.text || '').trim();
        if (!text) throw new Error('No readable text was found in the image.');

        try {
            const authForm = new FormData();
            authForm.append('file', file);
            const authResponse = await fetch('/api/analyze-image', { method: 'POST', body: authForm });
            const authData = await authResponse.json();
            if (authResponse.ok && authData.success) {
                state.imageAuthenticity = authData.authenticity;
            }
        } catch (_) {
            state.imageAuthenticity = {
                status: 'Indeterminate',
                summary: 'Image authenticity inspection was unavailable.',
                findings: []
            };
        }

        const lines = text.split('\n').filter(line => line.trim());
        document.getElementById('headlineInput').value = lines[0] ? lines[0].slice(0, 180) : `Uploaded Image: ${file.name}`;
        document.getElementById('newsTextInput').value = lines.length > 1 ? lines.slice(1).join('\n') : text;
        document.querySelector('[data-mode="text"]').click();
        state.inputType = 'image';
        state.fileType = file.name;
        state.ocrText = text;
        showToast(`OCR extracted text from ${file.name}.`, 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function handleDedicatedImageUpload(file) {
    const allowed = ['image/jpeg', 'image/png', 'image/webp'];
    const validByExtension = /\.(jpe?g|png|webp)$/i.test(file.name);
    if ((!allowed.includes(file.type) && !validByExtension) || file.size > 20 * 1024 * 1024) {
        showToast(file.size > 20 * 1024 * 1024 ? 'Image must be 20 MB or smaller.' : 'Upload a JPG, JPEG, PNG, or WEBP image.', 'error');
        return;
    }

    const preview = document.getElementById('imageScannerPreview');
    const reader = new FileReader();
    reader.onload = () => {
        preview.innerHTML = `<img src="${reader.result}" alt="Selected image preview" style="max-width:100%;max-height:300px;border-radius:12px;">`;
    };
    reader.readAsDataURL(file);
    showToast(`Scanning ${file.name}...`, 'info');

    try {
        if (!window.Tesseract) {
            await new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js';
                script.async = true;
                script.onload = resolve;
                script.onerror = () => reject(new Error('OCR library could not be loaded.'));
                document.head.appendChild(script);
            });
        }
        const language = state.ocrLanguage || 'eng';
        const result = await Tesseract.recognize(file, language, {
            logger: progress => {
                if (progress.status) showToast(`${progress.status.replace(/_/g, ' ')}${progress.progress ? ` ${Math.round(progress.progress * 100)}%` : ''}`, 'info');
            }
        });
        const text = (result.data.text || '').trim();
        if (!text) throw new Error('No readable text found. Try a clearer image or enter the text manually.');
        const lines = text.split('\n').filter(line => line.trim());
        document.getElementById('imageHeadlineInput').value = lines[0]?.slice(0, 180) || '';
        document.getElementById('imageExtractedText').value = lines.slice(1).join('\n') || text;
        state.inputType = 'image';
        state.fileType = file.name;
        state.ocrText = text;

        const formData = new FormData();
        formData.append('file', file);
        const authResponse = await fetch('/api/analyze-image', { method: 'POST', body: formData });
        const authData = await authResponse.json();
        if (!authResponse.ok || !authData.success) throw new Error(authData.error || 'Image metadata inspection failed.');
        state.imageAuthenticity = authData.authenticity;
        const authenticity = document.getElementById('imageAuthenticitySummary');
        authenticity.textContent = `${authData.authenticity.status}: ${authData.authenticity.summary} ${authData.authenticity.findings.join(' ')}`;
        showToast('OCR complete. Review or edit the extracted text before analysis.', 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function prepareFeatureAnalysis(headline, text, url, inputType, fileType = '') {
    document.getElementById('headlineInput').value = headline || '';
    document.getElementById('newsTextInput').value = text || '';
    document.getElementById('newsUrlInput').value = url || '';
    const mode = url && !text ? 'url' : 'text';
    const modeButton = document.querySelector(`[data-mode="${mode}"]`);
    if (modeButton) modeButton.click();
    state.inputType = inputType;
    state.fileType = fileType;
    state.ocrText = inputType === 'image' ? text : '';
    if (inputType !== 'image') state.imageAuthenticity = {};
    switchTab('articles');
    runAnalysis();
}

function analyzePostForm() {
    const text = document.getElementById('socialPostTextInput').value.trim();
    const url = document.getElementById('socialPostUrlInput').value.trim();
    if (!text && !url) {
        showToast('Paste post text or provide a public post URL.', 'error');
        return;
    }
    const headline = text ? text.split(/\r?\n/)[0].slice(0, 180) : '';
    prepareFeatureAnalysis(headline, text, url, 'social_post', 'Social Post');
}

function analyzeImageForm() {
    const text = document.getElementById('imageExtractedText').value.trim();
    if (!text) {
        showToast('Upload an image or enter extracted text before analysis.', 'error');
        return;
    }
    const headline = document.getElementById('imageHeadlineInput').value.trim() || text.split(/\r?\n/)[0].slice(0, 180);
    prepareFeatureAnalysis(headline, text, '', 'image', state.fileType);
}

/* Quick Example Prefills */
function prefillExample(type) {
    if (type === 'reuters') {
        document.getElementById('headlineInput').value = "WASHINGTON (Reuters) - Federal Reserve holds interest rates steady";
        document.getElementById('newsTextInput').value = "The Federal Reserve held benchmark interest rates steady on Wednesday following a two-day monetary policy meeting. Chairman Jerome Powell emphasized substantial progress toward the two percent inflation target while reiterating that the central bank remains prepared to adjust stance if economic risks emerge. Labor markets remain historically resilient across major sectors.";
        document.getElementById('newsUrlInput').value = "https://www.reuters.com/markets/rates-decision-2026";
        document.querySelector('[data-mode="text"]').click();
        showToast('Loaded verified Reuters wire report benchmark.', 'info');
    } else if (type === 'clickbait') {
        document.getElementById('headlineInput').value = "SHOCKING BOMBSHELL: Secret underground alien facility exposed under Washington!";
        document.getElementById('newsTextInput').value = "You won't believe what whistleblowers have finally leaked to the public! Proof that high-ranking political elites and secret shadow agencies have been concealing extraterrestrial technology for thirty years. Watch this explosive video immediately before mainstream media forces it offline! America must wake up right now to this horrifying conspiracy!";
        document.getElementById('newsUrlInput').value = "http://conspiracy-leak-alert.xyz/shocking-truth";
        document.querySelector('[data-mode="text"]').click();
        showToast('Loaded viral sensational hoax benchmark.', 'info');
    }
}

/* ==========================================================================
   Disinformation Vectors File Upload & OCR Ingestion
   ========================================================================== */

function triggerSectionUpload(type) {
    const input = document.getElementById(`${type}FileInput`);
    if (input) input.click();
}

function handleSectionFileUpload(file, type) {
    if (!file) return;

    showToast(`Uploading ${file.name}... Extracting article text`, 'info');

    // If it's a plain text or markdown file
    if (file.type === 'text/plain' || file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            const lines = content.split('\n').filter(l => l.trim().length > 0);
            const headline = lines.length > 0 ? lines[0].replace(/^#+\s*/, '') : `Uploaded Article: ${file.name}`;
            const text = lines.length > 1 ? lines.slice(1).join('\n') : content;
            testCaseStudy(headline, text, `uploaded://${file.name}`, type === 'post' ? 'social_post' : 'document');
        };
        reader.readAsText(file);
        return;
    }

    if (file.type.startsWith('image/')) {
        extractSectionImage(file, type);
        return;
    }

    extractSectionDocument(file, type);
}

async function extractSectionDocument(file, type) {
    const formData = new FormData();
    formData.append('file', file);
    try {
        const response = await fetch('/api/extract-file', { method: 'POST', body: formData });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || 'Could not extract the document.');

        testCaseStudy(data.headline || `Uploaded Article: ${file.name}`, data.text, `uploaded://${file.name}`, type === 'post' ? 'social_post' : 'document');
        showToast(`Extracted article from ${file.name}. Running Truth Scanner...`, 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function extractSectionImage(file, type) {
    try {
        if (!file.type.startsWith('image/') && !/\.(png|jpe?g|webp|bmp|tiff?)$/i.test(file.name)) {
            throw new Error('Please upload a valid image file.');
        }
        if (file.size > 20 * 1024 * 1024) {
            throw new Error('The image is too large. Maximum size is 20 MB.');
        }
        if (!window.Tesseract) {
            await new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js';
                script.onload = resolve;
                script.onerror = () => reject(new Error('OCR library could not be loaded.'));
                document.head.appendChild(script);
            });
        }
        showToast(`Running OCR on ${file.name}...`, 'info');
        const result = await Tesseract.recognize(file, state.ocrLanguage || 'eng');
        const text = (result.data.text || '').trim();
        if (!text) throw new Error('No readable text was found in the image.');
        const lines = text.split('\n').filter(line => line.trim());
        const headline = lines[0] ? lines[0].slice(0, 180) : `Uploaded Image: ${file.name}`;
        const body = lines.length > 1 ? lines.slice(1).join('\n') : text;
        testCaseStudy(headline, body, `file://${file.name}`, type === 'post' ? 'social_post' : 'image');
        showToast(`Extracted article text from ${file.name}. Running Truth Scanner...`, 'success');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

/* One-Click Disinformation Case Study Loader */
function testCaseStudy(headline, text, url, inputType = 'text') {
    switchTab('articles');
    setTimeout(() => {
        document.getElementById('headlineInput').value = headline;
        document.getElementById('newsTextInput').value = text;
        document.getElementById('newsUrlInput').value = url || '';
        const textTab = document.querySelector('[data-mode="text"]');
        if (textTab) textTab.click();
        state.inputType = inputType;
        state.fileType = inputType === 'image' || inputType === 'social_post' ? (url || '').split('/').pop() : '';
        state.ocrText = inputType === 'image' || inputType === 'social_post' ? text : '';
        scrollToVerification();
        showToast(`Loaded case study: "${headline.substring(0, 36)}..."`, 'info');
        setTimeout(() => {
            runAnalysis();
        }, 400);
    }, 150);
}

/* ==========================================================================
   AI NEWS SCANNING ANIMATION: Multi-Stage Execution
   ========================================================================== */

async function runAnalysis(articleMode = null) {
    if (articleMode !== 'upload' && articleMode !== 'paste') {
        showToast(t('uploadArticleBeforeScan'), 'error');
        return;
    }

    const isUpload = articleMode === 'upload';
    const text = document.getElementById(
        isUpload ? 'uploadedArticleText' : 'pastedArticleText'
    )?.value.trim() || '';
    if (isUpload && !articleUploadFile) {
        showToast(t('uploadArticleBeforeScan'), 'error');
        return;
    }
    if (!text) {
        showToast(isUpload ? t('noExtractedArticleText') : t('pasteArticleRequired'), 'error');
        return;
    }

    const scannerOverlay = document.getElementById('scannerOverlay');
    const laserBeam = document.getElementById('scanningLaserBeam');
    const analyzeButton = document.getElementById(
        isUpload ? 'analyzeUploadedArticleBtn' : 'analyzePastedArticleBtn'
    );
    const fileName = isUpload ? articleUploadFile.name : t('pasteText');
    const headline = isUpload ? articleUploadHeadline : '';
    if (laserBeam) laserBeam.classList.add('active');
    if (scannerOverlay) scannerOverlay.classList.add('active');
    if (analyzeButton) analyzeButton.disabled = true;

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text,
                headline,
                url: '',
                user_id: state.currentUser.username,
                input_type: isUpload ? 'document' : 'text',
                file_type: fileName,
                ocr_text: '',
                ocr_language: state.ocrLanguage
            })
        });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || t('analysisFailed'));

        state.currentReport = data;
        state.currentArticleReport = data;
        state.currentArticleText = [headline, text].filter(Boolean).join('\n');
        state.currentResultFileName = fileName;
        renderSimpleScanResult('article', data, fileName);
        loadDashboard();
        showToast(`${t('analysisComplete')}: ${t(predictionKey(data))}.`, 'success');
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        if (analyzeButton) {
            const remainingText = document.getElementById(
                isUpload ? 'uploadedArticleText' : 'pastedArticleText'
            )?.value.trim() || '';
            analyzeButton.disabled = !remainingText;
        }
        if (scannerOverlay) scannerOverlay.classList.remove('active');
        if (laserBeam) laserBeam.classList.remove('active');
    }
}

function renderArticleAnalysisResult(report, articleText) {
    const verdict = document.getElementById('articleResultVerdict');
    const prediction = report.classification || report.prediction;
    const verdictKey = prediction === 'Likely Real' || prediction === 'REAL'
        ? 'likelyReal'
        : prediction === 'Likely Fake' || prediction === 'FAKE' ? 'likelyFake' : 'unverified';
    if (verdict) {
        verdict.textContent = t(verdictKey);
        verdict.className = `article-result-verdict ${verdictKey === 'likelyReal' ? 'verdict-real' : verdictKey === 'likelyFake' ? 'verdict-fake' : ''}`;
    }

    const score = Number(report.credibility_score);
    const scoreElement = document.getElementById('articleAuthenticityScore');
    if (scoreElement) scoreElement.textContent = Number.isFinite(score) ? `${(score / 10).toFixed(1)} / 10` : '?';

    const confidenceMetric = document.getElementById('articleConfidenceMetric');
    const confidenceElement = document.getElementById('articleModelConfidence');
    const calibratedConfidence = Number(report.confidence);
    const isCalibrated = report.confidence_calibrated === true && Number.isFinite(calibratedConfidence);
    if (confidenceMetric) confidenceMetric.hidden = !isCalibrated;
    if (confidenceElement && isCalibrated) confidenceElement.textContent = `${calibratedConfidence.toFixed(1)}%`;

    const explanation = document.getElementById('articleExplanation');
    if (explanation) {
        explanation.replaceChildren();
        (report.reasons || []).forEach(reason => {
            const item = document.createElement('li');
            item.textContent = reason;
            explanation.appendChild(item);
        });
    }

    const suspicious = document.getElementById('articleSuspiciousPhrases');
    if (suspicious) {
        suspicious.replaceChildren();
        const terms = [
            ...(report.sensationalism?.detected_triggers || []),
            ...(report.xai?.top_fake_indicators || []).slice(0, 5).map(token => token.word),
            ...(report.manipulation_signals || [])
        ];
        [...new Set(terms)].forEach(signal => {
            const item = document.createElement('li');
            item.textContent = signal;
            suspicious.appendChild(item);
        });
        if (!terms.length) suspicious.textContent = t('noSuspiciousPhrases');
    }

    const evidence = document.getElementById('articleEvidence');
    if (evidence) {
        evidence.replaceChildren();
        const sources = Array.isArray(report.fact_check_evidence) ? report.fact_check_evidence : [];
        sources.forEach(source => {
            const href = typeof source === 'string' ? source : (source.url || source.link || '');
            const label = typeof source === 'string' ? source : (source.title || source.name || href);
            const row = document.createElement('p');
            if (href && /^https?:\/\//i.test(href)) {
                const link = document.createElement('a');
                link.href = href;
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.textContent = label || href;
                row.appendChild(link);
            } else {
                row.textContent = label || '';
            }
            if (row.textContent || row.querySelector('a')) evidence.appendChild(row);
        });
        if (report.source_url && /^https?:\/\//i.test(report.source_url)) {
            const row = document.createElement('p');
            const link = document.createElement('a');
            link.href = report.source_url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = report.source_domain || report.source_url;
            row.appendChild(link);
            evidence.appendChild(row);
        }
        if (!evidence.childElementCount) evidence.textContent = t('noLinksAvailable');
    }

    const extracted = document.getElementById('articleResultText');
    if (extracted) extracted.textContent = articleText;
}

function startAnotherArticle() {
    const results = document.getElementById('articleResults');
    const inputs = document.getElementById('articleInputMethods');
    if (results) results.hidden = true;
    if (inputs) inputs.hidden = false;
    removeArticleFile();
    state.currentReport = null;
    state.currentResultKind = null;
    state.currentResultFileName = '';
    state.currentArticleReport = null;
    state.currentArticleText = '';
    const pastedArticleText = document.getElementById('pastedArticleText');
    if (pastedArticleText) {
        pastedArticleText.value = '';
        pastedArticleText.dispatchEvent(new Event('input', { bubbles: true }));
    }
    document.getElementById('articleFileInput')?.focus();
}

function getArticleSuspiciousTerms(report) {
    const terms = [];
    const seen = new Set();
    const addTerms = (values, reasonKey) => {
        if (!Array.isArray(values)) return;
        values.forEach(value => {
            if (typeof value !== 'string') return;
            const term = value.trim();
            const normalized = term.toLocaleLowerCase();
            if (!term || seen.has(normalized)) return;
            seen.add(normalized);
            terms.push({ term, reasonKey });
        });
    };

    addTerms(report.sensationalism?.detected_triggers, 'suspiciousSensationalReason');
    addTerms(report.sensationalism?.anonymous_citations, 'suspiciousAnonymousReason');
    return terms;
}

function isArticleWordCharacter(character) {
    return Boolean(character && /[\p{L}\p{N}_]/u.test(character));
}

function renderHighlightedArticleText(container, articleText, terms) {
    container.replaceChildren();
    container.setAttribute('aria-label', t('extractedArticleText'));
    if (!articleText) return;

    const lowercaseText = articleText.toLocaleLowerCase();
    const matches = [];
    terms.forEach(({ term, reasonKey }) => {
        const searchableTerm = term.toLocaleLowerCase();
        let start = 0;
        while (searchableTerm && (start = lowercaseText.indexOf(searchableTerm, start)) !== -1) {
            const end = start + searchableTerm.length;
            if (!isArticleWordCharacter(articleText[start - 1]) && !isArticleWordCharacter(articleText[end])) {
                matches.push({ start, end, reasonKey });
            }
            start = end;
        }
    });

    matches.sort((left, right) => left.start - right.start || right.end - left.end);
    let cursor = 0;
    matches.forEach(match => {
        if (match.start < cursor) return;
        container.appendChild(document.createTextNode(articleText.slice(cursor, match.start)));
        const mark = document.createElement('mark');
        mark.className = 'suspicious-highlight';
        mark.textContent = articleText.slice(match.start, match.end);
        mark.title = t(match.reasonKey);
        container.appendChild(mark);
        cursor = match.end;
    });
    container.appendChild(document.createTextNode(articleText.slice(cursor)));
}

function renderArticleAnalysisEnhancements(report, articleText) {
    const section = document.getElementById('articleAnalysisEnhancements');
    if (!section) return;
    section.hidden = false;

    const terms = getArticleSuspiciousTerms(report);
    const language = report.language?.language || t('languageUnknown');
    const characterCount = Array.from(articleText || '').length;
    const confidence = report.confidence;
    const calibratedConfidence = report.confidence_calibrated === true
        && typeof confidence === 'number'
        && Number.isFinite(confidence);
    const setText = (id, value) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    };
    const formatNumber = value => value.toLocaleString(currentLanguage());

    setText('articleSummaryLanguage', language);
    setText('articleSummaryLength', formatNumber(characterCount));
    setText('articleSummaryTermCount', formatNumber(terms.length));
    setText('articleSummaryStatus', t('analysisComplete'));
    setText(
        'articleSummaryConfidence',
        calibratedConfidence ? `${confidence.toFixed(1)}%` : t('confidenceNotCalibrated')
    );

    const list = document.getElementById('articleSuspiciousTerms');
    if (list) {
        list.replaceChildren();
        if (!terms.length) {
            const item = document.createElement('li');
            item.textContent = t('noSuspiciousTerms');
            list.appendChild(item);
        } else {
            terms.forEach(({ term, reasonKey }) => {
                const item = document.createElement('li');
                const label = document.createElement('strong');
                const explanation = document.createElement('span');
                label.textContent = term;
                explanation.textContent = t(reasonKey);
                item.append(label, explanation);
                list.appendChild(item);
            });
        }
    }

    const highlightedText = document.getElementById('articleHighlightedText');
    if (highlightedText) renderHighlightedArticleText(highlightedText, articleText, terms);
}

function renderSimpleScanResult(kind, report, fileName, scroll = true) {
    const elements = {
        article: {
            panel: 'articleInputMethods', result: 'articleResults',
            filename: 'articleResultFileName', verdict: 'articleResultVerdict',
            confidence: 'articleResultConfidence', explanation: 'articleResultExplanation'
        },
        post: {
            panel: 'postInputPanel', result: 'postScanResults',
            filename: 'postResultFileName', verdict: 'postResultVerdict',
            confidence: 'postResultConfidence', explanation: 'postResultExplanation'
        },
        image: {
            panel: 'imageInputPanel', result: 'imageScanResults',
            filename: 'imageResultFileName', verdict: 'imageResultVerdict',
            explanation: 'imageResultExplanation'
        }
    }[kind];
    if (!elements) throw new Error('Unsupported scan result type.');
    state.currentReport = report;
    state.currentResultKind = kind;
    state.currentResultFileName = fileName || '';

    const verdictKey = predictionKey(report);
    const panel = document.getElementById(elements.panel);
    const result = document.getElementById(elements.result);
    const nameElement = document.getElementById(elements.filename);
    const verdictElement = document.getElementById(elements.verdict);
    const explanationElement = document.getElementById(elements.explanation);
    if (panel) panel.hidden = true;
    if (result) result.hidden = false;
    if (nameElement) nameElement.textContent = fileName || t('untitledScan');
    if (verdictElement) {
        verdictElement.textContent = t(verdictKey);
        verdictElement.className = `simple-result-verdict ${verdictKey}`;
    }
    if (explanationElement) explanationElement.textContent = explanationForPrediction(report);
    if (kind === 'article') {
        const evidence = Array.isArray(report.fact_check_evidence) ? report.fact_check_evidence : [];
        const evidencePanel = document.getElementById('articleFactCheckEvidence');
        const sourceElement = document.getElementById('articleFactCheckSource');
        const excerptElement = document.getElementById('articleFactCheckExcerpt');
        const linkElement = document.getElementById('articleFactCheckLink');
        const sourceEvidence = evidence.find(item => item && item.url);
        let safeSourceUrl = null;
        let sourceLinkLabel = '';
        if (sourceEvidence?.url) {
            try {
                const candidateUrl = new URL(sourceEvidence.url);
                const sourceLabels = {
                    'www.isro.gov.in': 'View official ISRO record',
                    'www.icc-cricket.com': 'View official ICC record'
                };
                if (candidateUrl.protocol === 'https:' && sourceLabels[candidateUrl.hostname]) {
                    safeSourceUrl = candidateUrl.href;
                    sourceLinkLabel = sourceLabels[candidateUrl.hostname];
                }
            } catch (_error) {
                safeSourceUrl = null;
            }
        }
        if (evidencePanel) evidencePanel.hidden = !sourceEvidence || !safeSourceUrl;
        if (sourceElement) {
            sourceElement.textContent = sourceEvidence
                ? `${sourceEvidence.source} — ${sourceEvidence.status}`
                : '';
        }
        if (excerptElement) excerptElement.textContent = sourceEvidence?.excerpt || '';
        if (linkElement) {
            linkElement.href = safeSourceUrl || '#';
            linkElement.textContent = sourceLinkLabel;
        }
    }

    const confidenceElement = elements.confidence
        ? document.getElementById(elements.confidence)
        : null;
    const confidence = Number(report.confidence);
    const calibrated = report.confidence_calibrated === true && Number.isFinite(confidence);
    if (confidenceElement) {
        confidenceElement.hidden = !calibrated;
        if (calibrated) confidenceElement.textContent = `${t('confidence')}: ${confidence.toFixed(1)}%`;
    }
    if (kind === 'article') renderArticleAnalysisEnhancements(report, state.currentArticleText);
    if (scroll) result?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function validateScreenshot(file) {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    const allowedExtension = /\.(jpe?g|png|webp)$/i.test(file.name);
    if (!allowedExtension || (file.type && !allowedTypes.includes(file.type))) {
        showToast(t('unsupportedImageType'), 'error');
        return false;
    }
    if (file.size > 20 * 1024 * 1024) {
        showToast(t('imageTooLarge'), 'error');
        return false;
    }
    return true;
}

function setImagePreview(file, previewId) {
    const preview = document.getElementById(previewId);
    if (!preview) return;
    const previousImage = preview.querySelector('img');
    if (previousImage?.src.startsWith('blob:')) URL.revokeObjectURL(previousImage.src);
    const image = document.createElement('img');
    image.src = URL.createObjectURL(file);
    image.alt = file.name;
    preview.replaceChildren(image);
}

function selectPostScreenshot(file) {
    if (!validateScreenshot(file)) {
        selectedPostScreenshot = null;
        const scanButton = document.getElementById('scanPostButton');
        const filename = document.getElementById('postFileName');
        const preview = document.getElementById('postScreenshotPreview');
        const previousImage = preview?.querySelector('img');
        if (previousImage?.src.startsWith('blob:')) URL.revokeObjectURL(previousImage.src);
        if (scanButton) scanButton.disabled = true;
        if (filename) filename.hidden = true;
        if (preview) preview.replaceChildren();
        return;
    }
    selectedPostScreenshot = file;
    const filename = document.getElementById('postFileName');
    const scanButton = document.getElementById('scanPostButton');
    if (filename) {
        filename.textContent = file.name;
        filename.hidden = false;
    }
    setImagePreview(file, 'postScreenshotPreview');
    if (scanButton) scanButton.disabled = false;
}

function selectImageForScan(file) {
    if (!validateScreenshot(file)) {
        selectedFakeImage = null;
        const scanButton = document.getElementById('scanImageButton');
        const filename = document.getElementById('imageFileName');
        const preview = document.getElementById('imageScannerPreview');
        const previousImage = preview?.querySelector('img');
        if (previousImage?.src.startsWith('blob:')) URL.revokeObjectURL(previousImage.src);
        if (scanButton) scanButton.disabled = true;
        if (filename) filename.hidden = true;
        if (preview) preview.replaceChildren();
        return;
    }
    selectedFakeImage = file;
    const filename = document.getElementById('imageFileName');
    const scanButton = document.getElementById('scanImageButton');
    if (filename) {
        filename.textContent = file.name;
        filename.hidden = false;
    }
    setImagePreview(file, 'imageScannerPreview');
    if (scanButton) scanButton.disabled = false;
}

async function loadTesseractLibrary() {
    if (window.Tesseract) return;
    if (!window.tesseractLoadPromise) {
        window.tesseractLoadPromise = new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js';
            script.async = true;
            script.onload = resolve;
            script.onerror = () => reject(new Error(t('ocrUnavailable')));
            document.head.appendChild(script);
        }).catch(error => {
            window.tesseractLoadPromise = null;
            throw error;
        });
    }
    await window.tesseractLoadPromise;
}

async function analyzeExtractedPostText(text, fileName) {
    const response = await fetch('/api/analyze-post-screenshot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            ocr_text: text,
            file_type: fileName,
            ocr_language: state.ocrLanguage
        })
    });
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.error || t('analysisFailed'));
    return data;
}

async function scanPostScreenshot() {
    if (!selectedPostScreenshot) {
        showToast(t('uploadPostBeforeScan'), 'error');
        return;
    }
    const button = document.getElementById('scanPostButton');
    if (button) button.disabled = true;
    try {
        await loadTesseractLibrary();
        const ocrResult = await window.Tesseract.recognize(selectedPostScreenshot, state.ocrLanguage || 'eng');
        const text = (ocrResult.data.text || '').trim();
        if (!text) throw new Error(t('noReadableScreenshotText'));
        const report = await analyzeExtractedPostText(text, selectedPostScreenshot.name);
        renderSimpleScanResult('post', report, selectedPostScreenshot.name);
        loadDashboard();
        showToast(`${t('analysisComplete')}: ${t(predictionKey(report))}.`, 'success');
    } catch (error) {
        showToast(error.message, 'error');
        if (button) button.disabled = false;
    }
}

function scanAnotherPost() {
    const input = document.getElementById('postFileInput');
    const panel = document.getElementById('postInputPanel');
    const result = document.getElementById('postScanResults');
    const filename = document.getElementById('postFileName');
    const preview = document.getElementById('postScreenshotPreview');
    const button = document.getElementById('scanPostButton');
    const image = preview?.querySelector('img');
    if (image?.src.startsWith('blob:')) URL.revokeObjectURL(image.src);
    if (input) input.value = '';
    if (filename) filename.hidden = true;
    if (preview) preview.replaceChildren();
    if (button) button.disabled = true;
    if (result) result.hidden = true;
    if (panel) panel.hidden = false;
    selectedPostScreenshot = null;
    if (state.currentResultKind === 'post') {
        state.currentReport = null;
        state.currentResultKind = null;
        state.currentResultFileName = '';
    }
}

async function scanImageAuthenticity() {
    if (!selectedFakeImage) {
        showToast(t('uploadImageBeforeScan'), 'error');
        return;
    }
    const button = document.getElementById('scanImageButton');
    if (button) button.disabled = true;
    try {
        const formData = new FormData();
        formData.append('file', selectedFakeImage);
        formData.append('save_to_history', 'true');
        const response = await fetch('/api/analyze-image', { method: 'POST', body: formData });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.error || t('imageInspectionFailed'));
        renderSimpleScanResult('image', {
            prediction: 'NEEDS_VERIFICATION',
            image_authenticity: data.authenticity
        }, selectedFakeImage.name);
        loadDashboard();
        showToast(t('imageScanComplete'), 'success');
    } catch (error) {
        showToast(error.message, 'error');
        if (button) button.disabled = false;
    }
}

function scanAnotherImage() {
    const input = document.getElementById('imageScannerFileInput');
    const panel = document.getElementById('imageInputPanel');
    const result = document.getElementById('imageScanResults');
    const filename = document.getElementById('imageFileName');
    const preview = document.getElementById('imageScannerPreview');
    const button = document.getElementById('scanImageButton');
    const image = preview?.querySelector('img');
    if (image?.src.startsWith('blob:')) URL.revokeObjectURL(image.src);
    if (input) input.value = '';
    if (filename) filename.hidden = true;
    if (preview) preview.replaceChildren();
    if (button) button.disabled = true;
    if (result) result.hidden = true;
    if (panel) panel.hidden = false;
    selectedFakeImage = null;
    if (state.currentResultKind === 'image') {
        state.currentReport = null;
        state.currentResultKind = null;
        state.currentResultFileName = '';
    }
}

/* ==========================================================================
   TRUTH INTELLIGENCE REPORT RENDERING
   ========================================================================== */

function renderIntelligenceReport(report) {
    // 1. Verdict Banner
    const banner = document.getElementById('reportBanner');
    const verdictText = document.getElementById('reportVerdictText');
    const riskBadge = document.getElementById('reportRiskBadge');
    const reportTitle = document.getElementById('reportArticleTitle');
    const reportMeta = document.getElementById('reportArticleMeta');

    if (banner) {
        banner.className = 'report-header-banner';
        if (report.classification === 'Likely Real') {
            banner.classList.add('banner-real');
            verdictText.innerHTML = `
                    <span class="verdict-badge-large verdict-real">${escapeHTML(t('likelyReal'))}</span>
            `;
        } else if (report.classification === 'Likely Fake') {
            banner.classList.add('banner-fake');
            verdictText.innerHTML = `
                    <span class="verdict-badge-large verdict-fake">${escapeHTML(t('likelyFake'))}</span>
            `;
        } else {
            banner.classList.add('banner-verify');
            verdictText.innerHTML = `
                    <span class="verdict-badge-large verdict-verify">${escapeHTML(t('unverified'))}</span>
            `;
        }
    }

    if (riskBadge) {
        riskBadge.innerHTML = `${escapeHTML(t('riskLevel'))}: <strong>${escapeHTML(report.risk_level || '')}</strong>`;
        riskBadge.className = 'token-chip ' + (report.risk_level === 'LOW' ? 'token-chip-real' : 'token-chip-fake');
    }

    if (reportTitle) reportTitle.textContent = report.title || "Untitled Intelligence Record";
    if (reportMeta) {
        const cat = report.category || "General";
        const words = report.word_count || 0;
        const domain = report.source_domain ? `• Domain: ${report.source_domain}` : "";
        reportMeta.textContent = `Category: ${cat} • ${words} words • Language: ${report.language?.language || 'English'} ${domain}`;
    }

    // 2. Progressive Radial Credibility Meter Animation
    const scoreVal = report.credibility_score;
    const scoreEl = document.getElementById('reportCredibilityScore');
    const circle = document.getElementById('reportMeterProgress');

    // Count up score
    animateValue(scoreEl, 0, scoreVal, 1400, '%');

    if (circle) {
        const radius = circle.r.baseVal.value;
        const circumference = 2 * Math.PI * radius;
        circle.style.strokeDasharray = `${circumference} ${circumference}`;
        circle.style.strokeDashoffset = circumference; // start at 0

        setTimeout(() => {
            const offset = circumference - (scoreVal / 100) * circumference;
            circle.style.strokeDashoffset = offset;

            if (scoreVal >= 65) {
                circle.style.stroke = 'var(--accent-lime)';
            } else if (scoreVal <= 35) {
                circle.style.stroke = 'var(--accent-coral)';
            } else {
                circle.style.stroke = 'var(--warning)';
            }
        }, 100);
    }

    // 3. Confidence & Metrics
    const confEl = document.getElementById('reportConfidenceScore');
    if (confEl) confEl.textContent = `${report.confidence}%`;

    // 4. Explainable AI Feature Attribution Tokens
    const fakeTokensContainer = document.getElementById('xaiFakeTokens');
    const realTokensContainer = document.getElementById('xaiRealTokens');

    if (fakeTokensContainer) {
        fakeTokensContainer.innerHTML = '';
        const topFake = report.xai?.top_fake_indicators || [];
        if (topFake.length === 0) {
            fakeTokensContainer.innerHTML = '<span style="font-size:0.85rem; color:var(--text-muted);">No prominent fake-leaning vocabulary detected.</span>';
        } else {
            topFake.forEach((t, idx) => {
                const chip = document.createElement('span');
                chip.className = 'token-chip token-chip-fake';
                chip.style.animation = `fadeInSlide 0.3s ease ${idx * 0.06}s both`;
                chip.innerHTML = `<strong>${t.word}</strong> <span style="font-size:0.7rem; opacity:0.85;">-${t.relative_impact}%</span>`;
                fakeTokensContainer.appendChild(chip);
            });
        }
    }

    if (realTokensContainer) {
        realTokensContainer.innerHTML = '';
        const topReal = report.xai?.top_real_indicators || [];
        if (topReal.length === 0) {
            realTokensContainer.innerHTML = '<span style="font-size:0.85rem; color:var(--text-muted);">No prominent real-leaning wire vocabulary detected.</span>';
        } else {
            topReal.forEach((t, idx) => {
                const chip = document.createElement('span');
                chip.className = 'token-chip token-chip-real';
                chip.style.animation = `fadeInSlide 0.3s ease ${idx * 0.06}s both`;
                chip.innerHTML = `<strong>${t.word}</strong> <span style="font-size:0.7rem; opacity:0.85;">+${t.relative_impact}%</span>`;
                realTokensContainer.appendChild(chip);
            });
        }
    }

    // 5. Emotional & Sensational Language
    const sensMeter = document.getElementById('sensationalIntensityBar');
    const sensScore = document.getElementById('sensationalIntensityScore');
    const sensLevel = document.getElementById('sensationalIntensityLevel');
    const triggersList = document.getElementById('sensationalTriggersList');

    if (report.sensationalism) {
        const s = report.sensationalism;
        if (sensMeter) sensMeter.style.width = `${s.intensity_score}%`;
        if (sensScore) sensScore.textContent = `${s.intensity_score}/100`;
        if (sensLevel) sensLevel.textContent = s.level;

        if (triggersList) {
            triggersList.innerHTML = '';
            if (s.detected_triggers && s.detected_triggers.length > 0) {
                s.detected_triggers.forEach(trig => {
                    const pill = document.createElement('span');
                    pill.className = 'token-chip token-chip-fake';
                    pill.textContent = trig;
                    triggersList.appendChild(pill);
                });
            } else {
                triggersList.innerHTML = '<span style="font-size:0.85rem; color:var(--text-muted);">No sensational triggers detected.</span>';
            }
        }
    }

    // 6. Headline Consistency
    const headScore = document.getElementById('headlineConsistencyScore');
    const headRating = document.getElementById('headlineConsistencyRating');
    const headExpl = document.getElementById('headlineConsistencyExplanation');

    if (report.headline_analysis) {
        const h = report.headline_analysis;
        if (headScore) headScore.textContent = `${h.consistency_score}%`;
        if (headRating) headRating.textContent = h.rating;
        if (headExpl) headExpl.textContent = h.explanation;
    }

    // 7. Manipulation Signals
    const manipContainer = document.getElementById('manipulationSignalsContainer');
    if (manipContainer) {
        manipContainer.innerHTML = '';
        (report.manipulation_signals || []).forEach(sig => {
            const item = document.createElement('li');
            item.style.marginBottom = '8px';
            item.innerHTML = `🛡️ <strong>${sig}</strong>`;
            manipContainer.appendChild(item);
        });
    }

    // 8. Reasons Behind Prediction
    const reasonsContainer = document.getElementById('reasonsContainer');
    if (reasonsContainer) {
        reasonsContainer.innerHTML = '';
        (report.reasons || []).forEach(reason => {
            const item = document.createElement('li');
            item.style.marginBottom = '8px';
            item.textContent = reason;
            reasonsContainer.appendChild(item);
        });
    }

    // 9. Suggested Verification Steps
    const stepsContainer = document.getElementById('verificationStepsContainer');
    if (stepsContainer) {
        stepsContainer.innerHTML = '';
        (report.verification_steps || []).forEach(step => {
            const item = document.createElement('li');
            item.style.marginBottom = '8px';
            item.textContent = step;
            stepsContainer.appendChild(item);
        });
    }

    // 10. Sentence Forensics Highlighting
    const sentencesContainer = document.getElementById('sentenceForensicsContainer');
    if (sentencesContainer) {
        sentencesContainer.innerHTML = '';
        const sData = report.sentence_analysis?.sentences || [];
        if (sData.length === 0) {
            sentencesContainer.innerHTML = '<p style="color:var(--text-muted);">Text too brief for granular sentence breakdown.</p>';
        } else {
            sData.forEach((s, idx) => {
                const sDiv = document.createElement('div');
                sDiv.className = `sentence-item sentence-${s.tag}`;
                sDiv.style.animation = `fadeInSlide 0.3s ease ${idx * 0.05}s both`;
                const tagLabel = s.tag === 'suspicious' 
                    ? '<span style="color:var(--accent-coral); font-family:var(--font-mono); font-size:0.75rem; font-weight:800;">[SUSPICIOUS PATTERN]</span> '
                    : (s.tag === 'credible' ? '<span style="color:var(--accent-lime); font-family:var(--font-mono); font-size:0.75rem; font-weight:800;">[CREDIBLE WIRE PATTERN]</span> ' : '');
                sDiv.innerHTML = `${tagLabel}${s.text}`;
                sentencesContainer.appendChild(sDiv);
            });
        }
    }

    // 11. Source info banner if present
    const sourceCard = document.getElementById('reportSourceIntelligenceCard');
    if (sourceCard) {
        if (report.source_info) {
            sourceCard.style.display = 'block';
            document.getElementById('reportSourceDomain').textContent = report.source_info.domain;
            document.getElementById('reportSourceReputation').textContent = report.source_info.rating;
            document.getElementById('reportSourceTrustScore').textContent = `${report.source_info.trust_score}/100`;
            document.getElementById('reportSourceSummary').textContent = report.source_info.summary;
        } else {
            sourceCard.style.display = 'none';
        }
    }
}

/* ==========================================================================
   Report Action Handlers (PDF, Copy, Share, Bookmark)
   ========================================================================== */

function copyReportSummary() {
    if (!state.currentReport) {
        showToast('No active report to copy.', 'error');
        return;
    }

    const summary = [
        'TRUTHLENS AI',
        `${t('fileNameLabel')}: ${state.currentResultFileName || state.currentReport.title || t('untitledScan')}`,
        `${t('resultLabel')}: ${t(predictionKey(state.currentReport))}`,
        explanationForPrediction(state.currentReport)
    ].join('\n');

    navigator.clipboard.writeText(summary)
        .then(() => showToast(t('analysisComplete'), 'success'))
        .catch(error => showToast(error.message, 'error'));
}

function downloadReportText() {
    if (!state.currentReport) {
        showToast('No active report to export.', 'error');
        return;
    }
    const report = state.currentReport;
    const lines = [
        'TRUTHLENS AI',
        `${t('fileNameLabel')}: ${state.currentResultFileName || report.title || t('untitledScan')}`,
        `${t('resultLabel')}: ${t(predictionKey(report))}`,
        explanationForPrediction(report),
        `${t('scanDateLabel')}: ${new Date().toLocaleString()}`
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `truthlens-result-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
    showToast('Report exported as .txt file!', 'success');
}

function downloadReportPDF() {
    if (!state.currentReport) {
        showToast('No active report to export.', 'error');
        return;
    }
    if (state.currentReport.id) {
        window.location.href = `/api/report/${state.currentReport.id}/pdf`;
        showToast('Preparing your PDF report...', 'success');
    } else {
        window.print();
    }
}

function openShareModal() {
    if (!state.currentReport) {
        showToast('No active report to share.', 'error');
        return;
    }

    const modal = document.getElementById('shareModal');
    const shareInput = document.getElementById('shareUrlInput');
    if (modal && shareInput) {
        const link = `${window.location.origin}/?tab=report&id=${state.currentReport.id || ''}`;
        shareInput.value = link;
        modal.classList.add('active');
    }
}

function closeShareModal() {
    const modal = document.getElementById('shareModal');
    if (modal) modal.classList.remove('active');
}

function copyShareLink() {
    const shareInput = document.getElementById('shareUrlInput');
    if (shareInput) {
        navigator.clipboard.writeText(shareInput.value)
            .then(() => showToast('Share link copied to clipboard!', 'success'));
    }
}

async function toggleSaveCurrentReport() {
    if (!state.currentReport || !state.currentReport.id) {
        showToast('Report cannot be saved yet.', 'error');
        return;
    }

    try {
        const res = await fetch(`/api/history/${state.currentReport.id}/save`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            const isSaved = data.is_saved === 1;
            showToast(isSaved ? 'Report bookmarked!' : 'Report removed from bookmarks.', 'success');
        }
    } catch (e) {
        showToast('Failed to update bookmark: ' + e.message, 'error');
    }
}

/* ==========================================================================
   Source Credibility Explorer
   ========================================================================== */

async function inspectSource() {
    const input = document.getElementById('sourceDomainInput').value.trim();
    if (!input) {
        showToast('Please enter a domain name (e.g. reuters.com, bbc.com, infowars.com).', 'error');
        return;
    }

    const resultsArea = document.getElementById('sourceExplorerResults');
    if (resultsArea) {
        resultsArea.innerHTML = '<div style="text-align:center; padding:30px; color:var(--accent-lime); font-family:var(--font-mono);">⚡ Querying global media index & inspecting DNS heuristics...</div>';
    }

    try {
        const res = await fetch(`/api/source?domain=${encodeURIComponent(input)}`);
        const data = await res.json();

        if (!data.success) {
            showToast(data.error || 'Source lookup failed.', 'error');
            return;
        }

        renderSourceResults(data.source);
    } catch (e) {
        showToast('Connection error: ' + e.message, 'error');
    }
}

function renderSourceResults(source) {
    const resultsArea = document.getElementById('sourceExplorerResults');
    if (!resultsArea) return;

    let scoreColor = 'var(--accent-lime)';
    if (source.trust_score < 40) scoreColor = 'var(--accent-coral)';
    else if (source.trust_score < 70) scoreColor = 'var(--warning)';

    let flagsHtml = '';
    if (source.flags && source.flags.length > 0) {
        flagsHtml = `
            <div style="margin-top:16px;">
                <span style="font-family:var(--font-mono); font-size:0.75rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Risk Indicators:</span>
                <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:6px;">
                    ${source.flags.map(f => `<span class="token-chip token-chip-fake">${f}</span>`).join('')}
                </div>
            </div>
        `;
    }

    let linksHtml = '';
    if (source.fact_check_links && source.fact_check_links.length > 0) {
        linksHtml = source.fact_check_links.map(l => `
            <a href="${l.url}" target="_blank" rel="noopener noreferrer" class="fact-check-link-item">
                <div>
                    <div style="font-weight:700; font-size:0.95rem; color:var(--text-cream);">${l.name}</div>
                    <div style="font-size:0.8rem; color:var(--text-muted);">${l.description}</div>
                </div>
                <span style="color:var(--accent-lime); font-size:1.15rem; font-weight:700;">↗</span>
            </a>
        `).join('');
    }

    resultsArea.innerHTML = `
        <div class="source-details-grid">
            <div class="glass-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:18px;">
                    <div>
                        <div class="badge-pill">${source.status}</div>
                        <h3 style="font-family:var(--font-heading); font-size:1.7rem; font-weight:800; color:var(--text-cream);">${source.name}</h3>
                        <span style="font-size:0.85rem; color:var(--text-muted); font-family:var(--font-mono);">${source.domain}</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:2.4rem; font-weight:900; font-family:var(--font-heading); color:${scoreColor};">
                            ${source.trust_score !== null ? source.trust_score : 'N/A'}
                        </div>
                        <span style="font-family:var(--font-mono); font-size:0.7rem; text-transform:uppercase; color:var(--text-muted); font-weight:700;">Trust Index</span>
                    </div>
                </div>

                <p style="color:var(--text-secondary); font-size:0.95rem; line-height:1.6; margin-bottom:18px;">
                    ${source.summary}
                </p>

                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:0.88rem; padding-top:16px; border-top:1px solid var(--border-card);">
                    <div><span style="color:var(--text-muted);">Category:</span> <strong>${source.category}</strong></div>
                    <div><span style="color:var(--text-muted);">Bias Rating:</span> <strong>${source.bias}</strong></div>
                    <div><span style="color:var(--text-muted);">Established:</span> <strong>${source.established}</strong></div>
                    <div><span style="color:var(--text-muted);">Ownership:</span> <strong>${source.ownership}</strong></div>
                </div>

                ${flagsHtml}
            </div>

            <div class="glass-card">
                <h4 style="font-family:var(--font-heading); font-size:1.2rem; font-weight:800; margin-bottom:16px; color:var(--text-cream);">
                    Verified Independent Watchdog Links
                </h4>
                <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:16px;">
                    Direct fact-check dossiers covering this publisher:
                </p>
                <div>${linksHtml}</div>
            </div>
        </div>
    `;
}

/* ==========================================================================
   AI News Explorer View
   ========================================================================== */

let activeCategoryFilter = 'All';

async function loadTrendingNews() {
    const container = document.getElementById('trendingNewsContainer');
    if (!container) return;

    try {
        const res = await fetch(`/api/history?limit=12&category=${activeCategoryFilter}`);
        const data = await res.json();

        if (!data.success || !data.history || data.history.length === 0) {
            container.innerHTML = '<div style="padding:40px; text-align:center; color:var(--text-muted);">No verified dispatches found in this category.</div>';
            return;
        }

        container.innerHTML = data.history.map(item => {
            const isReal = item.prediction === 'REAL';
            const badgeClass = isReal ? 'token-chip-real' : (item.prediction === 'FAKE' ? 'token-chip-fake' : 'token-chip');
            const badgeText = isReal ? 'Likely Real' : (item.prediction === 'FAKE' ? 'Likely Fake' : 'Verification Needed');

            return `
                <div class="glass-card" style="display:flex; flex-direction:column; justify-content:space-between;">
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                            <span class="badge-pill" style="margin-bottom:0;">${item.category}</span>
                            <span class="token-chip ${badgeClass}">${badgeText} (${item.confidence}%)</span>
                        </div>
                        <h4 style="font-family:var(--font-heading); font-size:1.15rem; font-weight:800; color:var(--text-cream); margin-bottom:10px; line-height:1.35;">
                            ${item.title}
                        </h4>
                        <p style="font-size:0.88rem; color:var(--text-secondary); line-height:1.55; margin-bottom:18px;">
                            ${item.content_snippet}
                        </p>
                    </div>

                    <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid var(--border-card); padding-top:14px;">
                        <span style="font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono);">
                            ${item.source_domain || 'Direct Stream'}
                        </span>
                        <button class="btn-secondary" style="padding:6px 14px; font-size:0.82rem;" onclick="viewHistoryItem(${item.id})">
                            Inspect ↗
                        </button>
                    </div>
                </div>
            `;
        }).join('');

    } catch (e) {
        container.innerHTML = '<div style="padding:40px; text-align:center; color:var(--accent-coral);">Failed to load news articles.</div>';
    }
}

function filterCategory(cat) {
    activeCategoryFilter = cat;
    document.querySelectorAll('.cat-pill-btn').forEach(btn => {
        if (btn.getAttribute('data-cat') === cat) btn.classList.add('active');
        else btn.classList.remove('active');
    });
    loadTrendingNews();
}

/* ==========================================================================
   Toast Notification System
   ========================================================================== */

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icon = type === 'success' ? '⚡' : (type === 'error' ? '🚨' : '✦');
    toast.innerHTML = `<span style="font-size:1.2rem;">${icon}</span><span style="font-size:0.92rem; font-weight:600;">${message}</span>`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4200);
}
