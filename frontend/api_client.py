"""
API Client for TrustAI FastAPI Backend.
Handles HTTP communication, environment configuration, and structured error handling.
"""

import os
import httpx
from dotenv import load_dotenv

# Load frontend environment variables
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


class TrustAIApiClient:
    def __init__(self, base_url: str = None, timeout: float = 30.0):
        self.base_url = (base_url or API_BASE_URL).rstrip("/")
        self.timeout = timeout

    def check_health(self) -> dict:
        """
        Queries GET /health endpoint to determine backend readiness.
        Returns health diagnostic dict or error flag.
        """
        try:
            with httpx.Client(timeout=4.0) as client:
                response = client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    return {"connected": True, "data": response.json()}
                return {
                    "connected": False,
                    "error": f"Backend returned HTTP {response.status_code}: {response.text}"
                }
        except httpx.ConnectError:
            return {
                "connected": False,
                "error": f"Cannot connect to backend at {self.base_url}. Is Uvicorn running?"
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    def query_document_assistant(self, question: str, top_k: int = 3) -> dict:
        """
        Submits POST /query to FastAPI backend.
        Returns parsed QueryResponse dictionary or structured error.
        """
        endpoint = f"{self.base_url}/query"
        payload = {"question": question.strip(), "top_k": top_k}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(endpoint, json=payload)

                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                elif response.status_code == 422:
                    return {
                        "success": False,
                        "error_type": "validation",
                        "error": "Question validation failed. Please provide a clear question (at least 2 characters)."
                    }
                else:
                    return {
                        "success": False,
                        "error_type": "server",
                        "error": f"Server error (HTTP {response.status_code}): {response.text}"
                    }
        except httpx.ConnectError:
            return {
                "success": False,
                "error_type": "connection",
                "error": f"Unable to reach FastAPI backend at {self.base_url}. Please verify the server is running."
            }
        except httpx.TimeoutException:
            return {
                "success": False,
                "error_type": "timeout",
                "error": "Request timed out while waiting for backend response. If Ollama is generating, it may be busy."
            }
        except Exception as e:
            return {
                "success": False,
                "error_type": "unknown",
                "error": f"Unexpected communication error: {str(e)}"
            }
