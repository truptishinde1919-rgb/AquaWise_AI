"""
main.py
=======
FastAPI application entrypoint for AquaWise AI.
Exposes ML model inference, metadata inspection, and health check endpoints.
Configured with CORS support for Next.js frontend deployed on Vercel or running locally.
"""

from pathlib import Path
import json
import os
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from starlette.concurrency import run_in_threadpool

from app.rag import (
    RagServiceError,
    citation_for_chunk,
    generate_answer,
    generate_embeddings,
    rag_database_status,
    search_research_chunks,
)

from app.schemas import (
    WaterParametersInput,
    PredictionResponse,
    ParameterStatus,
    HealthResponse,
    ChatRequest,
    ChatResponse,
)

# Load optional .env file
load_dotenv()

# Setup paths
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
MODELS_DIR = BACKEND_DIR / "models"
MODEL_FILE = MODELS_DIR / "water_potability_model.joblib"
METADATA_FILE = MODELS_DIR / "metadata.json"

# Initialize FastAPI application
app = FastAPI(
    title="AquaWise AI - Water Potability ML API",
    description="Machine Learning REST API for drinking water safety and quality assessment.",
    version="1.0.0",
)

# Configure CORS origins
raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,https://*.vercel.app"
)
allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ENVIRONMENT") != "production" else allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load ML artifacts safely into memory
ml_pipeline = None
metadata = None

if MODEL_FILE.exists() and METADATA_FILE.exists():
    try:
        ml_pipeline = joblib.load(MODEL_FILE)
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        print(f"[STARTUP] Successfully loaded model: {metadata.get('model_name')}")
    except Exception as e:
        print(f"[STARTUP ERROR] Could not load model: {e}")
else:
    print(f"[STARTUP WARNING] Model artifacts not found at {MODEL_FILE}")


@app.post("/api/chat", response_model=ChatResponse, tags=["AI Assistant"])
async def agri_chat(payload: ChatRequest):
    """Answer with OpenAI using semantically retrieved, page-cited research evidence."""
    try:
        query_embedding = (await generate_embeddings([payload.message]))[0]
        docs = await run_in_threadpool(search_research_chunks, query_embedding, 5)
        if not docs:
            return ChatResponse(
                answer=(
                    "I could not find sufficiently relevant research in the configured document library to "
                    "answer this reliably. Add suitable peer-reviewed or official technical sources and try again."
                ),
                references=[],
                provider="none",
                uncertainty="No relevant documents were retrieved; no LLM answer was generated.",
                evidence_used=False,
            )

        rag_answer = await generate_answer(
            payload.message,
            docs,
            [message.model_dump() for message in payload.history],
        )
        if not rag_answer.evidence_sufficient:
            return ChatResponse(
                answer=rag_answer.answer,
                references=[],
                provider="openai",
                uncertainty="Retrieved research was insufficient to answer; no source is cited as support.",
                evidence_used=False,
            )

        references = [
            {"source_index": index, **citation_for_chunk(docs[index - 1])}
            for index in rag_answer.citations
        ]
        return ChatResponse(
            answer=rag_answer.answer,
            references=references,
            provider="openai",
            uncertainty=(
                "The response is based on retrieved excerpts and cites their source pages. "
                "Evidence may not cover local conditions; verify agronomic decisions with local experts. "
                "No pesticide dose or application instruction is provided."
            ),
            evidence_used=True,
        )
    except RagServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@app.get("/", tags=["General"])
def read_root():
    """Welcome endpoint confirming API operational state."""
    return {
        "project": "AquaWise AI",
        "description": "Smart Water Potability & Quality Assessment API",
        "docs_url": "/docs",
        "status": "online",
    }


@app.get("/health", response_model=HealthResponse, tags=["Diagnostics"])
@app.get("/api/health", response_model=HealthResponse, tags=["Diagnostics"])
def health_check():
    """Returns runtime health and verifies whether the ML model is loaded."""
    return HealthResponse(
        status="healthy" if ml_pipeline is not None else "degraded",
        model_loaded=ml_pipeline is not None,
        model_name=metadata.get("model_name", "Unknown") if metadata else "None",
        environment=os.getenv("ENVIRONMENT", "development"),
    )


