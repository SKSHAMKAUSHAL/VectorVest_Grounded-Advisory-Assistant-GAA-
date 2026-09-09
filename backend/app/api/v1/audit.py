from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User, ComplianceAuditLog
from app.api.deps import require_role
from app.schemas.chat import AuditLogListResponse, AuditLogItemResponse

router = APIRouter(prefix="/audit", tags=["Compliance Audit"])

@router.get("/logs", response_model=AuditLogListResponse)
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    is_refusal: Optional[bool] = None,
    current_admin: User = Depends(require_role(["ComplianceAdmin"])),
    db: Session = Depends(get_db),
):
    """
    Retrieves full compliance audit trail of RM queries, retrieved chunks,
    guardrail confidence scores, and model answers.
    Restricted to ComplianceAdmin role.
    """
    query = db.query(ComplianceAuditLog).filter(
        ComplianceAuditLog.account_id == current_admin.account_id
    )

    if is_refusal is not None:
        query = query.filter(ComplianceAuditLog.is_refusal == is_refusal)

    total = query.count()
    logs = (
        query.order_by(ComplianceAuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return AuditLogListResponse(
        total=total,
        logs=[AuditLogItemResponse.model_validate(l) for l in logs],
    )
