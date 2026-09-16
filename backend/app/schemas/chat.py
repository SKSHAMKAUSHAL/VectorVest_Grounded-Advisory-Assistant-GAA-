from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str

class ChatQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, description="The RM's natural language policy or tax question.")
    chat_history: Optional[List[ChatMessage]] = Field(default_factory=list, description="Prior conversational context.")

class CitationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_name: str
    version: str
    clause_id: str
    page_number: int
    excerpt: str
    score: Optional[float] = 0.0

class ChatQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    answer: str
    citations: List[CitationItem]
    is_refusal: bool
    similarity_score: float
    rewritten_query: str
    latency_ms: int

class AuditLogItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    user_id: str
    query: str
    rewritten_query: Optional[str] = None
    similarity_score: float
    response: str
    is_refusal: bool
    latency_ms: int
    created_at: datetime

class AuditLogListResponse(BaseModel):
    total: int
    logs: List[AuditLogItemResponse]

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The natural language query to search for.")
    top_k: int = Field(default=5, ge=1, le=50, description="Maximum number of top results to retrieve.")
    include_discontinued: bool = Field(default=False, description="Whether to include discontinued products.")
    doc_type: Optional[str] = Field(default=None, description="Optional document type filter.")
    min_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Minimum cosine similarity score threshold.")

class SemanticSearchResultItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    score: float
    text: str
    metadata: Dict[str, Any]
    document_name: str
    version: str
    clause_id: str
    page_number: int
    doc_type: str
    effective_date: str

class SemanticSearchResponse(BaseModel):
    query: str
    account_id: str
    total_results: int
    results: List[SemanticSearchResultItem]

