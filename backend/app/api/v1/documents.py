from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, Document
from app.api.deps import get_current_user, require_role
from app.schemas.document import DocumentUploadResponse, DocumentItemResponse, DocumentListResponse
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
):
    """
    Uploads and indexes an investment policy PDF, tax circular, or product brochure.
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

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        result = ingestion_pipeline.process_and_index_document(
            db=db,
            account_id=current_user.account_id,
            user_id=current_user.id,
            filename=file.filename or "uploaded_document.pdf",
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

@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    current_admin: User = Depends(require_role(["ComplianceAdmin"])),
    db: Session = Depends(get_db),
):
    """
    Deletes a document and its indexed vector chunks.
    Restricted to users with 'ComplianceAdmin' role.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.account_id == current_admin.account_id,
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or does not belong to your tenant account.",
        )

    # Delete chunks from ChromaDB
    deleted_chunks = vector_store.delete_document_chunks(
        account_id=current_admin.account_id,
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
