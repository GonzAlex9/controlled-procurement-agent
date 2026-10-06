from fastapi.testclient import TestClient

from procurement_agent.api import app, store

client = TestClient(app)


def setup_function():
    store.approvals.clear()
    store.audit_events.clear()


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_render_head_probes_are_supported():
    assert client.head("/").status_code == 200
    assert client.head("/health").status_code == 200


def test_demo_ui_is_available():
    response = client.get("/demo")
    assert response.status_code == 200
    assert "Controlled Procurement Agent" in response.text
    assert "Analyze purchase request" in response.text
    assert 'step="0.01"' in response.text


def test_analyze_without_ai_is_reproducible():
    response = client.post(
        "/v1/purchase-requests/analyze",
        json={
            "id": "PR-API-1",
            "requester": "demo.user",
            "department": "IT",
            "category": "hardware",
            "vendor_id": "vendor-cloud",
            "amount_eur": 700,
            "justification": "Replacement monitor for engineering workstation.",
            "quotes_count": 1,
            "contains_personal_data": False,
            "recurring": False,
            "emergency": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["policy"]["decision"] == "auto_approve"
    assert data["analysis_mode"] == "deterministic"
    assert data["telemetry"]["analysis_mode"] == "deterministic"
    assert data["telemetry"]["decision"] == "auto_approve"
    assert data["telemetry"]["trace_id"]
    assert data["telemetry"]["total_duration_ms"] >= 0


def test_demo_config_exposes_ai_capability_flag():
    response = client.get("/v1/demo/config")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["ai_enabled"], bool)
    assert isinstance(data["persistence_enabled"], bool)
