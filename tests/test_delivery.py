"""Tests for export presets, render quality inspection and packaging approval.

These run without FFmpeg, a whisper model or a network connection. Media-dependent
behaviour is covered by the measurements the API feeds into ``evaluate_export``.
"""

import json
import os
import tempfile
import unittest

os.environ.setdefault("VYRALIS_DATA_DIR", tempfile.mkdtemp(prefix="vyralis-tests-"))

from backend.app.delivery import (  # noqa: E402
    approval_gate,
    evaluate_export,
    normalize_hashtags,
    preset_geometry,
    preset_list,
    validate_packaging,
)


def clean_probe(**overrides):
    probe = {
        "duration_seconds": 30.0,
        "size_bytes": 4_000_000,
        "width": 1080,
        "height": 1920,
        "video_codec": "h264",
        "audio_codec": "aac",
        "has_video": True,
        "has_audio": True,
    }
    probe.update(overrides)
    return probe


class PresetTests(unittest.TestCase):
    def test_known_presets_have_expected_geometry(self):
        self.assertEqual(preset_geometry("9:16"), (1080, 1920))
        self.assertEqual(preset_geometry("1:1"), (1080, 1080))
        self.assertEqual(preset_geometry("16:9"), (1920, 1080))

    def test_unknown_preset_is_rejected(self):
        with self.assertRaises(ValueError):
            preset_geometry("4:3")

    def test_preset_list_is_serialisable(self):
        self.assertEqual({item["preset"] for item in preset_list()}, {"9:16", "1:1", "16:9"})


class QualityInspectionTests(unittest.TestCase):
    def test_clean_render_passes(self):
        report = evaluate_export(
            expected_duration=30, preset="9:16", probe=clean_probe(), mean_volume_db=-18.4
        )
        self.assertEqual(report["status"], "pass")
        self.assertTrue(all(check["status"] == "pass" for check in report["checks"]))
        self.assertEqual(report["metrics"]["width"], 1080)

    def test_duration_drift_fails(self):
        report = evaluate_export(
            expected_duration=30, preset="9:16", probe=clean_probe(duration_seconds=12.0), mean_volume_db=-18.4
        )
        self.assertEqual(report["status"], "fail")
        self.assertIn("Duration", report["summary"])

    def test_wrong_frame_size_fails(self):
        report = evaluate_export(
            expected_duration=30, preset="9:16", probe=clean_probe(width=1920, height=1080), mean_volume_db=-18.4
        )
        self.assertEqual(report["status"], "fail")
        dimensions = next(check for check in report["checks"] if check["id"] == "dimensions")
        self.assertEqual(dimensions["status"], "fail")

    def test_landscape_render_rejected_for_vertical_preset(self):
        report = evaluate_export(
            expected_duration=30, preset="9:16", probe=clean_probe(width=1920, height=1080), mean_volume_db=-18.4
        )
        self.assertEqual(report["status"], "fail")

    def test_landscape_preset_requires_landscape_dimensions(self):
        good = evaluate_export(
            expected_duration=30, preset="16:9", probe=clean_probe(width=1920, height=1080), mean_volume_db=-18.4
        )
        self.assertEqual(good["status"], "pass")
        transposed = evaluate_export(
            expected_duration=30, preset="16:9", probe=clean_probe(width=1080, height=1920), mean_volume_db=-18.4
        )
        dimensions = next(check for check in transposed["checks"] if check["id"] == "dimensions")
        self.assertEqual(dimensions["status"], "fail")

    def test_black_frames_fail(self):
        report = evaluate_export(
            expected_duration=30, preset="9:16", probe=clean_probe(), black_seconds=6.0, mean_volume_db=-18.4
        )
        self.assertEqual(report["status"], "fail")
        self.assertIn("Black frames", report["summary"])

    def test_short_black_span_only_warns(self):
        report = evaluate_export(
            expected_duration=30, preset="9:16", probe=clean_probe(), black_seconds=0.4, mean_volume_db=-18.4
        )
        self.assertEqual(report["status"], "warn")

    def test_silent_audio_fails(self):
        report = evaluate_export(
            expected_duration=30, preset="9:16", probe=clean_probe(), mean_volume_db=-72.0
        )
        self.assertEqual(report["status"], "fail")
        self.assertIn("Audio level", report["summary"])

    def test_missing_audio_warns_instead_of_failing(self):
        report = evaluate_export(
            expected_duration=30, preset="9:16",
            probe=clean_probe(has_audio=False, audio_codec=None), mean_volume_db=None,
        )
        self.assertEqual(report["status"], "warn")

    def test_empty_file_fails(self):
        report = evaluate_export(
            expected_duration=30, preset="9:16", probe=clean_probe(size_bytes=10), mean_volume_db=-18.4
        )
        self.assertEqual(report["status"], "fail")
        self.assertIn("File integrity", report["summary"])

    def test_entirely_frozen_render_fails(self):
        report = evaluate_export(
            expected_duration=30, preset="9:16", probe=clean_probe(), frozen_seconds=29.0, mean_volume_db=-18.4
        )
        self.assertEqual(report["status"], "fail")

    def test_report_is_json_serialisable(self):
        report = evaluate_export(
            expected_duration=15, preset="1:1", probe=clean_probe(width=1080, height=1080), mean_volume_db=-20.0
        )
        self.assertIsInstance(json.dumps(report), str)
        self.assertEqual({"status", "summary", "checks", "metrics"}, set(report))
        self.assertEqual(len(report["checks"]), 8)


