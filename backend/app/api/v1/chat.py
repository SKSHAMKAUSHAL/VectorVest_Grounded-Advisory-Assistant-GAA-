import time
import json
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.models.models import User, ComplianceAuditLog
from app.api.deps import get_current_user
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse, CitationItem
from app.services.rag import rag_pipeline
from app.services.llm import llm_service

router = APIRouter(prefix="/chat", tags=["Grounded Advisory Chat"])

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
    db: Session = SessionLocal()
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
        # Non-blocking for client stream, but prints server error
        print(f"Error persisting audit log: {e}")
    finally:
        db.close()

@router.post("/query")
async def chat_query_stream(
    request: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
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

    return StreamingResponse(sse_event_stream(), media_type="text/event-stream")

@router.post("/query/sync", response_model=ChatQueryResponse)
def chat_query_sync(
    request: ChatQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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

    # Persist audit record
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

    return ChatQueryResponse(
        answer=response_text,
        citations=[CitationItem(**c) for c in citations],
        is_refusal=is_refusal,
        similarity_score=eval_result["top_score"],
        rewritten_query=eval_result["rewritten_query"],
        latency_ms=latency,
    )
