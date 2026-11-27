"""
TRUTHLENS AI — Streamlit Companion Interface
For users running Streamlit explicitly via: streamlit run streamlit_app.py
"""

import streamlit as st
import joblib
import io
import re
import zipfile
from truthlens.analyzer import engine
from truthlens.source_checker import check_source_credibility


def extract_uploaded_article(uploaded_file):
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()
    if name.endswith((".txt", ".md", ".csv", ".html", ".htm")):
        text = data.decode("utf-8", errors="replace")
        if name.endswith((".html", ".htm")):
            text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", text, flags=re.I | re.S)
            text = re.sub(r"<[^>]+>", " ", text)
        return text
    if name.endswith(".pdf"):
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n\n".join((page.extract_text() or "") for page in reader.pages)
    if name.endswith(".docx"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
        paragraphs = re.findall(r"<w:p\b[^>]*>(.*?)</w:p>", xml, flags=re.DOTALL)
        lines = []
        for paragraph in paragraphs:
            paragraph = re.sub(r"<[^>]+>", "", paragraph)
            if paragraph.strip():
                lines.append(paragraph.strip())
        return "\n".join(lines)
    return ""

st.set_page_config(
    page_title="TRUTHLENS AI — See Beyond the Headline",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
.stApp {
    background-color: #070B14;
    color: #F8FAFC;
}
.metric-card {
    background: rgba(17, 27, 48, 0.75);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ TRUTHLENS AI — See Beyond the Headline")
st.markdown("### **THE INTERNET IS LOUD. FIND WHAT'S TRUE.**")
st.caption("Advanced Language Intelligence • Explainable Predictions • Trustworthy Verification")
st.markdown("*A next-generation AI-driven news intelligence platform engineered to detect misinformation in an era of information overload.*")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Verified Corpus", "44,898+")
col2.metric("Accuracy Precision", "98.69%")
col3.metric("Vocabulary Dimensions", "122,201")
col4.metric("Inference Latency", "<40ms")

st.markdown("---")

headline_input = st.text_input("Article Headline (Optional):", placeholder="e.g. As U.S. budget fight looms, Republicans flip their fiscal script...")
news_input = st.text_area("News Article Content / Claims:", placeholder="Paste full article text here for deep forensic verification...", height=180)

uploaded_article = st.file_uploader(
    "Upload newspaper or article",
    type=["txt", "md", "csv", "html", "htm", "pdf", "docx"],
    help="Upload a TXT, HTML, PDF, or DOCX article. The text is extracted and loaded for analysis."
)
if uploaded_article is not None:
    try:
        uploaded_text = extract_uploaded_article(uploaded_article).strip()
        if uploaded_text:
            lines = [line.strip() for line in uploaded_text.splitlines() if line.strip()]
            if not news_input.strip():
                news_input = "\n".join(lines[1:]).strip() if len(lines) > 1 else uploaded_text
                headline_input = lines[0][:180] if lines else uploaded_article.name
            st.success(f"Extracted text from {uploaded_article.name}")
        else:
            st.warning("No readable text was found in the uploaded document.")
    except Exception as error:
        st.error(f"Could not extract the uploaded file: {error}")

if st.button("🔍 Analyze Article", type="primary"):
    if not news_input.strip() and not headline_input.strip():
        st.warning("⚠️ Please enter news text or a headline to inspect.")
    else:
        with st.spinner("Executing high-dimensional TF-IDF vectorization and Explainable AI analysis..."):
            report = engine.analyze(text=news_input, headline=headline_input)
            confidence_text = (
                f" (Calibrated confidence: {report['confidence']}%)"
                if report.get("confidence_calibrated") is True else ""
            )

            st.markdown("---")
            if report["classification"] == "Likely Real":
                st.success(f"✅ Prediction: {report['classification'].upper()}{confidence_text}")
            elif report["classification"] == "Likely Fake":
                st.error(f"❌ Prediction: {report['classification'].upper()}{confidence_text}")
            else:
                st.warning(f"⚠️ Prediction: {report['classification'].upper()}{confidence_text}")

            st.subheader("📊 Truth Intelligence Report")
            c1, c2, c3 = st.columns(3)
            c1.metric(
                "Credibility Score",
                f"{report['credibility_score']}%"
                if report.get("confidence_calibrated") is True else "Not calibrated"
            )
            c2.metric("Risk Level", report["risk_level"])
            c3.metric("Sensationalism", f"{report['sensationalism']['intensity_score']}/100")

            st.markdown("### 🔬 Explainable AI (XAI) Attribution")
            st.write("**Top Real-Leaning Tokens:**", ", ".join([f"`{t['word']}`" for t in report['xai']['top_real_indicators']]))
            st.write("**Top Fake-Leaning Tokens:**", ", ".join([f"`{t['word']}`" for t in report['xai']['top_fake_indicators']]))

            st.markdown("### 🛡️ Evidence & Signals")
            for s in report["manipulation_signals"]:
                st.write(f"- {s}")

            st.markdown("### 📋 Suggested Verification Steps")
            for step in report["verification_steps"]:
                st.write(f"- [ ] {step}")

st.markdown("---")
st.info("💡 For the complete production experience with interactive radar scanner, source credibility explorer, user analytics dashboard, and printable PDF reports, run: `python app.py` and open http://localhost:8089")
st.caption("Developed by Chinta Akshaya Satya Srija | Upgraded to TRUTHLENS AI Production Platform")
