"""Word-timed caption generation (ASS for burn-in, SRT/VTT for download).

Pure functions only: the API passes the transcript words and the clip window, and gets
back a subtitle file. No FFmpeg, no model, no filesystem access here.
"""

from __future__ import annotations

import re

CAPTION_STYLES: dict[str, dict[str, object]] = {
    "clean": {
        "label": "Clean",
        "words_per_cue": 6,
        "karaoke": False,
        "fontsize": 58,
        "uppercase": False,
        "primary": "&H00FFFFFF",
        "accent": "&H0000D7FF",
        "outline_px": 4,
        "shadow": 2,
        "margin_v": 180,
    },
    "karaoke": {
        "label": "Karaoke",
        "words_per_cue": 3,
        "karaoke": True,
        "fontsize": 70,
        "uppercase": False,
        "primary": "&H00FFFFFF",
        "accent": "&H0000D7FF",
        "outline_px": 5,
        "shadow": 3,
        "margin_v": 200,
    },
    "impact": {
        "label": "Impact",
        "words_per_cue": 2,
        "karaoke": True,
        "fontsize": 88,
        "uppercase": True,
        "primary": "&H00FFFFFF",
        "accent": "&H002BE5FF",
        "outline_px": 6,
        "shadow": 3,
        "margin_v": 240,
    },
}
DEFAULT_STYLE = "karaoke"

_ASS_UNSAFE = re.compile(r"[{}\\\r\n]")


def _clean_text(text: str) -> str:
    return _ASS_UNSAFE.sub(lambda match: " " if match.group(0) in "\r\n" else "", str(text)).strip()