class PackagingTests(unittest.TestCase):
    def test_hashtags_are_normalised_and_deduplicated(self):
        self.assertEqual(normalize_hashtags(["#Startup", "startup", " #founder ", "", "founder"]), ["Startup", "founder"])

    def test_valid_packaging(self):
        result = validate_packaging(
            destination="youtube_shorts",
            title="The pivot that changed everything",
            description="A short excerpt.",
            hashtags=["startup", "founder"],
        )
        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["counts"]["hashtags"], 2)

    def test_title_length_enforced_per_destination(self):
        result = validate_packaging(destination="youtube_shorts", title="x" * 101, hashtags=[])
        self.assertFalse(result["valid"])
        self.assertTrue(any("100" in error for error in result["errors"]))

    def test_empty_title_is_blocking(self):
        result = validate_packaging(destination="tiktok", title="   ")
        self.assertFalse(result["valid"])

    def test_unsupported_hashtag_characters_are_blocking(self):
        result = validate_packaging(destination="tiktok", title="A descriptive title", hashtags=["bad tag!"])
        self.assertFalse(result["valid"])

    def test_hashtag_limit_enforced(self):
        result = validate_packaging(destination="youtube_shorts", title="A descriptive title", hashtags=[f"tag{i}" for i in range(16)])
        self.assertEqual(result["counts"]["hashtags"], 16)
        self.assertFalse(result["valid"])

    def test_missing_hashtags_only_warns(self):
        result = validate_packaging(destination="instagram_reels", title="A descriptive title", hashtags=[])
        self.assertTrue(result["valid"])
        self.assertTrue(result["warnings"])

    def test_short_title_warns(self):
        result = validate_packaging(destination="tiktok", title="Short", hashtags=["topic"])
        self.assertTrue(result["valid"])
        self.assertTrue(any("12 characters" in warning for warning in result["warnings"]))

    def test_unknown_destination_rejected(self):
        with self.assertRaises(ValueError):
            validate_packaging(destination="myspace", title="Anything")


class ApprovalGateTests(unittest.TestCase):
    def test_requires_a_validated_export(self):
        gate = approval_gate(quality_status=None, packaging_valid=True, destination="tiktok")
        self.assertFalse(gate["allowed"])
        self.assertIn("Render the clip first", gate["blockers"][0])

    def test_failed_render_blocks_approval(self):
        gate = approval_gate(quality_status="fail", packaging_valid=True, destination="tiktok")
        self.assertFalse(gate["allowed"])

    def test_warned_render_can_be_approved(self):
        gate = approval_gate(quality_status="warn", packaging_valid=True, destination="tiktok")
        self.assertTrue(gate["allowed"])

    def test_invalid_packaging_blocks_approval(self):
        gate = approval_gate(quality_status="pass", packaging_valid=False, destination="tiktok")
        self.assertFalse(gate["allowed"])


