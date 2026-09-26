"""
RAG pipeline: Transcript -> Documents -> Chunking -> Embeddings -> FAISS ->
Retriever -> Groq LLM.

Embeddings: multilingual (Hindi + English) sentence-embedding model served
through the Hugging Face Inference API via `langchain-huggingface`'s
`HuggingFaceEndpointEmbeddings` (the current, non-deprecated integration).

LLM: Groq via `langchain-groq`'s `ChatGroq`.
"""
from __future__ import annotations

import logging
import re

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.services.transcript_service import TranscriptResult

logger = logging.getLogger(__name__)
settings = get_settings()

_embeddings_singleton: HuggingFaceEndpointEmbeddings | None = None


def get_embeddings() -> HuggingFaceEndpointEmbeddings:
    """Lazily instantiate a single shared embeddings client (thread-safe enough for our use)."""
    global _embeddings_singleton
    if _embeddings_singleton is None:
        _embeddings_singleton = HuggingFaceEndpointEmbeddings(
            model=settings.embedding_model,
            provider=settings.embedding_provider,
            huggingfacehub_api_token=settings.huggingfacehub_api_token or None,
        )
    return _embeddings_singleton


def get_llm(streaming: bool = False) -> ChatGroq:
    return ChatGroq(
        model=settings.groq_model,
        temperature=settings.groq_temperature,
        api_key=settings.groq_api_key,
        streaming=streaming,
    )


def transcript_to_documents(transcript: TranscriptResult) -> list[Document]:
    """Chunk a transcript into overlapping Documents, keeping the start timestamp
    of the *first* original segment folded into each chunk as metadata so we can
    surface "jump to this moment" citations with the answer.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", "। ", ". ", " ", ""],  # "। " = Hindi full stop (danda)
    )

    # Build a single text blob but remember character offset -> start-time mapping
    offset_map: list[tuple[int, float]] = []
    pieces: list[str] = []
    cursor = 0
    for seg in transcript.segments:
        text = seg["text"].strip()
        if not text:
            continue
        pieces.append(text)
        offset_map.append((cursor, seg["start"]))
        cursor += len(text) + 1  # +1 for the joining space

    full_text = " ".join(pieces)
    chunks = splitter.split_text(full_text)

    documents: list[Document] = []
    search_cursor = 0
    for chunk in chunks:
        idx = full_text.find(chunk[:50], search_cursor)
        if idx == -1:
            idx = full_text.find(chunk[:50])
        start_time = _nearest_start_time(idx if idx != -1 else search_cursor, offset_map)
        documents.append(
            Document(
                page_content=chunk,
                metadata={
                    "video_id": transcript.video_id,
                    "start": start_time,
                    "language": transcript.language_code,
                },
            )
        )
        search_cursor = max(search_cursor, idx if idx != -1 else search_cursor)

    return documents


def _nearest_start_time(char_offset: int, offset_map: list[tuple[int, float]]) -> float:
    best = 0.0
    for offset, start in offset_map:
        if offset > char_offset:
            break
        best = start
    return best


def build_vectorstore(documents: list[Document]) -> FAISS:
    embeddings = get_embeddings()
    return FAISS.from_documents(documents, embeddings)


ANSWER_PROMPT = ChatPromptTemplate.from_template(
    """You are a helpful assistant that answers questions about a YouTube video \
using ONLY the transcript context provided below. The transcript may be in \
Hindi, English, or a mix of both (Hinglish).

Rules:
- Answer strictly using the given context. If the answer is not contained in \
the context, say clearly that the video does not cover it — do not make things up.
- Reply in the SAME language the user asked the question in (Hindi question -> \
Hindi answer, English question -> English answer).
- Be concise and directly answer the question first, then add brief supporting detail.

Context from video transcript:
{context}

Question: {question}

Answer:"""
)

SUMMARY_PROMPT = ChatPromptTemplate.from_template(
    """Summarize the following YouTube video transcript in 4-6 sentences. \
Write the summary in the same primary language as the transcript (Hindi or \
English). Focus on the key topics, arguments, and takeaways.

Transcript excerpt:
{context}

Summary:"""
)

QUESTIONS_PROMPT = ChatPromptTemplate.from_template(
    """Based on the following YouTube video transcript excerpt, generate exactly \
5 short, specific questions a curious viewer might ask about this video's content. \
Write the questions in the same primary language as the transcript. \
Return ONLY the questions, one per line, no numbering, no extra commentary.

Transcript excerpt:
{context}

Questions:"""
)


def _format_docs(docs: list[Document]) -> str:
    return "\n\n".join(d.page_content for d in docs)


def answer_question(vectorstore: FAISS, question: str) -> tuple[str, list[Document]]:
    retriever = vectorstore.as_retriever(search_kwargs={"k": settings.retriever_k})
    source_docs = retriever.invoke(question)
    llm = get_llm()
    chain = ANSWER_PROMPT | llm | StrOutputParser()
    answer = chain.invoke({"context": _format_docs(source_docs), "question": question})
    return answer, source_docs


def stream_answer(vectorstore: FAISS, question: str):
    """Yields answer text chunks for SSE streaming. Returns source docs via side channel."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": settings.retriever_k})
    source_docs = retriever.invoke(question)
    llm = get_llm(streaming=True)
    chain = ANSWER_PROMPT | llm | StrOutputParser()
    stream = chain.stream({"context": _format_docs(source_docs), "question": question})
    return stream, source_docs


def summarize(documents: list[Document], max_chars: int = 6000) -> str:
    text = " ".join(d.page_content for d in documents)[:max_chars]
    llm = get_llm()
    chain = SUMMARY_PROMPT | llm | StrOutputParser()
    return chain.invoke({"context": text}).strip()


def suggest_questions(documents: list[Document], max_chars: int = 6000) -> list[str]:
    text = " ".join(d.page_content for d in documents)[:max_chars]
    llm = get_llm()
    chain = QUESTIONS_PROMPT | llm | StrOutputParser()
    raw = chain.invoke({"context": text})
    questions = []
    for line in raw.splitlines():
        cleaned = re.sub(r"^[\s\-\*\d\.\)]+", "", line).strip()
        if cleaned:
            questions.append(cleaned)
    return questions[:5]
