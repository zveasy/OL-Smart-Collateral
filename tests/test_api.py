import pytest
import sys
import types

kaleido_stub = types.SimpleNamespace(
    mint_nft=lambda *a, **k: None,
    owner_of=lambda *a, **k: None,
    token_uri=lambda *a, **k: None,
    tokens_by_owner=lambda *a, **k: None,
)
sys.modules['api_layer.rest_api.kaleido_client'] = kaleido_stub

from api_layer.rest_api import server


def test_mint_success(monkeypatch):
    def mock_mint(to_address, token_id, token_uri):
        return {"tokenId": token_id}
    monkeypatch.setattr(server, "mint_nft", mock_mint)

    resp = server.mint_asset(
        to_address="0x1234567890abcdef1234567890abcdef12345678",
        token_id="1",
        token_uri="https://test.com/1.json",
    )
    assert resp["tokenId"] == "1"


def test_mint_invalid_address():
    with pytest.raises(server.HTTPException):
        server.mint_asset("bad", "1", "https://test.com/1.json")


def test_owner_of_success(monkeypatch):
    def mock_owner(token_id):
        return {"owner": "0x1234567890abcdef1234567890abcdef12345678"}
    monkeypatch.setattr(server, "owner_of", mock_owner)
    resp = server.get_owner("1")
    assert resp["owner"].startswith("0x")


def test_owner_of_not_found(monkeypatch):
    def mock_owner(token_id):
        return {"error": "Token not found"}
    monkeypatch.setattr(server, "owner_of", mock_owner)
    with pytest.raises(server.HTTPException) as exc:
        server.get_owner("999")
    assert exc.value.status_code == 404


def test_carbon_mint_success(monkeypatch):
    def mock_mint(**kwargs):
        return {"hash": "0xabc"}
    monkeypatch.setattr(server, "mint_nft", mock_mint)
    req = server.MintRequest(
        to_address="0x2810f346088b6f9638a39b869a929e6eafb73398",
        token_id=1,
        token_uri="http://example.com/meta.json",
    )
    resp = server.carbon_mint(req)
    assert resp["status"] == "success"


def test_carbon_mint_invalid_token_id(monkeypatch):
    req = server.MintRequest(
        to_address="0x2810f346088b6f9638a39b869a929e6eafb73398",
        token_id=-1,
        token_uri="http://example.com/meta.json",
    )
    with pytest.raises(server.HTTPException) as exc:
        server.carbon_mint(req)
    assert exc.value.status_code == 422
