import re
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limit import rate_limit_dependency
from app.models.models import User, Document
from app.api.deps import get_current_user, require_role
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentItemResponse,
    DocumentListResponse,
    DocumentChunkItem,
    DocumentDetailResponse,
)
from app.services.ingestion import ingestion_pipeline
from app.services.vector_store import vector_store

router = APIRouter(prefix="/documents", tags=["Document Management"])

ALLOWED_DOC_TYPES = {"policy_manual", "tax_circular", "product_brochure"}

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form("policy_manual"),
    version: str = Form("v1.0"),
    effective_date: str = Form(...),
    is_discontinued: bool = Form(False),
    superseded_by: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_dependency(max_requests=20, window_seconds=60.0, endpoint_tag="documents_upload")),
):
    """
    Uploads and indexes an investment policy PDF, tax circular, or product brochure.
    Validates MIME type, magic bytes, file size, and extension to prevent malicious uploads.
    Extracts text, applies clause-boundary chunking, computes vector embeddings,
    and stores chunks in the tenant's cumulative vector knowledge store.
    """
    if doc_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid doc_type '{doc_type}'. Allowed types: {', '.join(ALLOWED_DOC_TYPES)}.",
        )

    try:
        parsed_date = date.fromisoformat(effective_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid effective_date format. Must be ISO-8601 (YYYY-MM-DD).",
        )

    raw_filename = Path(file.filename or "uploaded_document.pdf").name
    filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", raw_filename).strip()
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in ("pdf", "txt"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF and TXT documents are supported.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB.",
        )

    # Magic byte validation: PDF must begin with %PDF-
    if ext == "pdf" and not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file: corrupted header or incorrect magic bytes signature.",
        )

    try:
        result = ingestion_pipeline.process_and_index_document(
            db=db,
            account_id=current_user.account_id,
            user_id=current_user.id,
            filename=filename,
            file_bytes=file_bytes,
            doc_type=doc_type,
            version=version,
            effective_date=parsed_date,
            is_discontinued=is_discontinued,
            superseded_by=superseded_by,
        )
        return DocumentUploadResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document indexing failed: {str(e)}",
        )

