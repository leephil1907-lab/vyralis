"""Framing plans for vertical/square exports.

Pure geometry and smoothing live here so they can be tested without OpenCV:
the vision adapter may return focus points, this module decides the crop window.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

LAYOUTS: dict[str, str] = {
    "center": "Centre crop",
    "face": "Follow the subject (needs the vision extra)",
    "blur": "Blurred background fill",
}
DEFAULT_LAYOUT = "center"


def _even(value: float) -> int:
    return int(value) - int(value) % 2


def plan_focus(points: Iterable[float] | None, default: float = 0.5, smoothing: float = 0.35) -> float:
    """Turn sampled focus x-positions into one damped crop centre.

    Exponential smoothing keeps the crop from jittering between detections, and the
    result is clamped so the crop window can never leave the frame.
    """
    values = [min(1.0, max(0.0, float(point))) for point in (points or []) if point is not None]
    if not values:
        return default
    smoothed = values[0]
    alpha = min(0.9, max(0.05, smoothing))
    for value in values[1:]:
        smoothed = smoothed + alpha * (value - smoothed)
    return round(min(1.0, max(0.0, smoothed)), 4)


def crop_plan(
    src_w: int,
    src_h: int,
    out_w: int,
    out_h: int,
    focus_x: float = 0.5,
    focus_y: float = 0.5,
) -> dict[str, int]:
    """Compute the cover-scale and crop offsets for a focus point."""
    if src_w <= 0 or src_h <= 0:
        raise ValueError("Source dimensions must be positive.")
    # H.264 requires even dimensions; normalise before planning the crop window.
    out_w, out_h = max(2, _even(out_w)), max(2, _even(out_h))
    scale = max(out_w / src_w, out_h / src_h)
    scaled_w = max(out_w, _even(round(src_w * scale)))
    scaled_h = max(out_h, _even(round(src_h * scale)))
    max_x = max(0, scaled_w - out_w)
    max_y = max(0, scaled_h - out_h)
    x = min(max(0, int(round(focus_x * scaled_w - out_w / 2))), max_x)
    y = min(max(0, int(round(focus_y * scaled_h - out_h / 2))), max_y)
    return {
        "scaled_w": scaled_w,
        "scaled_h": scaled_h,
        "out_w": out_w,
        "out_h": out_h,
        "x": x,
        "y": y,
    }


def build_filter(
    *,
    layout: str,
    src_w: int,
    src_h: int,
    out_w: int,
    out_h: int,
    focus_x: float = 0.5,
    focus_y: float = 0.5,
    ass_path: Path | None = None,
) -> str:
    """Build an FFmpeg filter graph ending in ``[vout]``.

    ``ass_path`` is burned in with the subtitles filter (requires a libass-enabled
    FFmpeg build, which the packaged builds and distro packages provide).
    """
    out_w, out_h = _even(out_w), _even(out_h)
    if layout == "blur":
        # An input pad can only be consumed once, so split before scaling twice.
        graph = (
            f"[0:v]split=2[src_bg][src_fg];"
            f"[src_bg]scale={out_w}:{out_h}:force_original_aspect_ratio=increase,"
            f"crop={out_w}:{out_h},gblur=sigma=28[bg];"
            f"[src_fg]scale={out_w}:{out_h}:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[base]"
        )
    else:
        plan = crop_plan(src_w, src_h, out_w, out_h, focus_x, focus_y)
        graph = (
            f"[0:v]scale={plan['scaled_w']}:{plan['scaled_h']}:flags=lanczos,"
            f"crop={out_w}:{out_h}:{plan['x']}:{plan['y']},setsar=1[base]"
        )
    if ass_path is not None:
        escaped = str(ass_path).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
        graph += f";[base]subtitles=filename='{escaped}':alpha=1[vout]"
    else:
        graph += ";[base]null[vout]"
    return graph


def detect_focus_points(path: Path, samples: int = 10) -> list[float]:
    """Sample frames and return normalised face centres.

    Optional: requires the ``vision`` extra (opencv-python-headless, which bundles a
    Haar cascade). When it is unavailable the caller falls back to a centre crop and
    says so in the export report rather than pretending tracking happened.
    """
    try:
        import cv2  # type: ignore
    except ImportError:
        return []
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        return []
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(str(cascade_path))
    if detector.empty():
        capture.release()
        return []
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    points: list[float] = []
    if total <= 0:
        capture.release()
        return []
    step = max(1, total // max(1, samples))
    try:
        for index in range(0, total, step):
            capture.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, frame = capture.read()
            if not ok:
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = detector.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5, minSize=(48, 48))
            if len(faces) == 0:
                continue
            x, _, w, _ = max(faces, key=lambda box: box[2] * box[3])
            width = frame.shape[1] or 1
            points.append(round((x + w / 2) / width, 4))
    finally:
        capture.release()
    return points


def layout_report(layout: str, focus_points: list[float]) -> dict[str, Any]:
    return {
        "layout": layout if layout in LAYOUTS else DEFAULT_LAYOUT,
        "tracked": bool(focus_points),
        "samples": len(focus_points),
        "note": (
            "Subject tracking used the vision extra."
            if focus_points
            else "Centre crop — subject tracking was unavailable or found no face."
        ),
    }
