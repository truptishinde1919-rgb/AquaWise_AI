"use client";

import React from "react";
import { PredictionResponse } from "@/types/water";
import {
  DropletIcon,
  AlertTriangleIcon,
  CheckCircleIcon,
  ShieldCheckIcon,
  InfoIcon,
} from "./icons";

interface PredictionResultCardProps {
  result: PredictionResponse | null;
  loading: boolean;
  error: string | null;
}

export function PredictionResultCard({
  result,
  loading,
  error,
}: PredictionResultCardProps) {
  if (loading) {
    return (
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-8 shadow-sm flex flex-col items-center justify-center text-center min-h-[320px]">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
        <h4 className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm">
          Analyzing Water Sample...
        </h4>
        <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 max-w-xs">
          Computing feature vectors, scaling inputs, and running RandomForest decision trees.
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl p-6 shadow-sm">
        <div className="flex items-start gap-3">
          <AlertTriangleIcon className="w-6 h-6 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-rose-900 dark:text-rose-200 text-sm">
              Inference Request Failed
            </h4>
            <p className="text-xs text-rose-700 dark:text-rose-300 mt-1 font-mono">
              {error}
            </p>
            <p className="text-xs text-rose-600 dark:text-rose-400 mt-2">
              Please ensure your FastAPI backend is running locally on port 8000:
              <br />
              <code className="bg-rose-100 dark:bg-rose-900/60 px-1.5 py-0.5 rounded text-[11px] mt-1 inline-block">
                backend\.venv\Scripts\uvicorn.exe app.main:app --reload
              </code>
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-8 shadow-sm flex flex-col items-center justify-center text-center min-h-[320px]">
        <DropletIcon className="w-12 h-12 text-blue-500/40 mb-3" />
        <h4 className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm">
          No Prediction Yet
        </h4>
        <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 max-w-sm">
          Adjust the chemical parameter sliders or click one of the quick presets above, then click <strong>&quot;Analyze Potability&quot;</strong>.
        </p>
      </div>
    );
  }

  const isPotable = result.is_potable;
  const potablePercent = Math.round(result.potability_probability * 100);
  const nonPotablePercent = 100 - potablePercent;

  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-6 shadow-sm space-y-6">
      {/* Top Banner / Verdict */}
      <div
        className={`rounded-xl p-5 border flex items-center justify-between ${
          isPotable
            ? "bg-emerald-50/80 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800"
            : "bg-rose-50/80 dark:bg-rose-950/40 border-rose-300 dark:border-rose-800"
        }`}
      >
        <div className="flex items-center gap-3.5">
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              isPotable
                ? "bg-emerald-600 text-white"
                : "bg-rose-600 text-white"
            }`}
          >
            {isPotable ? (
              <ShieldCheckIcon className="w-7 h-7" />
            ) : (
              <AlertTriangleIcon className="w-7 h-7" />
            )}
          </div>
          <div>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              AI Decision Verdict
            </span>
            <h3
              className={`text-xl font-bold ${
                isPotable
                  ? "text-emerald-900 dark:text-emerald-200"
                  : "text-rose-900 dark:text-rose-200"
              }`}
            >
              {result.potability_label}
            </h3>
            <span className="text-xs font-medium text-zinc-600 dark:text-zinc-300">
              Quality Grade: <span className="font-semibold">{result.water_quality_grade}</span>
            </span>
          </div>
        </div>

        <div className="text-right">
          <div className="text-2xl font-black font-mono text-zinc-900 dark:text-zinc-100">
            {result.confidence_score}%
          </div>
          <span className="text-[10px] uppercase font-semibold text-zinc-500 dark:text-zinc-400">
            Model Confidence
          </span>
        </div>
      </div>

      {/* Probability Distribution Bar */}
      <div>
        <div className="flex justify-between items-center text-xs font-medium mb-1.5 text-zinc-700 dark:text-zinc-300">
          <span>Potable Probability: {potablePercent}%</span>
          <span>Non-Potable Probability: {nonPotablePercent}%</span>
        </div>
        <div className="w-full h-3 bg-rose-200 dark:bg-rose-900/60 rounded-full overflow-hidden flex">
          <div
            className="h-full bg-emerald-500 transition-all duration-500 rounded-l-full"
            style={{ width: `${potablePercent}%` }}
          />
        </div>
      </div>

      {/* Parameter Safety Checklist */}
      <div>
        <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400 mb-2.5">
          EPA &amp; WHO Guideline Audit
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {result.parameter_evaluations.map((item) => (
            <div
              key={item.parameter}
              className={`p-2.5 rounded-lg border text-xs flex items-center justify-between ${
                item.is_safe
                  ? "bg-zinc-50 dark:bg-zinc-800/50 border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300"
                  : "bg-amber-50/60 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200"
              }`}
            >
              <div className="flex items-center gap-2">
                {item.is_safe ? (
                  <CheckCircleIcon className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                ) : (
                  <AlertTriangleIcon className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                )}
                <div>
                  <span className="font-medium">{item.parameter}</span>
                  <div className="text-[10px] text-zinc-500 dark:text-zinc-400">
                    {item.value !== null ? `${item.value} ${item.unit}` : "N/A"} • Guideline: {item.safe_range}
                  </div>
                </div>
              </div>
              <span
                className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                  item.is_safe
                    ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                    : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                }`}
              >
                {item.is_safe ? "Compliant" : "Exceeded"}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Warnings breakdown if any */}
      {result.warnings.length > 0 && (
        <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-3 text-xs text-amber-900 dark:text-amber-200">
          <div className="font-semibold flex items-center gap-1.5 mb-1 text-amber-950 dark:text-amber-100">
            <AlertTriangleIcon className="w-4 h-4 text-amber-600" />
            Detected Chemical Anomalies ({result.warnings.length}):
          </div>
          <ul className="list-disc list-inside space-y-0.5 text-[11px] text-amber-800 dark:text-amber-300">
            {result.warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Mandatory Real-World Safety Disclaimer */}
      <div className="flex items-start gap-2 text-[11px] text-zinc-500 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-800/40 p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
        <InfoIcon className="w-4 h-4 shrink-0 text-blue-500 mt-0.5" />
        <p>
          <strong>Scientific Disclaimer:</strong> This assessment was generated by a trained scikit-learn machine learning model ({result.model_name}). In real municipal environments, chemical screening must be paired with certified microbiological laboratory testing (e.g. coliform bacteria cultures) before human consumption.
        </p>
      </div>
    </div>
  );
}
