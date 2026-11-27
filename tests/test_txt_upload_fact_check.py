import io
import unittest
from unittest.mock import patch

from flask import Flask

from truthlens.routes import api
from truthlens.upload_fact_verifier import ICC_T20_2024_FINAL_URL


ARTICLE_HEADLINE = "India beat South Africa by seven runs"
ARTICLE_BODY = (
    "The T20 World Cup 2024 final took place on June 29, 2024. "
    "India defeated South Africa by seven runs to win the final."
)
ARTICLE_TEXT = f"{ARTICLE_HEADLINE}\n{ARTICLE_BODY}"
ICC_SOURCE = {
    "success": True,
    "title": "India return to heroes' welcome | ICC Men's T20 World Cup, 2024 | ICC",
    "text": (
        "India's triumphant T20 World Cup 2024 squad returned home. "
        "India ended a 13-year global event drought with victory in the final, "
        "defeating South Africa by seven runs on Saturday. Jasprit Bumrah was named Player of the Tournament."
    ),
    "date": "2024-07-04T00:45:51.286Z",
}


def model_result():
    return {
        "title": ARTICLE_HEADLINE,
        "category": "Sports",
        "prediction": "NEEDS_VERIFICATION",
        "classification": "Needs Verification",
        "risk_level": "MODERATE",
        "confidence": 72.0,
        "credibility_score": 28.0,
        "content_snippet": ARTICLE_BODY,
        "manipulation_signals": [],
        "reasons": [],
        "verification_steps": [],
        "xai": {"top_fake_indicators": [], "top_real_indicators": []},
    }


class TxtUploadFactCheckTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.secret_key = "test-key"
        app.register_blueprint(api)
        self.client = app.test_client()

    def upload_txt(self, content, filename="t20-final.txt"):
        return self.client.post(
            "/api/extract-file",
            data={"file": (io.BytesIO(content), filename)},
            content_type="multipart/form-data",
        )

    def analyze_upload(self, extracted):
        return self.client.post(
            "/api/analyze",
            json={
                "headline": extracted["headline"],
                "text": extracted["text"],
                "input_type": "document",
                "file_type": extracted["filename"],
            },
        )

    def test_txt_upload_extracts_the_complete_article(self):
        response = self.upload_txt(ARTICLE_TEXT.encode("utf-8"))

        self.assertEqual(response.status_code, 200)
        extracted = response.get_json()
        self.assertEqual(extracted["headline"], ARTICLE_HEADLINE)
        self.assertEqual(extracted["text"], ARTICLE_BODY)
        self.assertEqual(f"{extracted['headline']}\n{extracted['text']}", ARTICLE_TEXT)

    def test_utf8_and_utf8_bom_txt_uploads_extract_identical_text(self):
        regular = self.upload_txt(ARTICLE_TEXT.encode("utf-8"))
        with_bom = self.upload_txt(b"\xef\xbb\xbf" + ARTICLE_TEXT.encode("utf-8"))

        self.assertEqual(regular.status_code, 200)
        self.assertEqual(with_bom.status_code, 200)
        self.assertEqual(
            (with_bom.get_json()["headline"], with_bom.get_json()["text"]),
            (regular.get_json()["headline"], regular.get_json()["text"]),
        )
        self.assertFalse(with_bom.get_json()["headline"].startswith("\ufeff"))

    def test_single_line_upload_is_not_duplicated_and_matches_paste_analysis(self):
        article = (
            "India defeated South Africa by seven runs in the T20 World Cup 2024 final "
            "on June 29, 2024."
        )
        extracted_response = self.upload_txt(article.encode("utf-8"))
        self.assertEqual(extracted_response.status_code, 200)
        extracted = extracted_response.get_json()
        self.assertEqual(extracted["headline"], "")
        self.assertEqual(extracted["text"], article)

        analyzer_calls = []

        def capture_analyzer(**kwargs):
            analyzer_calls.append(kwargs)
            return model_result()

        with (
            patch("truthlens.routes.engine.analyze", side_effect=capture_analyzer),
            patch(
                "truthlens.routes.verify_article_claims",
                return_value={"status": "Unverified", "summary": "No match.", "evidence": []},
            ) as common_verifier,
            patch(
                "truthlens.routes.verify_uploaded_t20_final_claim",
                return_value={"status": "Unverified", "summary": "", "evidence": []},
            ),
            patch("truthlens.routes.save_analysis", return_value="scan-id"),
        ):
            upload_response = self.analyze_upload(extracted)
            paste_response = self.client.post(
                "/api/analyze",
                json={"text": article, "input_type": "text"},
            )

        self.assertEqual(upload_response.status_code, 200)
        self.assertEqual(paste_response.status_code, 200)
        self.assertEqual(len(analyzer_calls), 2)
        normalized_inputs = [
            f"{call['headline']}\n{call['text']}".strip()
            for call in analyzer_calls
        ]
        self.assertEqual(normalized_inputs, [article, article])
        self.assertEqual(
            [call.args[0].strip() for call in common_verifier.call_args_list],
            [article, article],
        )

    def test_upload_and_paste_send_equivalent_text_without_changing_paste_branch(self):
        uploaded = self.upload_txt(ARTICLE_TEXT.encode("utf-8")).get_json()
        analyzer_calls = []

        def capture_analyzer(**kwargs):
            analyzer_calls.append(kwargs)
            return model_result()

        with (
            patch("truthlens.routes.engine.analyze", side_effect=capture_analyzer),
            patch(
                "truthlens.routes.verify_article_claims",
                return_value={"status": "Unverified", "summary": "No match.", "evidence": []},
            ) as common_verifier,
            patch(
                "truthlens.routes.verify_uploaded_t20_final_claim",
                return_value={"status": "Unverified", "summary": "", "evidence": []},
            ) as upload_verifier,
            patch("truthlens.routes.save_analysis", return_value="scan-id"),
        ):
            upload_response = self.analyze_upload(uploaded)
            paste_response = self.client.post(
                "/api/analyze",
                json={"text": ARTICLE_TEXT, "input_type": "text"},
            )

        self.assertEqual(upload_response.status_code, 200)
        self.assertEqual(paste_response.status_code, 200)
        self.assertEqual(len(analyzer_calls), 2)
        upload_call, paste_call = analyzer_calls
        upload_analysis_text = f"{upload_call['headline']}\n{upload_call['text']}".strip()
        paste_analysis_text = f"{paste_call['headline']}\n{paste_call['text']}".strip()
        self.assertEqual(upload_analysis_text, paste_analysis_text)
        self.assertEqual(
            [call.args[0].strip() for call in common_verifier.call_args_list],
            [ARTICLE_TEXT, ARTICLE_TEXT],
        )
        upload_verifier.assert_called_once_with(ARTICLE_TEXT)

    def test_uploaded_txt_returns_icc_evidence_based_verdict(self):
        extracted_response = self.upload_txt(ARTICLE_TEXT.encode("utf-8"))
        self.assertEqual(extracted_response.status_code, 200)

        with (
            patch(
                "truthlens.upload_fact_verifier.extract_article_from_url",
                return_value=ICC_SOURCE,
            ) as fetch_icc,
            patch("truthlens.routes.save_analysis", return_value="uploaded-scan-id") as save_scan,
        ):
            response = self.analyze_upload(extracted_response.get_json())

        result = response.get_json()
        self.assertEqual(response.status_code, 200, result)
        self.assertEqual(result["prediction"], "REAL")
        self.assertEqual(result["fact_check_status"], "Supported")
        self.assertEqual(result["fact_check_evidence"][0]["source"], "International Cricket Council (ICC)")
        self.assertEqual(result["fact_check_evidence"][0]["url"], ICC_T20_2024_FINAL_URL)
        self.assertEqual(result["model_prediction"], save_scan.call_args.args[0]["model_prediction"])
        fetch_icc.assert_called_once_with(ICC_T20_2024_FINAL_URL)

    def test_empty_and_invalid_txt_uploads_are_rejected(self):
        missing = self.client.post(
            "/api/extract-file",
            data={},
            content_type="multipart/form-data",
        )
        empty = self.upload_txt(b"")
        invalid = self.upload_txt(b"not a supported article", "article.exe")

        self.assertEqual(missing.status_code, 400)
        self.assertEqual(empty.status_code, 422)
        self.assertEqual(invalid.status_code, 400)
        self.assertFalse(missing.get_json()["success"])
        self.assertFalse(empty.get_json()["success"])
        self.assertFalse(invalid.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
