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
    IrrigationAssessmentInput,
    IrrigationAssessmentResponse,
    SoilMoistureForecastInput,
    SoilMoistureForecastResponse,
    IrrigationWaterQualityInput,
    IrrigationWaterQualityResponse,
    WaterForecastInput,
    WaterForecastResponse,
    PestRiskInput,
    PestRiskResponse,
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


IRRIGATION_CROP_FACTORS = {
    "rice": 1.35,
    "wheat": 1.1,
    "maize": 1.2,
    "cotton": 1.15,
    "soybean": 1.0,
    "tomato": 1.18,
    "chilli": 1.08,
    "brinjal": 1.1,
    "sugarcane": 1.3,
    "other": 1.0,
}

PEST_CROP_BASELINES = {
    "rice": 0.66,
    "wheat": 0.45,
    "maize": 0.58,
    "cotton": 0.7,
    "soybean": 0.54,
    "tomato": 0.72,
    "chilli": 0.68,
    "brinjal": 0.63,
    "sugarcane": 0.61,
    "other": 0.5,
}


def normalize_crop_name(crop: str) -> str:
    return crop.strip().lower()


def classify_irrigation_urgency(deficit_mm: float, soil_moisture_pct: float) -> str:
    if deficit_mm >= 35 or soil_moisture_pct < 25:
        return "High"
    if deficit_mm >= 18 or soil_moisture_pct < 40:
        return "Moderate"
    return "Low"


def classify_risk(score: float) -> str:
    if score >= 0.8:
        return "Very High"
    if score >= 0.6:
        return "High"
    if score >= 0.35:
        return "Moderate"
    return "Low"


def calculate_irrigation_assessment(payload: IrrigationAssessmentInput) -> IrrigationAssessmentResponse:
    crop_key = normalize_crop_name(payload.crop)
    crop_factor = IRRIGATION_CROP_FACTORS.get(crop_key, 1.0)
    stage_factor = {
        "seedling": 1.15,
        "vegetative": 1.1,
        "flowering": 1.2,
        "fruiting": 1.3,
        "maturity": 0.9,
        "harvest": 0.75,
    }.get(normalize_crop_name(payload.growth_stage), 1.0)

    rainfall_component = min(payload.rainfall_mm * 0.65, payload.crop_water_requirement_mm * 0.8)
    soil_component = max(0.0, (45.0 - payload.soil_moisture_pct) * 0.5)
    temp_component = max(0.0, (payload.temperature_c - 30.0) * 1.2)
    humidity_component = max(0.0, (45.0 - payload.humidity_pct) * 0.35)
    deficit_mm = max(
        0.0,
        (payload.crop_water_requirement_mm * stage_factor) - rainfall_component - soil_component - temp_component + humidity_component
    )

    estimated_liters = max(0.0, deficit_mm * payload.farm_area_ha * 10000.0 * crop_factor / 1000.0)
    urgency = classify_irrigation_urgency(deficit_mm, payload.soil_moisture_pct)

    if urgency == "High":
        timing = "Irrigate within the next 6-12 hours, ideally early morning."
    elif urgency == "Moderate":
        timing = "Irrigate within 24 hours using the next scheduled cycle."
    else:
        timing = "Continue monitoring; irrigate if forecasted dryness persists."

    explanation = (
        f"For {payload.crop.title()} in {payload.growth_stage.title()} stage, the field has a {payload.soil_moisture_pct:.1f}% soil moisture baseline "
        f"with {payload.rainfall_mm:.1f} mm rainfall and {payload.temperature_c:.1f}°C conditions. "
        f"The estimated water deficit is {deficit_mm:.1f} mm, which corresponds to {estimated_liters:.0f} liters over {payload.farm_area_ha} ha."
    )

    return IrrigationAssessmentResponse(
        estimated_irrigation_requirement_liters=round(estimated_liters, 2),
        irrigation_urgency=urgency,
        suggested_irrigation_timing=timing,
        water_deficit_mm=round(deficit_mm, 2),
        rainfall_contribution_mm=round(rainfall_component, 2),
        explanation=explanation,
    )


