from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.config import get_settings
from app.models.schemas import AskRequest, AskResponse, SourceChunk
from app.services import rag_service
from app.services.session_service import get_session_store

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/chat", tags=["chat"])
limiter = Limiter(key_func=get_remote_address)


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _get_session_or_404(session_id: str):
    store = get_session_store()
    session = store.get(session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired. Please process the video again.",
        )
    return session


@router.post("/ask", response_model=AskResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
def ask(request: Request, payload: AskRequest) -> AskResponse:
    session = _get_session_or_404(payload.session_id)
    store = get_session_store()

    try:
        answer, source_docs = rag_service.answer_question(session.vectorstore, payload.question)
    except Exception as exc:  # noqa: BLE001
        logger.exception("LLM error answering question for session %s", payload.session_id)
        raise HTTPException(status_code=502, detail=f"Failed to generate answer: {exc}") from exc

    store.append_message(payload.session_id, "user", payload.question)
    store.append_message(payload.session_id, "assistant", answer)

    sources = [
        SourceChunk(
            text=doc.page_content[:280],
            start=doc.metadata.get("start", 0.0),
            timestamp=_format_timestamp(doc.metadata.get("start", 0.0)),
        )
        for doc in source_docs
    ]
    return AskResponse(answer=answer, sources=sources)


@router.post("/stream")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
def ask_stream(request: Request, payload: AskRequest):
    session = _get_session_or_404(payload.session_id)
    store = get_session_store()

    def event_generator():
        full_answer = []
        try:
            stream, source_docs = rag_service.stream_answer(session.vectorstore, payload.question)
            sources = [
                {
                    "text": doc.page_content[:280],
                    "start": doc.metadata.get("start", 0.0),
                    "timestamp": _format_timestamp(doc.metadata.get("start", 0.0)),
                }
                for doc in source_docs
            ]
            yield f"event: sources\ndata: {json.dumps(sources)}\n\n"

            for chunk in stream:
                full_answer.append(chunk)
                yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"

            store.append_message(payload.session_id, "user", payload.question)
            store.append_message(payload.session_id, "assistant", "".join(full_answer))
            yield "event: done\ndata: {}\n\n"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Streaming error for session %s", payload.session_id)
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history/{session_id}")
def get_history(session_id: str):
    session = _get_session_or_404(session_id)
    return {"session_id": session_id, "messages": session.chat_history}
