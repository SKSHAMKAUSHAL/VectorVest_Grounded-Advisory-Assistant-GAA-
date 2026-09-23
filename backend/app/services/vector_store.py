import math
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from app.services.embedding import embedding_service


class VectorStore:
    def __init__(self, persist_dir: Optional[str] = None):
        target_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        db_path = Path(target_dir).resolve()
        db_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(db_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name = "wealthguard_chunks"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(
        self,
        account_id: str,
        document_id: str,
        document_name: str,
        version: str,
        doc_type: str,
        effective_date: str,
        is_discontinued: bool,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        is_superseded: bool = False,
    ) -> int:
        """
        Ingests and persists clause chunks into ChromaDB under the account's partition.
        Operates cumulatively: chunks from different documents are added alongside existing chunks.
        """
        if not chunks or not embeddings:
            return 0

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"chunk_{document_id}_{chunk.get('chunk_index', i)}"
            ids.append(chunk_id)
            documents.append(chunk.get("text", ""))

            metadatas.append({
                "account_id": str(account_id),
                "document_id": str(document_id),
                "document_name": str(document_name),
                "document_version": str(version),
                "doc_type": str(doc_type),
                "clause_id": str(chunk.get("clause_id", f"Page {chunk.get('page_number', 1)}")),
                "page_number": int(chunk.get("page_number", 1)),
                "chunk_index": int(chunk.get("chunk_index", i)),
                "is_discontinued": bool(is_discontinued),
                "is_superseded": bool(is_superseded),
                "effective_date": str(effective_date),
            })

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    def search(
        self,
        query_vector: List[float],
        account_id: str,
        top_k: int = 10,
        include_discontinued: bool = False,
        min_score: Optional[float] = None,
        doc_type: Optional[str] = None,
        document_id: Optional[str] = None,
        include_superseded: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Performs tenant-isolated vector retrieval with configurable top-k limit.

        Hard filters ensure:
        1. Query chunks belong EXCLUSIVELY to `account_id`.
        2. Discontinued products are excluded unless explicitly requested.
        3. Superseded circulars/policies are excluded unless explicitly requested.
        4. Optional metadata filters (doc_type, document_id) are strictly respected.
        5. Optional similarity threshold (min_score) prunes low-confidence candidates.

        Returns candidate list sorted descending by similarity score, capped at top_k.
        """
        # Input validation & edge cases
        if not account_id or top_k <= 0 or not query_vector:
            return []

        # Validate vector contents
        if not isinstance(query_vector, (list, tuple)):
            return []
        for val in query_vector:
            if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
                return []

        # Build dynamic where filter
        conditions: List[Dict[str, Any]] = [{"account_id": str(account_id)}]
        if not include_discontinued:
            conditions.append({"is_discontinued": False})
        if not include_superseded:
            conditions.append({"is_superseded": False})
        if doc_type:
            conditions.append({"doc_type": str(doc_type)})
        if document_id:
            conditions.append({"document_id": str(document_id)})

        where_filter = conditions[0] if len(conditions) == 1 else {"$and": conditions}

        count = self.collection.count()
        if count == 0:
            return []

        n_results = min(top_k, count)
        try:
            results = self.collection.query(
                query_embeddings=[list(query_vector)],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
        except Exception:
            return []

        candidates: List[Dict[str, Any]] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        for i in range(len(ids)):
            # In cosine space, similarity = 1.0 - distance
            dist = distances[i] if i < len(distances) else 1.0
            similarity = max(0.0, min(1.0, 1.0 - dist))
            score = round(similarity, 4)

            # Apply min_score threshold if specified
            if min_score is not None and score < min_score:
                continue

            meta = metas[i] if i < len(metas) else {}
            doc_text = docs[i] if i < len(docs) else ""

            candidates.append({
                "id": ids[i],
                "score": score,
                "text": doc_text,
                "metadata": meta,
                "document_name": meta.get("document_name", "Unknown"),
                "version": meta.get("document_version", "v1.0"),
                "clause_id": meta.get("clause_id", f"Page {meta.get('page_number', 1)}"),
                "page_number": int(meta.get("page_number", 1)),
                "doc_type": meta.get("doc_type", ""),
                "effective_date": meta.get("effective_date", ""),
                "is_superseded": bool(meta.get("is_superseded", False)),
            })

        # Sort descending by similarity score and truncate to top_k
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

    def mark_document_as_superseded(self, document_id: str) -> int:
        """
        Marks all chunks belonging to document_id as superseded in ChromaDB.
        Excludes these chunks from subsequent runtime advisory retrieval.
        """
        try:
            results = self.collection.get(
                where={"document_id": str(document_id)},
                include=["metadatas"]
            )
            if not results or not results["ids"]:
                return 0

            ids = results["ids"]
            metas = results["metadatas"]
            updated_metas = []
            for m in metas:
                m_copy = dict(m)
                m_copy["is_superseded"] = True
                updated_metas.append(m_copy)

            self.collection.update(
                ids=ids,
                metadatas=updated_metas,
            )
            return len(ids)
        except Exception:
            return 0

    def semantic_search(
        self,
        query_text: str,
        account_id: str,
        top_k: int = 5,
        include_discontinued: bool = False,
        min_score: Optional[float] = None,
        doc_type: Optional[str] = None,
        document_id: Optional[str] = None,
        include_superseded: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        High-level natural language semantic search.
        Embeds the query text and executes tenant-isolated top-k retrieval.
        """
        if not query_text or not isinstance(query_text, str) or not query_text.strip():
            return []

        query_vec = embedding_service.get_embedding(query_text.strip())
        return self.search(
            query_vector=query_vec,
            account_id=account_id,
            top_k=top_k,
            include_discontinued=include_discontinued,
            min_score=min_score,
            doc_type=doc_type,
            document_id=document_id,
            include_superseded=include_superseded,
        )

    def batch_semantic_search(
        self,
        queries: List[str],
        account_id: str,
        top_k: int = 5,
        include_discontinued: bool = False,
        min_score: Optional[float] = None,
        doc_type: Optional[str] = None,
        include_superseded: bool = False,
    ) -> List[List[Dict[str, Any]]]:
        """
        Executes batch semantic search for a collection of queries.
        Generates vector embeddings in batch for optimal throughput.
        """
        if not queries:
            return []

        cleaned_queries = [q.strip() if isinstance(q, str) else "" for q in queries]
        valid_queries = [q for q in cleaned_queries if q]
        if not valid_queries:
            return [[] for _ in queries]

        embeddings = embedding_service.get_embeddings(cleaned_queries)

        results: List[List[Dict[str, Any]]] = []
        for i, query_str in enumerate(cleaned_queries):
            if not query_str:
                results.append([])
            else:
                results.append(
                    self.search(
                        query_vector=embeddings[i],
                        account_id=account_id,
                        top_k=top_k,
                        include_discontinued=include_discontinued,
                        min_score=min_score,
                        doc_type=doc_type,
                        include_superseded=include_superseded,
                    )
                )
        return results

    def delete_document_chunks(self, account_id: str, document_id: str) -> int:
        """Removes all vector chunks belonging to a document under the specified tenant account."""
        where_filter = {
            "$and": [
                {"account_id": account_id},
                {"document_id": document_id},
            ]
        }
        # Retrieve IDs to delete
        existing = self.collection.get(where=where_filter)
        if existing and existing["ids"]:
            self.collection.delete(ids=existing["ids"])
            return len(existing["ids"])
        return 0

    def count_chunks_for_account(self, account_id: str) -> int:
        """Returns total active indexed chunks for a tenant account."""
        res = self.collection.get(where={"account_id": account_id})
        return len(res["ids"]) if res and res["ids"] else 0

vector_store = VectorStore()
