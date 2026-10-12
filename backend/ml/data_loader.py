"""
data_loader.py
==============
Module responsible for downloading, loading, and inspecting the real
Water Potability dataset.

Dataset Source:
- Environmental Protection Agency (EPA) / Kaggle Water Quality Benchmark
- 3,276 water samples evaluating safety for human consumption.
"""

from pathlib import Path
import urllib.request
import sys
import pandas as pd
import numpy as np

# Ensure Windows PowerShell/CMD does not crash on non-ASCII characters
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Canonical dataset URL
DATASET_URL = "https://raw.githubusercontent.com/fenago/datasets/main/water_potability.csv"

# Project path resolution
BACKEND_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BACKEND_DIR / "data" / "raw"
DATASET_FILE = RAW_DATA_DIR / "water_potability.csv"

FEATURE_NAMES = [
    "ph",
    "Hardness",
    "Solids",
    "Chloramines",
    "Sulfate",
    "Conductivity",
    "Organic_carbon",
    "Trihalomethanes",
    "Turbidity",
]
TARGET_NAME = "Potability"


def ensure_dataset_exists() -> Path:
    """
    Downloads the real dataset if it doesn't already exist locally.
    Saves it under backend/data/raw/water_potability.csv.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATASET_FILE.exists():
        print(f"[DOWNLOAD] Downloading dataset from:\n   {DATASET_URL}")
        try:
            urllib.request.urlretrieve(DATASET_URL, DATASET_FILE)
            print(f"[SUCCESS] Download complete! Saved to:\n   {DATASET_FILE}")
        except Exception as e:
            raise RuntimeError(
                f"Failed to download dataset: {e}\n"
                "Please verify your internet connection."
            ) from e
    else:
        print(f"[INFO] Dataset already exists at:\n   {DATASET_FILE}")
    return DATASET_FILE


def load_raw_data() -> pd.DataFrame:
    """
    Loads raw CSV data into a pandas DataFrame and validates expected schema.
    """
    csv_path = ensure_dataset_exists()
    df = pd.read_csv(csv_path)

    expected_cols = set(FEATURE_NAMES + [TARGET_NAME])
    actual_cols = set(df.columns)
    if not expected_cols.issubset(actual_cols):
        missing = expected_cols - actual_cols
        raise ValueError(f"Dataset missing required columns: {missing}")

    return df


def inspect_data(df: pd.DataFrame) -> dict:
    """
    Computes summary metrics to understand dataset health:
    - Missing value percentages
    - Class balance (Potable vs Non-Potable)
    - Basic feature distribution
    """
    total_samples = len(df)
    missing_counts = df.isnull().sum()
    missing_pct = (missing_counts / total_samples * 100).round(2)

    missing_report = {
        col: {"missing_count": int(missing_counts[col]), "missing_pct": float(missing_pct[col])}
        for col in df.columns
        if missing_counts[col] > 0
    }

    target_dist = df[TARGET_NAME].value_counts().to_dict()
    target_pct = (df[TARGET_NAME].value_counts(normalize=True) * 100).round(2).to_dict()

    summary = {
        "total_rows": total_samples,
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "target_distribution": {
            "0 (Not Potable)": {
                "count": int(target_dist.get(0, 0)),
                "pct": float(target_pct.get(0, 0.0)),
            },
            "1 (Potable)": {
                "count": int(target_dist.get(1, 0)),
                "pct": float(target_pct.get(1, 0.0)),
            },
        },
        "missing_features": missing_report,
    }
    return summary


if __name__ == "__main__":
    print("=" * 60)
    print(">> AquaWise AI - Exploratory Data Analysis & Validation")
    print("=" * 60)

    df = load_raw_data()
    summary = inspect_data(df)

    print(f"\n[DATA SUMMARY] Total Samples: {summary['total_rows']}")
    print(f"[DATA SUMMARY] Features: {len(FEATURE_NAMES)} input parameters, 1 binary target ({TARGET_NAME})")

    print("\n[CLASS DISTRIBUTION]")
    for label, stats in summary["target_distribution"].items():
        print(f"   - {label}: {stats['count']} samples ({stats['pct']}%)")

    print("\n[MISSING VALUES DETECTED]")
    for feature, stats in summary["missing_features"].items():
        print(
            f"   - {feature:16s}: {stats['missing_count']} missing "
            f"({stats['missing_pct']}%)"
        )

    print("\n[MENTOR INSIGHT ON MISSING VALUES]")
    print(
        "   Notice that 'ph', 'Sulfate', and 'Trihalomethanes' have significant missing values."
    )
    print(
        "   If we simply dropped missing rows (dropna()), we would lose ~40% of our real data!"
    )
    print(
        "   Instead, in our training pipeline, we will use median imputation (SimpleImputer)"
    )
    print(
        "   fitted ONLY on the training split to avoid data leakage."
    )
    print("=" * 60)
