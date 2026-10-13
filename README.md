# 🌊 AquaWise AI — Intelligent Water Potability & Quality Assessment

[![Live Web App](https://img.shields.io/badge/Live%20App-Vercel-black?style=for-the-badge&logo=vercel)](https://aqua-wise-ai.vercel.app)
[![API Backend](https://img.shields.io/badge/API-Render-46E3B7?style=for-the-badge&logo=render)](https://aquawise-ai-backend.onrender.com/docs)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.4-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)

**AquaWise AI** is a full-stack Machine Learning application that assesses drinking water potability and chemical safety using an ensemble Random Forest pipeline trained on real-world Environmental Protection Agency (EPA) water monitoring data.

The project features a decoupled microservices architecture: a high-performance **Python FastAPI** inference engine hosted on **Render** paired with a responsive **Next.js 16 + Tailwind CSS** laboratory dashboard deployed on **Vercel**.

---

## 🔗 Live Deployments & Repository

* 🌐 **Live Web Application:** [https://aqua-wise-ai.vercel.app](https://aqua-wise-ai.vercel.app)
* ⚡ **Interactive Swagger API Docs:** [https://aquawise-ai-backend.onrender.com/docs](https://aquawise-ai-backend.onrender.com/docs)
* 🐙 **GitHub Repository:** [https://github.com/truptishinde1919-rgb/AquaWise_AI](https://github.com/truptishinde1919-rgb/AquaWise_AI)

---

## ✨ Key Features

* **🔬 Interactive Chemical Laboratory:** Real-time sliders with dynamic safe/warning badges for 9 physical and chemical parameters based on official WHO/EPA guidelines.
* **⚡ 1-Click Scenario Presets:** Instantly load benchmark profiles: *Clean Tap Water*, *Pristine Mountain Spring*, *Industrial Runoff*, and *Deep Mineral Well*.
* **🧠 Model Explainability (Feature Drivers):** Computes Gini impurity decrease across 200 decision trees to visualize the exact statistical drivers behind every prediction.
* **🛡️ Zero Data-Leakage Pipeline:** Production `scikit-learn.pipeline.Pipeline` with median imputation prevents 40% data loss from real-world sensor dropouts without leaking test information.
* **☁️ Production Microservices:** Decoupled architecture isolates heavy Python scientific dependencies from lightweight Edge-rendered Next.js frontends.
* **🐳 Containerized:** Multi-stage Dockerfile baking pre-trained model artifacts at build time for fast, deterministic cold starts.

---

## 🏛️ System Architecture

```text
┌─────────────────────────────────┐
│     Next.js 16 Web Dashboard    │
│    (Deployed on Vercel Edge)    │
│     https://aqua-wise-ai.vercel.app    │
└────────────────┬────────────────┘
                 │  HTTPS / JSON
                 ▼
┌─────────────────────────────────┐
│       FastAPI REST Service      │
│      (Container on Render)      │
│   https://aquawise-ai-backend...│
└────────────────┬────────────────┘
                 │  In-Memory Inference
                 ▼
┌─────────────────────────────────┐
│     scikit-learn Pipeline       │
│  [SimpleImputer] → [StandardScaler] │
│      → [RandomForestClassifier] │
└─────────────────────────────────┘
```

---

## 🔬 Machine Learning Pipeline & Data Science

### 1. The Dataset
* **Source:** Verifiable benchmark dataset based on global municipal and natural water monitoring initiatives.
* **Total Samples:** `3,276` water bodies.
* **Class Balance:**
  * `0 (Not Potable / Unsafe)`: 1,998 samples (60.99%)
  * `1 (Potable / Safe to Drink)`: 1,278 samples (39.01%)

### 2. Missing Value Imputation Strategy
In raw sensor data, chemical measurements often experience sensor dropouts:
* **pH:** 14.99% missing (491 rows)
* **Sulfate:** 23.84% missing (781 rows)
* **Trihalomethanes:** 4.95% missing (162 rows)

> **Why NOT `df.dropna()`?** Dropping missing rows removes ~40% of the dataset, causing severe statistical bias.  
> **Solution:** A `SimpleImputer(strategy='median')` step inside the scikit-learn pipeline learns medians strictly from the 80% training split, preventing data leakage into the test set and live API requests.

### 3. Model Benchmark Results (20% Stratified Holdout Test Set)

| Model Candidate | Test Accuracy | Precision | Recall | F1-Score | ROC-AUC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **RandomForestClassifier** 🏆 | **65.85%** | **57.92%** | **45.70%** | **51.09%** | **0.6708** |
| **HistGradientBoostingClassifier** | 64.63% | 57.32% | 36.72% | 44.76% | 0.6250 |

### 4. Model Explainability — Top Feature Drivers

Computed via Mean Decrease in Impurity (MDI) across 200 decision trees:

| Rank | Water Parameter | Statistical Influence | Safe WHO/EPA Guideline |
| :---: | :--- | :---: | :--- |
| **1** | **Sulfate** | **15.59%** | $\le 250\text{ mg/L}$ |
| **2** | **pH** | **14.44%** | $6.5 - 8.5\text{ pH}$ |
| **3** | **Hardness** | **12.35%** | $\le 250\text{ mg/L}$ |
| **4** | **Chloramines** | **11.37%** | $\le 4.0\text{ ppm}$ |
| **5** | **Solids (TDS)** | **11.17%** | $\le 1,000\text{ ppm}$ |
| **6** | **Conductivity** | **9.37%** | $\le 400\text{ }\mu\text{S/cm}$ |
| **7** | **Organic Carbon** | **8.68%** | $\le 4.0\text{ ppm}$ |
| **8** | **Trihalomethanes** | **8.56%** | $\le 80\text{ }\mu\text{g/L}$ |
| **9** | **Turbidity** | **8.47%** | $\le 5.0\text{ NTU}$ |

---

## 📁 Project Directory Structure

```text
AquaWise_AI/
├── .gitignore                         # Excludes .venv, node_modules, and secrets
├── .env.example                       # Safe environment variables template
├── render.yaml                        # Infrastructure-as-code for Render cloud
├── README.md                          # Project documentation
│
├── backend/                           # Python ML & REST API
│   ├── Dockerfile                     # Python 3.11-slim production container
│   ├── .dockerignore
│   ├── requirements.txt               # fastapi, scikit-learn, pandas, numpy, uvicorn
│   ├── data/raw/water_potability.csv  # Canonical benchmark dataset (3,276 rows)
│   ├── ml/
│   │   ├── data_loader.py             # Schema validation & missing value EDA
│   │   └── train.py                   # Stratified training, evaluation & export
│   ├── models/
│   │   ├── water_potability_model.joblib  # Serialized ML pipeline artifact
│   │   └── metadata.json              # Distribution bounds & feature importances
│   ├── app/
│   │   ├── main.py                    # FastAPI server & CORS middleware
│   │   └── schemas.py                 # Pydantic bounds validation schemas
│   └── tests/                         # Automated test suite (10/10 passing)
│       ├── test_api.py                # Health & prediction endpoint tests
│       └── test_ml_pipeline.py        # Model loading & sanity checks
│
└── frontend/                          # Next.js Web Dashboard
    ├── package.json                   # Next.js 16, React 19, Tailwind CSS
    ├── .env.local                     # NEXT_PUBLIC_API_URL
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx               # Main interactive dashboard
    │   │   ├── layout.tsx             # Root layout & SEO metadata
    │   │   └── api/                   # Route proxies (/api/predict, /api/health)
    │   ├── components/                # Sliders, presets, result gauges, metrics
    │   └── types/water.ts             # TypeScript data contracts
```

---

## 💻 Local Development Setup (Windows)

### Prerequisites
* **Python:** `3.11+`
* **Node.js:** `18+` (v20 or v24 recommended)
* **Git**

---

### Step 1: Clone the Repository
```powershell
git clone https://github.com/truptishinde1919-rgb/AquaWise_AI.git
cd AquaWise_AI
```

---

### Step 2: Start the Python FastAPI Backend

Open PowerShell:
```powershell
# 1. Navigate to backend
cd backend

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Train model artifacts (takes ~10 seconds)
python ml\train.py

# 5. Start development server
uvicorn app.main:app --reload --port 8000
```

1. 🌐 See Your Live Public Website (For Anyone in the World)

Anyone on a phone, laptop, or tablet can access your live project:

Live Frontend Website: 👉 https://aqua-wise-ai.vercel.app

(or https://aqua-wise-da359h3lv-truptii-projects.vercel.app
)

You can share this link on your LinkedIn, resume, or with friends and recruiters!

### Step 3: Run the Test Suite

In your backend terminal:
```powershell
pytest tests -v
```
Output:
```text
======================== 10 passed in 2.72s ========================
```

---

### Step 4: Start the Next.js Frontend

Open a **second** PowerShell tab:
```powershell
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

Open your browser to:
👉 **[http://localhost:3000](http://localhost:3000)**

---

## 📡 API Reference

### 1. Health Diagnostic
* **`GET /health`** (or `/api/health`)
* **Response:**
  ```json
  {
    "status": "healthy",
    "model_loaded": true,
    "model_name": "RandomForestClassifier",
    "environment": "production"
  }
  ```

### 2. Model & Feature Metadata
* **`GET /api/metadata`**
* Returns numerical distributions (min, max, median, quartiles), EPA thresholds, and feature importance percentages for all 9 parameters.

### 3. Potability Prediction
* **`POST /api/predict`**
* **Request Body:**
  ```json
  {
    "ph": 7.35,
    "Hardness": 182.0,
    "Solids": 15400.0,
    "Chloramines": 3.4,
    "Sulfate": 235.0,
    "Conductivity": 360.0,
    "Organic_carbon": 2.8,
    "Trihalomethanes": 52.0,
    "Turbidity": 2.2
  }
  ```
* **Response:**
  ```json
  {
    "is_potable": true,
    "potability_label": "Potable (Safe to Drink)",
    "potability_probability": 0.716,
    "non_potability_probability": 0.284,
    "confidence_score": 71.6,
    "water_quality_grade": "High Quality / Potable",
    "top_drivers": ["Sulfate", "ph", "Hardness"],
    "parameter_evaluations": [...],
    "warnings": []
  }
  ```

---

## ☁️ Deployment Instructions

### Deploying the Backend on Render
1. Connect your GitHub repository on [dashboard.render.com](https://dashboard.render.com/).
2. Select **Web Service** $\rightarrow$ `backend`.
3. Set **Runtime:** `Python 3` (or `Docker`).
4. Set **Build Command:** `pip install -r requirements.txt && python ml/train.py`
5. Set **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Set **Plan:** `Free`.

### Deploying the Frontend on Vercel
1. Import your GitHub repository on [vercel.com/new](https://vercel.com/new).
2. Set **Root Directory** to `frontend`.
3. Add Environment Variable:
   * **Key:** `NEXT_PUBLIC_API_URL`
   * **Value:** Your live Render URL (e.g. `https://aquawise-ai-backend.onrender.com`).
4. Click **Deploy**.

---

## 🛡️ License & Ethics

* **Educational & Demonstration Use:** This software utilizes statistical machine learning. In real municipal or commercial applications, automated predictions must always be paired with certified microbiological laboratory testing (e.g., E. coli cultures).
* **License:** MIT License. Free to use, adapt, and build upon.
