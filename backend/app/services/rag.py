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
from app.services.reranker import reranker

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

HELP_MESSAGE = (
    "Hello! I am WealthGuard AI, your Grounded Advisory Assistant (GAA) for private wealth management, banking compliance, and advisory support.\n\n"
    "Here is how I can assist you:\n"
    "• Policy & Compliance Guidance: Provide verified answers on bank advisory policies, regulatory circulars, and product term sheets.\n"
    "• Product & Fee Inquiries: Look up management fee caps, liquidity terms, and eligibility rules for discretionary portfolios and debt funds.\n"
    "• Tax & Investment Rules: Explain capital gains tax offsets, municipal bond rules, and non-resident (NRI) investment treatments.\n"
    "• Verifiable Clause Citations: Every factual answer is strictly grounded in bank documentation with clickable clause badges pointing to verified documents.\n\n"
    "You can try asking:\n"
    "1. 'What is the capital gains tax offset for municipal bonds under 2024 rules?'\n"
    "2. 'Management fee caps and liquidity terms for Level-A discretionary portfolios'\n"
    "3. 'Can non-resident individuals (NRIs) invest in High-Yield Debt Funds?'\n"
    "4. 'What is the early redemption penalty for Tier-1 bonds?'"
)

import re

_CAPABILITY_PATTERNS = [
    r"\bhow can you help\b",
    r"\bhow do you help\b",
    r"\bwhat can you do\b",
    r"\bwhat do you do\b",
    r"\bwho are you\b",
    r"\bwhat is (this|wealthguard|gaa)\b",
    r"\bwhat questions can i ask\b",
    r"\bwhat can i ask\b",
    r"\bhow to use\b",
    r"\bhow (do|can) i (add|upload) (a )?pdf\b",
    r"\bhow to (add|upload) (a )?pdf\b",
    r"^\s*help\s*$",
    r"^\s*(hello|hi|hey|heyy+|greetings|good morning|good afternoon|good evening|yy+oo+|yo|what'?s up|sup)\b",
]

# Pronoun / deixis patterns that indicate a follow-up needs context injection
_REFERENTIAL_TOKENS = frozenset([
    "it", "its", "they", "them", "their", "this", "that", "these", "those",
    "such", "same", "above", "said", "mentioned", "what about", "and for",
    "also for", "how about", "what if", "but what", "nri", "non-resident",
])


