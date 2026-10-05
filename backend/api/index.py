import os
import sys
from pathlib import Path

# Ensure backend root is in sys.path so 'app.*' imports resolve cleanly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Configure serverless ephemeral storage for ChromaDB
if os.environ.get("VERCEL"):
    os.environ.setdefault("CHROMA_PERSIST_DIR", "/tmp/chromadb")
    os.environ.setdefault("VECTOR_DB_PATH", "/tmp/chromadb")

from app.main import app

# Export for ASGI serverless runners
__all__ = ["app"]
