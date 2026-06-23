"""Rate limiting for API routes."""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

__all__ = ["RateLimitExceeded", "_rate_limit_exceeded_handler", "limiter"]

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
