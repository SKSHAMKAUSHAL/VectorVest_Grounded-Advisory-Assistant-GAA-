import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, Integer, Float, DateTime, Date,
    ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid(prefix: str = "") -> str:
    uid = str(uuid.uuid4())
    return f"{prefix}{uid}" if prefix else uid

class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("acc_"))
    branch_name = Column(String(128), nullable=False)
    branch_code = Column(String(32), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    users = relationship("User", back_populates="account", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="account", cascade="all, delete-orphan", foreign_keys="Document.account_id")
    audit_logs = relationship("ComplianceAuditLog", back_populates="account", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("usr_"))
    account_id = Column(String(64), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False) # 'RM' or 'ComplianceAdmin'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    account = relationship("Account", back_populates="users")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    uploaded_documents = relationship("Document", back_populates="uploader", foreign_keys="Document.uploaded_by")
    audit_logs = relationship("ComplianceAuditLog", back_populates="user")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("tok_"))
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="password_reset_tokens")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("doc_"))
    account_id = Column(String(64), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by = Column(String(64), ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    version = Column(String(32), default="v1.0", nullable=False)
    doc_type = Column(String(64), nullable=False) # 'policy_manual', 'tax_circular', 'product_brochure'
    effective_date = Column(Date, nullable=False)
    superseded_by = Column(String(64), ForeignKey("documents.id"), nullable=True)
    is_discontinued = Column(Boolean, default=False, nullable=False, index=True)
    total_pages = Column(Integer, default=0, nullable=False)
    total_chunks = Column(Integer, default=0, nullable=False)
    status = Column(String(32), default="INDEXED", nullable=False) # 'PENDING', 'PROCESSING', 'INDEXED', 'FAILED'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    account = relationship("Account", back_populates="documents", foreign_keys=[account_id])
    uploader = relationship("User", back_populates="uploaded_documents", foreign_keys=[uploaded_by])
    superseding_doc = relationship("Document", remote_side=[id], foreign_keys=[superseded_by])

class ComplianceAuditLog(Base):
    __tablename__ = "compliance_audit_logs"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("aud_"))
    account_id = Column(String(64), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    rewritten_query = Column(Text, nullable=True)
    retrieved_chunk_ids = Column(JSON, nullable=False)
    similarity_score = Column(Float, nullable=False)
    response = Column(Text, nullable=False)
    is_refusal = Column(Boolean, default=False, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    account = relationship("Account", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
