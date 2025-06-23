import pytest
from fastapi.testclient import TestClient
from api_layer.rest_api.server import app

client = TestClient(app)

def test_mint_success(monkeypatch):
    # Patch mint_nft to simulate a successful blockchain response
    def mock_mint_nft(to_address, token_id, token_uri):
        return {"status": "success", "tokenId": token_id}
    app.dependency_overrides = {}  # Reset overrides
    import api_layer.rest_api.kaleido_client as kaleido_client
    monkeypatch.setattr(kaleido_client, "mint_nft", mock_mint_nft)

    response = client.post("/mint", json={
        "to_address": "0x1234567890abcdef1234567890abcdef12345678",
        "token_id": "1",
        "token_uri": "https://test.com/1.json"
    })
    assert response.status_code == 200
    assert response.json()["tokenId"] == "1"

def test_mint_invalid_address():
    response = client.post("/mint", json={
        "to_address": "badaddress",
        "token_id": "2",
        "token_uri": "https://test.com/2.json"
    })
    assert response.status_code == 422
    assert "Invalid Ethereum address" in response.text
def test_owner_of_success(monkeypatch):
    def mock_owner_of(token_id):
        return {"owner": "0x1234567890abcdef1234567890abcdef12345678"}
    import api_layer.rest_api.kaleido_client as kaleido_client
    monkeypatch.setattr(kaleido_client, "owner_of", mock_owner_of)

    response = client.get("/ownerOf/1")
    assert response.status_code == 200
    assert response.json()["owner"].startswith("0x")

def test_owner_of_not_found(monkeypatch):
    def mock_owner_of(token_id):
        return {"error": "Token not found"}
    import api_layer.rest_api.kaleido_client as kaleido_client
    monkeypatch.setattr(kaleido_client, "owner_of", mock_owner_of)

    response = client.get("/ownerOf/9999")
    assert response.status_code == 404
    assert "Kaleido error" in response.text