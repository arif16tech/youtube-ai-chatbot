"""
In-memory session store.

Holds one FAISS vectorstore + chat history per active "video session".
This is intentionally simple (a dict guarded by a lock) which is fine for a
single-process demo/small deployment. For horizontal scaling, swap this out
for Redis + a persisted FAISS index per session (see README "Scaling notes").
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field

from langchain_community.vectorstores import FAISS

from app.config import get_settings

settings = get_settings()


@dataclass
class Session:
    session_id: str
    video_id: str
    vectorstore: FAISS
    language: str
    is_generated: bool
    duration_seconds: float
    chat_history: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)

    def touch(self) -> None:
        self.last_used_at = time.time()


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def create(
        self,
        video_id: str,
        vectorstore: FAISS,
        language: str,
        is_generated: bool,
        duration_seconds: float,
    ) -> Session:
        self._evict_expired()
        with self._lock:
            if len(self._sessions) >= settings.max_sessions:
                oldest_id = min(self._sessions, key=lambda k: self._sessions[k].last_used_at)
                del self._sessions[oldest_id]
            session_id = str(uuid.uuid4())
            session = Session(
                session_id=session_id,
                video_id=video_id,
                vectorstore=vectorstore,
                language=language,
                is_generated=is_generated,
                duration_seconds=duration_seconds,
            )
            self._sessions[session_id] = session
            return session

    def get(self, session_id: str) -> Session | None:
        self._evict_expired()
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.touch()
            return session

    def append_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.chat_history.append({"role": role, "content": content})
                session.touch()

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def _evict_expired(self) -> None:
        ttl_seconds = settings.session_ttl_minutes * 60
        cutoff = time.time() - ttl_seconds
        with self._lock:
            expired = [sid for sid, s in self._sessions.items() if s.last_used_at < cutoff]
            for sid in expired:
                del self._sessions[sid]


_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    global _store
    if _store is None:
        _store = SessionStore()
    return _store
