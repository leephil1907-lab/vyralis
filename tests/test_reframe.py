"""Tests for framing maths and the FFmpeg filter graph.

No encoding happens here: the graph is a string, so every layout can be checked
exactly, including the crop window staying inside the scaled frame.
"""

import unittest
from pathlib import Path

from backend.app.reframe import (
    DEFAULT_LAYOUT,
    LAYOUTS,
    build_filter,
    crop_plan,
    detect_focus_points,
    layout_report,
    plan_focus,
)


class FocusTests(unittest.TestCase):
    def test_no_points_returns_centre(self):
        self.assertEqual(plan_focus([]), 0.5)
        self.assertEqual(plan_focus(None, default=0.5), 0.5)

    def test_single_point_is_used(self):
        self.assertAlmostEqual(plan_focus([0.8]), 0.8)

    def test_out_of_range_points_are_clamped(self):
        self.assertAlmostEqual(plan_focus([-2.0]), 0.0)
        self.assertAlmostEqual(plan_focus([9.0]), 1.0)

    def test_smoothing_damps_a_jump(self):
        settled = plan_focus([0.2, 0.2, 0.2])
        jumped = plan_focus([0.2, 0.2, 0.9])
        self.assertAlmostEqual(settled, 0.2)
        self.assertGreater(jumped, settled)
        self.assertLess(jumped, 0.9)

    def test_none_entries_are_skipped(self):
        self.assertAlmostEqual(plan_focus([None, 0.4, None]), 0.4)


class CropPlanTests(unittest.TestCase):
    def test_landscape_source_is_cover_scaled_for_vertical(self):
        plan = crop_plan(1920, 1080, 1080, 1920)
        self.assertEqual(plan["out_w"], 1080)
        self.assertEqual(plan["out_h"], 1920)
        self.assertGreaterEqual(plan["scaled_w"], 1080)
        self.assertGreaterEqual(plan["scaled_h"], 1920)
        self.assertEqual(plan["scaled_w"] % 2, 0)
        self.assertEqual(plan["scaled_h"] % 2, 0)

    def test_crop_offsets_stay_inside_the_scaled_frame(self):
        for focus in (0.0, 0.25, 0.5, 0.75, 1.0):
            with self.subTest(focus=focus):
                plan = crop_plan(1920, 1080, 1080, 1920, focus_x=focus)
                self.assertGreaterEqual(plan["x"], 0)
                self.assertGreaterEqual(plan["y"], 0)
                self.assertLessEqual(plan["x"] + plan["out_w"], plan["scaled_w"])
                self.assertLessEqual(plan["y"] + plan["out_h"], plan["scaled_h"])

    def test_focus_shifts_the_window(self):
        left = crop_plan(1920, 1080, 1080, 1920, focus_x=0.1)
        right = crop_plan(1920, 1080, 1080, 1920, focus_x=0.9)
        self.assertLess(left["x"], right["x"])

    def test_rejects_zero_dimensions(self):
        with self.assertRaises(ValueError):
            crop_plan(0, 1080, 1080, 1920)

    def test_odd_targets_are_made_even(self):
        plan = crop_plan(1280, 720, 1081, 1921)
        self.assertEqual(plan["out_w"], 1080)
        self.assertEqual(plan["out_h"], 1920)


class FilterTests(unittest.TestCase):
    def test_center_layout_ends_in_vout(self):
        graph = build_filter(layout="center", src_w=1920, src_h=1080, out_w=1080, out_h=1920)
        self.assertIn("[0:v]scale=", graph)
        self.assertIn("crop=1080:1920", graph)
        self.assertIn("setsar=1", graph)
        self.assertTrue(graph.endswith("[vout]"))
        self.assertEqual(graph.count("[vout]"), 1)

    def test_blur_layout_composites_two_streams(self):
        graph = build_filter(layout="blur", src_w=1920, src_h=1080, out_w=1080, out_h=1920)
        self.assertIn("[0:v]split=2", graph)
        self.assertIn("gblur=sigma=28", graph)
        self.assertEqual(graph.count("[0:v]"), 1)
        self.assertIn("force_original_aspect_ratio=decrease", graph)
        self.assertIn("overlay=(W-w)/2:(H-h)/2", graph)
        self.assertTrue(graph.endswith("[vout]"))

    def test_ass_path_is_burned_in_and_escaped(self):
        graph = build_filter(
            layout="center", src_w=1920, src_h=1080, out_w=1080, out_h=1920,
            ass_path=Path("/tmp/vy ralis/out.ass"),
        )
        self.assertIn("subtitles=filename=", graph)
        self.assertIn("/tmp/vy ralis/out.ass", graph)
        self.assertIn("[base]subtitles=", graph)

    def test_without_captions_the_graph_still_has_a_vout_label(self):
        graph = build_filter(layout="center", src_w=1920, src_h=1080, out_w=1080, out_h=1920, ass_path=None)
        self.assertIn("[base]null[vout]", graph)

    def test_unbalanced_brackets_are_avoided(self):
        for layout in LAYOUTS:
            with self.subTest(layout=layout):
                graph = build_filter(layout=layout, src_w=1920, src_h=1080, out_w=1080, out_h=1920)
                self.assertEqual(graph.count("["), graph.count("]"))


class ReportTests(unittest.TestCase):
    def test_untracked_layout_is_reported_honestly(self):
        report = layout_report("face", [])
        self.assertFalse(report["tracked"])
        self.assertIn("Centre crop", report["note"])

    def test_tracked_layout_is_reported(self):
        report = layout_report("face", [0.4, 0.5])
        self.assertTrue(report["tracked"])
        self.assertEqual(report["samples"], 2)

    def test_unknown_layout_falls_back(self):
        self.assertEqual(layout_report("nope", [])["layout"], DEFAULT_LAYOUT)

    def test_detection_is_optional(self):
        # Without the vision extra this returns an empty list instead of raising.
        self.assertEqual(detect_focus_points(Path("/nonexistent.mp4"), samples=1), [])


if __name__ == "__main__":
    unittest.main()
