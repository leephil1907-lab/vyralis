"""HTTP-surface tests for link ingestion, captions and export options.

These run against FastAPI's TestClient with a temporary data directory. The worker
pool is patched out: the tests cover request validation and persistence, not encoding.
They are skipped when FastAPI/httpx are not installed.
"""

import importlib.util
import json
import os
import tempfile
import unittest
import uuid

HAVE_FASTAPI = all(importlib.util.find_spec(name) for name in ("fastapi", "httpx"))

if HAVE_FASTAPI:
    os.environ.setdefault("VYRALIS_DATA_DIR", tempfile.mkdtemp(prefix="vyralis-api-tests-"))

    from fastapi.testclient import TestClient  # noqa: E402

    from backend.app import main  # noqa: E402


@unittest.skipUnless(HAVE_FASTAPI, "FastAPI and httpx are required for API tests")
class ApiSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        main.init_db()
        # Keep the queue out of the assertions; only request handling is under test.
        cls._enqueue = main.enqueue
        main.enqueue = lambda job_id: None
        cls.client = TestClient(main.app)

    @classmethod
    def tearDownClass(cls):
        main.enqueue = cls._enqueue

    def seed(self, *, with_transcript=True, with_hook=True):
        import tempfile as tf
        from pathlib import Path

        media = Path(tf.mkdtemp(prefix="vyralis-api-media-")) / "src.mp4"
        media.write_bytes(b"not really a video")
        asset_id, project_id, clip_id = uuid.uuid4().hex, uuid.uuid4().hex, uuid.uuid4().hex
        with main.connect() as db:
            db.execute(
                "INSERT INTO assets VALUES(?,?,?,?,?,?,?,?,?)",
                (asset_id, "src.mp4", media.stat().st_size, "video/mp4", str(media), main.now(), 10.0, 1280, 720),
            )
            db.execute(
                "INSERT INTO projects VALUES(?,?,?,?,?,?)",
                (project_id, asset_id, "Surface test", "ready", main.now(), main.now()),
            )
            db.execute(
                "INSERT INTO clips(id,project_id,rank,start_seconds,end_seconds,score,score_breakdown,reason,"
                "transcript,title,status,created_at,hook) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (clip_id, project_id, 1, 1.0, 4.0, 80, "{}", "reason", "Hello there.", "Surface clip",
                 "ready", main.now(), "a hook" if with_hook else None),
            )
        if with_transcript:
            words = [
                {"start": 1.2, "end": 1.6, "text": "Hello"},
                {"start": 1.6, "end": 2.1, "text": "there."},
                {"start": 2.6, "end": 3.0, "text": "Again."},
            ]
            main.save_transcript(project_id, [{"start": 1.2, "end": 3.0, "text": "Hello there. Again.", "words": words}])
        return project_id, clip_id

    # --- captions -------------------------------------------------------

    def test_caption_downloads_are_attachments(self):
        _, clip_id = self.seed()
        for fmt, media_type, marker in (
            ("srt", "application/x-subrip", "-->"),
            ("vtt", "text/vtt", "WEBVTT"),
            ("ass", "text/plain", "[Script Info]"),
        ):
            with self.subTest(fmt=fmt):
                response = self.client.get(f"/api/clips/{clip_id}/captions", params={"format": fmt, "style": "karaoke"})
                self.assertEqual(response.status_code, 200)
                self.assertIn(media_type, response.headers["content-type"])
                self.assertIn(f"filename=", response.headers["content-disposition"])
                self.assertIn(marker, response.text)
                self.assertIn(f".{fmt}", response.headers["content-disposition"])

    def test_caption_words_are_rebased_to_the_clip(self):
        _, clip_id = self.seed()
        response = self.client.get(f"/api/clips/{clip_id}/captions", params={"format": "srt"})
        self.assertIn("00:00:00,200 --> ", response.text)

    def test_unknown_caption_format_or_style_is_rejected(self):
        _, clip_id = self.seed()
        self.assertEqual(
            self.client.get(f"/api/clips/{clip_id}/captions", params={"format": "docx"}).status_code, 422)
        self.assertEqual(
            self.client.get(f"/api/clips/{clip_id}/captions", params={"format": "srt", "style": "neon"}).status_code, 422)

    def test_captions_require_a_word_transcript(self):
        _, clip_id = self.seed(with_transcript=False)
        self.assertEqual(self.client.get(f"/api/clips/{clip_id}/captions", params={"format": "srt"}).status_code, 409)

    def test_captions_for_a_missing_clip_are_404(self):
        self.assertEqual(
            self.client.get(f"/api/clips/{uuid.uuid4().hex}/captions", params={"format": "srt"}).status_code, 404)

    # --- transcript -----------------------------------------------------

    def test_transcript_endpoint_returns_segments_and_word_count(self):
        project_id, _ = self.seed()
        payload = self.client.get(f"/api/projects/{project_id}/transcript").json()
        self.assertEqual(payload["word_count"], 3)
        self.assertEqual(payload["segments"][0]["text"], "Hello there. Again.")

    def test_transcript_endpoint_404s_when_absent(self):
        self.assertEqual(
            self.client.get(f"/api/projects/{uuid.uuid4().hex}/transcript").status_code, 404)

    # --- export options -------------------------------------------------

    def test_export_options_are_persisted(self):
        _, clip_id = self.seed()
        options = {"preset": "1:1", "captions": True, "caption_style": "clean", "layout": "blur", "hook_overlay": False}
        response = self.client.post(f"/api/clips/{clip_id}/export", json=options)
        self.assertEqual(response.status_code, 200)
        export_id = response.json()["export_id"]
        with main.connect() as db:
            row = db.execute("SELECT options, layout FROM clip_exports WHERE id=?", (export_id,)).fetchone()
        self.assertEqual(json.loads(row["options"])["caption_style"], "clean")
        self.assertFalse(json.loads(row["options"])["hook_overlay"])
        self.assertEqual(row["layout"], "blur")

    def test_identical_options_are_idempotent_and_changes_create_a_new_export(self):
        _, clip_id = self.seed()
        base = {"preset": "9:16", "layout": "center"}
        first = self.client.post(f"/api/clips/{clip_id}/export", json=base).json()
        again = self.client.post(f"/api/clips/{clip_id}/export", json=base).json()
        changed = self.client.post(f"/api/clips/{clip_id}/export", json={**base, "layout": "blur"}).json()
        self.assertTrue(again.get("idempotent"))
        self.assertEqual(first["export_id"], again["export_id"])
        self.assertNotEqual(first["export_id"], changed["export_id"])

    # --- deployment surface ---------------------------------------------

    def test_readiness_reports_each_dependency(self):
        payload = self.client.get("/api/ready").json()
        ids = {check["id"] for check in payload["checks"]}
        self.assertTrue({"ffmpeg", "ffprobe", "yt-dlp", "storage", "database", "web-build"} <= ids)
        self.assertIn("ready", payload)

    def test_unknown_api_route_stays_json_404(self):
        response = self.client.get("/api/definitely-not-a-route")
        self.assertEqual(response.status_code, 404)
        self.assertIn("detail", response.json())

    # --- link ingestion -------------------------------------------------

    def test_preview_rejects_missing_and_unknown_urls(self):
        self.assertEqual(self.client.post("/api/sources/preview", json={"url": ""}).status_code, 422)
        self.assertEqual(self.client.post("/api/sources/preview", json={"url": "https://evil.example/x"}).status_code, 422)
        self.assertEqual(self.client.post("/api/sources/preview", json={"url": "file:///etc/passwd"}).status_code, 422)

    def test_from_link_requires_a_rights_attestation(self):
        response = self.client.post("/api/projects/from-link", json={"url": "https://youtu.be/dQw4w9WgXcQ"})
        self.assertEqual(response.status_code, 422)

    def test_from_link_rejects_unknown_hosts_even_with_attestation(self):
        response = self.client.post(
            "/api/projects/from-link", json={"url": "https://evil.example/x", "rights_attested": True})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
