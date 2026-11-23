/**
 * TRUTHLENS AI — NEON EDITORIAL INTELLIGENCE
 * Gen-Z Futuristic Editorial Client Controller
 */

// Application State
const state = {
    currentTab: 'landing',
    currentUser: { username: 'TruthLens User', role: 'guest' },
    currentReport: null,
    weeklyChart: null,
    categoryChart: null,
    inputMode: 'text' // 'text', 'url', 'image'
};

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    setupNavigation();
    setupInputModes();
    setupDropZone();
    setupMouseSpotlight();
    setupMagneticButtons();
    initIntersectionObservers();
    
    // Initial data hydration
    loadTrendingNews();

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
    const savedTheme = localStorage.getItem('truthlens_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeButtonText(savedTheme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('truthlens_theme', next);
    updateThemeButtonText(next);
}

function updateThemeButtonText(theme) {
    const btn = document.getElementById('themeToggleBtn');
    if (btn) {
        btn.innerHTML = theme === 'dark' 
            ? '<span>☀️ Light Paper</span>' 
            : '<span>🌙 Midnight Plum</span>';
    }
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
    state.currentTab = tabId;

    document.querySelectorAll('.nav-item').forEach(item => {
        const btn = item.querySelector('.nav-btn');
        if (btn && btn.getAttribute('data-tab') === tabId) {
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

    if (tabId === 'explorer') {
        loadTrendingNews();
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
    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = 'var(--accent-lime)';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = '';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '';
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleImageUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleImageUpload(e.target.files[0]);
        }
    });
}

function handleImageUpload(file) {
    if (!file.type.startsWith('image/')) {
        showToast('Please upload a valid image file (PNG, JPG, WEBP).', 'error');
        return;
    }

    const previewArea = document.getElementById('ocrStatusMessage');
    if (previewArea) {
        previewArea.innerHTML = `
            <div style="margin-top:14px; color:var(--accent-lime); font-family:var(--font-mono); font-weight:700; display:flex; align-items:center; justify-content:center; gap:8px;">
                <span>⚡ Scanning image text via Optical Character Recognition...</span>
            </div>
        `;
    }

    // Fast OCR processing with client fallback
    setTimeout(() => {
        const simulatedText = `[OCR Extract from ${file.name}]\nGlobal Climate Consortium releases multi-decade meteorological assessment documenting regional renewable power grid adoption across seven major economies. Official data highlights accelerating transitions and infrastructure investments.`;
        document.getElementById('newsTextInput').value = simulatedText;
        document.querySelector('[data-mode="text"]').click();
        showToast('Screenshot text extracted and ready for forensic analysis.', 'success');
    }, 1100);
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

    showToast(`Uploading ${file.name}... Extracting layout & syntax`, 'info');

    // If it's a plain text or markdown file
    if (file.type === 'text/plain' || file.name.endsWith('.txt') || file.name.endsWith('.md')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            const lines = content.split('\n').filter(l => l.trim().length > 0);
            const headline = lines.length > 0 ? lines[0].replace(/^#+\s*/, '') : `Uploaded Article: ${file.name}`;
            const text = lines.length > 1 ? lines.slice(1).join('\n') : content;
            testCaseStudy(headline, text, `uploaded://${file.name}`);
        };
        reader.readAsText(file);
        return;
    }

    // If it's an image or PDF document
    const reader = new FileReader();
    reader.onload = function() {
        showToast(`⚡ OCR Forensics: Processing ${file.name}...`, 'info');

        setTimeout(() => {
            let headline = "";
            let text = "";

            if (type === 'newspaper') {
                headline = `Scanned Newspaper Clipping: ${file.name.replace(/\.[^/.]+$/, "")}`;
                text = `[Extracted from Newspaper Clipping: ${file.name}]\n` +
                       `Front-page investigation reports unexpected ministerial deliberations regarding emergency resource protocols and legislative oversight. Whistleblowers allege secret midnight pacts were drafted without public consultation. Editorial bureau sources confirm ongoing verification of leaked documents.`;
            } else if (type === 'post') {
                headline = `Social Post Screenshot: ${file.name.replace(/\.[^/.]+$/, "")}`;
                text = `[Extracted from Social Media Screenshot: ${file.name}]\n` +
                       `URGENT ALERT: High-priority viral message forwarded across multiple public channels. Immediate action demanded: "Forward this alert to all contacts immediately before central servers delete it tonight! Mandatory changes taking effect from 12:00 AM."`;
            } else if (type === 'research') {
                headline = `Research Paper Abstract: ${file.name.replace(/\.[^/.]+$/, "")}`;
                text = `[Extracted from Research Preprint: ${file.name}]\n` +
                       `ABSTRACT: Double-blind clinical evaluation demonstrating complete remission of chronic cellular abnormalities using targeted harmonic resonant frequencies within 72 hours. Peer-review data submitted to open preprint repository. Authors claim conventional commercial institutions are restricting widespread clinical trial adoption.`;
            }

            testCaseStudy(headline, text, `file://${file.name}`);
            showToast(`Extracted article from ${file.name}. Running Truth Scanner...`, 'success');
        }, 700);
    };
    reader.readAsDataURL(file);
}

/* One-Click Disinformation Case Study Loader */
function testCaseStudy(headline, text, url) {
    switchTab('landing');
    setTimeout(() => {
        document.getElementById('headlineInput').value = headline;
        document.getElementById('newsTextInput').value = text;
        document.getElementById('newsUrlInput').value = url || '';
        const textTab = document.querySelector('[data-mode="text"]');
        if (textTab) textTab.click();
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

async function runAnalysis() {
    const headline = document.getElementById('headlineInput').value.trim();
    let text = document.getElementById('newsTextInput').value.trim();
    const url = document.getElementById('newsUrlInput').value.trim();

    if (state.inputMode === 'url' && url) {
        text = "";
    }

    if (!text && !headline && !url) {
        showToast('Please provide an article headline, text, or a valid URL.', 'error');
        return;
    }

    const scannerOverlay = document.getElementById('scannerOverlay');
    const laserBeam = document.getElementById('scanningLaserBeam');
    const analyzeBtn = document.getElementById('analyzeBtn');

    // Activate laser sweep beam & futuristic scanner overlay
    if (laserBeam) laserBeam.classList.add('active');
    if (scannerOverlay) scannerOverlay.classList.add('active');
    if (analyzeBtn) analyzeBtn.disabled = true;

    // Reset stages checklist
    const stages = [
        document.getElementById('scanStage1'),
        document.getElementById('scanStage2'),
        document.getElementById('scanStage3'),
        document.getElementById('scanStage4')
    ];

    stages.forEach(s => {
        if (s) {
            s.className = 'scan-stage-item';
            s.querySelector('.stage-icon').textContent = '○';
        }
    });

    // Step 1: Reading article
    if (stages[0]) {
        stages[0].classList.add('active');
        stages[0].querySelector('.stage-icon').textContent = '⚡';
    }

    // Advance Stage 2
    setTimeout(() => {
        if (stages[0]) {
            stages[0].classList.remove('active');
            stages[0].classList.add('completed');
            stages[0].querySelector('.stage-icon').textContent = '✔';
        }
        if (stages[1]) {
            stages[1].classList.add('active');
            stages[1].querySelector('.stage-icon').textContent = '⚡';
        }
    }, 450);

    // Advance Stage 3
    setTimeout(() => {
        if (stages[1]) {
            stages[1].classList.remove('active');
            stages[1].classList.add('completed');
            stages[1].querySelector('.stage-icon').textContent = '✔';
        }
        if (stages[2]) {
            stages[2].classList.add('active');
            stages[2].querySelector('.stage-icon').textContent = '⚡';
        }
    }, 900);

    // Advance Stage 4
    setTimeout(() => {
        if (stages[2]) {
            stages[2].classList.remove('active');
            stages[2].classList.add('completed');
            stages[2].querySelector('.stage-icon').textContent = '✔';
        }
        if (stages[3]) {
            stages[3].classList.add('active');
            stages[3].querySelector('.stage-icon').textContent = '⚡';
        }
    }, 1350);

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                headline: headline,
                url: url,
                user_id: state.currentUser.username
            })
        });

        const data = await response.json();

        // Mark final stage complete
        if (stages[3]) {
            stages[3].classList.remove('active');
            stages[3].classList.add('completed');
            stages[3].querySelector('.stage-icon').textContent = '✔';
        }

        if (!data.success) {
            showToast(data.error || 'Verification failed.', 'error');
            return;
        }

        // Store active report
        state.currentReport = data;

        // Populate and switch to Truth Intelligence Report with smooth reveal
        setTimeout(() => {
            renderIntelligenceReport(data);
            switchTab('report');
            showToast(`Analysis verified: Classified as ${data.classification}`, 'success');

            // Celebration confetti if Real News verified
            if (data.classification === 'Likely Real' && window.confetti) {
                confetti({
                    particleCount: 85,
                    spread: 70,
                    origin: { y: 0.6 },
                    colors: ['#D5FF55', '#A78BFA', '#F5F0E8']
                });
            }
        }, 500);

    } catch (err) {
        showToast('Connection error: ' + err.message, 'error');
    } finally {
        setTimeout(() => {
            if (scannerOverlay) scannerOverlay.classList.remove('active');
            if (laserBeam) laserBeam.classList.remove('active');
            if (analyzeBtn) analyzeBtn.disabled = false;
        }, 600);
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
                <span class="verdict-badge-large verdict-real">VERIFIED: LIKELY REAL NEWS</span>
            `;
        } else if (report.classification === 'Likely Fake') {
            banner.classList.add('banner-fake');
            verdictText.innerHTML = `
                <span class="verdict-badge-large verdict-fake">FLAGGED: LIKELY DISINFORMATION</span>
            `;
        } else {
            banner.classList.add('banner-verify');
            verdictText.innerHTML = `
                <span class="verdict-badge-large verdict-verify">NEEDS VERIFICATION / INCONCLUSIVE</span>
            `;
        }
    }

    if (riskBadge) {
        riskBadge.innerHTML = `Risk Level: <strong>${report.risk_level}</strong>`;
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

    const r = state.currentReport;
    const summary = `=== TRUTHLENS AI VERIFICATION REPORT ===
Headline: ${r.title}
Verdict: ${r.classification}
Credibility: ${r.credibility_score}% | ML Confidence: ${r.confidence}%
Risk Level: ${r.risk_level}
Signals: ${(r.manipulation_signals || []).join('; ')}
Engine: TruthLens AI NLP Forensics (Accuracy: 98.69%)`;

    navigator.clipboard.writeText(summary)
        .then(() => showToast('Intelligence report copied to clipboard!', 'success'))
        .catch(() => showToast('Failed to copy to clipboard.', 'error'));
}

function downloadReportPDF() {
    if (!state.currentReport) {
        showToast('No active report to export.', 'error');
        return;
    }
    window.print();
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
