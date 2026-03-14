import os

from fastapi.testclient import TestClient

os.environ.setdefault("KALEIDO_API_URL", "https://example.invalid/gateway")
os.environ.setdefault("KALEIDO_API_KEY", "test-kaleido-key")
os.environ.setdefault("CARBON_CONTRACT_ADDRESS", "0x2810f346088b6f9638a39b869a929e6eafb73398")
os.environ.setdefault("ADMIN_ADDRESS", "0x2810f346088b6f9638a39b869a929e6eafb73398")
os.environ.setdefault("API_TOKENS", "admin:test-admin-token,reader:test-reader-token")

from api_layer.rest_api.server import app

client = TestClient(app)


def test_health_live_and_request_id_header():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
    assert response.headers.get("X-Request-ID")


def test_health_ready_reports_ready():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_metrics_endpoint_emits_counters():
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    text = response.text
    assert "api_requests_total" in text
    assert "api_request_latency_ms_sum" in text
