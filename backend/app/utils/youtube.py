"""Helpers for parsing YouTube URLs / IDs."""
import re

_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")

_PATTERNS = [
    re.compile(r"(?:youtube\.com/watch\?v=|youtube\.com/watch\?.*&v=)([a-zA-Z0-9_-]{11})"),
    re.compile(r"youtu\.be/([a-zA-Z0-9_-]{11})"),
    re.compile(r"youtube\.com/embed/([a-zA-Z0-9_-]{11})"),
    re.compile(r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})"),
    re.compile(r"youtube\.com/live/([a-zA-Z0-9_-]{11})"),
    re.compile(r"m\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"),
]


class InvalidYouTubeURLError(ValueError):
    """Raised when a video ID cannot be extracted from the given input."""


def extract_video_id(url_or_id: str) -> str:
    """Extract an 11-character YouTube video ID from a URL, or validate a bare ID.

    Raises InvalidYouTubeURLError if nothing usable is found.
    """
    candidate = url_or_id.strip()

    if _ID_RE.match(candidate):
        return candidate

    for pattern in _PATTERNS:
        match = pattern.search(candidate)
        if match:
            return match.group(1)

    raise InvalidYouTubeURLError(
        f"Could not extract a valid YouTube video ID from: {url_or_id!r}"
    )
