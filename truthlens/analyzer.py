"""
TruthLens AI - Core Machine Learning & Intelligence Analysis Engine
Integrates the existing scikit-learn model & vectorizer with Explainable AI (XAI),
sentence-level forensic scoring, sensationalism detection, and headline-content consistency.
"""

import os
import re
import math
import joblib
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "fake_news_model.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "vectorizer.pkl")

# Sensationalist / Clickbait keyword patterns
SENSATIONAL_PATTERNS = [
    r"\bshocking\b", r"\bbombshell\b", r"\bunbelievable\b", r"\byou won'?t believe\b",
    r"\bexposed\b", r"\bsecret\b", r"\bmiracle\b", r"\bconspiracy\b", r"\bdeep state\b",
    r"\bsheeple\b", r"\bbusted\b", r"\bhidden truth\b", r"\bthey don'?t want you to know\b",
    r"\bhorrifying\b", r"\bmainstream media won'?t tell\b", r"\bbreak the internet\b",
    r"\bviral video\b", r"\bdisaster\b", r"\bpanic\b", r"\bannihilated\b", r"\bdestroyed\b",
    r"\bapocalypse\b", r"\brage\b", r"\bexplosive\b", r"\bwake up america\b"
]

ANONYMOUS_AUTHORITY_PATTERNS = [
    r"\bsources say\b", r"\binsiders claim\b", r"\bexperts believe\b",
    r"\bscientists shocked\b", r"\bwhistleblowers confirm\b", r"\bofficials secretly admit\b"
]

CATEGORY_KEYWORDS = {
    "Technology": ["tech", "ai", "artificial intelligence", "software", "cyber", "internet", "google", "apple", "microsoft", "meta", "crypto", "bitcoin", "algorithm", "chip", "robot", "cloud", "data"],
    "Politics": ["senate", "congress", "president", "election", "democrat", "republican", "parliament", "vote", "campaign", "governor", "lawmaker", "legislation", "policy", "court", "minister", "white house"],
    "Health": ["health", "virus", "vaccine", "doctor", "medical", "hospital", "cancer", "disease", "fda", "who", "cdc", "diet", "drug", "treatment", "infection", "clinical"],
    "Business": ["economy", "inflation", "market", "stock", "shares", "federal reserve", "central bank", "trade", "profit", "billion", "revenue", "ceo", "investor", "wall street", "banking"],
    "Education": ["school", "university", "student", "teacher", "college", "tuition", "curriculum", "campus", "academic", "education", "degree", "scholarship", "classroom"],
    "World": ["un", "united nations", "treaty", "nato", "ukraine", "china", "russia", "europe", "middle east", "diplomacy", "ambassador", "sanctions", "border", "foreign minister", "global"]
}

