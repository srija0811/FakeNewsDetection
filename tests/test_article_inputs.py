import io
import unittest
from unittest.mock import patch

from flask import Flask

from truthlens.routes import api


class ArticleInputRouteTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.secret_key = "test-key"
        app.register_blueprint(api)
        self.client = app.test_client()

    def test_uploaded_text_file_extracts_then_analyzes(self):
        uploaded = self.client.post(
            "/api/extract-file",
            data={"file": (io.BytesIO(b"Local council update\nThe council published its meeting schedule today."), "article.txt")},
            content_type="multipart/form-data",
        )

        self.assertEqual(uploaded.status_code, 200)
        extracted = uploaded.get_json()
        self.assertTrue(extracted["success"])
        self.assertEqual(extracted["headline"], "Local council update")
        self.assertIn("published its meeting schedule", extracted["text"])

        with patch("truthlens.routes.save_analysis", return_value="uploaded-test-id"):
            analyzed = self.client.post(
                "/api/analyze",
                json={
                    "headline": extracted["headline"],
                    "text": extracted["text"],
                    "input_type": "document",
                    "file_type": extracted["filename"],
                },
            )

        self.assertEqual(analyzed.status_code, 200)
        self.assertTrue(analyzed.get_json()["success"])

    def test_pasted_text_goes_directly_to_analysis_without_a_file(self):
        with patch("truthlens.routes.save_analysis", return_value="pasted-test-id"):
            response = self.client.post(
                "/api/analyze",
                json={
                    "text": "The city council published its meeting schedule today.",
                    "input_type": "text",
                    "file_type": "Paste Article Text",
                },
            )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertTrue(result["success"])
        self.assertEqual(result["input_type"], "text")

    def test_empty_pasted_text_is_rejected(self):
        response = self.client.post(
            "/api/analyze",
            json={"text": "   ", "input_type": "text"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])

    def test_unsupported_upload_extension_is_rejected(self):
        response = self.client.post(
            "/api/extract-file",
            data={"file": (io.BytesIO(b"not an article"), "article.exe")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
