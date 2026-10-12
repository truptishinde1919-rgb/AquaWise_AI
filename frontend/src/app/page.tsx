"use client";

import React, { useState, useEffect } from "react";
import { WaterParameters, PredictionResponse, ModelMetadata, FeatureMeta } from "@/types/water";
import { ParameterSlider } from "@/components/ParameterSlider";
import { PresetSelector, PRESETS } from "@/components/PresetSelector";
import { PredictionResultCard } from "@/components/PredictionResultCard";
import { ModelInfoCard } from "@/components/ModelInfoCard";
import { DropletIcon, SlidersIcon, RefreshCwIcon } from "@/components/icons";

// Static fallback features so UI is instantly functional even before API responds
const DEFAULT_FEATURES: Record<string, FeatureMeta> = {
  ph: {
    name: "ph",
    unit: "pH",
    description: "Acidity / Alkalinity level (0 to 14)",
    min: 0.0,
    max: 14.0,
    mean: 7.08,
    median: 7.04,
    q25: 6.09,
    q75: 8.06,
    safe_min: 6.5,
    safe_max: 8.5,
  },
  Hardness: {
    name: "Hardness",
    unit: "mg/L",
    description: "Capacity of water to precipitate soap",
    min: 47.0,
    max: 325.0,
    mean: 196.37,
    median: 196.97,
    q25: 176.85,
    q75: 216.67,
    safe_min: 0.0,
    safe_max: 250.0,
  },
  Solids: {
    name: "Solids",
    unit: "ppm",
    description: "Total Dissolved Solids (TDS)",
    min: 320.0,
    max: 61250.0,
    mean: 22014.09,
    median: 20927.83,
    q25: 15666.7,
    q75: 27332.8,
    safe_min: 0.0,
    safe_max: 1000.0,
  },
  Chloramines: {
    name: "Chloramines",
    unit: "ppm",
    description: "Chloramine disinfectant concentration",
    min: 0.35,
    max: 13.5,
    mean: 7.12,
    median: 7.13,
    q25: 6.13,
    q75: 8.11,
    safe_min: 0.0,
    safe_max: 4.0,
  },
  Sulfate: {
    name: "Sulfate",
    unit: "mg/L",
    description: "Naturally occurring mineral salts",
    min: 129.0,
    max: 482.0,
    mean: 333.78,
    median: 333.07,
    q25: 307.7,
    q75: 359.95,
    safe_min: 0.0,
    safe_max: 250.0,
  },
  Conductivity: {
    name: "Conductivity",
    unit: "μS/cm",
    description: "Electrical conductivity",
    min: 180.0,
    max: 755.0,
    mean: 426.21,
    median: 421.88,
    q25: 365.73,
    q75: 481.79,
    safe_min: 0.0,
    safe_max: 400.0,
  },
  Organic_carbon: {
    name: "Organic_carbon",
    unit: "ppm",
    description: "Total Organic Carbon (TOC)",
    min: 2.2,
    max: 28.5,
    mean: 14.28,
    median: 14.22,
    q25: 12.07,
    q75: 16.56,
    safe_min: 0.0,
    safe_max: 4.0,
  },
  Trihalomethanes: {
    name: "Trihalomethanes",
    unit: "μg/L",
    description: "Chlorine disinfection by-products",
    min: 0.7,
    max: 124.0,
    mean: 66.4,
    median: 66.4,
    q25: 55.84,
    q75: 77.34,
    safe_min: 0.0,
    safe_max: 80.0,
  },
  Turbidity: {
    name: "Turbidity",
    unit: "NTU",
    description: "Suspended particle cloudiness",
    min: 1.4,
    max: 6.8,
    mean: 3.97,
    median: 3.95,
    q25: 3.44,
    q75: 4.5,
    safe_min: 0.0,
    safe_max: 5.0,
  },
};

const INITIAL_PARAMS: WaterParameters = {
  ph: 7.35,
  Hardness: 182.0,
  Solids: 15400.0,
  Chloramines: 3.4,
  Sulfate: 235.0,
  Conductivity: 360.0,
  Organic_carbon: 2.8,
  Trihalomethanes: 52.0,
  Turbidity: 2.2,
};

