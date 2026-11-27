import unittest
from unittest.mock import patch

from flask import Flask

from truthlens.routes import api
from truthlens.upload_fact_verifier import ICC_T20_2024_FINAL_URL


ICC_REPORT = {
    "success": True,
    "title": "India return to heroes' welcome following T20 World Cup triumph",
    "text": (
        "India's triumphant T20 World Cup 2024 squad returned home. "
        "India ended a 13-year global event drought with victory in the final, "
        "defeating South Africa by seven runs on Saturday."
    ),
    "date": "2024-07-04T00:45:51.286Z",
}


def model_result():
    return {
        "title": "T20 World Cup final",
        "category": "Sports",
        "prediction": "FAKE",
        "classification": "Likely Fake",
        "risk_level": "HIGH",
        "confidence": 81.0,
        "credibility_score": 19.0,
        "content_snippet": "T20 World Cup final",
        "manipulation_signals": [],
        "reasons": [],
        "verification_steps": [],
        "xai": {"top_fake_indicators": [], "top_real_indicators": []},
    }


class T20FactVerifierRouteTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.secret_key = "test-key"
        app.register_blueprint(api)
        self.client = app.test_client()

    def analyze(self, headline, text):
        return self.client.post(
            "/api/analyze",
            json={"headline": headline, "text": text, "input_type": "text"},
        )

    def test_multiple_contradicted_result_claims_make_article_likely_fake(self):
        article = (
            "The 2024 T20 World Cup final ended with South Africa defeating India. "
            "South Africa chased 177 and won by five wickets. "
            "South Africa won its first Men's T20 World Cup. "
            "The ICC removed India's performance from tournament records."
        )
        with (
            patch(
                "truthlens.upload_fact_verifier.extract_article_from_url",
                return_value=ICC_REPORT,
            ) as fetch_icc,
            patch("truthlens.routes.engine.analyze", return_value=model_result()),
            patch("truthlens.routes.save_analysis", return_value=71),
        ):
            response = self.analyze("South Africa win the 2024 T20 World Cup final", article)

        result = response.get_json()
        self.assertEqual(response.status_code, 200, result)
        self.assertEqual(result["prediction"], "FAKE")
        self.assertEqual(result["model_prediction"], "FAKE")
        self.assertEqual(result["fact_check_status"], "Contradicted")
        self.assertTrue(any(item["status"] == "Contradicts" for item in result["fact_check_evidence"]))
        self.assertTrue(any(
            claim["kind"] == "margin" and claim["status"] == "Contradicts"
            for claim in result["fact_check_claims"]
        ))
        self.assertTrue(any(
            claim["kind"] == "unsupported_secondary" and claim["status"] == "Unverified"
            for claim in result["fact_check_claims"]
        ))
        self.assertTrue(any(
            claim["kind"] == "score" and claim["status"] == "Unverified"
            for claim in result["fact_check_claims"]
        ))
        self.assertTrue(any(
            item["status"] == "Contradicts" and "South Africa defeated India" in item["claim"]
            for item in result["fact_check_evidence"]
        ))
        fetch_icc.assert_called_once_with(ICC_T20_2024_FINAL_URL)

    def test_genuine_india_result_is_likely_real_without_overwriting_model_output(self):
        article = (
            "India's 176/7 was enough to beat South Africa's 169/8. "
            "India defeated South Africa by seven runs in the 2024 T20 World Cup final."
        )
        model = model_result()
        with (
            patch(
                "truthlens.upload_fact_verifier.extract_article_from_url",
                return_value=ICC_REPORT,
            ),
            patch("truthlens.routes.engine.analyze", return_value=model),
            patch("truthlens.routes.save_analysis", return_value=72) as save_scan,
        ):
            response = self.analyze("India win the T20 World Cup final", article)

        result = response.get_json()
        self.assertEqual(response.status_code, 200, result)
        self.assertEqual(result["prediction"], "REAL")
        self.assertEqual(result["model_prediction"], "FAKE")
        self.assertEqual(result["fact_check_status"], "Supported")
        self.assertTrue(result["fact_check_evidence"])
        self.assertTrue(all(item["url"] == ICC_T20_2024_FINAL_URL for item in result["fact_check_evidence"]))
        saved = save_scan.call_args.args[0]
        self.assertEqual(saved["prediction"], "REAL")
        self.assertEqual(saved["model_prediction"], "FAKE")

    def test_unrelated_unsupported_article_remains_unverified(self):
        with (
            patch("truthlens.upload_fact_verifier.extract_article_from_url") as fetch_icc,
            patch("truthlens.routes.engine.analyze", return_value=model_result()),
            patch("truthlens.routes.save_analysis", return_value=73),
        ):
            response = self.analyze(
                "Scientists announce an unknown planet discovery",
                "Researchers are planning a mission to study an unconfirmed planet next month.",
            )

        result = response.get_json()
        self.assertEqual(response.status_code, 200, result)
        self.assertEqual(result["prediction"], "NEEDS_VERIFICATION")
        self.assertEqual(result["fact_check_status"], "Unverified")
        fetch_icc.assert_not_called()

    def test_unsupported_secondary_claim_alone_does_not_make_article_fake(self):
        with (
            patch("truthlens.upload_fact_verifier.extract_article_from_url") as fetch_icc,
            patch("truthlens.routes.engine.analyze", return_value=model_result()),
            patch("truthlens.routes.save_analysis", return_value=74),
        ):
            response = self.analyze(
                "T20 World Cup 2024 final records",
                "The ICC removed India's performance from tournament records.",
            )

        result = response.get_json()
        self.assertEqual(response.status_code, 200, result)
        self.assertEqual(result["prediction"], "NEEDS_VERIFICATION")
        self.assertEqual(result["fact_check_status"], "Unverified")
        fetch_icc.assert_not_called()


if __name__ == "__main__":
    unittest.main()
