"""Pydantic request/response models shared across routers."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ProcessVideoRequest(BaseModel):
    url: str = Field(..., description="Full YouTube URL or bare video ID")
    preferred_languages: list[str] = Field(
        default_factory=lambda: ["hi", "en"],
        description="Ordered language preference for transcript retrieval",
    )

    @field_validator("url")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("url must not be empty")
        return v.strip()


class TranscriptSource(BaseModel):
    text: str
    start: float
    duration: float

    @property
    def timestamp(self) -> str:
        m, s = divmod(int(self.start), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


class ProcessVideoResponse(BaseModel):
    session_id: str
    video_id: str
    title: str | None = None
    language: str
    is_generated: bool
    chunk_count: int
    duration_seconds: float
    summary: str
    suggested_questions: list[str]


class AskRequest(BaseModel):
    session_id: str
    question: str = Field(..., min_length=1, max_length=2000)
    language: Literal["auto", "hi", "en"] = "auto"

    @field_validator("question")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be empty")
        return v.strip()


class SourceChunk(BaseModel):
    text: str
    start: float
    timestamp: str


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
