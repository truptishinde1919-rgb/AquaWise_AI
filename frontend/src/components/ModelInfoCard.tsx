"use client";

import React from "react";
import { ModelMetadata } from "@/types/water";
import { InfoIcon, ShieldCheckIcon } from "./icons";

interface ModelInfoCardProps {
  metadata: ModelMetadata | null;
}

export function ModelInfoCard({ metadata }: ModelInfoCardProps) {
  if (!metadata) return null;

  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800 pb-3">
        <div className="flex items-center gap-2">
          <ShieldCheckIcon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm">
            Model Architecture &amp; Benchmark Data
          </h3>
        </div>
        <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
          {metadata.model_name}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <div className="bg-zinc-50 dark:bg-zinc-800/50 p-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800">
          <div className="text-lg font-bold font-mono text-zinc-900 dark:text-zinc-100">
            {(metadata.metrics.roc_auc * 100).toFixed(1)}%
          </div>
          <span className="text-[10px] uppercase font-semibold text-zinc-500 dark:text-zinc-400">
            ROC-AUC Score
          </span>
        </div>
        <div className="bg-zinc-50 dark:bg-zinc-800/50 p-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800">
          <div className="text-lg font-bold font-mono text-zinc-900 dark:text-zinc-100">
            {(metadata.metrics.accuracy * 100).toFixed(1)}%
          </div>
          <span className="text-[10px] uppercase font-semibold text-zinc-500 dark:text-zinc-400">
            Test Accuracy
          </span>
        </div>
        <div className="bg-zinc-50 dark:bg-zinc-800/50 p-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800">
          <div className="text-lg font-bold font-mono text-zinc-900 dark:text-zinc-100">
            {(metadata.metrics.precision * 100).toFixed(1)}%
          </div>
          <span className="text-[10px] uppercase font-semibold text-zinc-500 dark:text-zinc-400">
            Precision
          </span>
        </div>
        <div className="bg-zinc-50 dark:bg-zinc-800/50 p-2.5 rounded-lg border border-zinc-200 dark:border-zinc-800">
          <div className="text-lg font-bold font-mono text-zinc-900 dark:text-zinc-100">
            {(metadata.metrics.recall * 100).toFixed(1)}%
          </div>
          <span className="text-[10px] uppercase font-semibold text-zinc-500 dark:text-zinc-400">
            Recall
          </span>
        </div>
      </div>

      <div className="text-xs text-zinc-600 dark:text-zinc-400 space-y-1.5 pt-1">
        <div className="flex items-start gap-1.5">
          <InfoIcon className="w-3.5 h-3.5 text-zinc-400 mt-0.5 shrink-0" />
          <span>
            <strong>Pipeline Preprocessing:</strong> Stratified 80/20 split &bull; Median Imputation (`SimpleImputer`) &bull; Standard Z-Score Normalization (`StandardScaler`) &bull; Balanced class-weight Random Forest.
          </span>
        </div>
        <div className="flex items-start gap-1.5">
          <InfoIcon className="w-3.5 h-3.5 text-zinc-400 mt-0.5 shrink-0" />
          <span>
            <strong>Verifiable Benchmark:</strong> 3,276 water samples compiled from global drinking water monitoring initiatives and EPA standards.
          </span>
        </div>
      </div>
    </div>
  );
}