class PackagingPersistenceTests(unittest.TestCase):
    """Exercises the SQLite layer used by the packaging endpoints, without HTTP or FFmpeg."""

    def setUp(self):
        from backend.app import main

        self.main = main
        main.init_db()
        with main.connect() as db:
            db.execute("INSERT OR REPLACE INTO assets(id,filename,size,content_type,path,created_at) VALUES('asset-test','demo.mp4',1024,'video/mp4','/tmp/demo.mp4',?)", (main.now(),))
            db.execute("INSERT OR REPLACE INTO projects(id,asset_id,title,status,created_at,updated_at) VALUES('project-test','asset-test','Demo','review',?,?)", (main.now(), main.now()))
            db.execute(
                "INSERT OR REPLACE INTO clips(id,project_id,rank,start_seconds,end_seconds,score,score_breakdown,reason,transcript,title,status,created_at) "
                "VALUES('clip-test','project-test',1,0,30,72,?,?,?,?,?,?)",
                (json.dumps({"hook": 70, "emotion": 60, "clarity": 80, "story": 75, "pacing": 75}),
                 "Heuristic reason.", "A founder explains why the first draft failed and what changed.", "Founder story", "ready", main.now()),
            )
            db.execute("DELETE FROM clip_packaging WHERE clip_id='clip-test'")
            db.execute("DELETE FROM clip_exports WHERE clip_id='clip-test'")

    def test_defaults_come_from_the_transcript(self):
        payloads = self.main.get_packaging("clip-test")
        self.assertEqual(len(payloads), 4)
        tiktok = next(item for item in payloads if item["destination"] == "tiktok")
        self.assertIn("founder", tiktok["title"].lower())
        self.assertTrue(tiktok["description"].startswith("A founder explains"))
        self.assertFalse(tiktok["approved"])
        self.assertFalse(tiktok["approval_gate"]["allowed"])

    def test_approval_is_blocked_until_a_render_is_ready(self):
        self.main.save_packaging("clip-test", self.main.PackagingRequest(
            destination="tiktok", title="A founder explains the first draft", description="Excerpt.", hashtags=["startup"],
        ))
        with self.assertRaises(Exception) as caught:
            self.main.approve_packaging("clip-test", self.main.ApprovalRequest(destination="tiktok", approved=True))
        self.assertIn("Render the clip first", str(caught.exception))

    def test_approval_succeeds_after_a_passing_render(self):
        from backend.app.delivery import evaluate_export

        report = evaluate_export(expected_duration=30, preset="9:16", probe={
            "duration_seconds": 30.0, "size_bytes": 4_000_000, "width": 1080, "height": 1920,
            "video_codec": "h264", "audio_codec": "aac", "has_video": True, "has_audio": True,
        }, mean_volume_db=-18.0)
        with self.main.connect() as db:
            db.execute(
                "INSERT INTO clip_exports(id,clip_id,preset,status,job_id,output_path,width,height,duration_seconds,quality_report,error,created_at,updated_at) "
                "VALUES('export-test','clip-test','9:16','ready',NULL,'/tmp/render.mp4',1080,1920,30,?,NULL,?,?)",
                (json.dumps(report), self.main.now(), self.main.now()),
            )
        self.main.save_packaging("clip-test", self.main.PackagingRequest(
            destination="tiktok", title="A founder explains the first draft", description="Excerpt.", hashtags=["startup"],
        ))
        approved = self.main.approve_packaging("clip-test", self.main.ApprovalRequest(destination="tiktok", approved=True))
        self.assertTrue(approved["approved"])
        self.assertTrue(approved["eligible"])
        self.assertEqual(approved["export"]["quality_status"], "pass")

        packages = self.main.publish_packages()
        self.assertEqual(len(packages["packages"]), 1)
        self.assertIn("nothing is posted", packages["note"])

    def test_editing_copy_revokes_approval(self):
        from backend.app.delivery import evaluate_export

        report = evaluate_export(expected_duration=30, preset="9:16", probe={
            "duration_seconds": 30.0, "size_bytes": 4_000_000, "width": 1080, "height": 1920,
            "video_codec": "h264", "audio_codec": "aac", "has_video": True, "has_audio": True,
        }, mean_volume_db=-18.0)
        with self.main.connect() as db:
            db.execute("DELETE FROM clip_exports WHERE clip_id='clip-test'")
            db.execute(
                "INSERT INTO clip_exports(id,clip_id,preset,status,job_id,output_path,width,height,duration_seconds,quality_report,error,created_at,updated_at) "
                "VALUES('export-test-2','clip-test','9:16','ready',NULL,'/tmp/render.mp4',1080,1920,30,?,NULL,?,?)",
                (json.dumps(report), self.main.now(), self.main.now()),
            )
        self.main.save_packaging("clip-test", self.main.PackagingRequest(
            destination="tiktok", title="The first version of this title", description="Excerpt.", hashtags=["startup"],
        ))
        self.main.approve_packaging("clip-test", self.main.ApprovalRequest(destination="tiktok", approved=True))
        updated = self.main.save_packaging("clip-test", self.main.PackagingRequest(
            destination="tiktok", title="A rewritten title for the same clip", description="Excerpt.", hashtags=["startup"],
        ))
        self.assertFalse(updated["approved"])
        self.assertEqual(self.main.publish_packages()["packages"], [])


if __name__ == "__main__":
    unittest.main()
