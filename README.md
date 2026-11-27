# TRUTHLENS AI — See Beyond the Headline 🛡️

**TRUTHLENS AI** is an advanced, production-quality news verification and Explainable AI (XAI) intelligence platform. It elevates traditional fake news detection into an auditable intelligence dashboard combining high-dimensional NLP forensics, transparent token attribution, domain reputation analysis, and sentence-level forensic highlighting.

---

## 🌟 Key Features

### 1. 🔬 Smart Multimodal News Verification
- **Text Verification**: Paste full news articles, quotes, or social media claims.
- **Autonomous URL Scraping**: Ingest articles directly from web URLs; extracts headline, body text, domain, author byline, and publication date.
- **Image / Screenshot OCR**: Upload news screenshots to extract textual claims for verification.
- **Language Detection & Text Preprocessing**: Ingests and normalizes articles across 122,201 TF-IDF semantic dimensions.

### 2. 📊 Truth Intelligence Report (Explainable AI)
- **Classification Verdict**: `Likely Real`, `Likely Fake`, or `Needs Verification`.
- **Credibility Score & ML Confidence**: Real-time probability estimation calculated directly from the pre-trained Logistic Regression model.
- **Explainable AI (XAI) Token Attribution**: Mathematically identifies the exact words that influenced the prediction (positive coefficients for Real wire style, negative coefficients for hoax rhetoric) with relative percentage impacts.
- **Sentence-by-Sentence Forensics**: Color-coded sentence highlighting (`[SUSPICIOUS PATTERN]` in rose, `[CREDIBLE WIRE PATTERN]` in emerald).
- **Sensationalism Intensity Index**: Evaluates emotional trigger words, clickbait patterns, and capitalization/punctuation anomalies (ALL-CAPS shouting, excessive exclamation).
- **Headline-Body Consistency Meter**: Cosine semantic coherence analysis between headline claims and body content.
- **Actionable Verification Checklist**: Context-specific investigative steps (wire cross-checks, debunk archives, author byline verification).

### 3. 🛡️ Source Credibility Explorer
- **Domain Reputation Registry**: Verified ratings for major global wire agencies (Reuters, AP, BBC, Bloomberg, Nature) and flagged disinformation networks.
- **Forensic URL Pattern Detection**: Detects typosquatting, high-risk TLDs (`.xyz`, `.click`, `.buzz`), numerical IP hosts, and hyphen abuse.
- **Unindexed Domain Principle**: Strictly follows journalistic integrity: *unindexed sources are marked for neutral corroboration, never presumed fake simply because they are unfamiliar.*
- **Direct Fact-Checking Links**: One-click searches on Reuters Fact Check, AP News, Snopes, PolitiFact, and FactCheck.org.

### 4. 🛰️ AI News Explorer
- Live feed of verified news items categorized by **Technology, Politics, Health, Business, Education, and World**.
- Instant keyword filtering and real source links.

### 5. 📈 User & Admin Dashboards
- **Analyst Dashboard**: Live KPI counters, Weekly Analysis Activity Chart, Category Distribution Chart, and paginated audit history table with search, bookmarks, and clear history.
- **Admin Console**: Real-time infrastructure telemetry, system health indicators (API latency, model memory status, database WAL), and Model Performance Evaluation with an interactive **Confusion Matrix** (Accuracy: 98.69%, Precision: 98.72%, Recall: 98.65%, F1-Score: 98.68%).

---

## 🚀 How to Run

### Method 1: Full-Stack Production Web Platform (Recommended)
Launches the Flask web server with the full cyber-navy UI, REST APIs, and SQLite database:

```bash
python app.py
```
Open your browser at: **[http://localhost:8089](http://localhost:8089)**

### Method 2: Streamlit Companion Interface
For users who prefer running Streamlit:

```bash
streamlit run app.py
# or
streamlit run streamlit_app.py
```

---

## 🏗️ Architecture & Project Structure

```
FakeNewsDetection/
├── app.py                     # Unified entrypoint (Flask platform or Streamlit runtime)
├── streamlit_app.py           # Dedicated Streamlit companion app
├── fake_news_model.pkl        # Pre-trained Logistic Regression model (Accuracy: 98.69%)
├── vectorizer.pkl             # Pre-trained TF-IDF vectorizer (122,201 features)
├── train_model.py             # Model training script & ISOT dataset pipeline
├── Fake.csv                   # ISOT dataset: Disinformation archive (23,481 rows)
├── True.csv                   # ISOT dataset: Reuters verified archive (21,417 rows)
├── truthlens.db               # SQLite database (auto-created on startup)
│
├── truthlens/                 # Core Intelligence Engine
│   ├── __init__.py
│   ├── analyzer.py            # Model inference, XAI token weights, sentence forensics
│   ├── source_checker.py      # Domain reputation, URL heuristics & watchdog links
│   ├── scraper.py             # URL content extractor with BeautifulSoup
│   ├── database.py            # SQLite schema, seed benchmarks & analytics
│   └── routes.py              # Flask Blueprint & REST API endpoints
│
├── templates/
│   └── index.html             # High-performance Single-Page Application (SPA)
│
└── static/
    ├── css/
    │   └── truthlens.css      # Midnight Cyber theme, glassmorphism, scanner animations
    └── js/
        └── truthlens.js       # Client state, Chart.js, PDF export, toasts, OCR
```

---

## 🛡️ Default Access Credentials

- **Admin Station**: Username `admin` | Password `admin123`
- **Analyst Station**: Username `researcher` | Password `demo123`
- Or click **Guest Analyst** in the bottom-left sidebar to sign in as any custom callsign.
