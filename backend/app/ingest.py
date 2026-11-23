"""Link ingestion rules and yt-dlp command construction.

Deliberately dependency-free: the API layer decides *whether* a URL may be fetched,
this module only encodes the policy so it can be unit tested.
"""

from __future__ import annotations

import ipaddress
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# Only these platforms are supported, and only these hosts may be fetched.
PLATFORM_HOSTS: dict[str, tuple[str, ...]] = {
    "youtube": ("youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"),
    "twitch": ("twitch.tv", "m.twitch.tv", "clips.twitch.tv"),
    "kick": ("kick.com", "m.kick.com"),
}
ALLOWED_HOSTS = {host for hosts in PLATFORM_HOSTS.values() for host in hosts}

MAX_URL_LENGTH = 2048
DEFAULT_MAX_DURATION = int(os.getenv("VYRALIS_MAX_SOURCE_DURATION", str(4 * 60 * 60)))
DEFAULT_MAX_HEIGHT = int(os.getenv("VYRALIS_MAX_SOURCE_HEIGHT", "1080"))

_YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


class SourceRejected(ValueError):
    """Raised when a URL is not permitted by the ingestion policy."""


def _host_allowed(host: str) -> str | None:
    host = host.lower().rstrip(".")
    for platform, hosts in PLATFORM_HOSTS.items():
        for allowed in hosts:
            if host == allowed or host.endswith("." + allowed):
                return platform
    return None


def parse_source_url(raw: str) -> dict[str, Any]:
    """Validate a user-supplied URL and normalise it for yt-dlp.

    Rejects non-HTTP schemes, credentials in the URL, IP literals, private hosts,
    unusual ports and unknown domains. This is the only place a link becomes trusted.
    """
    if not raw or not isinstance(raw, str):
        raise SourceRejected("Paste a video link first.")
    url = raw.strip()
    if len(url) > MAX_URL_LENGTH:
        raise SourceRejected("That link is too long.")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise SourceRejected("Only http and https links are supported.")
    if parsed.username or parsed.password:
        raise SourceRejected("Links with embedded credentials are not allowed.")
    if parsed.port and parsed.port not in {80, 443}:
        raise SourceRejected("Links on non-standard ports are not allowed.")
    host = parsed.hostname or ""
    if not host:
        raise SourceRejected("That link has no host.")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None:
        raise SourceRejected("Direct IP addresses are not allowed.")
    platform = _host_allowed(host)
    if not platform:
        raise SourceRejected("Supported sources: YouTube, Twitch and Kick links.")

    video_id = ""
    if platform == "youtube":
        if host == "youtu.be":
            video_id = parsed.path.strip("/").split("/")[0]
        elif parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/shorts/")[1].split("/")[0]
        else:
            match = re.search(r"(?:^|[?&])v=([A-Za-z0-9_-]+)", parsed.query)
            video_id = match.group(1) if match else ""
        if video_id and not _YOUTUBE_ID.match(video_id):
            raise SourceRejected("That YouTube video id looks malformed.")
    return {
        "platform": platform,
        "url": url,
        "host": host,
        "video_id": video_id,
    }


def ytdlp_metadata_cmd(url: str) -> list[str]:
    return [
        "yt-dlp", "--dump-single-json", "--no-playlist", "--no-warnings",
        "--skip-download", "--no-cache-dir", url,
    ]


def ytdlp_download_cmd(url: str, destination: Path, max_height: int = DEFAULT_MAX_HEIGHT) -> list[str]:
    return [
        "yt-dlp",
        "--no-playlist",
        "--no-warnings",
        "--no-progress",
        "--no-cache-dir",
        "--merge-output-format", "mp4",
        "--remux-video", "mp4",
        "-f", f"bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]/best",
        "-o", str(destination),
        url,
    ]


def parse_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalise a yt-dlp JSON payload into the fields the studio shows."""
    duration = payload.get("duration") or 0
    try:
        duration = float(duration)
    except (TypeError, ValueError):
        duration = 0.0
    thumbnails = payload.get("thumbnails") or []
    thumbnail = payload.get("thumbnail") or (thumbnails[-1].get("url") if thumbnails else None)
    return {
        "title": (payload.get("title") or "Untitled source")[:200],
        "duration_seconds": duration,
        "uploader": payload.get("uploader") or payload.get("channel") or "",
        "thumbnail": thumbnail,
        "is_live": bool(payload.get("is_live")),
        "live_status": payload.get("live_status"),
        "extractor": payload.get("extractor_key") or payload.get("extractor") or "",
        "webpage_url": payload.get("webpage_url") or "",
    }


def enforce_duration(metadata: dict[str, Any], limit: int = DEFAULT_MAX_DURATION) -> None:
    duration = float(metadata.get("duration_seconds") or 0)
    if duration and duration > limit:
        hours = limit / 3600
        label = f"{hours:g} hours"
        raise SourceRejected(f"That source is {duration / 3600:.1f} hours long. The limit is {label}; trim it first or raise VYRALIS_MAX_SOURCE_DURATION.")
    if metadata.get("is_live") and metadata.get("live_status") in {"is_live", "is_upcoming"}:
        raise SourceRejected("That link is a live broadcast. Paste the finished VOD or a clip instead.")


def safe_stem(metadata: dict[str, Any], fallback: str = "source") -> str:
    """A single path component for yt-dlp's output template.

    Strips separators, control characters and any dot run, so a crafted title can
    never climb out of the media directory or look like a flag.
    """
    raw = metadata.get("title") or fallback
    stem = re.sub(r"[^A-Za-z0-9._ -]+", "", str(raw)).strip()
    stem = re.sub(r"\.{2,}", ".", stem).strip(". ").replace(" ", "_")
    stem = stem.lstrip("-")
    return (stem[:80].strip("._-") or fallback)
