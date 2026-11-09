"""
schemas.py
==========
Pydantic data schemas for request validation, parameter bounds checking,
and structured API responses in AquaWise AI.
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Single message in a conversation history record."""
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    """Agricultural question to answer using retrieved research documents."""
    message: str = Field(..., min_length=2, max_length=2000)
    history: List[ChatMessage] = Field(default_factory=list, max_length=20)


class ResearchCitation(BaseModel):
    source_index: int
    title: str
    authors: Optional[List[str]] = None
    publication_year: Optional[int] = None
    page_number: int
    source_url: Optional[str] = None
    doi: Optional[str] = None
    license: Optional[str] = None


class ChatResponse(BaseModel):
    """Answer and verifiable citations from the research retrieval corpus."""
    answer: str
    references: List[ResearchCitation]
    provider: str
    uncertainty: str
    evidence_used: bool


class IrrigationAssessmentInput(BaseModel):
    """Input schema for irrigation requirement estimation in agricultural settings."""
    crop: str = Field(..., min_length=2, description="Crop type such as rice, wheat, maize, cotton, tomato")
    growth_stage: str = Field(..., min_length=2, description="Vegetative, flowering, fruiting, maturity")
    farm_area_ha: float = Field(..., gt=0, description="Farm size in hectares")
    soil_type: str = Field(..., min_length=2, description="Soil family like sandy loam, clay loam, loam")
    soil_moisture_pct: float = Field(..., ge=0, le=100, description="Current soil moisture percentage")
    temperature_c: float = Field(..., ge=-20, le=60, description="Air temperature in °C")
    humidity_pct: float = Field(..., ge=0, le=100, description="Relative humidity percentage")
    rainfall_mm: float = Field(..., ge=0, description="Rainfall received in mm")
    irrigation_method: str = Field(..., min_length=2, description="Drip, sprinkler, flood, rainfed")
    crop_water_requirement_mm: float = Field(..., gt=0, description="Crop water requirement in mm per season or day")
    weather_forecast: Optional[str] = Field(default=None, description="Short weather forecast summary")


class IrrigationAssessmentResponse(BaseModel):
    """Response from irrigation requirement model."""
    estimated_irrigation_requirement_liters: float
    irrigation_urgency: str
    suggested_irrigation_timing: str
    water_deficit_mm: float
    rainfall_contribution_mm: float
    explanation: str


class SoilMoistureForecastInput(BaseModel):
    """Input schema for soil moisture forecasting."""
    current_soil_moisture_pct: float = Field(..., ge=0, le=100)
    historical_soil_moisture_pct: List[float] = Field(default_factory=list, description="Recent history of soil moisture values")
    rainfall_mm: float = Field(default=0.0, ge=0)
    irrigation_events: int = Field(default=0, ge=0)
    temperature_c: float = Field(default=25.0, ge=-20, le=60)
    crop_water_requirement_mm: float = Field(default=60.0, gt=0)


class SoilMoistureForecastResponse(BaseModel):
    """Forecasted soil moisture and water stress information."""
    current_measured_moisture_pct: float
    forecast_soil_moisture_pct: float
    moisture_trend: str
    water_stress_warning: bool
    irrigation_alerts: List[str]
    explanation: str


class IrrigationWaterQualityInput(BaseModel):
    """Separate irrigation water suitability assessment, distinct from drinking-water potability."""
    ph: float = Field(..., ge=0.0, le=14.0)
    electrical_conductivity: float = Field(..., ge=0.0, le=5000.0)
    sodium_adsorption_ratio: float = Field(..., ge=0.0, le=50.0)
    salinity: float = Field(..., ge=0.0, le=20000.0)
    chloride: float = Field(..., ge=0.0, le=5000.0)
    bicarbonate: float = Field(..., ge=0.0, le=5000.0)
    boron: float = Field(..., ge=0.0, le=20.0)


class IrrigationWaterQualityResponse(BaseModel):
    """Water suitability for irrigation use."""
    suitability: str
    suitability_score: float
    reasons: List[str]
    safe_for_irrigation: bool
    explanation: str


class WaterForecastInput(BaseModel):
    """Input schema for daily and 7-day irrigation planning."""
    crop: str = Field(..., min_length=2)
    farm_area_ha: float = Field(..., gt=0)
    current_soil_moisture_pct: float = Field(..., ge=0, le=100)
    daily_water_requirement_liters: float = Field(..., ge=0)
    forecast_rainfall_mm: float = Field(..., ge=0)
    historical_usage_liters: List[float] = Field(default_factory=list)


class WaterForecastResponse(BaseModel):
    """Water forecast and consumption analytics."""
    daily_water_requirement_liters: float
    seven_day_irrigation_plan_liters: float
    water_usage_analytics: Dict[str, float]
    water_saving_suggestions: List[str]
    historical_comparison: str


