"""
schemas.py
==========
Pydantic data schemas for request validation, parameter bounds checking,
and structured API responses in AquaWise AI.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


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
    model_name: str
    model_version: str = "1.0.0"


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    model_name: str
    environment: str
