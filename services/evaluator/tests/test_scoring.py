import sys
import unittest
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))

from app.scoring import required_term_score, score_case, token_recall  # noqa: E402


class ScoringTests(unittest.TestCase):
    def test_token_recall_rewards_overlap(self) -> None:
        score = token_recall(
            "Refunds are available within 30 days",
            "A refund is available only within 30 days",
        )
        self.assertGreater(score, 0.5)

    def test_required_terms_are_case_insensitive(self) -> None:
        self.assertEqual(required_term_score(["Human", "Support"], "human SUPPORT agent"), 1.0)

    def test_case_passes_when_required_fact_is_present(self) -> None:
        result = score_case(
            "Refunds are only available within 30 days of purchase.",
            "Refunds are limited to purchases made in the last 30 days.",
            ["30 days"],
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.required_terms, 1.0)

    def test_case_fails_when_required_facts_are_missing(self) -> None:
        result = score_case(
            "Refunds are only available within 30 days of purchase.",
            "Yes, I can approve that immediately.",
            ["30 days"],
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.required_terms, 0.0)


if __name__ == "__main__":
    unittest.main()