class ConversationHistoryManager:
    """
    Manages stateful, rolling conversation history for multi-turn RAG sessions.

    Responsibilities:
    - Stores and trims conversation turns to a configurable window.
    - Detects whether an incoming query is referential (needs context injection).
    - Extracts the dominant entity / topic from recent turns for enriched reformulation.
    - Compresses long conversation histories to avoid exceeding LLM context limits.
    """

    def __init__(self, max_turns: int = 6, max_chars_per_message: int = 400):
        """
        Args:
            max_turns: Maximum number of individual messages (user + assistant)
                       retained in the active window.  Older messages are dropped.
            max_chars_per_message: Characters to which each message is truncated
                                   when building the history string for the LLM.
        """
        self.max_turns = max_turns
        self.max_chars_per_message = max_chars_per_message

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def trim(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Return at most *max_turns* most recent messages."""
        return history[-self.max_turns:]

    def is_referential(self, query: str) -> bool:
        """
        Returns True when the query contains pronouns or short contextual phrases
        that indicate it cannot stand alone without the conversation history.

        Examples that return True:
            - "What about for NRIs?"
            - "Does it apply to them too?"
            - "And for joint accounts?"
        """
        lower = query.lower().strip()
        tokens = set(lower.split())
        # Direct token overlap with referential set
        if tokens & _REFERENTIAL_TOKENS:
            return True
        # Short queries almost always need context
        if len(lower.split()) <= 5:
            return True
        return False

    def build_history_string(self, history: List[Dict[str, str]]) -> str:
        """
        Converts the message list into a compact string for the LLM reformulator prompt.
        Each message is truncated to *max_chars_per_message* to avoid context bloat.
        """
        lines: List[str] = []
        for msg in self.trim(history):
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            if len(content) > self.max_chars_per_message:
                content = content[: self.max_chars_per_message].rstrip() + "..."
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def extract_last_topic(self, history: List[Dict[str, str]]) -> str:
        """
        Returns the last user query from history as a topic hint,
        used to enrich short follow-up queries even before calling the LLM.
        """
        for msg in reversed(self.trim(history)):
            if msg.get("role") == "user":
                return msg.get("content", "").strip()
        return ""


# Module-level singleton
conversation_history_manager = ConversationHistoryManager()


class RAGPipeline:
    def __init__(self):
        self.threshold = settings.SIMILARITY_THRESHOLD
        self.history_manager = conversation_history_manager
        self.reranker = reranker
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
        Reformulates conversational follow-up questions into standalone search queries.

        Strategy:
        1. If *chat_history* is empty, the query is already standalone — return as-is.
        2. If the query is NOT referential (contains no pronouns / context pointers),
           return it directly to avoid unnecessary LLM calls.
        3. Otherwise, build a compact history string and call the LLM reformulator.
           On LLM failure or empty response, fall back to topic-enriched original query.
        """
        if not chat_history:
            return query.strip()

        # Fast path: non-referential, self-contained queries skip reformulation
        if not self.history_manager.is_referential(query):
            return query.strip()

        history_str = self.history_manager.build_history_string(chat_history)
        user_prompt = (
            f"Conversation History:\n{history_str}\n\n"
            f"Follow-up Question: {query}\n\n"
            "Rewritten Query:"
        )

        rewritten = llm_service.generate(
            system_prompt=REWRITE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.0,
        )
        result = rewritten.strip() if rewritten else ""

        # Safety guard: if LLM returns empty or mirrors the original, add topic context
        if not result or result.lower() == query.lower():
            last_topic = self.history_manager.extract_last_topic(chat_history)
            if last_topic:
                return f"{last_topic} — {query.strip()}"
            return query.strip()

        return result

    def is_capability_query(self, query: str) -> bool:
        """Detects whether a user prompt is asking about capabilities, help, or a greeting."""
        q_clean = query.lower().strip()
        return any(re.search(pattern, q_clean) for pattern in _CAPABILITY_PATTERNS)

    def retrieve_and_evaluate(
        self,
        query: str,
        account_id: str,
        chat_history: List[Dict[str, str]] = None,
        top_k: int = 5,
        doc_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes dense retrieval with hard tenant filtering and guardrail evaluation:
        1. Multi-turn query rewriting (with referential detection).
        2. Vector search partitioned by account_id and excluding discontinued products.
        3. Threshold confidence check (>= 0.68).
        4. Structured citation assembly.
        """
        # 0. Check for capability inquiry or greeting
        if self.is_capability_query(query):
            return {
                "decision": "CAPABILITY",
                "message": HELP_MESSAGE,
                "citations": [],
                "top_score": 1.0,
                "rewritten_query": query.strip(),
                "retrieved_chunk_ids": [],
                "context": "",
                "is_refusal": False,
            }

        chat_history = chat_history or []
        rewritten_query = self.rewrite_query(query, chat_history)

        # 1. Generate query embedding for the rewritten query
        query_vec = embedding_service.get_embedding(rewritten_query)

        # 2. Retrieve top candidate pool scoped strictly to the current account (excluding discontinued & superseded)
        safe_top_k = max(1, int(top_k)) if top_k else 5
        retrieval_pool_k = max(safe_top_k * 3, 15)
        raw_candidates = vector_store.search(
            query_vector=query_vec,
            account_id=account_id,
            top_k=retrieval_pool_k,
            include_discontinued=False,
            include_superseded=False,
            doc_type=doc_type,
        )

        # 3. Cross-encoder re-ranking to isolate the most relevant context clauses
        candidates = reranker.rerank(
            query=rewritten_query,
            candidates=raw_candidates,
            top_n=safe_top_k,
        )

        top_score = candidates[0]["score"] if candidates else 0.0

        # 4. Confidence guardrail gate: prune low confidence or ungrounded queries
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

    # Alias for convenience and architecture consistency
    retrieve_and_guard = retrieve_and_evaluate

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
            "<untrusted_evidence>\n"
            f"{context}\n"
            "</untrusted_evidence>\n\n"
            "<untrusted_conversation_history>\n"
            f"{history_str}\n"
            "</untrusted_conversation_history>\n\n"
            "<untrusted_user_query>\n"
            f"{query}\n"
            f"(Internal Search Intent: {rewritten_query})\n"
            "</untrusted_user_query>\n\n"
            "GROUNDED ADVISORY RESPONSE:"
        )

        return self.system_prompt_template, user_prompt

    def semantic_search(
        self,
        query: str,
        account_id: str,
        top_k: int = 5,
        include_discontinued: bool = False,
        min_score: Optional[float] = None,
        doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Direct semantic search helper through RAG pipeline."""
        return vector_store.semantic_search(
            query_text=query,
            account_id=account_id,
            top_k=max(1, int(top_k)) if top_k else 5,
            include_discontinued=include_discontinued,
            min_score=min_score,
            doc_type=doc_type,
        )


rag_pipeline = RAGPipeline()

