"""
Pytest configuration and fixtures for TrustAI backend test suite.
Sets up FastAPI TestClient with initialized lifespan services.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app


@pytest.fixture(scope="session")
def client():
    """
    Session-scoped TestClient that triggers FastAPI lifespan events,
    loading the persistent Chroma vector store once for the entire test run.
    """
    with TestClient(app) as test_client:
        yield test_client