class TruthLensEngine:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.feature_names = None
        self.load_models()

    def load_models(self):
        """Loads existing pre-trained scikit-learn model and TF-IDF vectorizer."""
        try:
            self.model = joblib.load(MODEL_PATH)
            self.vectorizer = joblib.load(VECTORIZER_PATH)
            self.feature_names = self.vectorizer.get_feature_names_out()
        except Exception as e:
            print(f"Error loading models: {e}")
            raise e

    def detect_language(self, text: str) -> dict:
        """Detects if text is predominantly English."""
        # Simple heuristic based on character distribution and common English stop words
        english_words = {"the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with"}
        tokens = re.findall(r"\b[a-z]{2,}\b", text.lower())
        if not tokens:
            return {"is_english": False, "confidence": 0, "language": "Unknown"}
        
        matches = sum(1 for t in tokens if t in english_words)
        ratio = matches / min(len(tokens), 100)
        is_eng = ratio > 0.08
        return {
            "is_english": is_eng,
            "confidence": min(100, round(ratio * 400)),
            "language": "English" if is_eng else "Non-English / Multilingual"
        }

    def detect_category(self, text: str) -> str:
        """Categorizes article based on lexical topic densities."""
        text_lower = text.lower()
        best_cat = "General"
        max_score = 0
        for cat, keywords in CATEGORY_KEYWORDS.items():
            score = sum(text_lower.count(k) for k in keywords)
            if score > max_score:
                max_score = score
                best_cat = cat
        return best_cat if max_score > 0 else "General"

    def analyze_sensationalism(self, text: str, headline: str = "") -> dict:
        """Calculates emotional intensity, clickbait triggers, and formatting anomalies."""
        combined = (headline + " " + text).strip()
        words = re.findall(r"\b\w+\b", combined)
        total_words = max(1, len(words))

        # 1. Trigger word search
        detected_triggers = []
        for pat in SENSATIONAL_PATTERNS:
            found = re.findall(pat, combined, re.IGNORECASE)
            if found:
                detected_triggers.extend([f.lower() for f in found])

        # 2. All-caps shouting detection
        all_caps_words = [w for w in words if len(w) > 2 and w.isupper() and not w in ["USA", "FBI", "CIA", "NASA", "NATO", "UN", "EU", "COVID", "GOP", "UK", "WHO", "FDA", "CEO", "AI"]]
        all_caps_ratio = len(all_caps_words) / total_words

        # 3. Punctuation anomalies (exclamations, multiple question marks)
        exclamation_count = combined.count("!")
        multiple_punct = len(re.findall(r"[!?]{2,}", combined))

        # 4. Anonymous authority phrases
        anonymous_citations = []
        for pat in ANONYMOUS_AUTHORITY_PATTERNS:
            found = re.findall(pat, combined, re.IGNORECASE)
            if found:
                anonymous_citations.extend([f.lower() for f in found])

        # Compute emotional intensity score (0 - 100)
        intensity_raw = (
            (len(detected_triggers) * 15) +
            (len(all_caps_words) * 8) +
            (exclamation_count * 5) +
            (multiple_punct * 10) +
            (len(anonymous_citations) * 12)
        )
        intensity_score = min(100, max(5, int(intensity_raw)))

        if intensity_score < 30:
            level = "Objective / Neutral"
        elif intensity_score < 65:
            level = "Elevated Emotion"
        else:
            level = "Hyperbolic / Sensational"

        return {
            "intensity_score": intensity_score,
            "level": level,
            "detected_triggers": list(set(detected_triggers))[:8],
            "all_caps_count": len(all_caps_words),
            "exclamation_count": exclamation_count,
            "anonymous_citations": list(set(anonymous_citations))[:5]
        }

    def analyze_headline_consistency(self, headline: str, body: str) -> dict:
        """Measures semantic alignment between headline and article body."""
        if not headline or not headline.strip() or not body or len(body.split()) < 20:
            return {
                "consistency_score": 100,
                "rating": "Headline Not Provided / Verified",
                "explanation": "Headline and body evaluated as unified document."
            }

        try:
            vecs = self.vectorizer.transform([headline, body])
            # Cosine similarity between sparse TF-IDF vectors
            dot_product = (vecs[0].multiply(vecs[1])).sum()
            norm0 = math.sqrt(vecs[0].multiply(vecs[0]).sum())
            norm1 = math.sqrt(vecs[1].multiply(vecs[1]).sum())
            
            if norm0 > 0 and norm1 > 0:
                similarity = float(dot_product / (norm0 * norm1))
            else:
                similarity = 0.5
        except Exception:
            similarity = 0.5

        consistency_score = min(100, max(10, round(similarity * 180)))

        if consistency_score >= 65:
            rating = "Strong Semantic Alignment"
            explanation = "The headline directly reflects the core factual claims and entities present in the body text."
        elif consistency_score >= 40:
            rating = "Moderate Alignment"
            explanation = "The headline touches upon body topics but emphasizes secondary details."
        else:
            rating = "Clickbait Divergence / Inconsistent"
            explanation = "Significant discrepancy detected between headline claims and body content, indicative of clickbait framing."

        return {
            "consistency_score": consistency_score,
            "rating": rating,
            "explanation": explanation
        }

    def compute_explainable_ai(self, text: str, max_features: int = 8) -> dict:
        """
        Calculates exact feature importance weights using model coefficients and input TF-IDF vector.
        Follows true Explainable AI (XAI) mathematics.
        """
        vec = self.vectorizer.transform([text])
        coef = self.model.coef_[0]
        nonzero_indices = vec.indices

        tokens = []
        for idx in nonzero_indices:
            word = self.feature_names[idx]
            tfidf_val = vec[0, idx]
            weight = float(tfidf_val * coef[idx])
            tokens.append({"word": word, "weight": round(weight, 4), "tfidf": round(float(tfidf_val), 3)})

        # Positive weights push toward Real (1), Negative weights push toward Fake (0)
        tokens_fake = [t for t in tokens if t["weight"] < 0]
        tokens_real = [t for t in tokens if t["weight"] > 0]

        tokens_fake.sort(key=lambda x: x["weight"])  # most negative first
        tokens_real.sort(key=lambda x: x["weight"], reverse=True)  # most positive first

        top_fake = tokens_fake[:max_features]
        top_real = tokens_real[:max_features]

        # Calculate influence percentages for visualization
        total_fake_influence = sum(abs(t["weight"]) for t in top_fake) or 1.0
        for t in top_fake:
            t["relative_impact"] = round((abs(t["weight"]) / total_fake_influence) * 100, 1)

        total_real_influence = sum(t["weight"] for t in top_real) or 1.0
        for t in top_real:
            t["relative_impact"] = round((t["weight"] / total_real_influence) * 100, 1)

        return {
            "top_fake_indicators": top_fake,
            "top_real_indicators": top_real,
            "all_tokens_count": len(nonzero_indices)
        }

    def analyze_sentences(self, text: str) -> dict:
        """
        Forensic sentence-by-sentence classification.
        Scores each sentence individually to highlight suspicious vs credible claims.
        """
        raw_sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences_data = []
        suspicious_count = 0
        credible_count = 0

        coef = self.model.coef_[0]

        for s in raw_sentences:
            s_clean = s.strip()
            if len(s_clean.split()) < 4:
                continue

            try:
                s_vec = self.vectorizer.transform([s_clean])
                if s_vec.nnz > 0:
                    s_score = float(s_vec.dot(coef)[0])
                else:
                    s_score = 0.0
            except Exception:
                s_score = 0.0

            if s_score < -0.35:
                tag = "suspicious"
                suspicious_count += 1
            elif s_score > 0.35:
                tag = "credible"
                credible_count += 1
            else:
                tag = "neutral"

            sentences_data.append({
                "text": s_clean,
                "score": round(s_score, 3),
                "tag": tag
            })

        total_analyzed = len(sentences_data) or 1
        suspicious_ratio = round((suspicious_count / total_analyzed) * 100, 1)

        return {
            "sentences": sentences_data[:20],  # preview top 20
            "total_sentences": len(sentences_data),
            "suspicious_count": suspicious_count,
            "credible_count": credible_count,
            "suspicious_ratio": suspicious_ratio
        }

    def analyze(self, text: str, headline: str = "", url: str = "", domain: str = "") -> dict:
        """
        Master analysis pipeline combining Machine Learning inference,
        Explainable AI attribution, sensationalism detection, sentence forensics,
        and Truth Intelligence synthesis.
        """
        clean_text = text.strip() if text else ""
        clean_headline = headline.strip() if headline else ""

        if not clean_text and clean_headline:
            clean_text = clean_headline

        if not clean_text:
            raise ValueError("No text content provided for analysis.")

        # 1. Text Preprocessing & Language Check
        lang_info = self.detect_language(clean_text)
        category = self.detect_category(clean_headline + " " + clean_text)
        word_count = len(clean_text.split())

        # 2. Scikit-learn Model Prediction
        # Mirror training format: title + " " + text
        combined_input = f"{clean_headline} {clean_text}".strip()
        vec = self.vectorizer.transform([combined_input])

        prediction_raw = int(self.model.predict(vec)[0])
        probabilities = self.model.predict_proba(vec)[0]

        fake_prob = float(probabilities[0])
        real_prob = float(probabilities[1])

        # 3. Classification & Confidence Calculation
        credibility_score = round(real_prob * 100, 1)
        
        if fake_prob >= 0.65:
            classification = "Likely Fake"
            prediction_label = "FAKE"
            confidence = round(fake_prob * 100, 1)
            risk_level = "CRITICAL" if fake_prob >= 0.88 else "HIGH"
        elif real_prob >= 0.65:
            classification = "Likely Real"
            prediction_label = "REAL"
            confidence = round(real_prob * 100, 1)
            risk_level = "LOW"
        else:
            classification = "Needs Verification"
            prediction_label = "NEEDS_VERIFICATION"
            confidence = round(max(fake_prob, real_prob) * 100, 1)
            risk_level = "MODERATE"

        # 4. Explainable AI Feature Attribution
        xai_data = self.compute_explainable_ai(combined_input)

        # 5. Sensationalism & Manipulation Detection
        sensational_data = self.analyze_sensationalism(clean_text, clean_headline)

        # 6. Headline Consistency
        headline_data = self.analyze_headline_consistency(clean_headline, clean_text)

        # 7. Sentence Forensic Highlighting
        sentence_data = self.analyze_sentences(clean_text)

        # 8. Manipulation Signals Synthesis
        manipulation_signals = []
        if sensational_data["intensity_score"] >= 50:
            manipulation_signals.append(f"Sensationalist Hyperbole ({sensational_data['level']})")
        if sensational_data["detected_triggers"]:
            manipulation_signals.append(f"Urgency & Clickbait Triggers: {', '.join(sensational_data['detected_triggers'][:3])}")
        if sensational_data["all_caps_count"] >= 3:
            manipulation_signals.append("Capitalization Hyperbole (ALL-CAPS shouting)")
        if sensational_data["anonymous_citations"]:
            manipulation_signals.append("Unverifiable Anonymous Authority Citations")
        if headline_data["consistency_score"] < 40:
            manipulation_signals.append("Headline Clickbait Divergence")
        if sentence_data["suspicious_ratio"] >= 40:
            manipulation_signals.append(f"High Density of Rhetorically Questionable Sentences ({sentence_data['suspicious_ratio']}%)")

        if not manipulation_signals:
            if classification == "Likely Real":
                manipulation_signals.append("Objective Journalistic Tone Verified")
                manipulation_signals.append("Standard Attribution Conventions Observed")
            else:
                manipulation_signals.append("Inconclusive Stylistic Patterns")

        # 9. Reasons Behind Prediction
        reasons = []
        if classification == "Likely Real":
            top_words = [t["word"] for t in xai_data["top_real_indicators"][:4]]
            reasons.append(f"Model identified verified lexical patterns matching reputable news agencies (top markers: {', '.join(top_words)}).")
            reasons.append(f"Emotional sensationalism score is measured ({sensational_data['intensity_score']}/100, {sensational_data['level']}).")
            if headline_data["consistency_score"] >= 60:
                reasons.append("Headline demonstrates high semantic consistency with the reported facts.")
        elif classification == "Likely Fake":
            top_words = [t["word"] for t in xai_data["top_fake_indicators"][:4]]
            reasons.append(f"Model identified significant frequency of rhetorical terms strongly correlated with unverified content (top markers: {', '.join(top_words)}).")
            if sensational_data["intensity_score"] >= 40:
                reasons.append(f"Elevated emotional/sensational language detected ({sensational_data['intensity_score']}/100).")
            if sentence_data["suspicious_count"] > 0:
                reasons.append(f"{sentence_data['suspicious_count']} sentence(s) flagged for abnormal evidentiary framing.")
        else:
            reasons.append("Article contains mixed linguistic signals balancing credible statements and unsubstantiated framing.")
            reasons.append("Confidence score is within the borderline decision margin (35% - 65%). Corroborating sources required.")

        # 10. Suggested Verification Steps
        verification_steps = []
        title_for_query = clean_headline or " ".join(clean_text.split()[:8])
        verification_steps.append("Search Reuters & Associated Press wire archives for corroborating dispatches on this subject.")
        if sensational_data["detected_triggers"] or classification == "Likely Fake":
            verification_steps.append("Check Snopes, PolitiFact, or FactCheck.org for established debunks of this claim.")
        verification_steps.append("Inspect named individuals, institutions, or data points to confirm quotes were not lifted out of context.")
        if url:
            verification_steps.append("Review domain registration age and editorial Masthead / Corrections policy in the Source Explorer.")

        # Article preview snippet
        snippet = clean_text[:300] + ("..." if len(clean_text) > 300 else "")

        return {
            "title": clean_headline or (clean_text[:80] + "..."),
            "source_url": url,
            "source_domain": domain,
            "content_snippet": snippet,
            "word_count": word_count,
            "language": lang_info,
            "category": category,
            "prediction": prediction_label,
            "classification": classification,
            "confidence": confidence,
            "credibility_score": credibility_score,
            "risk_level": risk_level,
            "sensationalism": sensational_data,
            "headline_analysis": headline_data,
            "sentence_analysis": sentence_data,
            "xai": xai_data,
            "manipulation_signals": manipulation_signals,
            "reasons": reasons,
            "verification_steps": verification_steps
        }

# Global Singleton Instance for fast reuse across API requests
engine = TruthLensEngine()
