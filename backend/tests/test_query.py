"""
Automated unit and integration tests for FastAPI endpoints:
1. Health check verification
2. Happy path valid query with grounded sources
3. Invalid request returning HTTP 422
4. Out-of-domain ungrounded query handling
"""

import pytest


def test_health_endpoint(client):
    """Verify GET /health returns status 200 and connected vector store."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["vector_store"] == "connected"
    assert data["collection_count"] > 0
    assert "trustai" in data["collection_name"]


def test_query_happy_path(client, monkeypatch):
    """
    Test 1 (Happy Path):
    Valid AI security query returns HTTP 200, grounded answer, and populated source list.
    """
    payload = {
        "question": "What is Prompt Injection and how can it be mitigated?",
        "top_k": 3
    }
    response = client.post("/query", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 10
    assert "sources" in data
    assert len(data["sources"]) > 0
    assert data["retrieval_count"] == len(data["sources"])
    assert data["latency_ms"] > 0

    # Verify provenance metadata on retrieved chunks
    top_source = data["sources"][0]
    assert "document" in top_source
    assert "page" in top_source
    assert "similarity" in top_source
    assert 0.0 <= top_source["similarity"] <= 1.0
    assert "snippet" in top_source


def test_query_validation_error_empty_body(client):
    """
    Test 2 (Validation Error):
    Empty or missing question payload triggers HTTP 422 Unprocessable Entity.
    """
    response = client.post("/query", json={})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_query_validation_error_short_question(client):
    """Question with less than 2 characters triggers HTTP 422."""
    response = client.post("/query", json={"question": "a"})
    assert response.status_code == 422


def test_query_out_of_domain_refusal(client):
    """
    Out-of-domain question triggers honest refusal without hallucination.
    """
    payload = {
        "question": "What is the secret recipe for strawberry cheesecake?",
        "top_k": 2
    }
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "do not have sufficient information" in data["answer"].lower()
