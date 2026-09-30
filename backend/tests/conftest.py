import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
settings.ENVIRONMENT = "test"
settings.DISABLE_RATE_LIMITS = True

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.models import Account, User, PasswordResetToken, Document, ComplianceAuditLog
from app.services.vector_store import vector_store
from app.main import app

import threading
from sqlalchemy import event

# Shared in-memory SQLite engine with thread-safe execution lock
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

_sqlite_cursor_lock = threading.RLock()

@event.listens_for(test_engine, "before_cursor_execute")
def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    _sqlite_cursor_lock.acquire()

@event.listens_for(test_engine, "after_cursor_execute")
def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    try:
        _sqlite_cursor_lock.release()
    except RuntimeError:
        pass

@event.listens_for(test_engine, "handle_error")
def _handle_error(exception_context):
    try:
        _sqlite_cursor_lock.release()
    except RuntimeError:
        pass

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply dependency override once for the test session
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_test_db():
    """Initializes tables and seeds baseline fixtures for every test."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()

    # Seed Accounts
    acc_central = Account(id="branch_12_central", branch_name="Central Branch #12", branch_code="BR-12")
    acc_north = Account(id="branch_01_north", branch_name="North Branch #01", branch_code="BR-01")
    db.add_all([acc_central, acc_north])
    db.commit()

    # Seed Users
    rm_user = User(
        id="usr_rm_test",
        account_id="branch_12_central",
        email="rm_test@wealth.bank.com",
        password_hash=get_password_hash("TestPassword123!"),
        full_name="Test RM",
        role="RM",
        is_active=True,
    )
    compliance_user = User(
        id="usr_comp_test",
        account_id="branch_12_central",
        email="comp_test@wealth.bank.com",
        password_hash=get_password_hash("AdminPassword123!"),
        full_name="Test Compliance Officer",
        role="ComplianceAdmin",
        is_active=True,
    )
    north_rm_user = User(
        id="usr_north_rm_test",
        account_id="branch_01_north",
        email="north_rm@wealth.bank.com",
        password_hash=get_password_hash("NorthPassword123!"),
        full_name="North RM",
        role="RM",
        is_active=True,
    )
    db.add_all([rm_user, compliance_user, north_rm_user])
    db.commit()
    db.close()

    # Reset ChromaDB collection items
    try:
        res = vector_store.collection.get()
        if res and res["ids"]:
            vector_store.collection.delete(ids=res["ids"])
    except Exception:
        pass

    yield

    # Clean all tables in reverse dependency order
    cleanup_db = TestingSessionLocal()
    cleanup_db.query(ComplianceAuditLog).delete()
    cleanup_db.query(PasswordResetToken).delete()
    cleanup_db.query(Document).delete()
    cleanup_db.query(User).delete()
    cleanup_db.query(Account).delete()
    cleanup_db.commit()
    cleanup_db.close()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client():
    """Provides FastAPI TestClient."""
    return TestClient(app)
