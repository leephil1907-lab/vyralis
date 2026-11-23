"""Tests for word-timed caption generation (ASS burn-in, SRT and VTT sidecars).

Everything here is pure string work, so it runs without FFmpeg or libass.
"""

import unittest

from backend.app.captions import (
    CAPTION_STYLES,
    ass_time,
    build_ass,
    build_srt,
    build_vtt,
    group_cues,
    srt_time,
    vtt_time,
    words_in_window,
)


def words(*items):
    return [{"start": start, "end": end, "text": text} for start, end, text in items]


SAMPLE = words(
    (0.0, 0.4, "Here"), (0.4, 0.7, "is"), (0.7, 1.2, "the"), (1.2, 1.6, "idea."),
    (3.4, 3.8, "Now"), (3.8, 4.2, "we"), (4.2, 4.9, "ship"), (4.9, 5.3, "it."),
)


class TimecodeTests(unittest.TestCase):
    def test_ass_time_uses_centiseconds(self):
        self.assertEqual(ass_time(0), "0:00:00.00")
        self.assertEqual(ass_time(65.25), "0:01:05.25")
        self.assertEqual(ass_time(-3), "0:00:00.00")

    def test_srt_and_vtt_timecodes(self):
        self.assertEqual(srt_time(1.5), "00:00:01,500")
        self.assertEqual(vtt_time(3661.004), "01:01:01.004")


class WindowTests(unittest.TestCase):
    def test_words_are_rebased_to_clip_start(self):
        window = words_in_window(SAMPLE, 3.0, 6.0)
        self.assertEqual([w["text"] for w in window], ["Now", "we", "ship", "it."])
        self.assertAlmostEqual(window[0]["start"], 0.4, places=3)

    def test_words_are_clipped_to_clip_end(self):
        window = words_in_window(SAMPLE, 0.0, 1.0)
        self.assertEqual(window[-1]["text"], "the")
        self.assertAlmostEqual(window[-1]["end"], 1.0, places=3)

    def test_ignores_broken_entries_and_empty_text(self):
        self.assertEqual(words_in_window([{"start": "x"}, {"start": 0, "end": 1, "text": "  "}], 0, 5), [])


class GroupingTests(unittest.TestCase):
    def test_breaks_on_silence(self):
        cues = group_cues(words_in_window(SAMPLE, 0.0, 6.0), per_cue=10)
        self.assertEqual(len(cues), 2)

    def test_breaks_on_cue_length(self):
        cues = group_cues(words_in_window(SAMPLE, 0.0, 6.0), per_cue=3)
        self.assertTrue(all(len(cue) <= 3 for cue in cues))

    def test_breaks_after_sentence_end(self):
        cues = group_cues(words_in_window(SAMPLE, 0.0, 6.0), per_cue=10, gap_break=5.0)
        self.assertGreaterEqual(len(cues), 2)


class AssTests(unittest.TestCase):
    def test_header_matches_export_frame(self):
        document = build_ass(SAMPLE, 0.0, 6.0, width=1080, height=1920, style="karaoke")
        self.assertIn("PlayResX: 1080", document)
        self.assertIn("PlayResY: 1920", document)
        self.assertIn("[V4+ Styles]", document)
        self.assertIn("[Events]", document)
        self.assertIn("Style: Caption", document)

    def test_karaoke_style_emits_sweep_tags(self):
        document = build_ass(SAMPLE, 0.0, 6.0, style="karaoke")
        self.assertIn(r"{\k", document)

    def test_clean_style_has_no_karaoke_tags(self):
        document = build_ass(SAMPLE, 0.0, 6.0, style="clean")
        self.assertNotIn(r"{\k", document)

    def test_impact_style_uppercases(self):
        document = build_ass(SAMPLE, 0.0, 6.0, style="impact")
        self.assertIn("HERE", document)

    def test_hook_is_a_separate_top_layer(self):
        document = build_ass(SAMPLE, 0.0, 6.0, hook="this changes everything")
        self.assertIn("Hook,,", document)
        self.assertIn("THIS CHANGES EVERYTHING", document)
        self.assertIn(r"\an8", document)

    def test_unknown_style_falls_back_to_default(self):
        document = build_ass(SAMPLE, 0.0, 6.0, style="nope")
        self.assertIn("Style: Caption", document)

    def test_wrapping_is_smart_so_long_hooks_wrap(self):
        self.assertIn("WrapStyle: 0", build_ass(SAMPLE, 0.0, 6.0))

    def test_long_hook_shrinks_to_fit_the_frame(self):
        document = build_ass(SAMPLE, 0.0, 6.0, style="impact",
                             hook="a very long hook line that would otherwise run off both edges of the frame")
        hook_style = next(line for line in document.splitlines() if line.startswith("Style: Hook"))
        caption_style = next(line for line in document.splitlines() if line.startswith("Style: Caption"))
        self.assertLess(int(hook_style.split(",")[2]), int(caption_style.split(",")[2]) * 1.15)

    def test_short_hook_keeps_the_enlarged_face(self):
        document = build_ass(SAMPLE, 0.0, 6.0, style="impact", hook="ship it")
        hook_style = next(line for line in document.splitlines() if line.startswith("Style: Hook"))
        caption_style = next(line for line in document.splitlines() if line.startswith("Style: Caption"))
        self.assertGreater(int(hook_style.split(",")[2]), int(caption_style.split(",")[2]))

    def test_text_cannot_inject_ass_overrides(self):
        poisoned = words((0.0, 1.0, "hello{\\an5}world"))
        document = build_ass(poisoned, 0.0, 1.0, style="clean")
        self.assertNotIn(r"{\an5}", document)

    def test_clip_without_words_still_produces_valid_document(self):
        document = build_ass([], 10.0, 20.0)
        self.assertIn("[Events]", document)

    def test_hook_is_clamped_to_the_clip_duration(self):
        document = build_ass(SAMPLE, 0.0, 1.0, hook="short clip")
        self.assertIn("0:00:00.00,0:00:01.00,Hook", document)

    def test_smaller_exports_scale_the_font(self):
        big = build_ass(SAMPLE, 0.0, 6.0, height=1920, style="clean")
        small = build_ass(SAMPLE, 0.0, 6.0, height=1080, style="clean")
        big_style = next(line for line in big.splitlines() if line.startswith("Style: Caption"))
        small_style = next(line for line in small.splitlines() if line.startswith("Style: Caption"))
        big_size = int(big_style.split(",")[2])
        small_size = int(small_style.split(",")[2])
        self.assertLess(small_size, big_size)


class SidecarTests(unittest.TestCase):
    def test_srt_has_sequential_blocks(self):
        document = build_srt(SAMPLE, 0.0, 6.0)
        self.assertTrue(document.startswith("1\n"))
        self.assertIn("00:00:00,000 --> ", document)
        self.assertIn("2\n", document)

    def test_vtt_starts_with_header(self):
        document = build_vtt(SAMPLE, 0.0, 6.0)
        self.assertTrue(document.startswith("WEBVTT"))
        self.assertIn("-->", document)

    def test_empty_window_yields_empty_srt(self):
        self.assertEqual(build_srt([], 0.0, 1.0), "")

    def test_every_style_produces_sidecars(self):
        for style in CAPTION_STYLES:
            with self.subTest(style=style):
                self.assertIn("-->", build_srt(SAMPLE, 0.0, 6.0, style))
                self.assertIn("-->", build_vtt(SAMPLE, 0.0, 6.0, style))


if __name__ == "__main__":
    unittest.main()
