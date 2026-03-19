"""
API key authentication for /carbon/* routes.
If API_KEY env is set, requests must provide X-API-Key or Authorization: Bearer <key>.
"""
from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

from api_layer.config import get_api_key

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER = HTTPBearer(auto_error=False)


async def verify_api_key(
    x_api_key: str | None = Security(API_KEY_HEADER),
    credentials: HTTPAuthorizationCredentials | None = Security(BEARER),
) -> None:
    """Verify API key. If API_KEY is not configured, allow all (dev mode)."""
    configured_key = get_api_key()
    if not configured_key:
        return

    token = x_api_key or (credentials.credentials if credentials else None)
    if not token or token != configured_key:
        raise HTTPException(401, "Invalid or missing API key")
