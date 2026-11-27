import io
import unittest
from unittest.mock import patch

from flask import Flask
from PIL import Image

from truthlens.routes import api


class MediaUploadRouteTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.secret_key = "test-key"
        app.register_blueprint(api)
        self.client = app.test_client()

    def create_image(self, image_format):
        output = io.BytesIO()
        Image.new("RGB", (18, 12), color=(40, 100, 160)).save(output, format=image_format)
        output.seek(0)
        return output

    def test_screenshot_ocr_text_uses_post_only_route_without_news_classifier(self):
        ocr_text = "T20 WORLD CUP 2024 FINAL\nSouth Africa defeated India by five wickets."
        with (
            patch("truthlens.routes.engine.analyze") as article_classifier,
            patch("truthlens.routes.save_analysis", return_value=91) as save_scan,
        ):
            response = self.client.post(
                "/api/analyze-post-screenshot",
                json={
                    "ocr_text": ocr_text,
                    "file_type": "post-screen.png",
                    "ocr_language": "eng",
                },
            )

        result = response.get_json()
        self.assertEqual(response.status_code, 200, result)
        self.assertEqual(result["prediction"], "NEEDS_VERIFICATION")
        self.assertEqual(result["model_prediction"], "NOT_RUN")
        self.assertFalse(result["confidence_calibrated"])
        self.assertEqual(result["ocr_text"], ocr_text)
        self.assertEqual(result["input_type"], "social_post")
        self.assertIn("no reliable social-post verification source", result["fact_check_summary"])
        article_classifier.assert_not_called()
        self.assertEqual(save_scan.call_args.args[0]["ocr_text"], ocr_text)
        self.assertEqual(save_scan.call_args.args[0]["model_prediction"], "NOT_RUN")

    def test_screenshot_route_rejects_empty_ocr_and_unsupported_file_types(self):
        empty_text = self.client.post(
            "/api/analyze-post-screenshot",
            json={"ocr_text": "  ", "file_type": "post.png"},
        )
        invalid_type = self.client.post(
            "/api/analyze-post-screenshot",
            json={"ocr_text": "Some readable text", "file_type": "post.gif"},
        )

        self.assertEqual(empty_text.status_code, 400)
        self.assertIn("No readable text", empty_text.get_json()["error"])
        self.assertEqual(invalid_type.status_code, 400)
        self.assertIn("Unsupported screenshot format", invalid_type.get_json()["error"])

    def test_fake_image_route_decodes_supported_formats_without_authenticity_model(self):
        formats = (
            ("post.jpg", "JPEG"),
            ("post.jpeg", "JPEG"),
            ("post.png", "PNG"),
            ("post.webp", "WEBP"),
        )
        with patch("truthlens.routes.engine.analyze") as article_classifier:
            for filename, image_format in formats:
                with self.subTest(filename=filename):
                    response = self.client.post(
                        "/api/analyze-image",
                        data={
                            "file": (self.create_image(image_format), filename),
                            "save_to_history": "true",
                        },
                        content_type="multipart/form-data",
                    )

                    result = response.get_json()
                    self.assertEqual(response.status_code, 200, result)
                    self.assertEqual(result["prediction"], "NEEDS_VERIFICATION")
                    self.assertEqual(result["authenticity"]["status"], "Unavailable")
                    self.assertFalse(result["authenticity"]["model_available"])
                    self.assertEqual(result["authenticity"]["format"], image_format)
                    self.assertEqual(result["authenticity"]["dimensions"], {"width": 18, "height": 12})
        article_classifier.assert_not_called()

    def test_fake_image_route_rejects_mismatched_and_undecodable_uploads(self):
        png_as_jpeg = self.client.post(
            "/api/analyze-image",
            data={"file": (self.create_image("PNG"), "post.jpg")},
            content_type="multipart/form-data",
        )
        corrupted = self.client.post(
            "/api/analyze-image",
            data={"file": (io.BytesIO(b"not an image"), "post.png")},
            content_type="multipart/form-data",
        )

        self.assertEqual(png_as_jpeg.status_code, 400)
        self.assertIn("does not match", png_as_jpeg.get_json()["error"])
        self.assertEqual(corrupted.status_code, 400)
        self.assertIn("Could not inspect image", corrupted.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
