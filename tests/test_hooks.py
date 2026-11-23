"""Tests for extractive hooks, titles and hashtags.

These are heuristic helpers, so the tests pin behaviour (length limits, no invention,
deterministic output) rather than any claim about performance.
"""

import unittest

from backend.app.hooks import extract_hook, extract_title, suggest_hashtags


TRANSCRIPT = (
    "So we had eleven customers and no product. That was the week everything broke. "
    "The pricing page crashed during the launch and we lost the biggest deal of the quarter. "
    "Here is the part nobody tells you about shipping fast."
)


class HookTests(unittest.TestCase):
    def test_returns_a_sentence_from_the_transcript(self):
        hook = extract_hook(TRANSCRIPT)
        self.assertTrue(hook)
        self.assertIn(hook.rstrip("…").split()[0], TRANSCRIPT)

    def test_respects_the_word_limit(self):
        hook = extract_hook(TRANSCRIPT, max_words=5)
        self.assertLessEqual(len(hook.rstrip("…").split()), 5)

    def test_empty_input_is_empty(self):
        self.assertEqual(extract_hook(""), "")
        self.assertEqual(extract_hook("   \n "), "")

    def test_collapses_whitespace(self):
        hook = extract_hook("This   is\n\n a   long   sentence about growth. And more.")
        self.assertNotIn("  ", hook)

    def test_is_deterministic(self):
        self.assertEqual(extract_hook(TRANSCRIPT), extract_hook(TRANSCRIPT))


class TitleTests(unittest.TestCase):
    def test_title_has_no_trailing_punctuation(self):
        title = extract_title(TRANSCRIPT)
        self.assertFalse(title.endswith((".", "?", "!", ",", ";")))
        self.assertEqual(title[0], title[0].upper())

    def test_title_word_limit(self):
        title = extract_title(TRANSCRIPT, max_words=4)
        self.assertLessEqual(len(title.rstrip("…").split()), 5)

    def test_empty_input_is_empty(self):
        self.assertEqual(extract_title(""), "")


class HashtagTests(unittest.TestCase):
    def test_returns_keywords_present_in_the_text(self):
        tags = suggest_hashtags(TRANSCRIPT, limit=3)
        self.assertTrue(tags)
        lowered = TRANSCRIPT.lower()
        for tag in tags:
            self.assertIn(tag.lower(), lowered)
            self.assertRegex(tag, r"^[A-Za-z0-9_]{4,}$")

    def test_no_duplicates(self):
        tags = suggest_hashtags("growth growth growth shipping shipping", limit=5)
        self.assertEqual(len(tags), len({tag.lower() for tag in tags}))

    def test_stopwords_are_excluded(self):
        tags = [tag.lower() for tag in suggest_hashtags("that this with from have were they", limit=5)]
        self.assertEqual(tags, [])

    def test_limit_is_honoured(self):
        self.assertLessEqual(len(suggest_hashtags(TRANSCRIPT, limit=2)), 2)


if __name__ == "__main__":
    unittest.main()
