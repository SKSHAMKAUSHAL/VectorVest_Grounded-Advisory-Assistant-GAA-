import time
import json
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.config import settings
from app.core.rate_limit import rate_limit_dependency
from app.models.models import User, ComplianceAuditLog
from app.api.deps import get_current_user
from app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    CitationItem,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResultItem,
)
from app.services.rag import rag_pipeline
from app.services.llm import llm_service
from app.services.vector_store import vector_store

logger = logging.getLogger("gaa.chat")

router = APIRouter(prefix="/chat", tags=["Grounded Advisory Chat"])

def get_db_session() -> Session:
    """Helper to get database session, respecting FastAPI dependency overrides in tests."""
    from app.main import app
    override = app.dependency_overrides.get(get_db)
    if override:
        gen = override()
        return next(gen)
    return SessionLocal()

def record_audit_log(
    account_id: str,
    user_id: str,
    query: str,
    rewritten_query: str,
    chunk_ids: list,
    score: float,
    response_text: str,
    is_refusal: bool,
    latency_ms: int,
):
    """Writes compliance audit record to relational database."""
    db: Session = get_db_session()
    try:
        log_entry = ComplianceAuditLog(
            account_id=account_id,
            user_id=user_id,
            query=query,
            rewritten_query=rewritten_query,
            retrieved_chunk_ids=chunk_ids,
            similarity_score=score,
            response=response_text,
            is_refusal=is_refusal,
            latency_ms=latency_ms,
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to persist compliance audit log: %s", str(e), exc_info=True)
    finally:
        db.close()

@router.post("/query")
async def chat_query_stream(
    request: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    _rate_limit: bool = Depends(rate_limit_dependency(max_requests=60, window_seconds=60.0, endpoint_tag="chat_query")),
):
    """
    Submits an RM advisory query and streams real-time tokens via Server-Sent Events (SSE).
    Emits token events, followed by structured citation metadata and done event.
    Logs full audit record upon stream completion.
    """
    start_time = time.time()
    history = [m.model_dump() for m in request.chat_history] if request.chat_history else []

    eval_result = rag_pipeline.retrieve_and_evaluate(
        query=request.query,
        account_id=current_user.account_id,
        chat_history=history,
    )

    async def sse_event_stream() -> AsyncGenerator[str, None]:
        accumulated_text = []

        if eval_result["decision"] == "REFUSAL":
            refusal_text = eval_result["message"]
            yield f"event: token\ndata: {json.dumps({'token': refusal_text})}\n\n"
            accumulated_text.append(refusal_text)

            yield f"event: citations\ndata: {json.dumps([])}\n\n"
            yield "event: done\ndata: [DONE]\n\n"

            latency = int((time.time() - start_time) * 1000)
            record_audit_log(
                account_id=current_user.account_id,
                user_id=current_user.id,
                query=request.query,
                rewritten_query=eval_result["rewritten_query"],
                chunk_ids=eval_result["retrieved_chunk_ids"],
                score=eval_result["top_score"],
                response_text=refusal_text,
                is_refusal=True,
                latency_ms=latency,
            )
            return

        # Generation Path
        try:
            system_prompt, user_prompt = rag_pipeline.build_generation_prompts(
                query=request.query,
                rewritten_query=eval_result["rewritten_query"],
                context=eval_result["context"],
                chat_history=history,
            )

            async for token in llm_service.stream_generate(system_prompt, user_prompt):
                accumulated_text.append(token)
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

            # Emit citations event
            yield f"event: citations\ndata: {json.dumps(eval_result['citations'])}\n\n"
            yield "event: done\ndata: [DONE]\n\n"

            latency = int((time.time() - start_time) * 1000)
            full_response = "".join(accumulated_text)
            record_audit_log(
                account_id=current_user.account_id,
                user_id=current_user.id,
                query=request.query,
                rewritten_query=eval_result["rewritten_query"],
                chunk_ids=eval_result["retrieved_chunk_ids"],
                score=eval_result["top_score"],
                response_text=full_response,
                is_refusal=False,
                latency_ms=latency,
            )
        except Exception as e:
            logger.error("SSE stream generation error: %s", str(e), exc_info=True)
            safe_error = (
                f"Advisory generation error: {str(e)}"
                if settings.ENVIRONMENT in ("development", "test")
                else "An unexpected error occurred during grounded advisory generation. Please retry or escalate."
            )
            yield f"event: error\ndata: {json.dumps({'error': safe_error})}\n\n"
            yield "event: done\ndata: [DONE]\n\n"
            latency = int((time.time() - start_time) * 1000)
            record_audit_log(
                account_id=current_user.account_id,
                user_id=current_user.id,
                query=request.query,
                rewritten_query=eval_result.get("rewritten_query", request.query),
                chunk_ids=eval_result.get("retrieved_chunk_ids", []),
                score=eval_result.get("top_score", 0.0),
                response_text=f"Stream error: {safe_error}",
                is_refusal=True,
                latency_ms=latency,
            )

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(
        sse_event_stream(),
        media_type="text/event-stream",
        headers=headers,
    )

@router.post("/query/sync", response_model=ChatQueryResponse)
def chat_query_sync(
    request: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_dependency(max_requests=60, window_seconds=60.0, endpoint_tag="chat_query")),
):
    """
    Synchronous version of /query.
    Returns structured JSON with complete answer, citations, confidence score, and refusal status.
    """
    start_time = time.time()
    history = [m.model_dump() for m in request.chat_history] if request.chat_history else []

    eval_result = rag_pipeline.retrieve_and_evaluate(
        query=request.query,
        account_id=current_user.account_id,
        chat_history=history,
    )

    if eval_result["decision"] == "REFUSAL":
        response_text = eval_result["message"]
        is_refusal = True
        citations = []
    else:
        system_prompt, user_prompt = rag_pipeline.build_generation_prompts(
            query=request.query,
            rewritten_query=eval_result["rewritten_query"],
            context=eval_result["context"],
            chat_history=history,
        )
        response_text = llm_service.generate(system_prompt, user_prompt)
        is_refusal = False
        citations = eval_result["citations"]

    latency = int((time.time() - start_time) * 1000)

    # Persist audit record safely
    try:
        log_entry = ComplianceAuditLog(
            account_id=current_user.account_id,
            user_id=current_user.id,
            query=request.query,
            rewritten_query=eval_result["rewritten_query"],
            retrieved_chunk_ids=eval_result["retrieved_chunk_ids"],
            similarity_score=eval_result["top_score"],
            response=response_text,
            is_refusal=is_refusal,
            latency_ms=latency,
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to persist synchronous audit log: %s", str(e), exc_info=True)

    return ChatQueryResponse(
        answer=response_text,
        citations=[CitationItem(**c) for c in citations],
        is_refusal=is_refusal,
        similarity_score=eval_result["top_score"],
        rewritten_query=eval_result["rewritten_query"],
        latency_ms=latency,
    )

@router.post("/search", response_model=SemanticSearchResponse)
def semantic_search_chunks(
    request: SemanticSearchRequest,
    current_user: User = Depends(get_current_user),
    _rate_limit: bool = Depends(rate_limit_dependency(max_requests=100, window_seconds=60.0, endpoint_tag="chat_search")),
):
    """
    Executes top-k semantic search directly against the tenant's indexed vector knowledge base.
    Returns ranked chunks with similarity scores, document metadata, and clause citations.
    """
    candidates = vector_store.semantic_search(
        query_text=request.query,
        account_id=current_user.account_id,
        top_k=request.top_k,
        include_discontinued=request.include_discontinued,
        min_score=request.min_score,
        doc_type=request.doc_type,
    )

    results = [SemanticSearchResultItem(**c) for c in candidates]
    return SemanticSearchResponse(
        query=request.query,
        account_id=current_user.account_id,
        total_results=len(results),
        results=results,
    )

@router.get("/citation-preview")
def preview_citation_chunk(
    chunk_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Tenant-secured citation preview endpoint.
    Retrieves full source excerpt for a given chunk_id strictly scoped to the caller's account_id.
    Prevents unauthorized cross-tenant chunk observation.
    """
    if not chunk_id or not isinstance(chunk_id, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid chunk_id parameter is required.",
        )

    try:
        results = vector_store.collection.get(
            ids=[chunk_id],
            include=["documents", "metadatas"],
        )
    except Exception as e:
        logger.error("Error retrieving citation preview chunk: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query citation chunk.",
        )

    if not results or not results["ids"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citation chunk not found or access denied.",
        )

    meta = results["metadatas"][0] if results["metadatas"] else {}
    if str(meta.get("account_id")) != str(current_user.account_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Citation chunk not found or access denied.",
        )

    doc_text = results["documents"][0] if results["documents"] else ""
    return {
        "chunk_id": chunk_id,
        "account_id": current_user.account_id,
        "document_name": meta.get("document_name", "Unknown"),
        "version": meta.get("document_version", "v1.0"),
        "clause_id": meta.get("clause_id", ""),
        "page_number": int(meta.get("page_number", 1)),
        "text": doc_text,
    }
