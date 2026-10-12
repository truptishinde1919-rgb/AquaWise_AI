# 🌊 AquaWise AI — Intelligent Water Potability & Quality Assessment

AquaWise AI is a full-stack Machine Learning application designed to predict drinking water potability based on chemical and physical water quality metrics (pH, Hardness, Solids, Chloramines, Sulfate, Conductivity, Organic Carbon, Trihalomethanes, and Turbidity).

Built with a decoupled microservices architecture:
* **Backend:** Python 3.13, **FastAPI**, **scikit-learn**, **pandas**, and **NumPy**.
* **Frontend:** **Next.js** (App Router), **TypeScript**, and **Tailwind CSS**, optimized for **Vercel** deployment.

---

## 🏛️ System Architecture

```text
AquaWise_AI/
├── backend/                       # Python Machine Learning & API Service
│   ├── .venv/                     # Isolated virtual environment
│   ├── data/raw/                  # Real EPA Water Potability dataset (3,276 rows)
│   ├── ml/
│   │   ├── data_loader.py         # Data validation, EDA & missing value inspection
│   │   └── train.py               # Pipeline training, cross-validation & artifact export
│   ├── models/
│   │   ├── water_potability_model.joblib  # Serialized scikit-learn pipeline (Imputer + Scaler + RF)
│   │   └── metadata.json          # Statistical distributions & EPA guideline thresholds
│   ├── app/
│   │   ├── main.py                # FastAPI endpoints (/health, /metadata, /predict)
│   │   └── schemas.py             # Pydantic request/response models with bounds validation
│   ├── tests/                     # Automated pytest suite (9 tests)
│   └── requirements.txt
│
└── frontend/                      # Next.js Web Dashboard (Vercel-ready)
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx           # Interactive water quality lab dashboard
    │   │   ├── layout.tsx         # Responsive root layout & metadata
    │   │   └── api/
    │   │       ├── predict/       # Route handler proxying inference to FastAPI
    │   │       └── health/        # Real-time backend connectivity check
    │   ├── components/            # UI components (sliders, presets, verdict gauges)
    │   └── types/                 # TypeScript data contracts
    ├── .env.local                 # Local environment config (NEXT_PUBLIC_API_URL)
    └── package.json
```

---

## 🔬 Machine Learning Pipeline Details

### 1. The Dataset
* **Source:** Verifiable benchmark based on EPA drinking water standards and Kaggle's Water Quality dataset.
* **Volume:** 3,276 water samples.
* **Class Balance:**
  * `0 (Non-Potable)`: 1,998 samples (60.99%)
  * `1 (Potable)`: 1,278 samples (39.01%)

### 2. Handling Missing Values Without Data Leakage
Three key parameters have real-world missing sensor entries:
* `ph`: 14.99% missing
* `Sulfate`: 23.84% missing
* `Trihalomethanes`: 4.95% missing

> **Why we don't use `df.dropna()`:** Dropping missing rows would delete ~40% of the dataset.
> **How we prevent data leakage:** We wrap a `SimpleImputer(strategy='median')` inside a `sklearn.pipeline.Pipeline`. The imputer learns medians **only** from the training split, and applies them seamlessly to test sets and live API queries.

### 3. Model Benchmark Results
Evaluated on a stratified 20% holdout test set (656 samples):

| Model Candidate | Test Accuracy | Precision | Recall | F1-Score | ROC-AUC |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RandomForestClassifier** 🏆 | **65.85%** | **57.92%** | **45.70%** | **51.09%** | **0.6708** |
| **HistGradientBoosting** | 64.63% | 57.32% | 36.72% | 44.76% | 0.6250 |

---

## 🚀 Running the Project Locally (Windows)

### Prerequisites
* Python 3.10+ (tested on Python 3.13)
* Node.js 18+ (tested on Node.js 24)
* PowerShell or Windows Terminal

---

### Step 1: Start the Python FastAPI Backend

Open a PowerShell terminal in the project root:

```powershell
# 1. Navigate to backend
cd backend

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Train or verify model artifacts (takes ~10 seconds)
python ml\train.py

# 4. Start the FastAPI development server
uvicorn app.main:app --reload --port 8000
```

The API will now be live:
* **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
* **Dataset Metadata:** [http://127.0.0.1:8000/api/metadata](http://127.0.0.1:8000/api/metadata)

---

### Step 2: Run the Backend Test Suite

In your backend terminal:

```powershell
pytest tests -v
```
All 9 unit and integration tests should pass.

---

### Step 3: Start the Next.js Frontend

Open a **second** PowerShell terminal in the project root:

```powershell
# 1. Navigate to frontend
cd frontend

# 2. Start development server
npm run dev
```

Open your browser to:
👉 **[http://localhost:3000](http://localhost:3000)**

---

## 🌐 Deploying to Production (Vercel + Cloud Backend)

### 1. Deploying Frontend on Vercel
1. Push your repository to GitHub.
2. In the [Vercel Dashboard](https://vercel.com/), click **Add New Project** and import your repository.
3. In **Root Directory**, click Edit and select `frontend`.
4. In **Environment Variables**, add:
   * `NEXT_PUBLIC_API_URL`: Your deployed backend URL (e.g. `https://aquawise-backend.onrender.com`).
5. Click **Deploy**.

### 2. Deploying Backend (e.g. on Render / Railway / Hugging Face Spaces)
Because Vercel serverless functions have bundle size limits for heavy scientific Python wheels (`scipy`, `scikit-learn`, `pandas`), host the FastAPI backend on a container-friendly platform:
* **Build Command:** `pip install -r backend/requirements.txt && python backend/ml/train.py`
* **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
* **Root Directory:** `backend`
* **Environment Variable:** `CORS_ORIGINS=https://your-app.vercel.app`

---

## 🛡️ Security & Secrets
* No sensitive secrets or production API keys are committed to Git.
* Copy `.env.example` to `.env` (backend) or `.env.local` (frontend) when customizing local ports or origins.
