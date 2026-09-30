from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime

class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    filename: str
    status: str
    chunks_created: int
    total_pages: int
    account_id: str
    version: str
    doc_type: str

class DocumentItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    uploaded_by: str
    filename: str
    version: str
    doc_type: str
    effective_date: date
    superseded_by: Optional[str] = None
    is_discontinued: bool
    total_pages: int
    total_chunks: int
    status: str
    created_at: datetime

class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentItemResponse]

class DocumentChunkItem(BaseModel):
    id: str
    clause_id: str
    page_number: int
    text: str
    chunk_index: int

class DocumentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document: DocumentItemResponse
    chunks: Optional[List[DocumentChunkItem]] = None

