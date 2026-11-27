import unittest
from unittest.mock import patch

from truthlens.fact_verifier import verify_article_claims


ISRO_SOURCE_TEXT = (
    "August 23, 2023 Chandrayaan-3 has successfully soft-landed on the moon. "
    "Congratulations, India! July 14, 2023 LVM3 M4 vehicle successfully launched "
    "Chandrayaan-3 into orbit."
)


class FactVerifierTests(unittest.TestCase):
    def test_isro_record_supports_the_dated_chandrayaan_landing_claim(self):
        with patch(
            "truthlens.fact_verifier.extract_article_from_url",
            return_value={"success": True, "text": ISRO_SOURCE_TEXT},
        ) as fetch_source:
            result = verify_article_claims(
                "On August 23, 2023, India's Chandrayaan-3 mission successfully landed "
                "on the Moon. The Vikram lander touched down and the Pragyan rover was deployed."
            )

        self.assertEqual(result["status"], "Supported")
        self.assertEqual(result["evidence"][0]["source"], "Indian Space Research Organisation (ISRO)")
        self.assertIn("successfully soft-landed", result["evidence"][0]["excerpt"])
        fetch_source.assert_called_once()

    def test_unmatched_claim_remains_unverified_without_a_source_lookup(self):
        with patch("truthlens.fact_verifier.extract_article_from_url") as fetch_source:
            result = verify_article_claims("A city council announced a new public transit plan.")

        self.assertEqual(result["status"], "Unverified")
        self.assertEqual(result["evidence"], [])
        fetch_source.assert_not_called()

    def test_false_launch_and_landing_claims_are_contradicted_by_isro(self):
        with patch(
            "truthlens.fact_verifier.extract_article_from_url",
            return_value={"success": True, "text": ISRO_SOURCE_TEXT},
        ):
            result = verify_article_claims(
                "Chandrayaan-3 was cancelled before launch in July 2023. "
                "The spacecraft never reached the Moon. "
                "The Vikram lander never performed a landing. "
                "India's August 23, 2023 landing reports are false."
            )

        self.assertEqual(result["status"], "Contradicted")
        self.assertEqual(len(result["evidence"]), 2)
        self.assertTrue(all(item["status"] == "Contradicts" for item in result["evidence"]))
        self.assertTrue(any("successfully soft-landed" in item["excerpt"] for item in result["evidence"]))
        self.assertTrue(any("successfully launched" in item["excerpt"] for item in result["evidence"]))

    def test_unrelated_unsupported_space_claim_remains_unverified(self):
        with patch("truthlens.fact_verifier.extract_article_from_url") as fetch_source:
            result = verify_article_claims(
                "Scientists are secretly planning a new mission to discover an unknown planet next month."
            )

        self.assertEqual(result["status"], "Unverified")
        self.assertEqual(result["evidence"], [])
        fetch_source.assert_not_called()


if __name__ == "__main__":
    unittest.main()
