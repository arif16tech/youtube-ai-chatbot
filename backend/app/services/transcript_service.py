"""
Fetches YouTube transcripts (manual or auto-generated) in Hindi/English.

Uses the current (v1.x) instance-based `youtube-transcript-api` interface:
    ytt_api = YouTubeTranscriptApi()
    ytt_api.fetch(video_id, languages=[...])
    ytt_api.list(video_id)
NOT the deprecated static `YouTubeTranscriptApi.get_transcript(...)` API.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

logger = logging.getLogger(__name__)


class TranscriptUnavailableError(Exception):
    """Raised when no usable transcript could be retrieved for a video."""


@dataclass
class TranscriptResult:
    video_id: str
    language: str
    language_code: str
    is_generated: bool
    segments: list[dict]  # [{"text": str, "start": float, "duration": float}, ...]

    @property
    def full_text(self) -> str:
        return " ".join(s["text"] for s in self.segments)

    @property
    def duration_seconds(self) -> float:
        if not self.segments:
            return 0.0
        last = self.segments[-1]
        return last["start"] + last["duration"]


def fetch_transcript(video_id: str, preferred_languages: list[str] | None = None) -> TranscriptResult:
    """Fetch the best-available transcript for a video.

    Tries manually created transcripts in the preferred languages first,
    then auto-generated ones, then falls back to any available transcript
    (translated to the first preferred language when possible).
    """
    preferred_languages = preferred_languages or ["hi", "en"]
    ytt_api = YouTubeTranscriptApi()

    try:
        transcript_list = ytt_api.list(video_id)
    except TranscriptsDisabled as exc:
        raise TranscriptUnavailableError(
            "Transcripts are disabled for this video."
        ) from exc
    except VideoUnavailable as exc:
        raise TranscriptUnavailableError(
            "This video is unavailable (private, deleted, or region-locked)."
        ) from exc
    except CouldNotRetrieveTranscript as exc:
        raise TranscriptUnavailableError(f"Could not retrieve transcript list: {exc}") from exc

    transcript = _select_best_transcript(transcript_list, preferred_languages)
    if transcript is None:
        raise TranscriptUnavailableError(
            "No transcript (manual, auto-generated, or translatable) is available "
            "for this video in the requested languages."
        )

    try:
        fetched = transcript.fetch()
    except NoTranscriptFound as exc:
        raise TranscriptUnavailableError("Transcript disappeared before it could be fetched.") from exc
    except CouldNotRetrieveTranscript as exc:
        raise TranscriptUnavailableError(f"Failed to fetch transcript: {exc}") from exc

    segments = [
        {"text": snippet.text, "start": snippet.start, "duration": snippet.duration}
        for snippet in fetched
        if snippet.text.strip()
    ]

    if not segments:
        raise TranscriptUnavailableError("Transcript was empty after fetching.")

    return TranscriptResult(
        video_id=video_id,
        language=transcript.language,
        language_code=transcript.language_code,
        is_generated=transcript.is_generated,
        segments=segments,
    )


def _select_best_transcript(transcript_list, preferred_languages: list[str]):
    """Pick manual > auto-generated in preferred languages, else translate, else any."""
    # 1) Manually created transcript in a preferred language
    try:
        return transcript_list.find_manually_created_transcript(preferred_languages)
    except NoTranscriptFound:
        pass

    # 2) Auto-generated transcript in a preferred language
    try:
        return transcript_list.find_generated_transcript(preferred_languages)
    except NoTranscriptFound:
        pass

    # 3) Any transcript, translated into the first preferred language if supported
    available = list(transcript_list)
    if not available:
        return None

    for transcript in available:
        if transcript.is_translatable:
            try:
                return transcript.translate(preferred_languages[0])
            except Exception:  # noqa: BLE001 - translation is best-effort
                continue

    # 4) Give up gracefully and use whatever exists (any language)
    return available[0]