export default function Home() {
  const [params, setParams] = useState<WaterParameters>(INITIAL_PARAMS);
  const [activePresetId, setActivePresetId] = useState<string | null>("tap_water");
  const [metadata, setMetadata] = useState<ModelMetadata | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  // Fetch initial model metadata and check backend health
  useEffect(() => {
    async function checkBackend() {
      try {
        const healthRes = await fetch("/api/health");
        const healthData = await healthRes.json();
        setBackendOnline(healthData.status === "connected");

        // Fetch rich metadata directly if backend is online
        const metaRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/api/metadata`);
        if (metaRes.ok) {
          const metaData = await metaRes.json();
          setMetadata(metaData);
        }
      } catch {
        setBackendOnline(false);
      }
    }
    checkBackend();
  }, []);

  const handleParamChange = (name: keyof WaterParameters, val: number) => {
    setActivePresetId(null);
    setParams((prev) => ({ ...prev, [name]: val }));
  };

  const handleSelectPreset = (values: WaterParameters) => {
    setParams(values);
    const matched = PRESETS.find((p) => JSON.stringify(p.values) === JSON.stringify(values));
    setActivePresetId(matched?.id || null);
  };

  const handleResetToMedian = () => {
    const medians: Partial<WaterParameters> = {};
    for (const [k, meta] of Object.entries(DEFAULT_FEATURES)) {
      medians[k as keyof WaterParameters] = meta.median;
    }
    setParams(medians as WaterParameters);
    setActivePresetId(null);
  };

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });

      if (!res.ok) {
        const errorBody = await res.json().catch(() => ({}));
        throw new Error(errorBody.detail || `Server responded with HTTP ${res.status}`);
      }

      const data: PredictionResponse = await res.json();
      setPrediction(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Inference request failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  // Trigger initial prediction on page mount
  useEffect(() => {
    handleAnalyze();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const featureList = metadata?.features || DEFAULT_FEATURES;
  const orderedKeys = metadata?.feature_order || Object.keys(DEFAULT_FEATURES);

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 antialiased selection:bg-blue-500 selection:text-white">
      {/* Top Header */}
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
              <DropletIcon className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold tracking-tight">AquaWise AI</h1>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                  v1.0 ML
                </span>
              </div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Machine Learning Water Potability &amp; Quality Assessment Platform
              </p>
            </div>
          </div>

          {/* Backend Connectivity Status */}
          <div className="flex items-center gap-2 text-xs">
            <span
              className={`inline-block w-2.5 h-2.5 rounded-full ${
                backendOnline === true
                  ? "bg-emerald-500 ring-4 ring-emerald-500/20"
                  : backendOnline === false
                  ? "bg-rose-500 ring-4 ring-rose-500/20"
                  : "bg-zinc-400 animate-pulse"
              }`}
            />
            <span className="hidden sm:inline text-zinc-600 dark:text-zinc-300 font-medium">
              {backendOnline === true
                ? "FastAPI ML Backend: Connected"
                : backendOnline === false
                ? "FastAPI ML Backend: Offline"
                : "Connecting..."}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Scenario Presets Bar */}
        <PresetSelector onSelectPreset={handleSelectPreset} activePresetId={activePresetId} />

        {/* Workspace Split Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Interactive Chemical & Physical Sliders */}
          <section className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <SlidersIcon className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <h2 className="text-sm font-bold text-zinc-900 dark:text-zinc-100">
                  Water Chemical &amp; Physical Parameters
                </h2>
              </div>
              <button
                onClick={handleResetToMedian}
                className="text-xs text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200 flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
              >
                <RefreshCwIcon className="w-3 h-3" />
                Reset to Median
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {orderedKeys.map((key) => {
                const meta = featureList[key];
                if (!meta) return null;
                return (
                  <ParameterSlider
                    key={key}
                    meta={meta}
                    value={params[key as keyof WaterParameters] ?? meta.median}
                    onChange={(val) => handleParamChange(key as keyof WaterParameters, val)}
                  />
                );
              })}
            </div>
          </section>

          {/* Right Column: CTA Button, Prediction Verdict & Model Info */}
          <section className="lg:col-span-5 space-y-5 sticky top-20">
            {/* Action Button */}
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="w-full py-3.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 disabled:opacity-50 text-white font-semibold text-sm shadow-md shadow-blue-600/20 hover:shadow-lg hover:shadow-blue-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Evaluating Potability...</span>
                </>
              ) : (
                <>
                  <DropletIcon className="w-4 h-4" />
                  <span>Analyze Potability with ML</span>
                </>
              )}
            </button>

            {/* Prediction Result Display */}
            <PredictionResultCard result={prediction} loading={loading} error={error} />

            {/* Model Architecture & Benchmark Insights */}
            <ModelInfoCard metadata={metadata} />
          </section>
        </div>
      </main>
    </div>
  );
}
