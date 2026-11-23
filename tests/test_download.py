"""Tests for the yt-dlp download step used by link ingestion.

A fake ``yt-dlp`` on PATH produces a real (tiny) MKV, so the test covers the part that
actually matters here: settling whatever the downloader produced into the exact media
path the rest of the pipeline expects, without leaving leftovers.

Skipped when FFmpeg is unavailable, because the fake downloader encodes a real clip.
"""

import importlib.util
import json
import os
import shutil
import stat
import tempfile
import unittest
import uuid
from pathlib import Path

os.environ.setdefault("VYRALIS_DATA_DIR", tempfile.mkdtemp(prefix="vyralis-download-tests-"))

from backend.app import main  # noqa: E402

HAVE_FFMPEG = bool(shutil.which("ffmpeg"))

FAKE_DOWNLOADER = '''#!/usr/bin/env python3
import subprocess
import sys

template = sys.argv[sys.argv.index("-o") + 1]
out = template.replace("%(ext)s", "mkv")
subprocess.run([
    "ffmpeg", "-y", "-loglevel", "error",
    "-f", "lavfi", "-i", "testsrc=size=320x180:rate=15:duration=1",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", out,
], check=True)
'''


@unittest.skipUnless(HAVE_FFMPEG, "FFmpeg is required to synthesise a download")
class DownloadSourceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="vyralis-download-"))
        self.media = self.root / "media"
        self.media.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        fake = self.bin / "yt-dlp"
        fake.write_text(FAKE_DOWNLOADER)
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.old_path = os.environ["PATH"]
        os.environ["PATH"] = f"{self.bin}{os.pathsep}{self.old_path}"
        main.init_db()
        self.asset_id = uuid.uuid4().hex
        self.job_id = uuid.uuid4().hex
        self.target = self.media / f"{self.asset_id}.mp4"
        self.project_id = uuid.uuid4().hex
        with main.connect() as db:
            db.execute(
                "INSERT INTO assets VALUES(?,?,?,?,?,?,?,?,?)",
                (self.asset_id, "source.mp4", 0, "video/mp4", str(self.target), main.now(), 0.0, None, None),
            )
            db.execute("INSERT INTO projects VALUES(?,?,?,?,?,?)",
                       (self.project_id, self.asset_id, "Download test", "queued", main.now(), main.now()))
            db.execute(
                "INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)",
                (self.job_id, self.project_id, "queued", "queued", 0, "queued",
                 json.dumps({"kind": "ingest", "source_url": "https://youtu.be/dQw4w9WgXcQ"}),
                 None, main.now(), main.now()),
            )

    def tearDown(self):
        os.environ["PATH"] = self.old_path
        shutil.rmtree(self.root, ignore_errors=True)

    def asset_row(self):
        with main.connect() as db:
            return db.execute("SELECT * FROM assets WHERE id=?", (self.asset_id,)).fetchone()

    def test_download_settles_at_the_expected_path_and_cleans_up(self):
        result = main.download_source(self.job_id, self.asset_row(), {"source_url": "https://youtu.be/dQw4w9WgXcQ"})
        self.assertEqual(result, self.target)
        self.assertTrue(result.exists())
        self.assertGreater(result.stat().st_size, 0)
        # The intermediate .mkv must not be left behind in the media store.
        self.assertEqual(sorted(path.name for path in self.media.iterdir()), [self.target.name])

    def test_download_is_reported_in_the_job_log(self):
        main.download_source(self.job_id, self.asset_row(), {"source_url": "https://youtu.be/dQw4w9WgXcQ"})
        with main.connect() as db:
            job = db.execute("SELECT stage, message FROM jobs WHERE id=?", (self.job_id,)).fetchone()
        self.assertEqual(job["stage"], "download")
        self.assertIn("yt-dlp", job["message"])

    def test_missing_downloader_is_a_clear_error(self):
        original = main.shutil.which
        main.shutil.which = lambda name: None if name == "yt-dlp" else original(name)
        try:
            with self.assertRaises(RuntimeError) as caught:
                main.download_source(self.job_id, self.asset_row(), {"source_url": "https://youtu.be/dQw4w9WgXcQ"})
            self.assertIn("pip install yt-dlp", str(caught.exception))
        finally:
            main.shutil.which = original

    def test_failed_download_leaves_no_file_behind(self):
        broken = self.bin / "yt-dlp"
        broken.write_text("#!/bin/sh\nexit 1\n")
        broken.chmod(broken.stat().st_mode | stat.S_IEXEC)
        with self.assertRaises(Exception):
            main.download_source(self.job_id, self.asset_row(), {"source_url": "https://youtu.be/dQw4w9WgXcQ"})
        self.assertEqual(list(self.media.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
