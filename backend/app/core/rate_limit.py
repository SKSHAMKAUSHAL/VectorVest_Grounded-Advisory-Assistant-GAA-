import time
import threading
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status
from app.core.config import settings


class InMemoryRateLimiter:
    """
    Thread-safe in-memory sliding-window rate limiter.
    Limits requests per client IP within a sliding time window.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._records: Dict[str, List[float]] = {}
        self._last_cleanup = time.time()

    def _cleanup_old_records(self, max_age: float = 3600.0):
        """Purges old expired entries to prevent memory growth."""
        now = time.time()
        if now - self._last_cleanup < 300.0:
            return

        with self._lock:
            cutoff = now - max_age
            keys_to_remove = []
            for key, timestamps in self._records.items():
                active = [t for t in timestamps if t > cutoff]
                if active:
                    self._records[key] = active
                else:
                    keys_to_remove.append(key)
            for k in keys_to_remove:
                del self._records[k]
            self._last_cleanup = now

    def is_allowed(self, key: str, max_requests: int, window_seconds: float) -> bool:
        """Checks if a request from 'key' is permitted under the rate limit."""
        # Allow disabling rate limiter in development/test if specified
        if getattr(settings, "DISABLE_RATE_LIMITS", False) or settings.ENVIRONMENT == "test":
            return True

        now = time.time()
        self._cleanup_old_records(window_seconds * 2)

        with self._lock:
            timestamps = self._records.setdefault(key, [])
            # Prune timestamps outside current window
            window_start = now - window_seconds
            valid_timestamps = [t for t in timestamps if t > window_start]
            self._records[key] = valid_timestamps

            if len(valid_timestamps) >= max_requests:
                return False

            self._records[key].append(now)
            return True


limiter = InMemoryRateLimiter()


def rate_limit_dependency(max_requests: int, window_seconds: float, endpoint_tag: str):
    """
    FastAPI dependency factory enforcing rate limits on endpoints.
    Identifies client by Forwarded/X-Real-IP/client.host + endpoint_tag.
    """
    def check_rate_limit(request: Request):
        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or request.headers.get("x-real-ip", "").strip()
            or (request.client.host if request.client else "127.0.0.1")
        )
        rate_key = f"{endpoint_tag}:{client_ip}"

        if not limiter.is_allowed(rate_key, max_requests=max_requests, window_seconds=window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {endpoint_tag}. Please try again later.",
                headers={"Retry-After": str(int(window_seconds))},
            )
        return True

    return check_rate_limit