@app.get("/api/rag/status", tags=["Diagnostics"])
async def research_rag_status():
    """Return sanitized database/vector status without exposing connection details."""
    status = await run_in_threadpool(rag_database_status)
    return {
        **status,
        "embedding_provider_configured": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.get("/api/metadata", tags=["Model Inspection"])
def get_metadata():
    """Returns dataset distributions, feature units, and model performance metrics."""
    if metadata is None:
        raise HTTPException(status_code=503, detail="Model metadata not currently available.")
    return metadata


def evaluate_parameter_safety(feature_name: str, value: float | None, meta: dict) -> ParameterStatus:
    """Evaluates an individual water chemical metric against WHO/EPA safety standards."""
    safe_min = meta.get("safe_min", 0.0)
    safe_max = meta.get("safe_max", 0.0)
    unit = meta.get("unit", "")

    if value is None:
        return ParameterStatus(
            parameter=feature_name,
            value=None,
            unit=unit,
            is_safe=True,
            safe_range=f"{safe_min} - {safe_max} {unit}",
            status_message="Value missing (imputed using dataset median).",
        )

    # Check boundaries
    is_safe = True
    msg = "Within acceptable guideline range."

    if safe_min > 0 and value < safe_min:
        is_safe = False
        msg = f"Low ({value:.2f} {unit} < {safe_min} {unit} minimum guideline)."
    elif safe_max > 0 and value > safe_max:
        is_safe = False
        msg = f"Elevated ({value:.2f} {unit} > {safe_max} {unit} maximum guideline)."

    return ParameterStatus(
        parameter=feature_name,
        value=round(value, 2),
        unit=unit,
        is_safe=is_safe,
        safe_range=f"{safe_min} - {safe_max} {unit}" if safe_max > 0 else f">= {safe_min} {unit}",
        status_message=msg,
    )


@app.post("/api/predict", response_model=PredictionResponse, tags=["Inference"])
def predict_potability(payload: WaterParametersInput):
    """
    Predicts water potability based on 9 chemical and physical parameters.
    """
    if ml_pipeline is None or metadata is None:
        raise HTTPException(
            status_code=503,
            detail="Machine learning model is not loaded. Run train.py first."
        )

    # Construct input dataframe matching exact feature order expected by pipeline
    input_dict = {
        feat: [getattr(payload, feat)]
        for feat in metadata["feature_order"]
    }
    df_input = pd.DataFrame(input_dict)

    try:
        # Run inference
        prediction = int(ml_pipeline.predict(df_input)[0])
        probabilities = ml_pipeline.predict_proba(df_input)[0]
        prob_not_potable = float(probabilities[0])
        prob_potable = float(probabilities[1])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

    # Evaluate individual parameters against EPA/WHO guidelines
    parameter_evals = []
    warnings = []
    for feat in metadata["feature_order"]:
        val = getattr(payload, feat)
        feat_meta = metadata["features"].get(feat, {})
        status = evaluate_parameter_safety(feat, val, feat_meta)
        parameter_evals.append(status)
        if not status.is_safe:
            warnings.append(f"{feat}: {status.status_message}")

    # Determine qualitative grade
    is_potable = bool(prediction == 1)
    confidence = max(prob_potable, prob_not_potable) * 100.0

    if is_potable and len(warnings) <= 1 and prob_potable >= 0.65:
        grade = "High Quality / Potable"
    elif is_potable:
        grade = "Moderate / Borderline Potable"
    elif prob_potable >= 0.40:
        grade = "Caution / Near Unsafe Threshold"
    else:
        grade = "Unsafe / Non-Potable"

    # Extract top drivers from metadata
    raw_imps = metadata.get("feature_importances", {})
    sorted_drivers = sorted(
        raw_imps.items(),
        key=lambda item: item[1].get("importance", 0),
        reverse=True
    )
    top_drivers = [driver[0] for driver in sorted_drivers[:3]]
    simple_imps = {k: v.get("importance_pct", 0.0) for k, v in raw_imps.items()}

    return PredictionResponse(
        is_potable=is_potable,
        potability_label="Potable (Safe to Drink)" if is_potable else "Not Potable (Unsafe)",
        potability_probability=round(prob_potable, 4),
        non_potability_probability=round(prob_not_potable, 4),
        confidence_score=round(confidence, 1),
        water_quality_grade=grade,
        parameter_evaluations=parameter_evals,
        warnings=warnings,
        top_drivers=top_drivers,
        feature_importances=simple_imps,
        model_name=metadata.get("model_name", "RandomForestClassifier"),
        model_version="1.0.0",
    )
