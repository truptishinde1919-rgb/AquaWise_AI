"use client";

import React from "react";
import { WaterParameters } from "@/types/water";
import { SparklesIcon } from "./icons";

interface Preset {
  id: string;
  name: string;
  tagline: string;
  expected: "Potable" | "Unsafe" | "Moderate";
  values: WaterParameters;
}

export const PRESETS: Preset[] = [
  {
    id: "tap_water",
    name: "Clean Tap Water",
    tagline: "Standard municipal treated drinking water",
    expected: "Potable",
    values: {
      ph: 7.35,
      Hardness: 182.0,
      Solids: 15400.0,
      Chloramines: 3.4,
      Sulfate: 235.0,
      Conductivity: 360.0,
      Organic_carbon: 2.8,
      Trihalomethanes: 52.0,
      Turbidity: 2.2,
    },
  },
  {
    id: "natural_spring",
    name: "Mountain Spring",
    tagline: "Natural high-clarity source water",
    expected: "Potable",
    values: {
      ph: 7.75,
      Hardness: 145.0,
      Solids: 9800.0,
      Chloramines: 1.8,
      Sulfate: 180.0,
      Conductivity: 280.0,
      Organic_carbon: 1.6,
      Trihalomethanes: 20.0,
      Turbidity: 1.1,
    },
  },
  {
    id: "industrial_runoff",
    name: "Industrial Runoff",
    tagline: "Untreated runoff with high solids & organics",
    expected: "Unsafe",
    values: {
      ph: 4.85,
      Hardness: 340.0,
      Solids: 39500.0,
      Chloramines: 8.9,
      Sulfate: 460.0,
      Conductivity: 690.0,
      Organic_carbon: 21.0,
      Trihalomethanes: 135.0,
      Turbidity: 8.2,
    },
  },
  {
    id: "mineral_well",
    name: "Deep Well Water",
    tagline: "High dissolved solids and elevated sulfate",
    expected: "Moderate",
    values: {
      ph: 8.65,
      Hardness: 265.0,
      Solids: 28500.0,
      Chloramines: 4.8,
      Sulfate: 365.0,
      Conductivity: 510.0,
      Organic_carbon: 10.5,
      Trihalomethanes: 78.0,
      Turbidity: 4.4,
    },
  },
];

interface PresetSelectorProps {
  onSelectPreset: (values: WaterParameters) => void;
  activePresetId: string | null;
}

export function PresetSelector({ onSelectPreset, activePresetId }: PresetSelectorProps) {
  return (
    <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <SparklesIcon className="w-4 h-4 text-blue-600 dark:text-blue-400" />
        <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 text-sm">
          Quick Water Sample Presets
        </h3>
        <span className="text-xs text-zinc-500 dark:text-zinc-400">
          (Click to load real benchmark test profiles)
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
        {PRESETS.map((preset) => {
          const isSelected = activePresetId === preset.id;
          return (
            <button
              key={preset.id}
              onClick={() => onSelectPreset(preset.values)}
              className={`text-left p-3 rounded-lg border text-xs transition-all ${
                isSelected
                  ? "border-blue-500 bg-blue-50/70 dark:bg-blue-950/40 text-blue-950 dark:text-blue-100 shadow-sm"
                  : "border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700 bg-zinc-50/50 dark:bg-zinc-800/40 text-zinc-800 dark:text-zinc-200"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold">{preset.name}</span>
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                    preset.expected === "Potable"
                      ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                      : preset.expected === "Unsafe"
                      ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                      : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
                  }`}
                >
                  {preset.expected}
                </span>
              </div>
              <p className="text-[11px] text-zinc-500 dark:text-zinc-400 line-clamp-1">
                {preset.tagline}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
