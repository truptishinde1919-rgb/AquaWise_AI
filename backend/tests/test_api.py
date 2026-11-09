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


def test_rag_status_endpoint_exposes_only_sanitized_configuration(monkeypatch):
    from app import main

    monkeypatch.setenv("OPENAI_API_KEY", "sensitive-test-key")
    monkeypatch.setattr(
        main,
        "rag_database_status",
        lambda: {
            "status": "ready",
            "database_configured": True,
            "database_connected": True,
            "pgvector_available": True,
            "schema_available": True,
            "document_count": 1,
            "chunk_count": 43,
        },
    )
    response = client.get("/api/rag/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["document_count"] == 1
    assert data["chunk_count"] == 43
    assert data["embedding_provider_configured"] is True
    assert "DATABASE_URL" not in data
    assert "OPENAI_API_KEY" not in data
    assert "sensitive-test-key" not in response.text


def test_rag_status_endpoint_reports_missing_services_without_secrets(monkeypatch):
    from app import main

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        main,
        "rag_database_status",
        lambda: {
            "status": "unconfigured",
            "database_configured": False,
            "database_connected": False,
            "pgvector_available": False,
            "schema_available": False,
            "document_count": None,
            "chunk_count": None,
        },
    )
    response = client.get("/api/rag/status")
    assert response.status_code == 200
    assert response.json()["status"] == "unconfigured"
    assert response.json()["embedding_provider_configured"] is False


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