def forecast_soil_moisture(payload: SoilMoistureForecastInput) -> SoilMoistureForecastResponse:
    history = payload.historical_soil_moisture_pct or [payload.current_soil_moisture_pct]
    average_history = float(np.mean(history)) if history else payload.current_soil_moisture_pct
    rainfall_factor = max(0.0, payload.rainfall_mm * 0.7)
    irrigation_factor = payload.irrigation_events * 6.0
    temperature_factor = max(0.0, (payload.temperature_c - 28.0) * 0.8)

    forecast = payload.current_soil_moisture_pct + (rainfall_factor / 10.0) - (temperature_factor / 2.5) + (irrigation_factor / 10.0)
    forecast = max(0.0, min(100.0, forecast))

    trend = "Drying trend" if forecast < average_history - 2.5 else "Stable moisture" if abs(forecast - average_history) <= 2.5 else "Improving moisture"
    water_stress_warning = forecast < 30.0 or payload.current_soil_moisture_pct < 25.0
    alerts = []
    if water_stress_warning:
        alerts.append("Water stress warning: soil moisture is below crop stress threshold.")
    if payload.rainfall_mm < 5:
        alerts.append("Low rainfall: irrigation support is likely needed in the next 24-48 hours.")
    if payload.irrigation_events == 0:
        alerts.append("No recent irrigation event recorded for the current soil condition.")

    explanation = (
        f"Measured soil moisture is {payload.current_soil_moisture_pct:.1f}% with a recent average of {average_history:.1f}%. "
        f"Based on rainfall ({payload.rainfall_mm:.1f} mm), irrigation events ({payload.irrigation_events}), and temperature ({payload.temperature_c:.1f}°C), "
        f"the next forecast is {forecast:.1f}% moisture, indicating a {trend.lower()} status."
    )

    return SoilMoistureForecastResponse(
        current_measured_moisture_pct=round(payload.current_soil_moisture_pct, 2),
        forecast_soil_moisture_pct=round(forecast, 2),
        moisture_trend=trend,
        water_stress_warning=water_stress_warning,
        irrigation_alerts=alerts,
        explanation=explanation,
    )


def assess_irrigation_water_quality(payload: IrrigationWaterQualityInput) -> IrrigationWaterQualityResponse:
    score = 100.0
    reasons = []

    if payload.ph < 6.0 or payload.ph > 8.5:
        score -= 18
        reasons.append("pH is outside the preferred irrigation range for many crops.")
    if payload.electrical_conductivity > 2500:
        score -= 22
        reasons.append("Electrical conductivity is elevated and may indicate salinity stress.")
    if payload.sodium_adsorption_ratio > 8:
        score -= 20
        reasons.append("Sodium adsorption ratio suggests sodicity risk.")
    if payload.salinity > 2000:
        score -= 18
        reasons.append("Salinity exceeds recommended irrigation tolerances for sensitive crops.")
    if payload.chloride > 350:
        score -= 10
        reasons.append("Chloride concentration may affect root-zone health over time.")
    if payload.bicarbonate > 300:
        score -= 8
        reasons.append("Bicarbonate accumulation could reduce nutrient availability.")
    if payload.boron > 1.0:
        score -= 12
        reasons.append("Boron is high enough to merit crop-specific management.")

    if not reasons:
        reasons.append("All key irrigation water quality indicators are within safe operating limits for general use.")

    suitability = "Good" if score >= 75 else "Moderate" if score >= 50 else "Poor"
    safe_for_irrigation = score >= 50
    explanation = (
        f"The current irrigation water holds a {score:.1f}/100 suitability score. "
        f"This assessment is separate from drinking-water potability and focuses on crop safety and soil impact."
    )

    return IrrigationWaterQualityResponse(
        suitability=suitability,
        suitability_score=round(max(0.0, score), 2),
        reasons=reasons,
        safe_for_irrigation=safe_for_irrigation,
        explanation=explanation,
    )


def build_water_forecast(payload: WaterForecastInput) -> WaterForecastResponse:
    usage_history = payload.historical_usage_liters or [payload.daily_water_requirement_liters]
    avg_usage = float(np.mean(usage_history)) if usage_history else payload.daily_water_requirement_liters
    daily_requirement = max(0.0, payload.daily_water_requirement_liters * (1.0 - min(payload.current_soil_moisture_pct, 70.0) / 100.0 * 0.35) + max(0.0, payload.forecast_rainfall_mm * 0.2))
    seven_day_plan = max(0.0, daily_requirement * 7.0 - payload.forecast_rainfall_mm * 0.5 * payload.farm_area_ha)
    water_usage = {
        "daily_requirement_liters": round(daily_requirement, 2),
        "avg_historical_usage_liters": round(avg_usage, 2),
        "variance_vs_history_pct": round(((daily_requirement - avg_usage) / avg_usage * 100.0) if avg_usage else 0.0, 2),
    }
    suggestions = []
    if payload.current_soil_moisture_pct < 35:
        suggestions.append("Increase irrigation frequency during the next dry cycle to prevent crop stress.")
    if payload.forecast_rainfall_mm > 20:
        suggestions.append("Reduce scheduled irrigation volume because rainfall is expected to provide partial crop water demand.")
    suggestions.append("Use drip irrigation on the next cycle to reduce evaporation and improve water-use efficiency.")
    comparison = (
        f"Current daily demand is {daily_requirement:.0f} L/day compared with an average historical usage of {avg_usage:.0f} L/day. "
        f"This is a {water_usage['variance_vs_history_pct']:.1f}% deviation from recent trends."
    )
    return WaterForecastResponse(
        daily_water_requirement_liters=round(daily_requirement, 2),
        seven_day_irrigation_plan_liters=round(seven_day_plan, 2),
        water_usage_analytics=water_usage,
        water_saving_suggestions=suggestions,
        historical_comparison=comparison,
    )