class PestRiskInput(BaseModel):
    """Input schema for crop-specific pest risk assessment."""
    crop: str = Field(..., min_length=2)
    crop_variety: str = Field(default="standard", min_length=1)
    growth_stage: str = Field(..., min_length=2)
    temperature_c: float = Field(..., ge=-20, le=60)
    relative_humidity_pct: float = Field(..., ge=0, le=100)
    rainfall_mm: float = Field(..., ge=0)
    leaf_wetness_pct: float = Field(..., ge=0, le=100)
    soil_moisture_pct: float = Field(..., ge=0, le=100)
    location: str = Field(default="Unknown", min_length=1)
    season: str = Field(default="Kharif", min_length=2)
    recent_pest_observations: str = Field(default="None")
    previous_pest_history: str = Field(default="None")


class PestRiskResponse(BaseModel):
    """Risk assessment and explanatory factors for crop pest prediction."""
    crop: str
    risk_level: str
    risk_score: float
    uncertainty: str
    risk_factors: List[str]
    explanation: str
    model_status: str
    data_provenance: Dict[str, Any]


class WaterParametersInput(BaseModel):
    """
    Input schema representing 9 chemical and physical water metrics.
    Fields are Optional to support real-world scenarios where certain sensor
    readings may be missing (our trained pipeline's SimpleImputer handles them).
    """
    ph: Optional[float] = Field(
        default=7.0,
        ge=0.0,
        le=14.0,
        description="Water pH level (0.0 to 14.0). Safe drinking range: 6.5 - 8.5."
    )
    Hardness: Optional[float] = Field(
        default=196.37,
        ge=0.0,
        le=500.0,
        description="Capacity of water to precipitate soap (mg/L)."
    )
    Solids: Optional[float] = Field(
        default=20927.83,
        ge=0.0,
        le=70000.0,
        description="Total Dissolved Solids (TDS in ppm). Desirable: < 500-1000 ppm."
    )
    Chloramines: Optional[float] = Field(
        default=7.13,
        ge=0.0,
        le=20.0,
        description="Amount of Chloramines disinfectant (ppm). Safe EPA limit: <= 4.0 ppm."
    )
    Sulfate: Optional[float] = Field(
        default=333.07,
        ge=0.0,
        le=600.0,
        description="Dissolved Sulfate mineral content (mg/L). Safe EPA limit: <= 250 mg/L."
    )
    Conductivity: Optional[float] = Field(
        default=421.88,
        ge=0.0,
        le=1000.0,
        description="Electrical conductivity (μS/cm). Safe guideline: <= 400 μS/cm."
    )
    Organic_carbon: Optional[float] = Field(
        default=14.22,
        ge=0.0,
        le=50.0,
        description="Total Organic Carbon content (ppm). Typical safe limit: <= 4.0 ppm."
    )
    Trihalomethanes: Optional[float] = Field(
        default=66.40,
        ge=0.0,
        le=200.0,
        description="Trihalomethanes chlorine by-products (μg/L). Safe EPA limit: <= 80 μg/L."
    )
    Turbidity: Optional[float] = Field(
        default=3.95,
        ge=0.0,
        le=15.0,
        description="Light emission property / cloudiness (NTU). Safe WHO limit: <= 5.0 NTU."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "ph": 7.25,
                "Hardness": 185.50,
                "Solids": 18200.0,
                "Chloramines": 3.80,
                "Sulfate": 240.0,
                "Conductivity": 380.0,
                "Organic_carbon": 3.20,
                "Trihalomethanes": 65.0,
                "Turbidity": 2.10
            }
        }
    }


class ParameterStatus(BaseModel):
    """Status assessment for a single water quality parameter."""
    parameter: str
    value: Optional[float]
    unit: str
    is_safe: bool
    safe_range: str
    status_message: str


class PredictionResponse(BaseModel):
    """Comprehensive prediction response payload."""
    is_potable: bool
    potability_label: str  # "Potable (Safe to Drink)" or "Not Potable (Unsafe)"
    potability_probability: float  # e.g. 0.78 (78%)
    non_potability_probability: float  # e.g. 0.22 (22%)
    confidence_score: float  # max probability as a percentage (e.g. 78.0%)
    water_quality_grade: str  # "Safe / High Quality", "Caution / Moderate", "Unsafe"
    parameter_evaluations: List[ParameterStatus]
    warnings: List[str]
    top_drivers: List[str] = Field(default_factory=list, description="Top 3 features driving this prediction")
    feature_importances: Optional[Dict[str, float]] = None
    model_name: str
    model_version: str = "1.0.0"


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    model_name: str
    environment: str
