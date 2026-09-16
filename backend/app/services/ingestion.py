
import io
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import date
from sqlalchemy.orm import Session
from pypdf import PdfReader

from app.models.models import Document
from app.services.chunking import chunk_document_pages, clean_text
from app.services.embedding import embedding_service
from app.services.vector_store import vector_store


# Document ingestion pipeline:
#
# Uploaded file
#     ↓
# File persistence
#     ↓
# Database document record
#     ↓
# Text extraction
#     ↓
# Clause-aware chunking
#     ↓
# Embedding generation
#     ↓
# Vector store indexing
#     ↓
# Document status update
#
# The pipeline keeps document processing separate from API routing so
# ingestion can be reused independently of the upload endpoint.


def extract_pages_from_pdf_bytes(file_bytes: bytes) -> List[Dict[str, Any]]:
    """Extracts text per page from in-memory PDF bytes."""
    pages_data: List[Dict[str, Any]] = []
    stream = io.BytesIO(file_bytes)
    reader = PdfReader(stream)

    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        # Remove common running headers/footers (e.g., "Page X of Y", confidential stamps)
        cleaned = clean_text(text)
        if cleaned:
            pages_data.append({
                "page_number": idx + 1,
                "text": cleaned,
            })

    return pages_data

def extract_pages_from_text(raw_text: str) -> List[Dict[str, Any]]:
    """Fallback text extractor for plain text files."""
    cleaned = clean_text(raw_text)
    return [{"page_number": 1, "text": cleaned}] if cleaned else []

class IngestionPipeline:
    def __init__(self):
        self.upload_dir = Path("./data/uploads").resolve()
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def process_and_index_document(
        self,
        db: Session,
        account_id: str,
        user_id: str,
        filename: str,
        file_bytes: bytes,
        doc_type: str,
        version: str,
        effective_date: date,
        is_discontinued: bool = False,
        superseded_by: str = None,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end ingestion:
        1. Saves physical document file.
        2. Creates database record with status 'PROCESSING'.
        3. Extracts text per page.
        4. Applies clause-aware chunking.
        5. Computes vector embeddings.
        6. Persists chunks into ChromaDB (cumulative memory).
        7. Updates database record to 'INDEXED'.
        """
        # Save file to disk
        safe_filename = f"{account_id}_{version}_{filename}".replace(" ", "_")
        target_path = self.upload_dir / safe_filename
        with open(target_path, "wb") as f:
            f.write(file_bytes)

        # Create relational Document record
        doc_record = Document(
            account_id=account_id,
            uploaded_by=user_id,
            filename=filename,
            file_path=str(target_path),
            version=version,
            doc_type=doc_type,
            effective_date=effective_date,
            superseded_by=superseded_by,
            is_discontinued=is_discontinued,
            total_pages=0,
            total_chunks=0,
            status="PROCESSING",
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

        try:
            # 1. Text extraction
            if filename.lower().endswith(".pdf"):
                pages = extract_pages_from_pdf_bytes(file_bytes)
            else:
                text_content = file_bytes.decode("utf-8", errors="ignore")
                pages = extract_pages_from_text(text_content)

            total_pages = len(pages)
            if not pages:
                # Document has no readable text
                doc_record.status = "INDEXED"
                doc_record.total_pages = 0
                doc_record.total_chunks = 0
                db.commit()
                return {
                    "document_id": doc_record.id,
                    "filename": filename,
                    "status": "INDEXED",
                    "chunks_created": 0,
                    "total_pages": 0,
                    "account_id": account_id,
                }

            # 2. Clause-aware chunking
            chunks = chunk_document_pages(pages, max_tokens=500, overlap_tokens=50)
            chunk_texts = [c["text"] for c in chunks]

            # 3. Vector embedding generation
            embeddings = embedding_service.get_embeddings(chunk_texts)

            # 4. Upsert into ChromaDB
            vector_store.add_chunks(
                account_id=account_id,
                document_id=doc_record.id,
                document_name=filename,
                version=version,
                doc_type=doc_type,
                effective_date=str(effective_date),
                is_discontinued=is_discontinued,
                chunks=chunks,
                embeddings=embeddings,
            )

            # 5. Finalize DB record
            doc_record.total_pages = total_pages
            doc_record.total_chunks = len(chunks)
            doc_record.status = "INDEXED"
            db.commit()
            db.refresh(doc_record)

            return {
                "document_id": doc_record.id,
                "filename": filename,
                "status": "INDEXED",
                "chunks_created": len(chunks),
                "total_pages": total_pages,
                "account_id": account_id,
                "version": version,
                "doc_type": doc_type,
            }

        except Exception as e:
            db.rollback()
            doc_record.status = "FAILED"
            db.commit()
            raise RuntimeError(f"Failed to ingest document '{filename}': {str(e)}") from e

ingestion_pipeline = IngestionPipeline()
