"""
test_ml_pipeline.py
===================
Unit tests for the AquaWise AI machine learning artifacts and pipeline:
- Artifact existence and schema verification
- Real model inference sanity
- Robustness to missing input values (handled via trained imputer)
- Probability calibration (probabilities sum to 1.0)
"""

from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODEL_FILE = BACKEND_DIR / "models" / "water_potability_model.joblib"
METADATA_FILE = BACKEND_DIR / "models" / "metadata.json"


@pytest.fixture(scope="module")
def model_artifacts():
    """Loads model and metadata once for the test suite."""
    assert MODEL_FILE.exists(), f"Model artifact not found at {MODEL_FILE}"
    assert METADATA_FILE.exists(), f"Metadata artifact not found at {METADATA_FILE}"

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    model = joblib.load(MODEL_FILE)
    return {"model": model, "metadata": metadata}


def test_metadata_structure(model_artifacts):
    metadata = model_artifacts["metadata"]
    assert "model_name" in metadata
    assert "features" in metadata
    assert "feature_order" in metadata
    assert len(metadata["feature_order"]) == 9

    # Verify each feature has valid ranges
    for feat_name, feat_meta in metadata["features"].items():
        assert feat_meta["min"] < feat_meta["max"]
        assert feat_meta["min"] <= feat_meta["median"] <= feat_meta["max"]


def test_model_inference_valid_sample(model_artifacts):
    model = model_artifacts["model"]
    metadata = model_artifacts["metadata"]

    # Construct input DataFrame with median values
    sample_data = {
        feat: [metadata["features"][feat]["median"]]
        for feat in metadata["feature_order"]
    }
    df_sample = pd.DataFrame(sample_data)

    pred = model.predict(df_sample)
    proba = model.predict_proba(df_sample)

    assert pred[0] in [0, 1]
    assert proba.shape == (1, 2)
    assert np.isclose(proba[0].sum(), 1.0, atol=1e-5)
    assert 0.0 <= proba[0][0] <= 1.0
    assert 0.0 <= proba[0][1] <= 1.0


def test_model_robustness_with_missing_values(model_artifacts):
    """
    Ensures that if user omits optional fields (e.g. pH is None/NaN),
    the pipeline's SimpleImputer handles it gracefully without crashing.
    """
    model = model_artifacts["model"]
    metadata = model_artifacts["metadata"]

    # Sample with np.nan for pH and Sulfate (common real-world sensor dropouts)
    sample_data = {
        feat: [np.nan if feat in ["ph", "Sulfate"] else metadata["features"][feat]["mean"]]
        for feat in metadata["feature_order"]
    }
    df_sample = pd.DataFrame(sample_data)

    pred = model.predict(df_sample)
    proba = model.predict_proba(df_sample)

    assert pred[0] in [0, 1]
    assert np.isclose(proba[0].sum(), 1.0, atol=1e-5)
