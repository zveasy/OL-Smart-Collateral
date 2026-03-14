import os
import types
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure runtime/env configuration is present before app import.
os.environ.setdefault("KALEIDO_API_URL", "https://example.invalid/gateway")
os.environ.setdefault("KALEIDO_API_KEY", "test-kaleido-key")
os.environ.setdefault("CARBON_CONTRACT_ADDRESS", "0x2810f346088b6f9638a39b869a929e6eafb73398")
os.environ.setdefault("ADMIN_ADDRESS", "0x2810f346088b6f9638a39b869a929e6eafb73398")
os.environ.setdefault("API_TOKENS", "admin:test-admin-token,reader:test-reader-token")

from api_layer.rest_api.server import app
from api_layer.rest_api import carbon_routes

client = TestClient(app)

kaleido_stub = types.SimpleNamespace(
    mint_nft=lambda *a, **k: None,
    owner_of=lambda *a, **k: None,
    token_uri=lambda *a, **k: None,
    tokens_by_owner=lambda *a, **k: None,
)
sys.modules["api_layer.rest_api.kaleido_client"] = kaleido_stub

READER_HEADERS = {"Authorization": "Bearer test-reader-token"}


def _admin_headers(key: str) -> dict[str, str]:
    return {
        "Authorization": "Bearer test-admin-token",
        "Idempotency-Key": key,
    }


def _mint_payload():
    return {
        "to_address": "0x1234567890abcdef1234567890abcdef12345678",
        "token_id": 1,
        "amount": 1,
        "token_uri": "https://test.com/1.json",
    }


def test_mint_success(monkeypatch):
    def mock_mint(to_address, token_id, amount, token_uri):
        return {"status": "success", "tokenId": token_id}

    monkeypatch.setattr(carbon_routes, "mint_nft", mock_mint)
    resp = client.post("/carbon/mint", json=_mint_payload(), headers=_admin_headers("mint-success"))
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


def test_mint_invalid_address(monkeypatch):
    monkeypatch.setattr(carbon_routes, "mint_nft", lambda *a, **k: {"status": "success"})
    payload = _mint_payload()
    payload["to_address"] = "bad"
    resp = client.post("/carbon/mint", json=payload, headers=_admin_headers("mint-invalid-address"))
    assert resp.status_code == 422


def test_owner_of_success(monkeypatch):
    monkeypatch.setattr(
        carbon_routes,
        "owner_of",
        lambda token_id: {"owner": "0x1234567890abcdef1234567890abcdef12345678"},
    )
    resp = client.get("/carbon/owner/1", headers=READER_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["owner"].lower() == "0x1234567890abcdef1234567890abcdef12345678"


def test_owner_of_not_found_is_sanitized(monkeypatch):
    def mock_owner(token_id):
        import requests

        response = requests.Response()
        response.status_code = 404
        response._content = b"Token not found"
        raise requests.HTTPError(response=response)

    monkeypatch.setattr(carbon_routes, "owner_of", mock_owner)
    resp = client.get("/carbon/owner/999", headers=READER_HEADERS)
    assert resp.status_code == 502
    assert resp.json()["detail"] == "Upstream service error"


def test_carbon_mint_invalid_token_id(monkeypatch):
    monkeypatch.setattr(carbon_routes, "mint_nft", lambda *a, **k: {"status": "success"})
    payload = _mint_payload()
    payload["token_id"] = -1
    resp = client.post("/carbon/mint", json=payload, headers=_admin_headers("mint-invalid-token-id"))
    assert resp.status_code == 422


def test_missing_bearer_token_rejected():
    resp = client.get("/carbon/owner/1")
    assert resp.status_code == 401


def test_insufficient_role_rejected():
    resp = client.post("/carbon/mint", json=_mint_payload(), headers={"Authorization": "Bearer test-reader-token", "Idempotency-Key": "idempotent-key-2"})
    assert resp.status_code == 403


def test_missing_idempotency_key_rejected_for_writes():
    resp = client.post(
        "/carbon/mint",
        json=_mint_payload(),
        headers={"Authorization": "Bearer test-admin-token"},
    )
    assert resp.status_code == 400


def test_idempotent_replay(monkeypatch):
    calls = {"n": 0}

    def mock_mint(*args, **kwargs):
        calls["n"] += 1
        return {"status": "success", "tokenId": 1}

    monkeypatch.setattr(carbon_routes, "mint_nft", mock_mint)

    headers = {
        "Authorization": "Bearer test-admin-token",
        "Idempotency-Key": "same-key",
    }
    first = client.post("/carbon/mint", json=_mint_payload(), headers=headers)
    second = client.post("/carbon/mint", json=_mint_payload(), headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.headers.get("X-Idempotent-Replay") == "true"
    assert calls["n"] == 1
