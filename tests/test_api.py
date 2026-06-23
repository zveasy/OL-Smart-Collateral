import sys
import types
# tests/test_api.py
from fastapi.testclient import TestClient
from api_layer.rest_api.server import app           # only need the app
from api_layer.rest_api import carbon_routes

client = TestClient(app)

kaleido_stub = types.SimpleNamespace(
    mint_nft=lambda *a, **k: None,
    owner_of=lambda *a, **k: None,
    token_uri=lambda *a, **k: None,
    tokens_by_owner=lambda *a, **k: None,
)
sys.modules['api_layer.rest_api.kaleido_client'] = kaleido_stub


def test_mint_success(monkeypatch):
    def mock_mint(to_address, token_id, amount, token_uri):
        #return {"tokenId": token_id}
         return {"status": "success", "tokenId": token_id}
    monkeypatch.setattr(carbon_routes, "mint_nft", mock_mint)

    # resp = server.mint_asset(
    #     to_address="0x1234567890abcdef1234567890abcdef12345678",
    #     token_id="1",
    #     token_uri="https://test.com/1.json",
    # )
    payload = {
        "to_address": "0x1234567890abcdef1234567890abcdef12345678",
        "token_id": 1,
        "amount": 1,
        "token_uri": "https://test.com/1.json",
    }
    resp = client.post("/carbon/mint", json=payload) 
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    #assert resp["tokenId"] == "1"


def test_mint_invalid_address(monkeypatch):
    # with pytest.raises(server.HTTPException):
    #     server.mint_asset("bad", "1", "https://test.com/1.json")
    monkeypatch.setattr(
        carbon_routes, "mint_nft",
        lambda *a, **k: {"status": "success"}
    )

    bad_payload = {
        "to_address": "bad",               # invalid ETH address
        "token_id": 1,
        "amount": 1,
        "token_uri": "https://test.com/1.json"
    }
    resp = client.post("/carbon/mint", json=bad_payload)
    assert resp.status_code == 422                    


def test_owner_of_success(monkeypatch):
    def mock_owner(token_id):
        return {"owner": "0x1234567890abcdef1234567890abcdef12345678"}
    monkeypatch.setattr(carbon_routes, "owner_of", mock_owner)
    resp = client.get("/carbon/owner/1")              # HTTP call
    assert resp.status_code == 200
    assert resp.json()["owner"].lower() == "0x1234567890abcdef1234567890abcdef12345678"

    # resp = server.get_owner("1")
    # assert resp["owner"].startswith("0x")


def test_owner_of_not_found(monkeypatch):
    def mock_owner(token_id):
        import requests
        resp = requests.Response()
        resp.status_code = 404
        resp._content = b"Token not found"
        raise requests.HTTPError(response=resp)
        return {"error": "Token not found"}
    monkeypatch.setattr(carbon_routes, "owner_of", mock_owner)

    resp = client.get("/carbon/owner/999")               # ← HTTP call
    assert resp.status_code == 502  
    # with pytest.raises(server.HTTPException) as exc:
    #     server.get_owner("999")
    # assert exc.value.status_code == 404


def test_carbon_mint_success(monkeypatch):
    def mock_mint(to_address, token_id, amount, token_uri):
        return {"status": "success", "hash": "0xabc"}
        #return {"hash": "0xabc"}
    monkeypatch.setattr(carbon_routes, "mint_nft", mock_mint)
    # req = server.MintRequest(
    #     to_address="0x2810f346088b6f9638a39b869a929e6eafb73398",
    #     token_id=1,
    #     token_uri="http://example.com/meta.json",
    # )
    payload = {
        "to_address": "0x2810f346088b6f9638a39b869a929e6eafb73398",
        "token_id": 1,
        "amount": 1,
        "token_uri": "http://example.com/meta.json",
    }
    resp = client.post("/carbon/mint", json=payload)
    assert resp.status_code == 200
    assert resp.json()["hash"] == "0xabc"
    # resp = server.carbon_mint(req)
    # assert resp["status"] == "success"


def test_carbon_mint_invalid_token_id(monkeypatch):
    monkeypatch.setattr(
        carbon_routes, "mint_nft",
        lambda *a, **k: {"status": "success"}
    )
    # req = server.MintRequest(
    #     to_address="0x2810f346088b6f9638a39b869a929e6eafb73398",
    #     token_id=-1,
    #     token_uri="http://example.com/meta.json",
    # )
    bad_payload = {
        "to_address": "0x2810f346088b6f9638a39b869a929e6eafb73398",
        "token_id": -1,                     # invalid
        "amount": 1,
        "token_uri": "http://example.com/meta.json"
    }
    resp = client.post("/carbon/mint", json=bad_payload)
    assert resp.status_code == 422
    # with pytest.raises(server.HTTPException) as exc:
    #     server.carbon_mint(req)
    # assert exc.value.status_code == 422
