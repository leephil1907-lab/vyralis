import unittest

from backend.app.main import score_candidate


class HighlightScoringTests(unittest.TestCase):
    def test_score_is_bounded_and_explainable(self):
        score, breakdown, reason = score_candidate(
            "Why did this invention change everything? Because the founder refused to give up.",
            34.0,
        )
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        self.assertEqual(set(breakdown), {"hook", "emotion", "clarity", "story", "pacing"})
        self.assertTrue(reason)

    def test_duration_changes_pacing_score(self):
        _, short_breakdown, _ = score_candidate("A clear story with a beginning and payoff.", 35)
        _, long_breakdown, _ = score_candidate("A clear story with a beginning and payoff.", 120)
        self.assertGreater(short_breakdown["pacing"], long_breakdown["pacing"])


if __name__ == "__main__":
    unittest.main()
