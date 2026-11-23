"""Delivery-domain helpers: export presets, output quality inspection and packaging rules.

Everything in this module is pure and dependency-free so it can be unit tested without
FFmpeg, a model download or a database. The API layer feeds it real measurements.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

# Render presets are fixed so exports are reproducible and testable.
PRESETS: dict[str, dict[str, Any]] = {
    "9:16": {"label": "Vertical 9:16", "width": 1080, "height": 1920, "use": "Shorts, Reels, TikTok"},
    "1:1": {"label": "Square 1:1", "width": 1080, "height": 1080, "use": "Feed posts and carousels"},
    "16:9": {"label": "Landscape 16:9", "width": 1920, "height": 1080, "use": "YouTube and embedded players"},
}

# Per-destination packaging limits. These are platform-published limits, not estimates.
DESTINATIONS: dict[str, dict[str, Any]] = {
    "youtube_shorts": {"label": "YouTube Shorts", "title_max": 100, "description_max": 5000, "hashtag_max": 15},
    "tiktok": {"label": "TikTok", "title_max": 2200, "description_max": 2200, "hashtag_max": 30},
    "instagram_reels": {"label": "Instagram Reels", "title_max": 2200, "description_max": 2200, "hashtag_max": 30},
    "export_package": {"label": "Manual upload package", "title_max": 300, "description_max": 5000, "hashtag_max": 30},
}

_HASHTAG_RE = re.compile(r"^[A-Za-z0-9_]{1,60}$")


def preset_geometry(preset: str) -> tuple[int, int]:
    """Return (width, height) for a preset, raising ValueError for unknown names."""
    try:
        item = PRESETS[preset]
    except KeyError as exc:
        raise ValueError(f"Unknown export preset '{preset}'.") from exc
    return int(item["width"]), int(item["height"])


def preset_list() -> list[dict[str, Any]]:
    return [{"preset": key, **value} for key, value in PRESETS.items()]


def _check(checks: list[dict[str, str]], check_id: str, label: str, status: str, detail: str) -> None:
    checks.append({"id": check_id, "label": label, "status": status, "detail": detail})


def evaluate_export(
    *,
    expected_duration: float,
    preset: str,
    probe: dict[str, Any],
    black_seconds: float = 0.0,
    frozen_seconds: float = 0.0,
    mean_volume_db: float | None = None,
) -> dict[str, Any]:
    """Build an evidence-based quality report for a rendered file.

    ``probe`` is the subset of FFprobe output we rely on. The result is intentionally
    conservative: a check can warn without blocking a download, but a failed check
    means the file should not be handed to a creator.
    """
    width, height = preset_geometry(preset)
    checks: list[dict[str, str]] = []
    duration = float(probe.get("duration_seconds") or 0)
    expected = max(0.1, float(expected_duration))

    # 1. Duration must match the edit within a tolerance, otherwise the cut slipped.
    delta = abs(duration - expected)
    tolerance_fail = max(1.0, expected * 0.08)
    tolerance_warn = max(0.5, expected * 0.03)
    if duration <= 0:
        _check(checks, "duration", "Duration", "fail", "The rendered file has no readable duration.")
    elif delta > tolerance_fail:
        _check(checks, "duration", "Duration", "fail", f"Rendered {duration:.2f}s against an expected {expected:.2f}s (difference {delta:.2f}s).")
    elif delta > tolerance_warn:
        _check(checks, "duration", "Duration", "warn", f"Rendered {duration:.2f}s against an expected {expected:.2f}s — within tolerance but worth a look.")
    else:
        _check(checks, "duration", "Duration", "pass", f"{duration:.2f}s matches the clip edit.")

    # 2. Frame size and codec.
    got_w, got_h = int(probe.get("width") or 0), int(probe.get("height") or 0)
    if (got_w, got_h) == (width, height):
        _check(checks, "dimensions", "Frame size", "pass", f"{got_w}×{got_h} matches the {preset} preset.")
    else:
        _check(checks, "dimensions", "Frame size", "fail", f"Expected {width}×{height} for {preset}, got {got_w}×{got_h}.")

    video_codec = str(probe.get("video_codec") or "unknown").lower()
    if video_codec in {"h264", "avc1"}:
        _check(checks, "video_codec", "Video codec", "pass", "H.264 video stream.")
    elif probe.get("has_video") is False:
        _check(checks, "video_codec", "Video codec", "fail", "The render has no video stream.")
    else:
        _check(checks, "video_codec", "Video codec", "warn", f"Unexpected video codec '{video_codec}'.")

    # 3. Audio: silence is a warning, not a hard failure, but the creator should know.
    if probe.get("has_audio"):
        audio_codec = str(probe.get("audio_codec") or "unknown").lower()
        if audio_codec in {"aac"}:
            _check(checks, "audio_stream", "Audio stream", "pass", "AAC audio stream present.")
        else:
            _check(checks, "audio_stream", "Audio stream", "warn", f"Audio codec '{audio_codec}' is not AAC.")
        if mean_volume_db is None:
            _check(checks, "loudness", "Audio level", "warn", "Audio level could not be measured.")
        elif mean_volume_db < -60:
            _check(checks, "loudness", "Audio level", "fail", f"Mean volume {mean_volume_db:.1f} dB is effectively silent.")
        elif mean_volume_db < -45:
            _check(checks, "loudness", "Audio level", "warn", f"Mean volume {mean_volume_db:.1f} dB is very quiet.")
        else:
            _check(checks, "loudness", "Audio level", "pass", f"Mean volume {mean_volume_db:.1f} dB.")
    else:
        _check(checks, "audio_stream", "Audio stream", "warn", "The render has no audio stream.")

    # 4. Black and frozen frames indicate a bad seek or a broken source range.
    black_fail = max(1.0, expected * 0.1)
    if black_seconds > black_fail:
        _check(checks, "black_frames", "Black frames", "fail", f"{black_seconds:.2f}s of the render is black.")
    elif black_seconds > 0:
        _check(checks, "black_frames", "Black frames", "warn", f"{black_seconds:.2f}s of black frames detected.")
    else:
        _check(checks, "black_frames", "Black frames", "pass", "No black frames detected.")

    if frozen_seconds >= expected * 0.8:
        _check(checks, "frozen_frames", "Frozen picture", "fail", f"{frozen_seconds:.2f}s of the clip is a frozen frame.")
    elif frozen_seconds > max(1.5, expected * 0.25):
        _check(checks, "frozen_frames", "Frozen picture", "warn", f"{frozen_seconds:.2f}s of frozen video detected.")
    else:
        _check(checks, "frozen_frames", "Frozen picture", "pass", "No long frozen spans detected.")

    # 5. A zero-byte or truncated container is never acceptable.
    size = int(probe.get("size_bytes") or 0)
    if size < 1024:
        _check(checks, "file", "File integrity", "fail", "The rendered file is empty or truncated.")
    else:
        _check(checks, "file", "File integrity", "pass", f"{size / 1024 / 1024:.1f} MB rendered file.")

    failures = [c for c in checks if c["status"] == "fail"]
    warnings = [c for c in checks if c["status"] == "warn"]
    status = "fail" if failures else "warn" if warnings else "pass"
    if failures:
        summary = f"{len(failures)} blocking issue{'s' if len(failures) != 1 else ''}: " + "; ".join(c["label"] for c in failures) + "."
    elif warnings:
        summary = "Render is usable with " + str(len(warnings)) + " warning" + ("s" if len(warnings) != 1 else "") + "."
    else:
        summary = "All automated checks passed."

    return {
        "status": status,
        "summary": summary,
        "checks": checks,
        "metrics": {
            "duration_seconds": round(duration, 3),
            "expected_duration_seconds": round(expected, 3),
            "width": got_w,
            "height": got_h,
            "black_seconds": round(float(black_seconds), 3),
            "frozen_seconds": round(float(frozen_seconds), 3),
            "mean_volume_db": None if mean_volume_db is None else round(float(mean_volume_db), 1),
            "size_bytes": size,
        },
    }


def normalize_hashtags(values: Iterable[str] | None) -> list[str]:
    """Strip leading '#', trim whitespace, drop duplicates and empty entries."""
    seen: set[str] = set()
    result: list[str] = []
    for raw in values or []:
        clean = str(raw).strip().lstrip("#").strip()
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(clean)
    return result


def validate_packaging(
    *,
    destination: str,
    title: str,
    description: str = "",
    hashtags: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Validate packaging copy against the destination's real limits."""
    if destination not in DESTINATIONS:
        raise ValueError(f"Unknown destination '{destination}'.")
    limits = DESTINATIONS[destination]
    tags = normalize_hashtags(hashtags)
    errors: list[str] = []
    warnings: list[str] = []

    clean_title = (title or "").strip()
    clean_description = (description or "").strip()

    if not clean_title:
        errors.append("A title is required before this package can be approved.")
    elif len(clean_title) > limits["title_max"]:
        errors.append(f"Title is {len(clean_title)} characters; {limits['label']} allows {limits['title_max']}.")
    elif len(clean_title) < 12:
        warnings.append("Titles under 12 characters rarely explain the moment — consider adding a hook.")

    if len(clean_description) > limits["description_max"]:
        errors.append(f"Description is {len(clean_description)} characters; {limits['label']} allows {limits['description_max']}.")

    if len(tags) > limits["hashtag_max"]:
        errors.append(f"{len(tags)} hashtags supplied; {limits['label']} allows {limits['hashtag_max']}.")
    if not tags:
        warnings.append("No hashtags yet — add two or three that describe the topic.")
    for tag in tags:
        if not _HASHTAG_RE.match(tag):
            errors.append(f"Hashtag '{tag}' contains unsupported characters (letters, numbers and underscores only).")
    if clean_title.count("#") > 0:
        warnings.append("Hashtags work better in the hashtag field than inside the title.")

    return {
        "destination": destination,
        "destination_label": limits["label"],
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "title": len(clean_title),
            "description": len(clean_description),
            "hashtags": len(tags),
            "title_max": limits["title_max"],
            "description_max": limits["description_max"],
            "hashtag_max": limits["hashtag_max"],
        },
        "hashtags": tags,
    }


def approval_gate(*, quality_status: str | None, packaging_valid: bool, destination: str) -> dict[str, Any]:
    """Decide whether a package may be approved for delivery.

    Approval only ever authorises a *manual* delivery package: VYRALIS does not post to a
    platform without a connected, authorized provider, and that provider does not exist yet.
    """
    blockers: list[str] = []
    if quality_status is None:
        blockers.append("Render the clip first — there is no validated export to deliver.")
    elif quality_status == "fail":
        blockers.append("The latest render failed automated quality inspection.")
    if not packaging_valid:
        blockers.append("Fix the packaging errors for this destination.")
    if destination not in DESTINATIONS:
        blockers.append("Unknown destination.")
    return {"allowed": not blockers, "blockers": blockers}
