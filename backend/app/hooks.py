"""Deterministic hook, title and hashtag drafting from a transcript window.

No model is called here on purpose: these are extractive, explainable drafts that a
creator edits. If an LLM is configured later it can replace the ranking function, not
the contract.
"""

from __future__ import annotations

import re

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "so", "because", "that", "this",
    "these", "those", "is", "are", "was", "were", "be", "been", "being", "am", "do", "does",
    "did", "have", "has", "had", "i", "you", "he", "she", "it", "we", "they", "me", "him",
    "her", "us", "them", "my", "your", "his", "their", "our", "its", "of", "to", "in", "on",
    "at", "for", "with", "about", "as", "by", "from", "up", "down", "out", "into", "over",
    "just", "really", "very", "like", "know", "think", "going", "got", "get", "one", "thing",
    "things", "there", "here", "what", "when", "where", "who", "why", "how", "not", "no",
    "yeah", "okay", "ok", "um", "uh", "right", "well", "actually", "basically", "literally",
}

_HOOK_CUES = (
    "why", "how", "never", "always", "nobody", "everybody", "everyone", "secret",
    "mistake", "wrong", "truth", "changed", "learned", "realized", "realised",
    "because", "but", "stopped", "started", "failed", "won", "lost", "best", "worst",
    "first", "last", "biggest", "hardest",
)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", str(text))
    return [part.strip() for part in parts if part.strip()]


def _score_sentence(sentence: str, index: int) -> float:
    lower = sentence.lower()
    words = lower.split()
    score = 0.0
    score += sum(1.6 for cue in _HOOK_CUES if cue in lower)
    if "?" in sentence:
        score += 1.2
    if re.search(r"\b\d+\b", sentence):
        score += 0.8
    if 5 <= len(words) <= 22:
        score += 1.4
    elif len(words) > 34:
        score -= 1.0
    if index == 0:
        score += 0.6
    return score


def _trim_words(text: str, limit: int) -> str:
    words = text.split()
    if len(words) <= limit:
        return text.strip().strip(",;:")
    return " ".join(words[:limit]).rstrip(",;:") + "…"


def extract_hook(text: str, max_words: int = 10) -> str:
    """Pick the most hook-like sentence and trim it to overlay length."""
    sentences = _sentences(text)
    if not sentences:
        return ""
    best = max(enumerate(sentences), key=lambda item: _score_sentence(item[1], item[0]))[1]
    hook = re.sub(r"\s+", " ", best).strip().strip('"')
    return _trim_words(hook, max_words)


def extract_title(text: str, max_words: int = 12) -> str:
    """A readable working title: the hook without trailing punctuation, sentence-cased."""
    hook = extract_hook(text, max_words=max_words).rstrip("…").strip()
    hook = hook.rstrip(".?!,;:")
    if not hook:
        return ""
    hook = hook[0].upper() + hook[1:]
    return _trim_words(hook, max_words)


def suggest_hashtags(text: str, limit: int = 5) -> list[str]:
    """Rank transcript keywords into camel-cased hashtags. Extractive, not invented."""
    counts: dict[str, int] = {}
    for raw in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", str(text)):
        word = raw.strip("'-").lower()
        if word in _STOPWORDS or len(word) < 4:
            continue
        counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    tags: list[str] = []
    seen: set[str] = set()
    for word, _ in ranked:
        tag = re.sub(r"[^A-Za-z0-9_]", "", word)
        if len(tag) < 4 or tag.lower() in seen:
            continue
        seen.add(tag.lower())
        tags.append(tag)
        if len(tags) >= limit:
            break
    return tags
