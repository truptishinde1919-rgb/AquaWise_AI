"""
train.py
========
Machine learning pipeline training, cross-validation, evaluation,
and serialization for AquaWise AI.

Key Steps:
1. Stratified Train/Test Split (preserves 61/39 class ratio).
2. Pipeline Construction:
   - Median Imputation (prevents ~40% data loss from missing values).
   - Standardization (scales features to mean=0, std=1).
   - Model Candidates: RandomForest vs HistGradientBoosting.
3. Metric Evaluation: Accuracy, Precision, Recall, F1, ROC-AUC.
4. Export: Serialized pipeline (.joblib) and domain metadata (.json).
"""

from pathlib import Path
import json
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Ensure UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "models"
MODEL_FILE = MODELS_DIR / "water_potability_model.joblib"
METADATA_FILE = MODELS_DIR / "metadata.json"

# Import data loader
sys.path.insert(0, str(BACKEND_DIR))
from ml.data_loader import load_raw_data, FEATURE_NAMES, TARGET_NAME

# EPA/WHO recommended water parameter thresholds & units for UI guidance
EPA_STANDARDS = {
    "ph": {
        "unit": "pH",
        "description": "Acidity / Alkalinity level",
        "safe_min": 6.5,
        "safe_max": 8.5,
    },
    "Hardness": {
        "unit": "mg/L",
        "description": "Capacity of water to precipitate soap",
        "safe_min": 0.0,
        "safe_max": 250.0,
    },
    "Solids": {
        "unit": "ppm",
        "description": "Total Dissolved Solids (TDS)",
        "safe_min": 0.0,
        "safe_max": 1000.0,
    },
    "Chloramines": {
        "unit": "ppm",
        "description": "Chloramine disinfectant concentration",
        "safe_min": 0.0,
        "safe_max": 4.0,
    },
    "Sulfate": {
        "unit": "mg/L",
        "description": "Naturally occurring mineral salts",
        "safe_min": 0.0,
        "safe_max": 250.0,
    },
    "Conductivity": {
        "unit": "μS/cm",
        "description": "Electrical conductivity",
        "safe_min": 0.0,
        "safe_max": 400.0,
    },
    "Organic_carbon": {
        "unit": "ppm",
        "description": "Total Organic Carbon (TOC)",
        "safe_min": 0.0,
        "safe_max": 4.0,
    },
    "Trihalomethanes": {
        "unit": "μg/L",
        "description": "By-products of chlorine treatment",
        "safe_min": 0.0,
        "safe_max": 80.0,
    },
    "Turbidity": {
        "unit": "NTU",
        "description": "Cloudiness caused by suspended particles",
        "safe_min": 0.0,
        "safe_max": 5.0,
    },
}


def compute_feature_statistics(df: pd.DataFrame) -> dict:
    """
    Computes distribution statistics (min, max, mean, median, 25%, 75%)
    for each feature to power interactive frontend sliders and default values.
    """
    stats = {}
    for feature in FEATURE_NAMES:
        series = df[feature].dropna()
        epa = EPA_STANDARDS.get(feature, {})
        stats[feature] = {
            "name": feature,
            "unit": epa.get("unit", ""),
            "description": epa.get("description", ""),
            "min": round(float(series.min()), 2),
            "max": round(float(series.max()), 2),
            "mean": round(float(series.mean()), 2),
            "median": round(float(series.median()), 2),
            "q25": round(float(series.quantile(0.25)), 2),
            "q75": round(float(series.quantile(0.75)), 2),
            "safe_min": epa.get("safe_min", 0.0),
            "safe_max": epa.get("safe_max", 0.0),
        }
    return stats


def train_and_evaluate():
    """
    Orchestrates end-to-end training, candidate comparison, and export.
    """
    print("=" * 65)
    print(">> AquaWise AI - Model Training & Evaluation Pipeline")
    print("=" * 65)

    # 1. Load dataset
    df = load_raw_data()
    X = df[FEATURE_NAMES]
    y = df[TARGET_NAME]

    # 2. Stratified Train-Test Split (80% train / 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"\n[DATA SPLIT] Training set: {len(X_train)} samples | Test set: {len(X_test)} samples")

    # 3. Define candidate pipelines
    # Candidate A: Random Forest with class balancing
    rf_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("classifier", RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=4,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )),
    ])

    # Candidate B: Histogram-based Gradient Boosting
    hgb_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("classifier", HistGradientBoostingClassifier(
            max_iter=150,
            learning_rate=0.08,
            max_depth=8,
            random_state=42
        )),
    ])

    candidates = {
        "RandomForestClassifier": rf_pipeline,
        "HistGradientBoostingClassifier": hgb_pipeline,
    }

    best_name = None
    best_pipeline = None
    best_score = -1.0
    evaluation_results = {}

    print("\n[TRAINING & EVALUATION]")
    for name, pipeline in candidates.items():
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc = roc_auc_score(y_test, y_proba)

        evaluation_results[name] = {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "roc_auc": round(float(roc), 4),
        }

        print(f"\n   Model: {name}")
        print(f"   - Accuracy : {acc:.4f}")
        print(f"   - Precision: {prec:.4f}")
        print(f"   - Recall   : {rec:.4f}")
        print(f"   - F1-Score : {f1:.4f}")
        print(f"   - ROC-AUC  : {roc:.4f}")

        # Choose best model primarily based on ROC-AUC
        if roc > best_score:
            best_score = roc
            best_name = name
            best_pipeline = pipeline

    print(f"\n[BEST MODEL SELECTED] {best_name} (ROC-AUC: {best_score:.4f})")

    # 4. Serialize model and export metadata
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipeline, MODEL_FILE)
    print(f"[EXPORT] Saved serialized pipeline to:\n         {MODEL_FILE}")

    feature_stats = compute_feature_statistics(df)
    metadata = {
        "model_name": best_name,
        "primary_metric": "roc_auc",
        "roc_auc": evaluation_results[best_name]["roc_auc"],
        "metrics": evaluation_results[best_name],
        "all_candidate_metrics": evaluation_results,
        "features": feature_stats,
        "feature_order": FEATURE_NAMES,
        "target": {
            "name": TARGET_NAME,
            "classes": {0: "Not Potable", 1: "Potable"},
        },
    }

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[EXPORT] Saved model & feature metadata to:\n         {METADATA_FILE}")
    print("=" * 65)

    return best_pipeline, metadata


if __name__ == "__main__":
    train_and_evaluate()
