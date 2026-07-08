import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "request_id" in data
    assert response.headers.get("X-Request-ID") == data["request_id"]


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    # Verify our RED and USE custom metric definitions are present
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
    assert "ai_inference_duration_seconds" in content
    assert "business_actions_total" in content


def test_ask_successful_request_with_correlation_id():
    """Test Input 1: Golden Flow demonstrating successful AI analysis and ticket creation."""
    custom_request_id = "test-golden-req-999"
    payload = {
        "question": "High memory utilization alerts on worker pod order-processor-8f4b after deployment.",
        "context": {"environment": "production", "service": "order-processor"}
    }
    response = client.post(
        "/ask",
        json=payload,
        headers={"X-Request-ID": custom_request_id}
    )

    assert response.status_code == 200
    # Verify correlation ID propagation
    assert response.headers["X-Request-ID"] == custom_request_id
    body = response.json()
    assert body["request_id"] == custom_request_id
    assert body["status"] == "success"

    data = body["data"]
    assert "ai_analysis" in data
    assert data["business_action"]["action_type"] == "CREATE_INCIDENT_TICKET"
    assert data["business_action"]["ticket_id"].startswith("INC-")
    assert data["business_action"]["status"] == "CREATED"


def test_ask_failing_request_fault_injection():
    """Test Input 2: Failing Request demonstrating observability fault injection & error tracing."""
    fault_request_id = "test-fault-req-500"
    payload = {
        "question": "Database connection pool exhausted on checkout service."
    }
    response = client.post(
        "/ask",
        json=payload,
        headers={
            "X-Request-ID": fault_request_id,
            "X-Inject-Fault": "llm_timeout"
        }
    )

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == fault_request_id
    body = response.json()
    assert body["request_id"] == fault_request_id
    assert "TimeoutError" in body["message"] or "Simulated LLM Provider Timeout" in body["message"]


def test_metrics_reflect_execution():
    """Verify Prometheus metrics incremented after executing successful and failing requests."""
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    # Verify business action counter and exception counter were recorded
    assert 'business_actions_total{action_type="CREATE_INCIDENT_TICKET",severity="HIGH",status="CREATED"}' in content
    assert 'app_exceptions_total{endpoint="/ask",exception_type="TimeoutError"}' in content
