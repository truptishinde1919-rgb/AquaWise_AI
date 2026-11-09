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
* **🌱 Farmer Dashboard Prototype:** Responsive navigation for farm overview, irrigation, crop scanning, IPM guidance, growth tracking, and the research assistant. Existing prediction/chat routes remain connected; weather and image-classification examples are clearly labeled demos, and farmer profile data is stored only in the current browser.

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

## Research-backed agricultural assistant (RAG)

The chat endpoint first uses OpenAI embeddings and PostgreSQL/pgvector retrieval. If vector retrieval is unavailable or empty, it searches the bundled, CC BY 4.0 Frontiers plant-disease PDF locally and still returns page citations. If OpenAI answer generation is unavailable, the endpoint returns short, directly quoted passages labeled as PDF excerpts rather than implying they are an AI-generated interpretation. The UI shows source details and an evidence note for each cited page. Reported study accuracy must be attributed to the paper and explicitly distinguished from AquaWise model performance. Additional documents must have verified provenance and reuse licenses before ingestion.

### Backend environment

Set these variables in `backend/.env` for local work and in Render's backend service settings for production:

* `OPENAI_API_KEY` — backend-only key used for `text-embedding-3-small` embeddings and `gpt-4o-mini` answers.
* `DATABASE_URL` — PostgreSQL connection string for a database with pgvector available.
* `RAG_MIN_SIMILARITY` — optional cosine-similarity floor for retrieved chunks (default `0.2`).

Do **not** add the OpenAI key to Vercel or any `NEXT_PUBLIC_*` variable. The frontend only needs `NEXT_PUBLIC_API_URL` pointing to the FastAPI service.

### Database setup and PDF ingestion

1. Create a PostgreSQL database with the pgvector extension available. Enable the extension and create the RAG tables/index:

   ```powershell
   psql $env:DATABASE_URL -f backend\sql\rag_schema.sql
   ```

2. Install backend dependencies and configure `backend/.env` with `OPENAI_API_KEY` and `DATABASE_URL`.
3. Create a JSON metadata file using verified details only. Example:

   ```json
   {
     "title": "Verified document title",
     "authors": null,
     "publication_year": null,
     "source_url": null,
     "doi": null,
     "license": null
   }
   ```

4. Ingest a text-based PDF (scanned image-only PDFs are rejected; OCR is not currently included):

   ```powershell
   cd backend
   .\.venv\Scripts\python.exe scripts\ingest_research_pdf.py path\to\paper.pdf --metadata path\to\metadata.json
   ```

The ingester extracts text page-by-page, chunks it, generates embeddings, persists provenance and citations, and rejects duplicate file hashes. It does not download papers automatically. Full-text PDF ingestion currently requires an explicitly verified **CC BY 4.0** license plus verified authors, publication year, and a DOI or source URL; restricted or unspecified licenses fail closed before embedding.

### Live PostgreSQL/pgvector verification

The backend exposes `GET /api/rag/status`. It reports only configuration booleans, readiness state, and corpus counts; it never returns the database URL, host, username, password, or API key. Status values include `unconfigured`, `unavailable`, `pgvector_missing`, `schema_missing`, `empty`, and `ready`.

After configuring `backend/.env`, applying the schema, and starting the backend, run these checks from PowerShell:

```powershell
# Confirm the backend can reach PostgreSQL and sees pgvector, tables, and stored rows.
Invoke-RestMethod http://127.0.0.1:8000/api/rag/status | ConvertTo-Json

# Confirm metadata, page-preserving chunks, generated vector dimensions, and chunk IDs in PostgreSQL.
psql $env:DATABASE_URL -c "SELECT d.id AS document_id, d.title, d.doi, count(c.id) AS chunk_count, min(c.page_number) AS first_page, max(c.page_number) AS last_page, min(vector_dims(c.embedding)) AS min_vector_dimensions, max(vector_dims(c.embedding)) AS max_vector_dimensions FROM research_documents d JOIN research_chunks c ON c.document_id = d.id GROUP BY d.id, d.title, d.doi ORDER BY d.id;"

# Ask a question supported by the ingested paper; use the actual API response to verify
# evidence_used, answer citation markers, and references with matching source_index/page_number.
$body = @{ message = "What dataset did the study use?"; history = @() } | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/chat -Method Post -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 8

# An unrelated question must return evidence_used=false and references=[] when evidence is insufficient.
$body = @{ message = "What is the best pesticide for my crop?"; history = @() } | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/chat -Method Post -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 8
```

Confirm backend logs for the supported question show `document_id`, `chunk_id`, `page_number`, and `similarity`; check that the cited page belongs to the retrieved PDF text and each displayed `source_index` matches an inline answer citation. The SQL result must show at least one document, one chunk, and exactly 1536 vector dimensions. The unsupported question must have no fabricated citations. A healthy status endpoint or passing mocked tests alone does **not** prove successful semantic retrieval. Run these checks against the configured database and OpenAI provider before claiming live RAG acceptance. For Render, call `https://<your-render-service>/api/rag/status` and use the same SQL checks with that service's PostgreSQL database; do not put backend secrets in Vercel.

### Local development and deployment

```powershell
# Backend, from repository root
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Frontend, in a second terminal
cd frontend
npm ci
npm test
npm run build
npm run dev
```

For Render, deploy the existing FastAPI backend as before, add `OPENAI_API_KEY`, `DATABASE_URL`, and optionally `RAG_MIN_SIMILARITY`, then run the SQL schema against the pgvector database and ingest the approved documents. For Vercel, keep the current frontend root and set only `NEXT_PUBLIC_API_URL` to the Render API URL. Existing potability and agricultural prediction routes are unchanged.

If neither the vector corpus nor the bundled PDF contains relevant passages, the chat endpoint returns an explicit no-evidence response. When vector or answer-generation services are unavailable, it may return a clearly labeled extractive PDF response with page citations; this fallback is lexical retrieval, not a substitute for semantic RAG. Automated tests verify actual PDF page text, local fallback ranking, citation excerpts, and mocked provider/database behavior. These tests do not prove that live semantic retrieval works; a configured OpenAI account and PostgreSQL/pgvector instance are required for that validation.

---

## 🛡️ License & Ethics

* **Educational & Demonstration Use:** This software utilizes statistical machine learning. In real municipal or commercial applications, automated predictions must always be paired with certified microbiological laboratory testing (e.g., E. coli cultures).
* **License:** MIT License. Free to use, adapt, and build upon.
