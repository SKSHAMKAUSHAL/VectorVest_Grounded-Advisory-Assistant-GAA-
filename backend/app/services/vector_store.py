import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.config import settings

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
    ) -> List[Dict[str, Any]]:
        """
        Performs tenant-isolated vector retrieval.
        Hard filters ensure:
        1. Query chunks belong EXCLUSIVELY to `account_id`.
        2. Discontinued products are excluded unless explicitly requested.
        """
        if include_discontinued:
            where_filter = {"account_id": account_id}
        else:
            where_filter = {
                "$and": [
                    {"account_id": account_id},
                    {"is_discontinued": False},
                ]
            }

        count = self.collection.count()
        if count == 0:
            return []

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k, count),
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )

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

            candidates.append({
                "id": ids[i],
                "score": round(similarity, 4),
                "text": docs[i] if i < len(docs) else "",
                "metadata": metas[i] if i < len(metas) else {},
            })

        # Sort descending by similarity score
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates

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
