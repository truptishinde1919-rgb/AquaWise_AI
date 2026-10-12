"""
test_api.py
===========
Integration tests for FastAPI endpoints using TestClient.
Verifies schema validation, prediction accuracy, missing value handling,
and HTTP error statuses.
"""

from pathlib import Path
import sys
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["project"] == "AquaWise AI"


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "model_name" in data


def test_root_health_endpoint():
    """Verify /health works identically for Docker and cloud platform health checks."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert "model_name" in data


def test_metadata_endpoint():
    response = client.get("/api/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "features" in data
    assert "feature_order" in data
    assert len(data["feature_order"]) == 9


def test_predict_standard_payload():
    payload = {
        "ph": 7.2,
        "Hardness": 180.0,
        "Solids": 16000.0,
        "Chloramines": 3.5,
        "Sulfate": 240.0,
        "Conductivity": 390.0,
        "Organic_carbon": 3.0,
        "Trihalomethanes": 60.0,
        "Turbidity": 2.2,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "is_potable" in data
    assert "potability_label" in data
    assert "potability_probability" in data
    assert "confidence_score" in data
    assert "parameter_evaluations" in data
    assert len(data["parameter_evaluations"]) == 9
    assert 0.0 <= data["potability_probability"] <= 1.0


def test_predict_validation_error_on_invalid_bounds():
    """pH cannot be 99.0 (exceeds max 14.0). Should return 422 Unprocessable Entity."""
    invalid_payload = {
        "ph": 99.0,
    }
    response = client.post("/api/predict", json=invalid_payload)
    assert response.status_code == 422


def test_predict_with_default_imputed_payload():
    """Testing default / empty payload to ensure pipeline imputation works through API."""
    response = client.post("/api/predict", json={})
    assert response.status_code == 200
    data = response.json()
    assert "potability_label" in data