def test_agri_irrigation_endpoint():
    payload = {
        "crop": "rice",
        "growth_stage": "vegetative",
        "farm_area_ha": 3.5,
        "soil_type": "clay loam",
        "soil_moisture_pct": 32.0,
        "temperature_c": 31.0,
        "humidity_pct": 64.0,
        "rainfall_mm": 12.0,
        "irrigation_method": "drip",
        "crop_water_requirement_mm": 68.0,
        "weather_forecast": "Dry spell expected during next 48 hours.",
    }
    response = client.post("/api/agri/irrigation", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "estimated_irrigation_requirement_liters" in data
    assert data["irrigation_urgency"] in {"Low", "Moderate", "High"}


def test_agri_pest_risk_endpoint():
    payload = {
        "crop": "rice",
        "crop_variety": "Basmati",
        "growth_stage": "vegetative",
        "temperature_c": 29.0,
        "relative_humidity_pct": 82.0,
        "rainfall_mm": 35.0,
        "leaf_wetness_pct": 75.0,
        "soil_moisture_pct": 62.0,
        "location": "Satara",
        "season": "Kharif",
        "recent_pest_observations": "Leaf blight identified in lower canopy",
        "previous_pest_history": "High risk in previous season",
    }
    response = client.post("/api/agri/pest-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_level" in data
    assert "risk_score" in data
    assert data["model_status"] == "baseline-rule-based model"


def test_chat_endpoint_returns_research_citations(monkeypatch):
    from app import main, rag

    def fail_local_knowledge_fallback(*args, **kwargs):
        raise AssertionError("Local knowledge fallback must not provide chatbot answers.")

    monkeypatch.setattr(main, "retrieve_knowledge", fail_local_knowledge_fallback, raising=False)

    async def embeddings(texts):
        return [[0.0] * 1536]

    async def answer(question, chunks, history):
        assert history == []
        return rag.RagAnswer("Evidence-based answer [1].", True, (1,))

    monkeypatch.setattr(main, "generate_embeddings", embeddings)
    monkeypatch.setattr(
        main,
        "search_research_chunks",
        lambda embedding, limit: [
            {
                "title": "Verified irrigation study",
                "authors": ["A. Researcher"],
                "publication_year": 2021,
                "source_url": "https://example.org/study",
                "doi": "10.0000/example",
                "license": "CC BY 4.0",
                "page_number": 8,
                "text": "Retrieved evidence.",
                "similarity": 0.9,
            }
        ],
    )
    monkeypatch.setattr(main, "generate_answer", answer)
    payload = {
        "message": "How does irrigation water quality affect crops?",
        "history": [],
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Evidence-based answer [1]."
    assert data["provider"] == "openai"
    assert data["evidence_used"] is True
    assert data["references"][0]["title"] == "Verified irrigation study"
    assert data["references"][0]["source_index"] == 1
    assert data["references"][0]["page_number"] == 8
    assert data["references"][0]["doi"] == "10.0000/example"


def test_chat_endpoint_maps_only_cited_chunks_to_source_panel(monkeypatch):
    from app import main, rag

    async def embeddings(texts):
        return [[0.0] * 1536]

    docs = [
        {
            "title": "Plant disease paper",
            "authors": ["A. Author"],
            "publication_year": 2016,
            "source_url": "https://doi.org/10.0000/example",
            "doi": "10.0000/example",
            "page_number": 1,
            "text": "Other retrieved excerpt.",
            "similarity": 0.8,
        },
        {
            "title": "Plant disease paper",
            "authors": ["A. Author"],
            "publication_year": 2016,
            "source_url": "https://doi.org/10.0000/example",
            "doi": "10.0000/example",
            "page_number": 8,
            "text": "Domain-shift excerpt.",
            "similarity": 0.9,
        },
    ]

    async def answer(question, chunks, history):
        assert chunks == docs
        return rag.RagAnswer("The reported field performance changed [2].", True, (2,))

    monkeypatch.setattr(main, "generate_embeddings", embeddings)
    monkeypatch.setattr(main, "search_research_chunks", lambda embedding, limit: docs)
    monkeypatch.setattr(main, "generate_answer", answer)
    response = client.post(
        "/api/chat",
        json={"message": "What happened under different image conditions?", "history": []},
    )
    assert response.status_code == 200
    assert response.json()["references"] == [
        {
            "source_index": 2,
            "title": "Plant disease paper",
            "authors": ["A. Author"],
            "publication_year": 2016,
            "page_number": 8,
            "source_url": "https://doi.org/10.0000/example",
            "doi": "10.0000/example",
            "license": None,
        }
    ]


def test_chat_endpoint_reports_insufficient_retrieved_evidence_without_citation(monkeypatch):
    from app import main, rag

    async def embeddings(texts):
        return [[0.0] * 1536]

    async def answer(question, chunks, history):
        return rag.RagAnswer("This paper does not establish a pesticide recommendation.", False)

    monkeypatch.setattr(main, "generate_embeddings", embeddings)
    monkeypatch.setattr(
        main,
        "search_research_chunks",
        lambda embedding, limit: [
            {
                "title": "Plant disease paper",
                "authors": ["A. Author"],
                "publication_year": 2016,
                "page_number": 1,
                "text": "CNN-based disease classification.",
                "similarity": 0.8,
            }
        ],
    )
    monkeypatch.setattr(main, "generate_answer", answer)
    response = client.post(
        "/api/chat",
        json={"message": "What pesticide should I use?", "history": []},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"
    assert data["evidence_used"] is False
    assert data["references"] == []


def test_chat_endpoint_reports_empty_retrieval_without_faking_llm(monkeypatch):
    from app import main

    async def embeddings(texts):
        return [[0.0] * 1536]

    monkeypatch.setattr(main, "generate_embeddings", embeddings)
    monkeypatch.setattr(main, "search_research_chunks", lambda embedding, limit: [])
    monkeypatch.setattr(
        main,
        "generate_answer",
        lambda *args: (_ for _ in ()).throw(AssertionError("LLM must not run without evidence")),
    )
    response = client.post("/api/chat", json={"message": "Question with no evidence", "history": []})
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "none"
    assert data["evidence_used"] is False
    assert data["references"] == []


def test_chat_endpoint_returns_explicit_provider_error(monkeypatch):
    from app import main, rag

    async def embeddings(texts):
        raise rag.RagServiceError("The provider rejected credentials.", 503)

    monkeypatch.setattr(main, "generate_embeddings", embeddings)
    response = client.post("/api/chat", json={"message": "Question", "history": []})
    assert response.status_code == 503
    assert "credentials" in response.json()["detail"]
