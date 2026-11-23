"""
TRUTHLENS AI — Streamlit Companion Interface
For users running Streamlit explicitly via: streamlit run streamlit_app.py
"""

import streamlit as st
import joblib
from truthlens.analyzer import engine
from truthlens.source_checker import check_source_credibility

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

if st.button("🔍 Analyze Article", type="primary"):
    if not news_input.strip() and not headline_input.strip():
        st.warning("⚠️ Please enter news text or a headline to inspect.")
    else:
        with st.spinner("Executing high-dimensional TF-IDF vectorization and Explainable AI analysis..."):
            report = engine.analyze(text=news_input, headline=headline_input)

            st.markdown("---")
            if report["classification"] == "Likely Real":
                st.success(f"✅ Prediction: {report['classification'].upper()} (Confidence: {report['confidence']}%, Credibility: {report['credibility_score']}%)")
            elif report["classification"] == "Likely Fake":
                st.error(f"❌ Prediction: {report['classification'].upper()} (Confidence: {report['confidence']}%, Credibility: {report['credibility_score']}%)")
            else:
                st.warning(f"⚠️ Prediction: {report['classification'].upper()} (Confidence: {report['confidence']}%, Credibility: {report['credibility_score']}%)")

            st.subheader("📊 Truth Intelligence Report")
            c1, c2, c3 = st.columns(3)
            c1.metric("Credibility Score", f"{report['credibility_score']}%")
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
st.info("💡 For the complete production experience with interactive radar scanner, source credibility explorer, user analytics dashboard, and printable PDF reports, run: `python app.py` and open http://127.0.0.1:5000")
st.caption("Developed by Chinta Akshaya Satya Srija | Upgraded to TRUTHLENS AI Production Platform")
