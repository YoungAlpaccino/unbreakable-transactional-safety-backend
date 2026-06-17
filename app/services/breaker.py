"""
Tiny in-process circuit breaker (sketch).

Tracks the most recent failure rate; once the threshold is crossed it
opens for a cooldown window. The submit endpoint refuses traffic while
the breaker is open so we shed load instead of piling on.
"""
import time
from app.config import settings


class Breaker:
    def __init__(self, *, threshold: int, cooldown: float):
        self._threshold = threshold
        self._cooldown  = cooldown
        self._failures  = 0
        self._opened_at = 0.0

    def is_open(self) -> bool:
        if self._opened_at == 0.0:
            return False
        if time.monotonic() - self._opened_at < self._cooldown:
            return True
        # half-open: let the next attempt through
        self._opened_at = 0.0
        self._failures  = 0
        return False

    def record_success(self):
        self._failures  = 0
        self._opened_at = 0.0

    def record_failure(self):
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = time.monotonic()


downstream_breaker = Breaker(
    threshold=settings.breaker_failure_threshold,
    cooldown=settings.breaker_cooldown_seconds,
)
