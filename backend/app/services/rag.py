# RAG service flow:
# 1. Rewrite conversational queries into standalone search queries.
# 2. Generate an embedding for the rewritten query.
# 3. Retrieve relevant chunks from the tenant-scoped vector store.
# 4. Apply the similarity threshold guardrail.
# 5. Build grounded context and structured citations for generation.
#
# This module intentionally keeps retrieval and response-generation
# preparation separate so each stage can be tested independently.

from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from app.core.config import settings
from app.services.embedding import embedding_service
from app.services.vector_store import vector_store
from app.services.llm import llm_service

REWRITE_SYSTEM_PROMPT = """You are a search query reformulator.
Given the conversation history and a follow-up question, rewrite the follow-up question into an independent, fully qualified search query.
Do NOT answer the question. Only output the rewritten search string.

Conversation History:
{chat_history}

Follow-up Question: {query}

Rewritten Query:"""

REFUSAL_MESSAGE = (
    "I cannot find approved bank guidance on this topic within your account's "
    "uploaded documentation. Please escalate this request to the Compliance and Legal Department."
)

class RAGPipeline:
    def __init__(self):
        self.threshold = settings.SIMILARITY_THRESHOLD
        self._load_system_prompt()

    def _load_system_prompt(self):
        """Loads verified system prompt from file or fallback."""
        prompt_path = Path(__file__).resolve().parent.parent.parent.parent / "prompts" / "system_prompt.txt"
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt_template = f.read()
        else:
            self.system_prompt_template = (
                "You are the Grounded Advisory Assistant (GAA). "
                "Base answers EXCLUSIVELY on the provided CONTEXT CHUNKS. "
                "Cite every claim with [Doc: <name>, Ver: <ver>, Clause: <clause>]. "
                "If context is missing or insufficient, refuse deterministically."
            )

    def rewrite_query(self, query: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Reformulates conversational follow-up questions (e.g. 'What about for NRIs?')
        into standalone queries.
        """
        if not chat_history:
            return query.strip()

        history_lines = []
        for msg in chat_history[-6:]: # Keep last 3 turns
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            history_lines.append(f"{role}: {content}")

        history_str = "\n".join(history_lines)
        user_prompt = f"Conversation History:\n{history_str}\n\nFollow-up Question: {query}\n\nRewritten Query:"
        
        rewritten = llm_service.generate(
            system_prompt=REWRITE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.0,
        )
        return rewritten.strip() if rewritten else query.strip()

    def retrieve_and_evaluate(
        self,
        query: str,
        account_id: str,
        chat_history: List[Dict[str, str]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Executes dense retrieval with hard tenant filtering and guardrail evaluation:
        1. Multi-turn query rewriting.
        2. Vector search partitioned by account_id and excluding discontinued products.
        3. Threshold confidence check (>= 0.68).
        4. Structured citation assembly.
        """
        chat_history = chat_history or []
        rewritten_query = self.rewrite_query(query, chat_history)

   # 1. Generate query embedding.
# The rewritten query is embedded rather than the original follow-up
# question so retrieval can operate on a complete search intent.
        query_vec = embedding_service.get_embedding(rewritten_query)

       # 1. Generate query embedding.
# The rewritten query is embedded rather than the original follow-up
# question so retrieval can operate on a complete search intent.
        candidates = vector_store.search(
            query_vector=query_vec,
            account_id=account_id,
            top_k=top_k,
            include_discontinued=False,
        )

        top_score = candidates[0]["score"] if candidates else 0.0

        # 2. Retrieve candidates scoped to the current account.
# Tenant filtering is delegated to the vector store so that retrieval
# cannot accidentally mix documents between accounts.
        if not candidates or top_score < self.threshold:
            return {
                "decision": "REFUSAL",
                "message": REFUSAL_MESSAGE,
                "citations": [],
                "top_score": top_score,
                "rewritten_query": rewritten_query,
                "retrieved_chunk_ids": [c["id"] for c in candidates],
                "context": "",
                "is_refusal": True,
            }

        # 4. Assemble context and citations
        context_blocks: List[str] = []
        citations: List[Dict[str, Any]] = []
        chunk_ids: List[str] = []

        for cand in candidates:
            meta = cand.get("metadata", {})
            chunk_ids.append(cand["id"])
            doc_name = meta.get("document_name", "Unknown")
            version = meta.get("document_version", "v1.0")
            clause_id = meta.get("clause_id", f"Page {meta.get('page_number', 1)}")
            page_num = meta.get("page_number", 1)
            chunk_text = cand.get("text", "")

            tag = f"[Doc: {doc_name}, Ver: {version}, Clause: {clause_id}, Page: {page_num}]"
            context_blocks.append(f"{tag}\n{chunk_text}\n")

            citations.append({
                "document_name": doc_name,
                "version": version,
                "clause_id": clause_id,
                "page_number": page_num,
                "excerpt": chunk_text[:250] + ("..." if len(chunk_text) > 250 else ""),
                "score": cand.get("score", 0.0),
            })

        return {
            "decision": "GENERATE",
            "message": "",
            "citations": citations,
            "top_score": top_score,
            "rewritten_query": rewritten_query,
            "retrieved_chunk_ids": chunk_ids,
            "context": "\n".join(context_blocks),
            "is_refusal": False,
        }

    def build_generation_prompts(
        self,
        query: str,
        rewritten_query: str,
        context: str,
        chat_history: List[Dict[str, str]],
    ) -> Tuple[str, str]:
        """Prepares system and user prompts for the generation model."""
        history_lines = [
            f"{m.get('role', 'user').capitalize()}: {m.get('content', '')}"
            for m in chat_history[-6:]
        ]
        history_str = "\n".join(history_lines) if history_lines else "None."

        user_prompt = (
            f"CONTEXT CHUNKS:\n{context}\n\n"
            f"CONVERSATION HISTORY:\n{history_str}\n\n"
            f"RELATIONSHIP MANAGER'S INQUIRY:\n{query}\n"
            f"(Internal Search Intent: {rewritten_query})\n\n"
            "GROUNDED ADVISORY RESPONSE:"
        )

        return self.system_prompt_template, user_prompt

rag_pipeline = RAGPipeline()