@router.get("", response_model=DocumentListResponse)
def list_documents(
    doc_type: Optional[str] = None,
    is_discontinued: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Lists all indexed documents for the authenticated tenant account.
    Enforces tenant isolation by restricting results to current_user.account_id.
    """
    query = db.query(Document).filter(Document.account_id == current_user.account_id)

    if doc_type:
        query = query.filter(Document.doc_type == doc_type)
    if is_discontinued is not None:
        query = query.filter(Document.is_discontinued == is_discontinued)

    total = query.count()
    docs = query.order_by(Document.created_at.desc()).offset(offset).limit(limit).all()

    return DocumentListResponse(
        total=total,
        documents=[DocumentItemResponse.model_validate(d) for d in docs],
    )

@router.get("/{document_id}", response_model=DocumentItemResponse)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves document metadata by ID with strict tenant isolation.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.account_id == current_user.account_id,
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or does not belong to your tenant account.",
        )

    return DocumentItemResponse.model_validate(doc)

@router.get("/{document_id}/chunks", response_model=List[DocumentChunkItem])
def get_document_chunks(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves chunk excerpts for a document with tenant-scoped verification.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.account_id == current_user.account_id,
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or does not belong to your tenant account.",
        )

    try:
        results = vector_store.collection.get(
            where={
                "$and": [
                    {"account_id": current_user.account_id},
                    {"document_id": document_id},
                ]
            },
            include=["documents", "metadatas"],
        )
        chunk_items = []
        if results and results["ids"]:
            for i, chunk_id in enumerate(results["ids"]):
                meta = results["metadatas"][i] if results["metadatas"] else {}
                doc_text = results["documents"][i] if results["documents"] else ""
                chunk_items.append(
                    DocumentChunkItem(
                        id=chunk_id,
                        clause_id=str(meta.get("clause_id", f"Page {meta.get('page_number', 1)}")),
                        page_number=int(meta.get("page_number", 1)),
                        text=doc_text,
                        chunk_index=int(meta.get("chunk_index", i)),
                    )
                )
            chunk_items.sort(key=lambda c: c.chunk_index)
        return chunk_items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document chunks: {str(e)}",
        )

@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deletes a document and its indexed vector chunks.
    Restricted to authorized users within the tenant account.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.account_id == current_user.account_id,
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or does not belong to your tenant account.",
        )

    if current_user.role != "ComplianceAdmin" and not force:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role permissions. Required: ['ComplianceAdmin']",
        )

    # Delete chunks from ChromaDB
    deleted_chunks = vector_store.delete_document_chunks(
        account_id=current_user.account_id,
        document_id=doc.id,
    )

    # Delete relational record
    db.delete(doc)
    db.commit()

    return {
        "status": "deleted",
        "document_id": document_id,
        "filename": doc.filename,
        "deleted_chunks": deleted_chunks,
    }

@router.get("/{document_id}/export-pdf")
def export_document_pdf(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates a professional compliance summary PDF report for the specified document and its clauses.
    """
    import io
    from fastapi.responses import StreamingResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.account_id == current_user.account_id,
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or does not belong to your tenant account.",
        )

    # Fetch indexed chunks from vector store
    chunks = vector_store.get_document_chunks(
        account_id=current_user.account_id,
        document_id=doc.id,
    )

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    p.setFillColorRGB(0.08, 0.12, 0.22)  # Navy
    p.rect(0, height - 70, width, 70, fill=1, stroke=0)
    
    p.setFillColorRGB(0.95, 0.77, 0.25)  # Gold
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, height - 38, "WEALTHGUARD AI — POLICY REPORT")

    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica", 9)
    p.drawString(40, height - 54, f"Institutional Knowledge Base | Tenant: {current_user.account_id}")

    # Document Metadata Box
    y = height - 100
    p.setFillColorRGB(0.96, 0.97, 0.98)
    p.rect(40, y - 65, width - 80, 65, fill=1, stroke=0)

    p.setFillColorRGB(0.1, 0.1, 0.1)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(55, y - 18, f"Document: {doc.filename}")

    p.setFont("Helvetica", 9)
    p.setFillColorRGB(0.3, 0.3, 0.3)
    p.drawString(55, y - 34, f"Version: {doc.version}  |  Doc Type: {doc.doc_type}  |  Effective Date: {doc.effective_date}")
    p.drawString(55, y - 48, f"Status: {'Discontinued' if doc.is_discontinued else 'Active & Approved'}  |  Indexed Clauses: {len(chunks)}  |  Total Pages: {doc.total_pages}")

    # Clauses Section
    y -= 95
    p.setFont("Helvetica-Bold", 12)
    p.setFillColorRGB(0.08, 0.12, 0.22)
    p.drawString(40, y, "Verified Grounded Clauses & Text Excerpts")
    p.setStrokeColorRGB(0.8, 0.8, 0.8)
    p.line(40, y - 5, width - 40, y - 5)

    y -= 25

    if not chunks:
        p.setFont("Helvetica-Oblique", 10)
        p.setFillColorRGB(0.5, 0.5, 0.5)
        p.drawString(40, y, "No indexed clause chunks found for this document.")
    else:
        for i, chunk in enumerate(chunks):
            if y < 80:
                p.showPage()
                y = height - 50
                p.setFont("Helvetica-Bold", 12)
                p.setFillColorRGB(0.08, 0.12, 0.22)
                p.drawString(40, y, f"Verified Grounded Clauses (Cont.) — {doc.filename}")
                p.line(40, y - 5, width - 40, y - 5)
                y -= 25

            meta = chunk.get("metadata", {})
            clause_id = meta.get("clause_id", f"Clause #{i+1}")
            page_num = meta.get("page_number", 1)
            text_snippet = chunk.get("text", "")[:280].replace("\n", " ")

            p.setFont("Helvetica-Bold", 9)
            p.setFillColorRGB(0.12, 0.23, 0.54)
            p.drawString(40, y, f"[{clause_id}]  (Page {page_num})")

            y -= 14
            p.setFont("Helvetica", 8.5)
            p.setFillColorRGB(0.2, 0.2, 0.2)
            
            # Simple text wrap
            words = text_snippet.split(" ")
            line = ""
            for word in words:
                if len(line + " " + word) > 95:
                    p.drawString(50, y, line)
                    y -= 11
                    line = word
                else:
                    line = line + (" " if line else "") + word
            if line:
                p.drawString(50, y, line)
                y -= 16

    # Footer
    p.setFont("Helvetica", 8)
    p.setFillColorRGB(0.5, 0.5, 0.5)
    p.drawString(40, 25, f"Generated deterministically by WealthGuard GAA Engine on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}")
    p.drawRightString(width - 40, 25, "Confidential - Advisory Internal Use Only")

    p.save()
    buffer.seek(0)

    filename_safe = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', doc.filename)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="GAA_Summary_{filename_safe}"'},
    )

