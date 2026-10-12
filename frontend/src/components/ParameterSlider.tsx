"use client";

import React from "react";
import { FeatureMeta } from "@/types/water";
import { CheckCircleIcon, AlertTriangleIcon } from "./icons";

interface ParameterSliderProps {
  meta: FeatureMeta;
  value: number;
  onChange: (value: number) => void;
}

export function ParameterSlider({ meta, value, onChange }: ParameterSliderProps) {
  // Check if within EPA/WHO safe range
  const isSafe =
    (meta.safe_min === 0 || value >= meta.safe_min) &&
    (meta.safe_max === 0 || value <= meta.safe_max);

  // Step size calculation based on range magnitude
  const range = meta.max - meta.min;
  const step = range > 1000 ? 50 : range > 100 ? 1 : 0.05;

  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 shadow-sm hover:border-blue-400 dark:hover:border-blue-500 transition-colors">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm">
              {meta.name}
            </h4>
            <span className="text-xs px-2 py-0.5 rounded-full font-mono bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">
              {meta.unit}
            </span>
          </div>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5 line-clamp-1">
            {meta.description}
          </p>
        </div>

        {/* Safe threshold badge */}
        <span
          className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-md ${
            isSafe
              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800"
              : "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 border border-amber-200 dark:border-amber-800"
          }`}
        >
          {isSafe ? (
            <>
              <CheckCircleIcon className="w-3 h-3" />
              <span>Safe</span>
            </>
          ) : (
            <>
              <AlertTriangleIcon className="w-3 h-3" />
              <span>Warning</span>
            </>
          )}
        </span>
      </div>

      {/* Slider & Number Input */}
      <div className="space-y-2 mt-3">
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={meta.min}
            max={meta.max}
            step={step}
            value={value}
            onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
            className="w-full h-1.5 bg-zinc-200 dark:bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-blue-600 dark:accent-blue-500"
          />
          <input
            type="number"
            min={meta.min}
            max={meta.max}
            step={step}
            value={value}
            onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
            className="w-24 text-right font-mono text-xs px-2 py-1 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Guideline helper footer */}
        <div className="flex justify-between items-center text-[10px] text-zinc-500 dark:text-zinc-400 font-mono">
          <span>Min: {meta.min}</span>
          <span className="text-zinc-600 dark:text-zinc-300 font-sans">
            Guideline: {meta.safe_min > 0 ? `${meta.safe_min} - ` : "<= "}
            {meta.safe_max} {meta.unit}
          </span>
          <span>Max: {meta.max}</span>
        </div>
      </div>
    </div>
  );
}