def ass_time(seconds: float) -> str:
    """ASS timestamps are H:MM:SS.cc with centisecond precision."""
    seconds = max(0.0, float(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{int(hours)}:{int(minutes):02d}:{int(secs):02d}.{int(round((secs - int(secs)) * 100)) % 100:02d}"


def srt_time(seconds: float) -> str:
    millis = int(round(max(0.0, float(seconds)) * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def vtt_time(seconds: float) -> str:
    return srt_time(seconds).replace(",", ".")


def words_in_window(words: list[dict[str, object]], start: float, end: float) -> list[dict[str, object]]:
    """Words overlapping [start, end), re-based so the clip begins at 0."""
    result: list[dict[str, object]] = []
    for word in words:
        try:
            word_start = float(word.get("start", 0))
            word_end = float(word.get("end", word_start))
        except (TypeError, ValueError):
            continue
        if word_end <= start or word_start >= end:
            continue
        text = _clean_text(word.get("text", ""))
        if not text:
            continue
        result.append({
            "start": round(max(0.0, word_start - start), 3),
            "end": round(max(0.0, min(word_end, end) - start), 3),
            "text": text,
        })
    return result


def group_cues(words: list[dict[str, object]], per_cue: int, gap_break: float = 0.65) -> list[list[dict[str, object]]]:
    """Split words into short cues, breaking on length, silence or sentence end."""
    cues: list[list[dict[str, object]]] = []
    current: list[dict[str, object]] = []
    for word in words:
        if not current:
            current = [word]
            continue
        previous = current[-1]
        gap = float(word["start"]) - float(previous["end"])
        sentence_end = str(previous["text"]).endswith((".", "!", "?", "…"))
        if len(current) >= per_cue or gap > gap_break or sentence_end:
            cues.append(current)
            current = [word]
        else:
            current.append(word)
    if current:
        cues.append(current)
    return cues


def _karaoke_text(cue: list[dict[str, object]], uppercase: bool) -> str:
    parts = []
    for word in cue:
        text = str(word["text"])
        if uppercase:
            text = text.upper()
        duration_cs = max(4, int(round((float(word["end"]) - float(word["start"])) * 100)))
        parts.append(f"{{\\k{duration_cs}}}{text}")
    return " ".join(parts)


def build_ass(
    words: list[dict[str, object]],
    clip_start: float,
    clip_end: float,
    *,
    width: int = 1080,
    height: int = 1920,
    style: str = DEFAULT_STYLE,
    hook: str | None = None,
    hook_seconds: float = 3.2,
) -> str:
    """Render word-timed captions as an ASS document sized for the export frame."""
    spec = CAPTION_STYLES.get(style, CAPTION_STYLES[DEFAULT_STYLE])
    scale = max(0.55, height / 1920)
    fontsize = int(round(int(spec["fontsize"]) * scale))
    margin_v = int(round(int(spec["margin_v"]) * scale))
    outline_px = int(spec["outline_px"])
    shadow = int(spec["shadow"])
    uppercase = bool(spec["uppercase"])
    per_cue = int(spec["words_per_cue"])
    karaoke = bool(spec["karaoke"])
    primary = str(spec["primary"])
    accent = str(spec["accent"])

    # Hooks are one-liners, so shrink the hook face until the line fits the frame.
    hook_text = _clean_text(hook).upper() if hook else ""
    hook_fontsize = int(round(fontsize * 1.15))
    if hook_text:
        available = max(200, width - 120)
        estimated = len(hook_text) * hook_fontsize * 0.58
        if estimated > available:
            hook_fontsize = max(22, int(round(hook_fontsize * available / estimated)))

    # SecondaryColour drives the karaoke sweep; for non-karaoke styles it is unused.
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {width}\n"
        f"PlayResY: {height}\n"
        # Smart wrapping: a long hook line wraps instead of being cut off at the frame edge.
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n"
        "YCbCr Matrix: TV.709\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Caption,Arial,{fontsize},{primary},{accent},&H00101010,&H80000000,"
        f"-1,0,0,0,100,100,0,0,1,{outline_px},{shadow},2,60,60,{margin_v},1\n"
        f"Style: Hook,Arial,{hook_fontsize},&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,"
        f"-1,0,0,0,100,100,0,0,1,5,3,8,60,60,70,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )

    events: list[str] = []
    clip_duration = max(0.1, clip_end - clip_start)
    if hook_text:
        events.append(
            f"Dialogue: 1,0:00:00.00,{ass_time(min(hook_seconds, clip_duration))},Hook,,0,0,0,,"
            f"{{\\an8\\fad(180,180)}}{hook_text}"
        )

    window = words_in_window(words, clip_start, clip_end)
    for cue in group_cues(window, per_cue):
        start = float(cue[0]["start"])
        end = max(float(cue[-1]["end"]), start + 0.5)
        end = min(end, clip_duration)
        text = _karaoke_text(cue, uppercase) if karaoke else " ".join(
            str(word["text"]).upper() if uppercase else str(word["text"]) for word in cue
        )
        if not text:
            continue
        events.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Caption,,0,0,0,,{text}")

    return header + "\n".join(events) + "\n"


def build_srt(words: list[dict[str, object]], clip_start: float, clip_end: float, style: str = DEFAULT_STYLE) -> str:
    spec = CAPTION_STYLES.get(style, CAPTION_STYLES[DEFAULT_STYLE])
    window = words_in_window(words, clip_start, clip_end)
    blocks: list[str] = []
    for index, cue in enumerate(group_cues(window, int(spec["words_per_cue"])), 1):
        start = float(cue[0]["start"])
        end = max(float(cue[-1]["end"]), start + 0.4)
        text = " ".join(str(word["text"]) for word in cue)
        if bool(spec["uppercase"]):
            text = text.upper()
        blocks.append(f"{index}\n{srt_time(start)} --> {srt_time(end)}\n{text}\n")
    return "\n".join(blocks)


def build_vtt(words: list[dict[str, object]], clip_start: float, clip_end: float, style: str = DEFAULT_STYLE) -> str:
    spec = CAPTION_STYLES.get(style, CAPTION_STYLES[DEFAULT_STYLE])
    window = words_in_window(words, clip_start, clip_end)
    blocks: list[str] = ["WEBVTT\n"]
    for index, cue in enumerate(group_cues(window, int(spec["words_per_cue"])), 1):
        start = float(cue[0]["start"])
        end = max(float(cue[-1]["end"]), start + 0.4)
        text = " ".join(str(word["text"]) for word in cue)
        if bool(spec["uppercase"]):
            text = text.upper()
        blocks.append(f"{index}\n{vtt_time(start)} --> {vtt_time(end)}\n{text}\n")
    return "\n".join(blocks)
