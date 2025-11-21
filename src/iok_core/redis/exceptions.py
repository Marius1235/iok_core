from __future__ import annotations

from typing import Optional


class RedisError(Exception):
    """Base exception for all iok_core Redis errors"""


class RedisDisabledError(RedisError):
    """Raised when Redis is explicitly disabled via config"""

    def __init__(self, message: str = "Redis is disabled via IOK_REDIS_DISABLED or global config"):
        super().__init__(message)


class RedisConnectionError(RedisError):
    """Raised when we cannot connect or communicate with Redis"""

    def __init__(
        self,
        message: str = "Failed to connect or communicate with Redis",
        original_exc: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.original_exc = original_exc

    def __str__(self) -> str:
        if self.original_exc:
            return f"{self.args[0]}: {self.original_exc}"
        return super().__str__()


class RedisCircuitBreakerOpen(RedisError):
    """Raised when circuit breaker is open (temporary Redis outage)"""

    def __init__(self, retry_after_seconds: int = 30):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Redis circuit breaker open — retry after {retry_after_seconds}s")


class RedisKeyError(RedisError, KeyError):
    """Raised when a Redis key operation fails (e.g. key not found with GET)"""
    pass


class RedisSerializationError(RedisError, ValueError):
    """Raised when serialization/deserialization fails (e.g. orjson error)"""
    pass