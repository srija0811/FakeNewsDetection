import unittest

import numpy as np

from truthlens.analyzer import MIN_CLASSIFICATION_PROBABILITY, TruthLensEngine


class FixedVectorizer:
    def transform(self, texts):
        return texts


class FixedModel:
    def __init__(self, classes, probabilities):
        self.classes_ = np.asarray(classes)
        self.probabilities = probabilities

    def predict_proba(self, _vector):
        return np.asarray([self.probabilities])


def build_engine(classes, probabilities):
    engine = TruthLensEngine.__new__(TruthLensEngine)
    engine.model = FixedModel(classes, probabilities)
    engine.vectorizer = FixedVectorizer()
    engine.compute_explainable_ai = lambda _text: {
        "top_real_indicators": [],
        "top_fake_indicators": [],
    }
    engine.analyze_sensationalism = lambda *_args: {
        "intensity_score": 0,
        "level": "Low",
        "detected_triggers": [],
        "all_caps_count": 0,
        "anonymous_citations": [],
    }
    engine.analyze_headline_consistency = lambda *_args: {"consistency_score": 70}
    engine.analyze_sentences = lambda *_args: {
        "suspicious_count": 0,
        "suspicious_ratio": 0,
    }
    return engine


class AnalyzerPredictionTests(unittest.TestCase):
    def test_decision_threshold_is_eighty_percent(self):
        self.assertEqual(MIN_CLASSIFICATION_PROBABILITY, 0.80)

    def test_moderate_fake_probability_returns_unverified(self):
        engine = build_engine([0, 1], [0.7002, 0.2998])

        result = engine.analyze("The local council reported the latest update.")

        self.assertEqual(result["prediction"], "NEEDS_VERIFICATION")
        self.assertFalse(result["confidence_calibrated"])

    def test_high_probability_predictions_keep_their_labels(self):
        fake = build_engine([0, 1], [0.95, 0.05]).analyze(
            "The local council reported the latest update."
        )
        real = build_engine([0, 1], [0.05, 0.95]).analyze(
            "The local council reported the latest update."
        )

        self.assertEqual(fake["prediction"], "FAKE")
        self.assertEqual(real["prediction"], "REAL")

    def test_probability_order_follows_model_class_labels(self):
        result = build_engine([1, 0], [0.95, 0.05]).analyze(
            "The local council reported the latest update."
        )

        self.assertEqual(result["prediction"], "REAL")

    def test_non_english_input_is_unverified(self):
        result = build_engine([0, 1], [0.95, 0.05]).analyze(
            "ప్రభుత్వం ఈ రోజు కొత్త ప్రకటన విడుదల చేసింది."
        )

        self.assertEqual(result["prediction"], "NEEDS_VERIFICATION")


if __name__ == "__main__":
    unittest.main()
