"""Tests for the link-ingestion policy and yt-dlp command building.

No network and no yt-dlp binary are required: these cover the validation rules that
decide whether a URL is allowed to reach the downloader at all.
"""

import unittest
from pathlib import Path

from backend.app.ingest import (
    DEFAULT_MAX_HEIGHT,
    SourceRejected,
    enforce_duration,
    parse_metadata,
    parse_source_url,
    safe_stem,
    ytdlp_download_cmd,
    ytdlp_metadata_cmd,
)


class ParseSourceUrlTests(unittest.TestCase):
    def test_accepts_youtube_watch_url(self):
        result = parse_source_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertEqual(result["platform"], "youtube")
        self.assertEqual(result["video_id"], "dQw4w9WgXcQ")

    def test_accepts_short_and_shorts_forms(self):
        self.assertEqual(parse_source_url("https://youtu.be/dQw4w9WgXcQ")["platform"], "youtube")
        shorts = parse_source_url("https://www.youtube.com/shorts/dQw4w9WgXcQ?feature=share")
        self.assertEqual(shorts["video_id"], "dQw4w9WgXcQ")

    def test_accepts_twitch_and_kick(self):
        self.assertEqual(parse_source_url("https://www.twitch.tv/videos/123456789")["platform"], "twitch")
        self.assertEqual(parse_source_url("https://kick.com/somechannel")["platform"], "kick")

    def test_rejects_unknown_host(self):
        with self.assertRaises(SourceRejected):
            parse_source_url("https://example.com/watch?v=abc")

    def test_rejects_non_http_schemes(self):
        for value in ("ftp://youtube.com/watch?v=dQw4w9WgXcQ", "javascript:alert(1)", "file:///etc/passwd"):
            with self.subTest(value=value), self.assertRaises(SourceRejected):
                parse_source_url(value)

    def test_rejects_credentials_and_ports_and_ips(self):
        bad = [
            "https://user:pass@youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com:8443/watch?v=dQw4w9WgXcQ",
            "https://127.0.0.1/watch?v=dQw4w9WgXcQ",
            "https://[::1]/watch?v=dQw4w9WgXcQ",
        ]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(SourceRejected):
                parse_source_url(value)

    def test_rejects_malformed_youtube_id(self):
        with self.assertRaises(SourceRejected):
            parse_source_url("https://youtu.be/short")

    def test_rejects_empty_and_overlong_input(self):
        with self.assertRaises(SourceRejected):
            parse_source_url("   ")
        with self.assertRaises(SourceRejected):
            parse_source_url("https://youtu.be/" + "a" * 3000)

    def test_lookalike_hosts_are_not_accepted(self):
        with self.assertRaises(SourceRejected):
            parse_source_url("https://youtube.com.evil.example/watch?v=dQw4w9WgXcQ")


class CommandTests(unittest.TestCase):
    def test_metadata_command_is_a_skip_download(self):
        command = ytdlp_metadata_cmd("https://youtu.be/dQw4w9WgXcQ")
        self.assertEqual(command[0], "yt-dlp")
        self.assertIn("--dump-single-json", command)
        self.assertIn("--skip-download", command)
        self.assertNotIn("--exec", command)

    def test_download_command_caps_height_and_remuxes_mp4(self):
        command = ytdlp_download_cmd("https://youtu.be/dQw4w9WgXcQ", Path("/tmp/out.%(ext)s"), 720)
        joined = " ".join(command)
        self.assertIn("height<=720", joined)
        self.assertIn("--merge-output-format mp4", joined)
        self.assertIn("--no-playlist", command)
        self.assertEqual(command[-1], "https://youtu.be/dQw4w9WgXcQ")
        self.assertIn(str(DEFAULT_MAX_HEIGHT), " ".join(ytdlp_download_cmd("https://youtu.be/dQw4w9WgXcQ", Path("/tmp/x"))))


class MetadataTests(unittest.TestCase):
    def test_parse_metadata_normalises_fields(self):
        info = parse_metadata({
            "title": "A talk about ships",
            "duration": "1830.5",
            "channel": "Studio",
            "thumbnails": [{"url": "https://img/1.jpg"}, {"url": "https://img/2.jpg"}],
            "extractor_key": "Youtube",
            "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        })
        self.assertEqual(info["title"], "A talk about ships")
        self.assertEqual(info["duration_seconds"], 1830.5)
        self.assertEqual(info["uploader"], "Studio")
        self.assertEqual(info["thumbnail"], "https://img/2.jpg")
        self.assertEqual(info["extractor"], "Youtube")

    def test_parse_metadata_survives_missing_and_bad_values(self):
        info = parse_metadata({"duration": "not-a-number"})
        self.assertEqual(info["duration_seconds"], 0.0)
        self.assertEqual(info["title"], "Untitled source")


class DurationTests(unittest.TestCase):
    def test_allows_short_sources(self):
        enforce_duration({"duration_seconds": 300}, limit=600)

    def test_rejects_over_limit(self):
        with self.assertRaises(SourceRejected):
            enforce_duration({"duration_seconds": 700}, limit=600)

    def test_rejects_live_and_upcoming(self):
        for status in ("is_live", "is_upcoming"):
            with self.subTest(status=status), self.assertRaises(SourceRejected):
                enforce_duration({"duration_seconds": 60, "is_live": True, "live_status": status})

    def test_finished_stream_is_allowed(self):
        enforce_duration({"duration_seconds": 60, "is_live": False, "live_status": "was_live"})


class SafeStemTests(unittest.TestCase):
    def test_strips_path_and_option_characters(self):
        stem = safe_stem({"title": "../../etc/passwd -rf"})
        self.assertNotIn("/", stem)
        self.assertNotIn("..", stem)
        self.assertTrue(stem)

    def test_has_a_fallback(self):
        self.assertEqual(safe_stem({}, fallback="source"), "source")


if __name__ == "__main__":
    unittest.main()
