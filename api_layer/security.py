from __future__ import annotations

import hmac
import os
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_ROLE_ORDER = {
    "reader": 10,
    "admin": 20,
}

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    role: str
    token_fingerprint: str


def _parse_api_tokens(raw: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        if ":" not in item:
            continue
        role, token = item.split(":", 1)
        role = role.strip().lower()
        token = token.strip()
        if role in _ROLE_ORDER and token:
            tokens.append((role, token))
    return tokens


def _match_role_for_token(token: str) -> str | None:
    raw = os.getenv("API_TOKENS", "")
    configured = _parse_api_tokens(raw)
    for role, configured_token in configured:
        if hmac.compare_digest(token, configured_token):
            return role
    return None


def require_role(required_role: str) -> Callable[[HTTPAuthorizationCredentials | None], AuthContext]:
    required_role = required_role.lower()
    if required_role not in _ROLE_ORDER:
        raise ValueError(f"unknown role: {required_role}")

    def _dependency(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    ) -> AuthContext:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Missing bearer token")

        token = credentials.credentials
        matched_role = _match_role_for_token(token)
        if matched_role is None:
            raise HTTPException(status_code=401, detail="Invalid bearer token")

        if _ROLE_ORDER[matched_role] < _ROLE_ORDER[required_role]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return AuthContext(role=matched_role, token_fingerprint=token[:6] + "...")

    return _dependency
