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

from app.schemas import (
    WaterParametersInput,
    PredictionResponse,
    ParameterStatus,
    HealthResponse,
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


@app.get("/", tags=["General"])
def read_root():
    """Welcome endpoint confirming API operational state."""
    return {
        "project": "AquaWise AI",
        "description": "Smart Water Potability & Quality Assessment API",
        "docs_url": "/docs",
        "status": "online",
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Diagnostics"])
def health_check():
    """Returns runtime health and verifies whether the ML model is loaded."""
    return HealthResponse(
        status="healthy" if ml_pipeline is not None else "degraded",
        model_loaded=ml_pipeline is not None,
        model_name=metadata.get("model_name", "Unknown") if metadata else "None",
        environment=os.getenv("ENVIRONMENT", "development"),
    )


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
