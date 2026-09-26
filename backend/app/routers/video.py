from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import get_settings
from app.models.schemas import ProcessVideoRequest, ProcessVideoResponse
from app.services import rag_service
from app.services.session_service import get_session_store
from app.services.transcript_service import TranscriptUnavailableError, fetch_transcript
from app.utils.youtube import InvalidYouTubeURLError, extract_video_id

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/video", tags=["video"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/process", response_model=ProcessVideoResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
def process_video(request: Request, payload: ProcessVideoRequest) -> ProcessVideoResponse:
    try:
        video_id = extract_video_id(payload.url)
    except InvalidYouTubeURLError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        transcript = fetch_transcript(video_id, payload.preferred_languages)
    except TranscriptUnavailableError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error fetching transcript for %s", video_id)
        raise HTTPException(
            status_code=502, detail=f"Failed to fetch transcript: {exc}"
        ) from exc

    try:
        documents = rag_service.transcript_to_documents(transcript)
        vectorstore = rag_service.build_vectorstore(documents)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to build vector index for %s", video_id)
        raise HTTPException(
            status_code=502, detail=f"Failed to build embeddings/index: {exc}"
        ) from exc

    try:
        summary = rag_service.summarize(documents)
        suggested = rag_service.suggest_questions(documents)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to summarize / suggest questions for %s", video_id)
        summary = "Summary unavailable right now (LLM error)."
        suggested = []

    store = get_session_store()
    session = store.create(
        video_id=video_id,
        vectorstore=vectorstore,
        language=transcript.language_code,
        is_generated=transcript.is_generated,
        duration_seconds=transcript.duration_seconds,
    )

    return ProcessVideoResponse(
        session_id=session.session_id,
        video_id=video_id,
        title=None,
        language=transcript.language_code,
        is_generated=transcript.is_generated,
        chunk_count=len(documents),
        duration_seconds=transcript.duration_seconds,
        summary=summary,
        suggested_questions=suggested,
    )
