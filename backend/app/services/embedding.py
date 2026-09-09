import hashlib
import math
from typing import List
from app.core.config import settings

def _deterministic_mock_embedding(text: str, dim: int = 1536) -> List[float]:
    """
    Generates a deterministic, normalized 1536-dimensional vector for a text string.
    Ensures tests and offline dev work without needing an external OpenAI API call.
    """
    words = text.lower().split()
    vector = [0.0] * dim
    
    # Generate repeatable pseudo-random components based on text tokens
    for i, word in enumerate(words):
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        pos = (h + i) % dim
        val = ((h % 1000) / 500.0) - 1.0 # Float between -1.0 and 1.0
        vector[pos] += val

    # Add a base hash component so even identical words in different orders differ
    full_h = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    for j in range(min(dim, 32)):
        vector[j] += ((full_h >> (j * 8)) & 0xFF) / 255.0

    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    else:
        vector[0] = 1.0
        
    return vector

class EmbeddingService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_EMBEDDING_MODEL
        self._openai_client = None

        if self.api_key and not self.api_key.startswith("sk-mock") and not self.api_key.startswith("sk-your"):
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=self.api_key)
            except Exception:
                self._openai_client = None

    def get_embedding(self, text: str) -> List[float]:
        """Returns 1536-dimensional embedding for a single text string."""
        if self._openai_client:
            try:
                response = self._openai_client.embeddings.create(
                    input=text,
                    model=self.model,
                )
                return response.data[0].embedding
            except Exception as e:
                # Fallback to deterministic embedding on error / network timeout
                return _deterministic_mock_embedding(text)
        return _deterministic_mock_embedding(text)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Returns embeddings for a batch of text strings."""
        if not texts:
            return []
            
        if self._openai_client:
            try:
                response = self._openai_client.embeddings.create(
                    input=texts,
                    model=self.model,
                )
                return [d.embedding for d in response.data]
            except Exception as e:
                return [_deterministic_mock_embedding(t) for t in texts]
                
        return [_deterministic_mock_embedding(t) for t in texts]

embedding_service = EmbeddingService()
