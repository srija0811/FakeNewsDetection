import io
import unittest
from unittest.mock import patch

from flask import Flask
from PIL import Image

from truthlens.routes import api


class ScanRouteTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.secret_key = "test-key"
        app.register_blueprint(api)
        self.client = app.test_client()

    def analyze_post(self, headline, text):
        with patch("truthlens.routes.save_analysis", return_value="test-scan-id"):
            return self.client.post(
                "/api/analyze",
                json={
                    "headline": headline,
                    "text": text,
                    "input_type": "social_post",
                    "ocr_text": f"{headline}\n{text}",
                    "ocr_language": "eng",
                },
            )

    def test_isro_chandrayaan_announcement_is_not_labeled_fake(self):
        response = self.analyze_post(
            "Chandrayaan-3",
            "Chandrayaan-3 has successfully soft-landed on the moon. Congratulations, India!",
        )

        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()["prediction"], "NEEDS_VERIFICATION")

    def test_article_fact_check_overrides_final_verdict_without_overwriting_model_output(self):
        model_result = {
            "title": "Chandrayaan-3",
            "category": "Science",
            "prediction": "NEEDS_VERIFICATION",
            "classification": "Needs Verification",
            "risk_level": "MODERATE",
            "confidence": 66.7,
            "credibility_score": 33.3,
            "content_snippet": "Chandrayaan-3 successfully soft-landed.",
            "manipulation_signals": [],
            "reasons": ["Model did not reach its decision threshold."],
            "verification_steps": [],
            "xai": {"top_fake_indicators": [], "top_real_indicators": []},
        }
        fact_check = {
            "status": "Supported",
            "summary": "ISRO confirms the dated landing claim.",
            "evidence": [{
                "source": "Indian Space Research Organisation (ISRO)",
                "url": "https://www.isro.gov.in/ISRO_EN/Chandrayaan3.html",
                "claim": "Chandrayaan-3 successfully soft-landed on the Moon on August 23, 2023.",
                "excerpt": "Chandrayaan-3 has successfully soft-landed on the moon.",
                "status": "Supports",
            }],
        }
        with (
            patch("truthlens.routes.engine.analyze", return_value=model_result),
            patch("truthlens.routes.verify_article_claims", return_value=fact_check),
            patch("truthlens.routes.save_analysis", return_value=54) as save_scan,
        ):
            response = self.client.post(
                "/api/analyze",
                json={
                    "headline": "Chandrayaan-3",
                    "text": "Chandrayaan-3 successfully soft-landed on the Moon on August 23, 2023.",
                    "input_type": "text",
                },
            )

        result = response.get_json()
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(result["prediction"], "REAL")
        self.assertEqual(result["model_prediction"], "NEEDS_VERIFICATION")
        self.assertEqual(result["fact_check_status"], "Supported")
        self.assertEqual(result["fact_check_evidence"], fact_check["evidence"])
        self.assertFalse(result["confidence_calibrated"])
        saved = save_scan.call_args.args[0]
        self.assertEqual(saved["prediction"], "REAL")
        self.assertEqual(saved["model_prediction"], "NEEDS_VERIFICATION")
        self.assertEqual(saved["category"], "Science")
        self.assertEqual(saved["fact_check_status"], "Supported")

    def test_article_fact_check_returns_fake_for_claim_contradicted_by_isro(self):
        model_result = {
            "title": "Chandrayaan-3",
            "category": "Science",
            "prediction": "REAL",
            "classification": "Likely Real",
            "risk_level": "LOW",
            "confidence": 81.0,
            "credibility_score": 81.0,
            "content_snippet": "Chandrayaan-3 never reached the Moon.",
            "manipulation_signals": [],
            "reasons": [],
            "verification_steps": [],
            "xai": {"top_fake_indicators": [], "top_real_indicators": []},
        }
        fact_check = {
            "status": "Contradicted",
            "summary": "ISRO confirms that Chandrayaan-3 launched and landed.",
            "evidence": [{
                "source": "Indian Space Research Organisation (ISRO)",
                "url": "https://www.isro.gov.in/ISRO_EN/Chandrayaan3.html",
                "claim": "Chandrayaan-3 never reached the Moon.",
                "excerpt": "Chandrayaan-3 has successfully soft-landed on the moon.",
                "status": "Contradicts",
            }],
        }
        with (
            patch("truthlens.routes.engine.analyze", return_value=model_result),
            patch("truthlens.routes.verify_article_claims", return_value=fact_check),
            patch("truthlens.routes.save_analysis", return_value=55) as save_scan,
        ):
            response = self.client.post(
                "/api/analyze",
                json={
                    "headline": "Chandrayaan-3",
                    "text": "The spacecraft never reached the Moon.",
                    "input_type": "text",
                },
            )

        result = response.get_json()
        self.assertEqual(response.status_code, 200, result)
        self.assertEqual(result["prediction"], "FAKE")
        self.assertEqual(result["model_prediction"], "REAL")
        self.assertEqual(result["fact_check_status"], "Contradicted")
        self.assertEqual(save_scan.call_args.args[0]["model_prediction"], "REAL")

    def test_exact_false_article_returns_fake_through_the_real_verifier_route(self):
        source_text = (
            "August 23, 2023 Chandrayaan-3 has successfully soft-landed on the moon. "
            "Congratulations, India! July 14, 2023 LVM3 M4 vehicle successfully launched "
            "Chandrayaan-3 into orbit."
        )
        article = (
            "Chandrayaan-3 was cancelled before launch in July 2023. "
            "The spacecraft never reached the Moon. "
            "The Vikram lander never performed a landing. "
            "India's August 23, 2023 landing reports are false."
        )
        with (
            patch(
                "truthlens.fact_verifier.extract_article_from_url",
                return_value={"success": True, "text": source_text},
            ),
            patch("truthlens.routes.save_analysis", return_value=56) as save_scan,
            self.assertLogs("truthlens.fact_verifier", level="WARNING") as diagnostic_logs,
        ):
            response = self.client.post(
                "/api/analyze",
                json={
                    "headline": "Chandrayaan-3",
                    "text": article,
                    "input_type": "text",
                },
            )

        result = response.get_json()
        self.assertEqual(response.status_code, 200, result)
        self.assertEqual(result["prediction"], "FAKE")
        self.assertEqual(result["classification"], "Likely Fake")
        self.assertEqual(result["fact_check_status"], "Contradicted")
        self.assertTrue(result["fact_check_evidence"])
        self.assertEqual(result["model_prediction"], save_scan.call_args.args[0]["model_prediction"])
        self.assertIn("extracted_claim", diagnostic_logs.output[0])
        self.assertIn("retrieved_sources", diagnostic_logs.output[0])
        self.assertIn("source_content", diagnostic_logs.output[0])
        self.assertIn("evidence_match", diagnostic_logs.output[0])
        self.assertIn("contradiction_detected", diagnostic_logs.output[0])

    def test_posts_do_not_use_the_news_article_classifier_as_a_verdict(self):
        response = self.analyze_post(
            "Viral post",
            "I am distributing cryptocurrency to users who retweet and verify their wallet key.",
        )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result["prediction"], "NEEDS_VERIFICATION")
        self.assertFalse(result["confidence_calibrated"])
        self.assertIn("social-media posts", result["reasons"][0])

    def test_image_scan_explicitly_returns_unverified_without_a_model(self):
        image_bytes = io.BytesIO()
        Image.new("RGB", (2, 2), color="white").save(image_bytes, format="PNG")
        image_bytes.seek(0)

        response = self.client.post(
            "/api/analyze-image",
            data={"file": (image_bytes, "post.png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result["prediction"], "NEEDS_VERIFICATION")
        self.assertEqual(result["authenticity"]["status"], "Unavailable")
        self.assertFalse(result["authenticity"]["model_available"])


if __name__ == "__main__":
    unittest.main()
