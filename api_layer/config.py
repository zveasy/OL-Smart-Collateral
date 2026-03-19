"""
Application configuration and environment validation.
Validates required env vars at startup; raises clear errors if missing.
"""
from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv

load_dotenv()

# Required for Kaleido / blockchain
REQUIRED_ENV = [
    "KALEIDO_API_URL",
    "KALEIDO_API_KEY",
    "CARBON_CONTRACT_ADDRESS",
    "ADMIN_ADDRESS",
]


def validate_env() -> None:
    """Validate required environment variables. Raise ValueError with missing keys."""
    missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and set values."
        )


def get_cors_origins() -> List[str]:
    """CORS allowed origins. In production set CORS_ALLOW_ORIGINS to explicit origins."""
    raw = os.getenv("CORS_ALLOW_ORIGINS", "*").strip()
    return [o.strip() for o in raw.split(",") if o.strip()]


def get_api_key() -> str | None:
    """Optional API key for REST API. If set, all /carbon/* routes require X-API-Key or Bearer."""
    return os.getenv("API_KEY") or None


def get_log_level() -> str:
    return os.getenv("LOG_LEVEL", "INFO").upper()


def get_log_format() -> str:
    """'json' for structured JSON logs; anything else for human-readable."""
    return os.getenv("LOG_FORMAT", "").lower().strip()


def get_docs_enabled() -> bool:
    """If False, disable /docs and /redoc (e.g. when ENVIRONMENT=production)."""
    if os.getenv("DOCS_ENABLED", "").lower() in ("0", "false", "no"):
        return False
    if os.getenv("ENVIRONMENT", "").lower() == "production":
        return False
    return True