def assess_pest_risk(payload: PestRiskInput) -> PestRiskResponse:
    crop_key = normalize_crop_name(payload.crop)
    base_risk = PEST_CROP_BASELINES.get(crop_key, 0.5)
    humidity_factor = max(0.0, payload.relative_humidity_pct - 60.0) / 50.0
    rainfall_factor = min(1.0, payload.rainfall_mm / 80.0)
    leaf_factor = min(1.0, payload.leaf_wetness_pct / 100.0)
    moisture_factor = max(0.0, (payload.soil_moisture_pct - 35.0) / 65.0)
    temperature_factor = 0.0
    if 24 <= payload.temperature_c <= 32:
        temperature_factor = 0.25
    elif payload.temperature_c > 32:
        temperature_factor = 0.45

    combined_score = min(
        1.0,
        base_risk
        + humidity_factor * 0.25
        + rainfall_factor * 0.2
        + leaf_factor * 0.25
        + moisture_factor * 0.15
        + temperature_factor * 0.15,
    )

    if "fungal" in payload.recent_pest_observations.lower() or "blast" in payload.recent_pest_observations.lower():
        combined_score = min(1.0, combined_score + 0.1)
    if "history" in payload.previous_pest_history.lower() and "high" in payload.previous_pest_history.lower():
        combined_score = min(1.0, combined_score + 0.08)

    risk_level = classify_risk(combined_score)
    if combined_score < 0.35:
        uncertainty = "Low"
    elif combined_score < 0.7:
        uncertainty = "Moderate"
    else:
        uncertainty = "High"

    risk_factors = []
    if payload.relative_humidity_pct > 75:
        risk_factors.append("High humidity favors disease pressure and pest survival")
    if payload.rainfall_mm > 25:
        risk_factors.append("Frequent rainfall creates a wet canopy conducive to infestation")
    if payload.leaf_wetness_pct > 60:
        risk_factors.append("Leaf wetness increases fungal and insect activity")
    if payload.soil_moisture_pct > 60:
        risk_factors.append("Excessive soil moisture can increase secondary pest pressure")
    if not risk_factors:
        risk_factors.append("Current conditions are mostly stable, but seasonal pressure still requires monitoring")

    explanation = (
        f"The pest-risk model for {payload.crop.title()} in {payload.location} during {payload.season} indicates {risk_level.lower()} risk. "
        f"This score is based on humidity, rainfall, leaf wetness, soil moisture, and recent observations.")

    return PestRiskResponse(
        crop=payload.crop.title(),
        risk_level=risk_level,
        risk_score=round(combined_score, 4),
        uncertainty=uncertainty,
        risk_factors=risk_factors,
        explanation=explanation,
        model_status="baseline-rule-based model",
        data_provenance={
            "crop": payload.crop,
            "location": payload.location,
            "growth_stage": payload.growth_stage,
            "season": payload.season,
            "recent_pest_observations": payload.recent_pest_observations,
            "previous_pest_history": payload.previous_pest_history,
        },
    )


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


@app.post("/api/agri/irrigation", response_model=IrrigationAssessmentResponse, tags=["Agricultural Intelligence"])
def irrigation_assessment(payload: IrrigationAssessmentInput):
    """Estimate irrigation need and urgency from field and weather conditions."""
    return calculate_irrigation_assessment(payload)


@app.post("/api/agri/soil-moisture", response_model=SoilMoistureForecastResponse, tags=["Agricultural Intelligence"])
def soil_moisture_forecast(payload: SoilMoistureForecastInput):
    """Forecast soil moisture and detect likely water-stress conditions."""
    return forecast_soil_moisture(payload)


@app.post("/api/agri/water-quality", response_model=IrrigationWaterQualityResponse, tags=["Agricultural Intelligence"])
def irrigation_water_quality(payload: IrrigationWaterQualityInput):
    """Assess irrigation suitability separately from drinking-water potability."""
    return assess_irrigation_water_quality(payload)


@app.post("/api/agri/water-forecast", response_model=WaterForecastResponse, tags=["Agricultural Intelligence"])
def water_forecast(payload: WaterForecastInput):
    """Project daily and 7-day water requirements with savings suggestions."""
    return build_water_forecast(payload)


@app.post("/api/agri/pest-risk", response_model=PestRiskResponse, tags=["Agricultural Intelligence"])
def pest_risk(payload: PestRiskInput):
    """Provide a crop-specific pest risk estimate using a baseline rule-driven model when labeled data is absent."""
    return assess_pest_risk(payload)


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
