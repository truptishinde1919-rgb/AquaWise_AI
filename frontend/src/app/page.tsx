"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import Image from "next/image";

type ModuleId = "overview" | "irrigation" | "crop-health" | "treatments" | "growth" | "assistant";
type IconName = "grid" | "drop" | "leaf" | "shield" | "calendar" | "chat" | "arrow" | "sun" | "cloud" | "upload" | "mic" | "bell" | "sparkles" | "check" | "camera" | "clock" | "sprout";

type FarmerProfile = {
  name: string;
  location: string;
  farmArea: number;
  crop: string;
  variety: string;
  soilType: string;
  sowingDate: string;
};

type ChatCitation = {
  source_index: number;
  title: string;
  authors: string[] | null;
  publication_year: number | null;
  page_number: number;
  source_url: string | null;
  doi: string | null;
  license: string | null;
  excerpt?: string | null;
};

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  references?: ChatCitation[];
  uncertainty?: string;
  provider?: string;
};

type PotabilityResult = {
  potability_label: string;
  confidence_score: number;
  potability_probability: number;
  water_quality_grade: string;
};

type IrrigationResult = {
  irrigation_urgency: string;
  estimated_irrigation_requirement_liters: number;
  suggested_irrigation_timing: string;
  explanation: string;
};

type SoilMoistureResult = {
  moisture_trend: string;
  forecast_soil_moisture_pct: number;
  water_stress_warning: boolean;
  explanation: string;
};

type WaterQualityResult = {
  suitability: string;
  suitability_score: number;
  explanation: string;
};

type WaterForecastResult = {
  seven_day_irrigation_plan_liters: number;
  daily_water_requirement_liters: number;
  historical_comparison: string;
};

type PestRiskResult = {
  risk_level: string;
  risk_score: number;
  uncertainty: string;
  explanation: string;
};

const modules: { id: ModuleId; label: string; icon: IconName }[] = [
  { id: "overview", label: "Dashboard", icon: "grid" },
  { id: "irrigation", label: "Smart Irrigation", icon: "drop" },
  { id: "crop-health", label: "Crop Scanner", icon: "leaf" },
  { id: "treatments", label: "Treatment Advisor", icon: "shield" },
  { id: "growth", label: "Growth Tracker", icon: "calendar" },
  { id: "assistant", label: "AI Assistant", icon: "chat" },
];

const initialProfile: FarmerProfile = {
  name: "Trupti Shinde",
  location: "Karjat, Maharashtra",
  farmArea: 4.5,
  crop: "Rice",
  variety: "Basmati",
  soilType: "Clay loam",
  sowingDate: new Date().toISOString().slice(0, 10),
};

const irrigationDefaults = {
  crop: "rice",
  growth_stage: "vegetative",
  farm_area_ha: 4.5,
  soil_type: "clay loam",
  soil_moisture_pct: 38,
  temperature_c: 30,
  humidity_pct: 68,
  rainfall_mm: 18,
  irrigation_method: "drip",
  crop_water_requirement_mm: 72,
  weather_forecast: "Hot and dry next 2 days with minimal rainfall.",
};

const soilDefaults = {
  current_soil_moisture_pct: 38,
  historical_soil_moisture_pct: [42, 40, 35, 33],
  rainfall_mm: 18,
  irrigation_events: 1,
  temperature_c: 30,
  crop_water_requirement_mm: 72,
};

const waterQualityDefaults = {
  ph: 7.3,
  electrical_conductivity: 1300,
  sodium_adsorption_ratio: 5.8,
  salinity: 1100,
  chloride: 210,
  bicarbonate: 240,
  boron: 0.7,
};

const waterForecastDefaults = {
  crop: "rice",
  farm_area_ha: 4.5,
  current_soil_moisture_pct: 38,
  daily_water_requirement_liters: 8500,
  forecast_rainfall_mm: 22,
  historical_usage_liters: [7800, 8100, 8200, 8600, 8900],
};

const pestDefaults = {
  crop: "rice",
  crop_variety: "Basmati",
  growth_stage: "vegetative",
  temperature_c: 29,
  relative_humidity_pct: 82,
  rainfall_mm: 34,
  leaf_wetness_pct: 78,
  soil_moisture_pct: 62,
  location: "Satara",
  season: "Kharif",
  recent_pest_observations: "Leaf blight on older leaves; moderate canopy moisture",
  previous_pest_history: "High risk in previous season",
};

const cropDurationDays: Record<string, number> = {
  rice: 120,
  wheat: 125,
  tomato: 100,
  cotton: 160,
  maize: 110,
};

function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, React.ReactNode> = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    drop: <><path d="M12 3.5S6 10 6 14a6 6 0 0 0 12 0c0-4-6-10.5-6-10.5Z" /><path d="M9.5 15.5a2.5 2.5 0 0 0 2.5 2" /></>,
    leaf: <><path d="M20 4c-8 0-13 3-13 9a5 5 0 0 0 5 5c6 0 8-7 8-14Z" /><path d="M4 21c3-6 7-9 13-13" /></>,
    shield: <><path d="M12 3 19 6v5c0 5-3 8-7 10-4-2-7-5-7-10V6l7-3Z" /><path d="m9 12 2 2 4-4" /></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></>,
    chat: <><path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H6l-3 2v-6a7.5 7.5 0 1 1 17-3.5Z" /><path d="M8 11h.01M12 11h.01M16 11h.01" /></>,
    arrow: <><path d="M5 12h14M13 6l6 6-6 6" /></>,
    sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42" /></>,
    cloud: <path d="M7 18a5 5 0 1 1 1-9.9 6 6 0 0 1 11 2.4A4 4 0 0 1 18 18H7Z" />,
    upload: <><path d="M12 16V4m-5 5 5-5 5 5" /><path d="M4 16v4h16v-4" /></>,
    mic: <><rect x="9" y="3" width="6" height="12" rx="3" /><path d="M5 11a7 7 0 0 0 14 0m-7 7v3m-4 0h8" /></>,
    bell: <><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" /><path d="M10 21h4" /></>,
    sparkles: <><path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3Z" /><path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    camera: <><path d="M4 7h3l2-3h6l2 3h3a2 2 0 0 1 2 2v10H2V9a2 2 0 0 1 2-2Z" /><circle cx="12" cy="13" r="3" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    sprout: <><path d="M12 21v-9" /><path d="M12 12C5 12 4 7 4 4c5 0 8 2 8 8ZM12 15c0-5 3-8 8-8 0 4-1 8-8 8Z" /></>,
  };
  return (
    <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {paths[name]}
    </svg>
  );
}

function Panel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_3px_14px_rgba(20,54,38,0.04)] sm:p-6 ${className}`}>{children}</section>;
}

function Label({ children, htmlFor }: { children: React.ReactNode; htmlFor?: string }) {
  return <label htmlFor={htmlFor} className="mb-1.5 block text-xs font-semibold tracking-wide text-slate-600">{children}</label>;
}

function Input({ label, className = "", ...props }: React.InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  const id = props.id ?? props.name;
  return (
    <div className={className}>
      <Label htmlFor={id}>{label}</Label>
      <input {...props} id={id} className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-emerald-500 focus:ring-4 focus:ring-emerald-50" />
    </div>
  );
}

function Select({ label, options, className = "", ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { label: string; options: { value: string; label: string }[] }) {
  const id = props.id ?? props.name;
  return (
    <div className={className}>
      <Label htmlFor={id}>{label}</Label>
      <select {...props} id={id} className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm text-slate-800 outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-50">
        {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select>
    </div>
  );
}

function PrimaryButton({ children, busy = false, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { busy?: boolean }) {
  return (
    <button {...props} disabled={props.disabled || busy} className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 disabled:cursor-not-allowed disabled:opacity-55 ${props.className ?? ""}`}>
      {children}
    </button>
  );
}

function StatusPill({ children, tone = "green" }: { children: React.ReactNode; tone?: "green" | "amber" | "slate" | "blue" }) {
  const tones = {
    green: "bg-emerald-50 text-emerald-800 ring-emerald-700/10",
    amber: "bg-amber-50 text-amber-800 ring-amber-700/10",
    slate: "bg-slate-100 text-slate-600 ring-slate-500/10",
    blue: "bg-sky-50 text-sky-800 ring-sky-700/10",
  };
  return <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold ring-1 ring-inset ${tones[tone]}`}>{children}</span>;
}

export default function Home() {
  const [activeModule, setActiveModule] = useState<ModuleId>("overview");
  const [profile, setProfile] = useState<FarmerProfile>(initialProfile);
  const [profileSaved, setProfileSaved] = useState(false);
  const [irrigationInput, setIrrigationInput] = useState(irrigationDefaults);
  const [soilInput, setSoilInput] = useState(soilDefaults);
  const [qualityInput, setQualityInput] = useState(waterQualityDefaults);
  const [forecastInput, setForecastInput] = useState(waterForecastDefaults);
  const [pestInput, setPestInput] = useState(pestDefaults);
  const [potabilityResult, setPotabilityResult] = useState<PotabilityResult | null>(null);
  const [irrigationResult, setIrrigationResult] = useState<IrrigationResult | null>(null);
  const [soilResult, setSoilResult] = useState<SoilMoistureResult | null>(null);
  const [qualityResult, setQualityResult] = useState<WaterQualityResult | null>(null);
  const [forecastResult, setForecastResult] = useState<WaterForecastResult | null>(null);
  const [pestResult, setPestResult] = useState<PestRiskResult | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [chatLanguage, setChatLanguage] = useState("English");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { role: "assistant", content: "Namaste! Ask me about irrigation, water quality, crop health or sustainable farm practices. I’ll cite research sources when available and flag uncertainty." },
  ]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const imagePreviewUrl = useRef<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageDemoResult, setImageDemoResult] = useState(false);
  const [growthStage, setGrowthStage] = useState("Vegetative");
  const [growthCrop, setGrowthCrop] = useState("Rice");
  const [growthSowingDate, setGrowthSowingDate] = useState(initialProfile.sowingDate);
  const [growthUpdated, setGrowthUpdated] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      try {
        const saved = window.localStorage.getItem("aquawise-farmer-profile");
        if (saved) {
          const storedProfile = { ...initialProfile, ...JSON.parse(saved) as Partial<FarmerProfile> };
          if (storedProfile.name === "Ravi Patil") storedProfile.name = initialProfile.name;
          if (storedProfile.location === "Satara, Maharashtra") storedProfile.location = initialProfile.location;
          setProfile(storedProfile);
        }
      } catch {
        setError("Saved farm details could not be loaded from this browser.");
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => () => {
    if (imagePreviewUrl.current) URL.revokeObjectURL(imagePreviewUrl.current);
  }, []);

  const callApi = async <T,>(path: string, payload: Record<string, unknown>): Promise<T> => {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data?.error || data?.detail || "Request failed. Please try again.");
    return data as T;
  };

  const runAssessment = async <T,>(key: string, endpoint: string, payload: Record<string, unknown>, onResult: (result: T) => void) => {
    setLoading(key);
    setError(null);
    try {
      onResult(await callApi<T>(endpoint, payload));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The assessment service is unavailable.");
    } finally {
      setLoading(null);
    }
  };

  const handlePotabilityCheck = () => runAssessment<PotabilityResult>("potability", "/api/predict", {
    ph: 7.2, Hardness: 180, Solids: 16000, Chloramines: 3.5, Sulfate: 240,
    Conductivity: 390, Organic_carbon: 3, Trihalomethanes: 60, Turbidity: 2.2,
  }, setPotabilityResult);

  const handleIrrigation = () => runAssessment<IrrigationResult>("irrigation", "/api/agri/irrigation", irrigationInput, setIrrigationResult);
  const handleSoilForecast = () => runAssessment<SoilMoistureResult>("soil", "/api/agri/soil-moisture", soilInput, setSoilResult);
  const handleWaterQuality = () => runAssessment<WaterQualityResult>("quality", "/api/agri/water-quality", qualityInput, setQualityResult);
  const handleForecast = () => runAssessment<WaterForecastResult>("forecast", "/api/agri/water-forecast", forecastInput, setForecastResult);
  const handlePestRisk = () => runAssessment<PestRiskResult>("pest", "/api/agri/pest-risk", pestInput, setPestResult);

  const handleChatSubmit = async (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();
    const question = chatInput.trim();
    if (!question || chatLoading) return;
    const nextMessages = [...chatMessages, { role: "user" as const, content: question }];
    setChatMessages(nextMessages);
    setChatInput("");
    setChatLoading(true);
    setChatError(null);
    const languageInstruction = chatLanguage === "English" ? "" : `\n\nPlease answer in ${chatLanguage}.`;
    try {
      const result = await callApi<{
        answer: string;
        references: ChatCitation[];
        uncertainty: string;
        provider: string;
      }>("/api/chat", {
        message: `${question}${languageInstruction}`,
        history: nextMessages.slice(-12).map(({ role, content }) => ({ role, content })),
      });
      setChatMessages([
        ...nextMessages,
        { role: "assistant", content: result.answer, references: result.references, uncertainty: result.uncertainty, provider: result.provider },
      ]);
    } catch (reason) {
      setChatError(reason instanceof Error ? reason.message : "The agricultural research assistant is unavailable.");
    } finally {
      setChatLoading(false);
    }
  };

  const growthDate = (() => {
    if (!growthSowingDate) return null;
    const date = new Date(`${growthSowingDate}T00:00:00`);
    if (Number.isNaN(date.getTime())) return null;
    date.setDate(date.getDate() + (cropDurationDays[growthCrop.toLowerCase()] ?? 120));
    return date.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  })();

  const saveProfile = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      window.localStorage.setItem("aquawise-farmer-profile", JSON.stringify(profile));
      setProfileSaved(true);
      window.setTimeout(() => setProfileSaved(false), 2500);
    } catch {
      setProfileSaved(false);
      setError("Farm profile could not be saved in this browser.");
    }
  };

  const selectImage = (file: File | null) => {
    if (imagePreviewUrl.current) URL.revokeObjectURL(imagePreviewUrl.current);
    imagePreviewUrl.current = file ? URL.createObjectURL(file) : null;
    setImagePreview(imagePreviewUrl.current);
    setImageFile(file);
    setImageDemoResult(false);
  };

  const handleImageDemo = () => {
    if (imageFile) setImageDemoResult(true);
  };

  const pageTitle = modules.find((item) => item.id === activeModule)?.label ?? "Farm overview";

  return (
    <div className="min-h-screen bg-[#edf5ff] text-slate-800">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[236px] flex-col border-r border-blue-950/20 bg-[#082b50] text-white lg:flex">
        <div className="flex items-center gap-3 px-6 py-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-300 text-blue-950"><Icon name="drop" size={23} /></div>
          <div><div className="text-[17px] font-bold tracking-tight">AquaWise<span className="text-sky-300"> AI</span></div><div className="text-[10px] font-medium tracking-[0.18em] text-blue-100/70">SMART FARMING</div></div>
        </div>
        <div className="mx-4 mb-5 rounded-xl border border-white/10 bg-white/[0.06] p-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-sky-200 text-sm font-bold text-blue-950">{profile.name.split(" ").map((part) => part[0]).join("").slice(0, 2)}</div>
            <div className="min-w-0"><div className="truncate text-sm font-semibold">{profile.name}</div><div className="truncate text-xs text-blue-100/70">{profile.location}</div></div>
          </div>
        </div>
        <div className="px-6 pb-2 text-[10px] font-bold uppercase tracking-[0.18em] text-blue-100/50">Farm workspace</div>
        <nav aria-label="Main navigation" className="space-y-1 px-3">
          {modules.map((item) => (
            <button key={item.id} onClick={() => setActiveModule(item.id)} className={`flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-left text-[13px] font-medium transition ${activeModule === item.id ? "bg-sky-100 text-blue-950 shadow-sm" : "text-blue-50/80 hover:bg-white/10 hover:text-white"}`}>
              <Icon name={item.icon} size={18} />{item.label}
            </button>
          ))}
        </nav>
        <div className="mt-auto p-4">
          <div className="rounded-xl border border-white/10 bg-white/[0.06] p-3 text-xs leading-5 text-blue-50/80">
            <div className="mb-1 flex items-center gap-2 font-semibold text-sky-100"><Icon name="sparkles" size={15} /> Prototype mode</div>
            Some weather and vision panels use illustrative demo data.
          </div>
          <div className="px-2 pt-4 text-[10px] text-blue-100/45">AquaWise AI · Farmer workspace</div>
        </div>
      </aside>

      <div className="lg:pl-[236px]">
        <header className="sticky top-0 z-20 border-b border-blue-100 bg-[#f7fbff]/95 px-4 py-3 backdrop-blur-md sm:px-7 lg:px-9">
          <div className="mx-auto flex max-w-[1480px] items-center justify-between gap-4">
            <div className="min-w-0">
              <div className="text-[11px] font-semibold uppercase tracking-[0.15em] text-blue-800/65">Farm workspace <span className="px-1 text-slate-300">/</span> {pageTitle}</div>
              <div className="mt-0.5 truncate text-lg font-bold tracking-tight text-slate-900 sm:text-xl">{activeModule === "overview" ? `Welcome, ${profile.name.split(" ")[0]}! 👋` : pageTitle}</div>
            </div>
            <div className="flex shrink-0 items-center gap-2 sm:gap-3">
              <StatusPill tone="amber"><span className="h-1.5 w-1.5 rounded-full bg-amber-500" /> Demo data</StatusPill>
              <button type="button" aria-label="Alerts are sample notifications" title="Sample alerts only" className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"><Icon name="bell" size={18} /><span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-amber-500 ring-2 ring-white" /></button>
              <button onClick={() => setActiveModule("overview")} className="hidden items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 sm:flex"><span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-[10px] text-emerald-800">{profile.name.slice(0, 1)}</span>My farm</button>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-[1480px] px-4 pb-28 pt-5 sm:px-7 sm:pt-7 lg:px-9 lg:pb-10">
          {error && <div role="alert" className="mb-5 flex items-start justify-between gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"><span>{error}</span><button aria-label="Dismiss error" onClick={() => setError(null)} className="font-bold">×</button></div>}

          {activeModule === "overview" && (
            <div className="space-y-6">
              <section className="flex flex-wrap items-end justify-between gap-3">
                <div><h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl">Farmer Dashboard</h1><p className="mt-1 text-sm text-slate-500">Here&apos;s your farm overview for today.</p></div>
                <StatusPill tone="amber">Demo overview · sample values</StatusPill>
              </section>

              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {[
                  { label: "Weather today", value: "28°C", note: "Partly cloudy · demo", icon: "sun" as const, tone: "text-sky-700 bg-sky-50" },
                  { label: "Soil moisture", value: `${irrigationInput.soil_moisture_pct}%`, note: "Sample field reading", icon: "drop" as const, tone: "text-emerald-700 bg-emerald-50" },
                  { label: "Irrigation alert", value: irrigationResult?.irrigation_urgency ?? "Review plan", note: irrigationResult ? "Backend assessment" : "No live alert service", icon: "cloud" as const, tone: "text-amber-700 bg-amber-50" },
                  { label: "Pest alert", value: pestResult?.risk_level ?? "Check leaves", note: pestResult ? "Risk assessment API" : "Sample reminder", icon: "leaf" as const, tone: "text-rose-700 bg-rose-50" },
                ].map((stat) => (
                  <Panel key={stat.label} className="p-4 sm:p-5">
                    <div className="flex items-start justify-between"><div className="text-xs font-semibold text-slate-500">{stat.label}</div><div className={`flex h-9 w-9 items-center justify-center rounded-xl ${stat.tone}`}><Icon name={stat.icon} size={18} /></div></div>
                    <div className="mt-2 text-2xl font-bold capitalize tracking-tight text-slate-900">{stat.value}</div><div className="mt-1 text-[11px] text-slate-500">{stat.note}</div>
                  </Panel>
                ))}
              </div>

              <div className="grid gap-6 xl:grid-cols-[1.55fr_1fr]">
                <Panel>
                  <div className="flex items-center justify-between gap-3"><div><h2 className="text-base font-bold text-slate-900">Your crops</h2><p className="mt-1 text-xs text-slate-500">Crop record · sample profile</p></div><StatusPill tone="green">1 field</StatusPill></div>
                  <div className="mt-4 flex gap-4 rounded-xl bg-[#f7fbff] p-3">
                    <div className="flex min-h-32 w-28 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br from-lime-200 via-emerald-300 to-green-700 text-5xl shadow-inner" aria-label="Illustrative rice crop tile">🌾</div>
                    <div className="flex min-w-0 flex-1 flex-col justify-center">
                      <div className="text-base font-bold text-slate-900">{profile.crop || "Rice"}</div><div className="mt-1 text-[11px] text-slate-500">Growth stage: {growthStage}</div><div className="mt-2 text-xs font-semibold text-slate-700">Field health: <span className="text-emerald-700">{pestResult ? `${pestResult.risk_level} risk` : "Good · sample"}</span></div>
                      <button onClick={() => setActiveModule("crop-health")} className="mt-4 self-start text-[11px] font-bold text-blue-700 hover:underline">View crop details <span aria-hidden="true">→</span></button>
                    </div>
                  </div>
                  <p className="mt-3 text-[10px] leading-4 text-slate-400">Crop illustration and health label are sample data, not a field image or disease diagnosis.</p>
                </Panel>

                <Panel>
                  <div className="flex items-start justify-between gap-3"><div><h2 className="text-base font-bold text-slate-900">7-day forecast</h2><p className="mt-1 text-xs text-slate-500">{profile.location} · sample forecast</p></div><StatusPill tone="amber">Demo</StatusPill></div>
                  <div className="mt-5 grid grid-cols-4 gap-y-4 sm:grid-cols-7">
                    {[["Mon", "32°", "sun"], ["Tue", "31°", "cloud"], ["Wed", "30°", "cloud"], ["Thu", "29°", "cloud"], ["Fri", "28°", "cloud"], ["Sat", "29°", "sun"], ["Sun", "31°", "cloud"]].map(([day, temp, icon]) => (
                      <div key={day} className="flex flex-col items-center"><Icon name={icon as IconName} size={20} /><div className="mt-2 text-xs font-bold text-slate-800">{temp}</div><div className="mt-1 text-[10px] text-slate-500">{day}</div></div>
                    ))}
                  </div>
                  <div className="mt-5 rounded-xl border border-blue-100 bg-blue-50/70 p-3 text-[11px] leading-5 text-blue-900">Weather is illustrative only; connect a trusted forecast service before using it for field decisions.</div>
                </Panel>
              </div>

              <Panel>
                <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-base font-bold text-slate-900">Farmer profile & farm details</h2><p className="mt-1 text-xs text-slate-500">Saved in this browser only; not synced to an account.</p></div><StatusPill tone="slate">Local demo</StatusPill></div>
                <form onSubmit={saveProfile} className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <Input label="Farmer name" value={profile.name} onChange={(e) => setProfile({ ...profile, name: e.target.value })} />
                  <Input label="Location" value={profile.location} onChange={(e) => setProfile({ ...profile, location: e.target.value })} />
                  <Input label="Farm area (ha)" type="number" min="0" step="0.1" value={profile.farmArea} onChange={(e) => setProfile({ ...profile, farmArea: Number(e.target.value) })} />
                  <Input label="Main crop" value={profile.crop} onChange={(e) => setProfile({ ...profile, crop: e.target.value })} />
                  <div className="flex items-center justify-between gap-3 sm:col-span-2 xl:col-span-4"><span className="text-[11px] text-slate-500">{profileSaved ? "Profile saved locally" : "Sample profile details — not synced to a server"}</span><PrimaryButton type="submit"><Icon name="check" size={15} />Save profile</PrimaryButton></div>
                </form>
              </Panel>

              <div>
                <div className="mb-3 flex items-end justify-between"><div><h2 className="text-base font-bold text-slate-900">Your farm toolkit</h2><p className="mt-1 text-xs text-slate-500">Open a module to start a sample workflow.</p></div></div>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {modules.filter((item) => item.id !== "overview").map((item) => (
                    <button key={item.id} onClick={() => setActiveModule(item.id)} className="group flex min-h-24 items-center gap-4 rounded-2xl border border-slate-200/80 bg-white p-4 text-left shadow-[0_3px_14px_rgba(20,54,38,0.04)] transition hover:-translate-y-0.5 hover:border-emerald-300 hover:shadow-md">
                      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-800"><Icon name={item.icon} size={21} /></span>
                      <span className="min-w-0 flex-1"><span className="block text-sm font-bold text-slate-900">{item.label}</span><span className="mt-1 block text-xs text-slate-500">{item.id === "irrigation" ? "Water planning and suitability" : item.id === "crop-health" ? "Risk assessment and image demo" : item.id === "treatments" ? "Practical non-chemical IPM" : item.id === "growth" ? "Track stage and harvest window" : "Ask the research assistant"}</span></span>
                      <Icon name="arrow" size={16} />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeModule === "irrigation" && (
            <div className="space-y-6">
              <div className="flex flex-wrap items-end justify-between gap-3"><div><h1 className="text-xl font-bold text-slate-900">Smart irrigation planner</h1><p className="mt-1 text-sm text-slate-500">Use field observations and rainfall estimates to review water needs.</p></div><StatusPill tone="blue">API assessments + manual sample inputs</StatusPill></div>
              <div className="grid gap-6 xl:grid-cols-[1.3fr_0.8fr]">
                <Panel>
                  <div className="mb-5 flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-base font-bold">Field inputs</h2><p className="mt-1 text-xs text-slate-500">No sensor or live weather connection is configured.</p></div><StatusPill tone="amber">Enter observed values</StatusPill></div>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <Select label="Crop" value={irrigationInput.crop} onChange={(e) => setIrrigationInput({ ...irrigationInput, crop: e.target.value })} options={[{ value: "rice", label: "Rice" }, { value: "wheat", label: "Wheat" }, { value: "tomato", label: "Tomato" }, { value: "maize", label: "Maize" }]} />
                    <Select label="Growth stage" value={irrigationInput.growth_stage} onChange={(e) => setIrrigationInput({ ...irrigationInput, growth_stage: e.target.value })} options={["seedling", "vegetative", "flowering", "maturity"].map((stage) => ({ value: stage, label: stage[0].toUpperCase() + stage.slice(1) }))} />
                    <Input label="Sowing date" type="date" value={profile.sowingDate} onChange={(e) => { setProfile({ ...profile, sowingDate: e.target.value }); setGrowthSowingDate(e.target.value); }} />
                    <Input label="Farm area (ha)" type="number" min="0" step="0.1" value={irrigationInput.farm_area_ha} onChange={(e) => setIrrigationInput({ ...irrigationInput, farm_area_ha: Number(e.target.value) })} />
                    <Select label="Soil type" value={irrigationInput.soil_type} onChange={(e) => setIrrigationInput({ ...irrigationInput, soil_type: e.target.value })} options={["sandy", "loam", "clay loam", "clay"].map((soil) => ({ value: soil, label: soil.replace(/\b\w/g, (letter) => letter.toUpperCase()) }))} />
                    <Input label="Soil moisture (%)" type="number" min="0" max="100" value={irrigationInput.soil_moisture_pct} onChange={(e) => setIrrigationInput({ ...irrigationInput, soil_moisture_pct: Number(e.target.value) })} />
                    <Input label="Expected rainfall (mm)" type="number" min="0" value={irrigationInput.rainfall_mm} onChange={(e) => setIrrigationInput({ ...irrigationInput, rainfall_mm: Number(e.target.value) })} />
                    <Input label="Temperature (°C)" type="number" value={irrigationInput.temperature_c} onChange={(e) => setIrrigationInput({ ...irrigationInput, temperature_c: Number(e.target.value) })} />
                    <Input label="Humidity (%)" type="number" min="0" max="100" value={irrigationInput.humidity_pct} onChange={(e) => setIrrigationInput({ ...irrigationInput, humidity_pct: Number(e.target.value) })} />
                    <Select label="Irrigation method" value={irrigationInput.irrigation_method} onChange={(e) => setIrrigationInput({ ...irrigationInput, irrigation_method: e.target.value })} options={["drip", "sprinkler", "surface"].map((method) => ({ value: method, label: method[0].toUpperCase() + method.slice(1) }))} />
                  </div>
                  <div className="mt-5 flex flex-wrap gap-2"><PrimaryButton onClick={handleIrrigation} busy={loading === "irrigation"}>{loading === "irrigation" ? "Assessing…" : "Assess irrigation need"} <Icon name="arrow" size={16} /></PrimaryButton><button onClick={handleSoilForecast} disabled={loading === "soil"} className="min-h-11 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50">{loading === "soil" ? "Forecasting…" : "Forecast soil moisture"}</button></div>
                  {irrigationResult && <div className="mt-5 rounded-xl border border-emerald-100 bg-emerald-50/70 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><div className="text-sm font-bold capitalize text-emerald-950">{irrigationResult.irrigation_urgency} irrigation urgency</div><StatusPill>{irrigationResult.suggested_irrigation_timing}</StatusPill></div><div className="mt-3 text-2xl font-bold text-emerald-950">{irrigationResult.estimated_irrigation_requirement_liters.toLocaleString()} <span className="text-sm font-semibold">litres estimated</span></div><p className="mt-2 text-xs leading-5 text-emerald-900/80">{irrigationResult.explanation}</p><div className="mt-3 text-[10px] text-emerald-800">Backend assessment output; validate against local field conditions.</div></div>}
                  {soilResult && <div className="mt-3 rounded-xl border border-sky-100 bg-sky-50 p-4"><div className="flex items-center justify-between"><span className="text-sm font-bold text-sky-950">Soil moisture forecast</span><StatusPill tone={soilResult.water_stress_warning ? "amber" : "blue"}>{soilResult.moisture_trend}</StatusPill></div><div className="mt-2 text-lg font-bold text-sky-950">{soilResult.forecast_soil_moisture_pct}% forecast moisture</div><p className="mt-1 text-xs leading-5 text-sky-900/80">{soilResult.explanation}</p></div>}
                  <div className="mt-5 grid gap-3 border-t border-slate-100 pt-4 sm:grid-cols-3">
                    <Input label="Moisture now (%)" type="number" min="0" max="100" value={soilInput.current_soil_moisture_pct} onChange={(e) => setSoilInput({ ...soilInput, current_soil_moisture_pct: Number(e.target.value) })} />
                    <Input label="Recent rainfall (mm)" type="number" min="0" value={soilInput.rainfall_mm} onChange={(e) => setSoilInput({ ...soilInput, rainfall_mm: Number(e.target.value) })} />
                    <Input label="Irrigation events" type="number" min="0" value={soilInput.irrigation_events} onChange={(e) => setSoilInput({ ...soilInput, irrigation_events: Number(e.target.value) })} />
                  </div>
                </Panel>
                <div className="space-y-6">
                  <Panel>
                    <div className="flex items-start justify-between gap-3"><div><h2 className="text-base font-bold">7-day water plan</h2><p className="mt-1 text-xs text-slate-500">Existing AquaWise forecast endpoint</p></div><Icon name="calendar" /></div>
                    <Input className="mt-4" label="Daily water need (litres)" type="number" min="0" value={forecastInput.daily_water_requirement_liters} onChange={(e) => setForecastInput({ ...forecastInput, daily_water_requirement_liters: Number(e.target.value) })} />
                    <Input className="mt-3" label="Forecast rainfall (mm)" type="number" min="0" value={forecastInput.forecast_rainfall_mm} onChange={(e) => setForecastInput({ ...forecastInput, forecast_rainfall_mm: Number(e.target.value) })} />
                    <PrimaryButton className="mt-4 w-full" onClick={handleForecast} busy={loading === "forecast"}>{loading === "forecast" ? "Planning…" : "Generate water plan"}</PrimaryButton>
                    {forecastResult && <div className="mt-4 rounded-xl bg-slate-50 p-4"><div className="text-xs font-semibold text-slate-500">Estimated 7-day irrigation</div><div className="mt-1 text-2xl font-bold text-slate-900">{forecastResult.seven_day_irrigation_plan_liters.toLocaleString()} L</div><p className="mt-2 text-xs text-slate-600">{forecastResult.historical_comparison}</p></div>}
                  </Panel>
                  <Panel>
                    <div className="flex items-start justify-between gap-3"><div><h2 className="text-base font-bold">Irrigation water quality</h2><p className="mt-1 text-xs text-slate-500">Separate from drinking-water potability.</p></div><Icon name="drop" /></div>
                    <div className="mt-4 grid grid-cols-2 gap-3"><Input label="pH" type="number" step="0.1" value={qualityInput.ph} onChange={(e) => setQualityInput({ ...qualityInput, ph: Number(e.target.value) })} /><Input label="EC (µS/cm)" type="number" value={qualityInput.electrical_conductivity} onChange={(e) => setQualityInput({ ...qualityInput, electrical_conductivity: Number(e.target.value) })} /><Input label="SAR" type="number" step="0.1" value={qualityInput.sodium_adsorption_ratio} onChange={(e) => setQualityInput({ ...qualityInput, sodium_adsorption_ratio: Number(e.target.value) })} /><Input label="Salinity" type="number" value={qualityInput.salinity} onChange={(e) => setQualityInput({ ...qualityInput, salinity: Number(e.target.value) })} /></div>
                    <PrimaryButton className="mt-4 w-full" onClick={handleWaterQuality} busy={loading === "quality"}>{loading === "quality" ? "Checking…" : "Assess irrigation water"}</PrimaryButton>
                    {qualityResult && <div className="mt-4 rounded-xl bg-violet-50 p-3 text-sm text-violet-950"><strong>{qualityResult.suitability} suitability · {qualityResult.suitability_score}/100</strong><p className="mt-1 text-xs leading-5">{qualityResult.explanation}</p></div>}
                  </Panel>
                </div>
              </div>
              <Panel className="border-slate-300">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div><div className="flex items-center gap-2"><Icon name="drop" /><h2 className="text-base font-bold">Drinking-water potability</h2><StatusPill tone="slate">Existing model</StatusPill></div><p className="mt-1 text-xs leading-5 text-slate-500">Preserved from AquaWise AI. This drinking-water model is distinct from irrigation suitability.</p></div><PrimaryButton onClick={handlePotabilityCheck} busy={loading === "potability"}>{loading === "potability" ? "Analyzing…" : "Run potability check"}</PrimaryButton></div>
                {potabilityResult && <div className="mt-4 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-950"><strong>{potabilityResult.potability_label}</strong><span className="ml-3">Confidence {potabilityResult.confidence_score}% · Grade {potabilityResult.water_quality_grade}</span><div className="mt-1 text-xs">Model probability: {potabilityResult.potability_probability}</div></div>}
              </Panel>
            </div>
          )}

          {activeModule === "crop-health" && (
            <div className="space-y-6">
              <div><h1 className="text-xl font-bold text-slate-900">Crop health & pest detection</h1><p className="mt-1 text-sm text-slate-500">Record a field image and assess environmental pest risk.</p></div>
              <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
                <Panel>
                  <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-base font-bold">Plant image check</h2><p className="mt-1 text-xs text-slate-500">Upload or capture an image for a prototype walkthrough.</p></div><StatusPill tone="amber">Classifier not connected</StatusPill></div>
                  <label htmlFor="plant-photo" className="mt-5 flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-emerald-200 bg-emerald-50/40 p-5 text-center transition hover:border-emerald-400 hover:bg-emerald-50">
                    {imagePreview ? <Image src={imagePreview} alt="Selected crop for illustrative preview" width={720} height={480} unoptimized className="max-h-64 max-w-full rounded-xl object-contain" /> : <><span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-emerald-800 shadow-sm"><Icon name="camera" size={26} /></span><span className="mt-3 text-sm font-bold text-slate-800">Take a photo or upload an image</span><span className="mt-1 text-xs text-slate-500">JPG, PNG or WebP · preview stays in this browser</span><span className="mt-4 inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700"><Icon name="upload" size={15} />Choose image</span></>}
                    <input id="plant-photo" type="file" accept="image/*" capture="environment" className="sr-only" onChange={(event) => selectImage(event.target.files?.[0] ?? null)} />
                  </label>
                  {imagePreview && <div className="mt-3 flex flex-wrap items-center justify-between gap-2"><span className="max-w-[70%] truncate text-xs text-slate-500">{imageFile?.name}</span><button onClick={() => selectImage(null)} className="min-h-10 rounded-lg px-3 text-xs font-semibold text-slate-600 hover:bg-slate-100">Remove photo</button></div>}
                  <PrimaryButton className="mt-4 w-full" disabled={!imageFile} onClick={handleImageDemo}><Icon name="sparkles" size={16} />Show illustrative result</PrimaryButton>
                  {imageDemoResult && <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4"><div className="flex flex-wrap items-center justify-between gap-2"><strong className="text-sm text-amber-950">Illustrative example: possible leaf spot</strong><StatusPill tone="amber">Simulated output</StatusPill></div><div className="mt-3 h-2 overflow-hidden rounded-full bg-amber-100"><div className="h-full w-[68%] rounded-full bg-amber-500" /></div><div className="mt-1 text-right text-[11px] font-semibold text-amber-900">68% sample score · not model confidence</div><p className="mt-3 text-xs leading-5 text-amber-950/80">This is a fixed prototype example, not an analysis of your image. No computer-vision model is connected. Confirm symptoms with a local agronomist before taking action.</p></div>}
                </Panel>

                <Panel>
                  <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-base font-bold">Pest-risk assessment</h2><p className="mt-1 text-xs text-slate-500">Environmental risk endpoint; not image diagnosis.</p></div><StatusPill tone="blue">Backend assessment</StatusPill></div>
                  <div className="mt-5 grid gap-3 sm:grid-cols-2">
                    <Select label="Crop" value={pestInput.crop} onChange={(e) => setPestInput({ ...pestInput, crop: e.target.value })} options={["rice", "wheat", "tomato", "maize", "cotton"].map((crop) => ({ value: crop, label: crop[0].toUpperCase() + crop.slice(1) }))} />
                    <Select label="Growth stage" value={pestInput.growth_stage} onChange={(e) => setPestInput({ ...pestInput, growth_stage: e.target.value })} options={["seedling", "vegetative", "flowering", "maturity"].map((stage) => ({ value: stage, label: stage[0].toUpperCase() + stage.slice(1) }))} />
                    <Input label="Temperature (°C)" type="number" value={pestInput.temperature_c} onChange={(e) => setPestInput({ ...pestInput, temperature_c: Number(e.target.value) })} />
                    <Input label="Relative humidity (%)" type="number" value={pestInput.relative_humidity_pct} onChange={(e) => setPestInput({ ...pestInput, relative_humidity_pct: Number(e.target.value) })} />
                    <Input label="Recent rainfall (mm)" type="number" value={pestInput.rainfall_mm} onChange={(e) => setPestInput({ ...pestInput, rainfall_mm: Number(e.target.value) })} />
                    <Input label="Leaf wetness (%)" type="number" value={pestInput.leaf_wetness_pct} onChange={(e) => setPestInput({ ...pestInput, leaf_wetness_pct: Number(e.target.value) })} />
                  </div>
                  <PrimaryButton className="mt-4 w-full" onClick={handlePestRisk} busy={loading === "pest"}>{loading === "pest" ? "Assessing…" : "Assess pest risk"}</PrimaryButton>
                  {pestResult && <div className="mt-4 rounded-xl border border-sky-100 bg-sky-50 p-4"><div className="flex items-center justify-between gap-2"><strong className="capitalize text-sky-950">{pestResult.risk_level} risk</strong><StatusPill tone="blue">Score {pestResult.risk_score}</StatusPill></div><p className="mt-2 text-xs leading-5 text-sky-950/80">{pestResult.explanation}</p><p className="mt-2 text-[11px] text-sky-900/70">Uncertainty: {pestResult.uncertainty}</p></div>}
                  <div className="mt-4 rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-600"><strong className="text-slate-800">Next step:</strong> Scout multiple plants across the field and record symptom location, spread and severity. A risk score is not a confirmed diagnosis.</div>
                </Panel>
              </div>
            </div>
          )}

          {activeModule === "treatments" && (
            <div className="space-y-6">
              <div><h1 className="text-xl font-bold text-slate-900">Integrated pest management</h1><p className="mt-1 text-sm text-slate-500">Practical, prevention-first guidance with clear limits on chemical advice.</p></div>
              <Panel className="border-amber-200 bg-amber-50/70">
                <div className="flex items-start gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-800"><Icon name="shield" /></span><div><h2 className="text-sm font-bold text-amber-950">No verified regional pesticide labels connected</h2><p className="mt-1 text-xs leading-5 text-amber-900/80">AquaWise will not invent a product, dose, tank mix, application interval or pre-harvest interval. Check current local registrations and the complete product label with an agricultural extension professional before using any pesticide.</p></div></div>
              </Panel>
              <div className="grid gap-6 lg:grid-cols-2">
                <Panel>
                  <h2 className="text-base font-bold">Start with field verification</h2><p className="mt-1 text-xs text-slate-500">Use these general scouting steps while the issue is being identified.</p>
                  <ol className="mt-5 space-y-4">
                    {[
                      ["01", "Inspect and document", "Check several plants in different field areas. Note affected plant parts, pattern, recent weather and how quickly symptoms spread."],
                      ["02", "Compare symptoms", "Look for signs of insects, fungal growth, nutrient stress or waterlogging. Similar symptoms can have different causes."],
                      ["03", "Reduce conducive conditions", "Use clean tools, remove heavily affected material where locally advised, manage weeds and avoid unnecessary leaf wetness."],
                      ["04", "Recheck before treating", "Monitor whether symptoms change. Seek an extension diagnosis if damage is spreading or the crop is at a sensitive stage."],
                    ].map(([number, title, description]) => <li key={number} className="flex gap-3"><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-[11px] font-bold text-emerald-800">{number}</span><div><div className="text-sm font-semibold text-slate-900">{title}</div><p className="mt-1 text-xs leading-5 text-slate-600">{description}</p></div></li>)}
                  </ol>
                </Panel>
                <Panel>
                  <h2 className="text-base font-bold">Treatment decision support</h2><p className="mt-1 text-xs text-slate-500">Options to discuss with a qualified local advisor after diagnosis.</p>
                  <div className="mt-5 space-y-3">
                    <div className="rounded-xl border border-slate-200 p-4"><div className="flex items-center gap-2 text-sm font-bold text-slate-900"><Icon name="sprout" size={17} /> Cultural and mechanical controls</div><p className="mt-2 text-xs leading-5 text-slate-600">Ask about crop rotation, sanitation, resistant varieties, planting timing, trapping or physical removal where suitable for your crop and pest.</p></div>
                    <div className="rounded-xl border border-slate-200 p-4"><div className="flex items-center gap-2 text-sm font-bold text-slate-900"><Icon name="leaf" size={17} /> Biological control</div><p className="mt-2 text-xs leading-5 text-slate-600">Ask a local extension officer which biological control agents are registered and appropriate for the confirmed pest and crop in your region.</p></div>
                    <div className="rounded-xl border border-slate-200 p-4"><div className="flex items-center gap-2 text-sm font-bold text-slate-900"><Icon name="check" size={17} /> If a pesticide is considered</div><p className="mt-2 text-xs leading-5 text-slate-600">Verify crop and pest registration, label dose, protective equipment, re-entry interval, pre-harvest interval and local legal requirements from the current product label.</p></div>
                  </div>
                  <button onClick={() => setActiveModule("assistant")} className="mt-4 min-h-11 rounded-xl border border-emerald-200 px-4 py-2 text-sm font-semibold text-emerald-800 hover:bg-emerald-50">Ask the research assistant <span aria-hidden="true">→</span></button>
                </Panel>
              </div>
            </div>
          )}

          {activeModule === "growth" && (
            <div className="space-y-6">
              <div><h1 className="text-xl font-bold text-slate-900">Crop growth tracker</h1><p className="mt-1 text-sm text-slate-500">Keep a simple field record and view an illustrative harvest window.</p></div>
              <div className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
                <Panel>
                  <div className="flex items-start justify-between"><div><h2 className="text-base font-bold">Crop record</h2><p className="mt-1 text-xs text-slate-500">Updates apply to this browser prototype.</p></div><StatusPill tone="slate">Local only</StatusPill></div>
                  <div className="mt-5 grid gap-4 sm:grid-cols-2">
                    <Select label="Crop" value={growthCrop} onChange={(e) => { setGrowthCrop(e.target.value); setGrowthUpdated(false); }} options={Object.keys(cropDurationDays).map((crop) => ({ value: crop[0].toUpperCase() + crop.slice(1), label: crop[0].toUpperCase() + crop.slice(1) }))} />
                    <Input label="Variety" value={profile.variety} onChange={(e) => setProfile({ ...profile, variety: e.target.value })} />
                    <Input label="Sowing date" type="date" value={growthSowingDate} onChange={(e) => { setGrowthSowingDate(e.target.value); setGrowthUpdated(false); }} />
                    <Select label="Current growth stage" value={growthStage} onChange={(e) => { setGrowthStage(e.target.value); setGrowthUpdated(false); }} options={["Seedling", "Vegetative", "Flowering", "Grain filling", "Maturity"].map((stage) => ({ value: stage, label: stage }))} />
                    <Select label="Farm soil type" value={profile.soilType} onChange={(e) => setProfile({ ...profile, soilType: e.target.value })} options={["Sandy", "Loam", "Clay loam", "Clay"].map((soil) => ({ value: soil, label: soil }))} />
                    <Input label="Field notes" placeholder="Add a short observation" />
                  </div>
                  <PrimaryButton className="mt-5" onClick={() => setGrowthUpdated(true)}><Icon name="check" size={16} />Update crop record</PrimaryButton>
                </Panel>
                <Panel>
                  <div className="flex items-start justify-between gap-3"><div><h2 className="text-base font-bold">Growth outlook</h2><p className="mt-1 text-xs text-slate-500">Simple calendar estimate, not an ML prediction.</p></div><StatusPill tone="amber">Illustrative</StatusPill></div>
                  <div className="mt-5 rounded-2xl bg-gradient-to-br from-emerald-50 to-sky-50 p-5">
                    <div className="flex items-center gap-2 text-xs font-semibold text-emerald-800"><Icon name="clock" size={16} /> EXPECTED HARVEST WINDOW</div>
                    <div className="mt-2 text-2xl font-bold tracking-tight text-slate-900">{growthDate ?? "Add sowing date"}</div>
                    <div className="mt-2 text-xs text-slate-600">{growthCrop} · {growthStage} stage · {profile.variety || "Variety not set"}</div>
                    <div className="mt-5 grid grid-cols-4 gap-1">
                      {["Sowing", "Vegetative", "Flowering", "Harvest"].map((stage, index) => <div key={stage}><div className={`h-1.5 rounded-full ${index <= (growthStage === "Seedling" ? 0 : growthStage === "Vegetative" ? 1 : growthStage === "Flowering" ? 2 : 3) ? "bg-emerald-600" : "bg-slate-200"}`} /><div className="mt-2 text-[9px] text-slate-500 sm:text-[10px]">{stage}</div></div>)}
                    </div>
                  </div>
                  <p className="mt-4 text-xs leading-5 text-slate-600">Planning estimate based on a typical crop duration only. Actual growth and harvest timing depend on variety, local weather, soil, water, planting conditions and field management. Confirm timing with local agronomy guidance.</p>
                  {growthUpdated && <div role="status" className="mt-3 rounded-lg bg-emerald-50 px-3 py-2 text-xs font-medium text-emerald-800">Crop record updated in this prototype.</div>}
                </Panel>
              </div>
            </div>
          )}

          {activeModule === "assistant" && (
            <div className="mx-auto max-w-4xl space-y-5">
              <div><h1 className="text-xl font-bold text-slate-900">AI farmer assistant</h1><p className="mt-1 text-sm text-slate-500">Ask questions about the available research PDF; answers include page citations and evidence notes.</p></div>
              <Panel className="overflow-hidden p-0">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-5 py-4 sm:px-6">
                  <div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100 text-emerald-800"><Icon name="sparkles" size={21} /></span><div><div className="text-sm font-bold text-slate-900">AquaWise research assistant</div><div className="mt-0.5 flex items-center gap-1.5 text-[11px] text-slate-500"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Page-cited answers · PDF excerpt fallback</div></div></div>
                  <Select aria-label="Response language" label="Language" value={chatLanguage} onChange={(e) => setChatLanguage(e.target.value)} options={["English", "Hindi", "Marathi"].map((language) => ({ value: language, label: language }))} />
                </div>
                <div className="max-h-[55vh] min-h-72 space-y-4 overflow-y-auto bg-[#fbfcfb] px-4 py-5 sm:px-6" aria-live="polite">
                  {chatMessages.map((message, index) => (
                    <div key={`${message.role}-${index}`} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[92%] rounded-2xl px-4 py-3 sm:max-w-[82%] ${message.role === "user" ? "rounded-br-md bg-emerald-800 text-white" : "rounded-bl-md border border-slate-200 bg-white text-slate-700 shadow-sm"}`}>
                        {message.provider === "pdf-extractive" && <div className="mb-2 inline-flex rounded-full bg-amber-50 px-2.5 py-1 text-[10px] font-semibold text-amber-800">PDF excerpts · AI summary unavailable</div>}
                        <div className="whitespace-pre-wrap text-sm leading-6">{message.content}</div>
                        {message.references && message.references.length > 0 && <div className="mt-3 border-t border-slate-200 pt-2.5"><div className="mb-1.5 text-[10px] font-bold uppercase tracking-wider text-emerald-800">Source references & evidence notes</div><ul className="space-y-2">{message.references.map((citation, citationIndex) => {
                          const doiUrl = citation.doi ? citation.doi.startsWith("http") ? citation.doi : `https://doi.org/${citation.doi}` : null;
                          const href = citation.source_url || doiUrl;
                          return <li key={`${citation.title}-${citation.page_number}-${citationIndex}`} className="text-[11px] leading-5 text-slate-600"><div><span className="mr-1 font-bold">[{citation.source_index}]</span>{href ? <a href={href} target="_blank" rel="noreferrer" className="font-semibold text-emerald-800 underline">{citation.title}</a> : <strong>{citation.title}</strong>}{citation.publication_year ? ` (${citation.publication_year})` : ""} — p. {citation.page_number}{citation.authors?.length ? ` · ${citation.authors.join(", ")}` : ""}{citation.doi ? ` · DOI ${citation.doi.replace(/^https?:\/\/doi\.org\//, "")}` : ""}</div>{citation.excerpt && <blockquote className="mt-1.5 border-l-2 border-emerald-300 pl-2.5 text-slate-500">Evidence note: “{citation.excerpt}”</blockquote>}</li>;
                        })}</ul></div>}
                        {message.uncertainty && <p className="mt-2 border-t border-slate-200 pt-2 text-[11px] leading-5 text-slate-500">{message.uncertainty}</p>}
                      </div>
                    </div>
                  ))}
                  {chatLoading && <div className="text-xs text-slate-500" role="status">Checking available evidence…</div>}
                </div>
                <form onSubmit={handleChatSubmit} className="border-t border-slate-100 bg-white p-4 sm:p-5">
                  <label className="sr-only" htmlFor="farmer-question">Your agricultural question</label>
                  <div className="flex items-end gap-2">
                    <textarea id="farmer-question" value={chatInput} onChange={(e) => setChatInput(e.target.value)} rows={2} placeholder="Ask about irrigation, crop health, pests or soil…" className="min-h-12 flex-1 resize-y rounded-xl border border-slate-200 px-3.5 py-3 text-sm outline-none focus:border-emerald-500 focus:ring-4 focus:ring-emerald-50" />
                    <button type="button" disabled title="Voice input is a prototype control; speech recognition is not connected" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-slate-200 text-slate-400 disabled:cursor-not-allowed"><Icon name="mic" size={18} /></button>
                    <PrimaryButton type="submit" disabled={!chatInput.trim() || chatLoading} className="h-11 w-11 shrink-0 !px-0" aria-label="Send message"><Icon name="arrow" size={18} /></PrimaryButton>
                  </div>
                  {chatError && <p role="alert" className="mt-2 text-xs text-rose-700">{chatError}</p>}
                  <div className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-400"><span>Answers may be uncertain. Verify important decisions with local experts.</span><span>Voice input not connected</span></div>
                </form>
              </Panel>
            </div>
          )}
        </main>
      </div>

      <nav aria-label="Mobile navigation" className="fixed inset-x-0 bottom-0 z-40 overflow-x-auto border-t border-slate-200 bg-white/95 px-2 pt-2 pb-[calc(0.5rem+env(safe-area-inset-bottom))] shadow-[0_-5px_20px_rgba(15,23,42,0.08)] backdrop-blur lg:hidden">
        <div className="mx-auto grid w-full max-w-2xl grid-cols-6 gap-1">
          {modules.map((item) => <button key={item.id} title={item.label} onClick={() => setActiveModule(item.id)} className={`flex min-h-12 min-w-0 flex-col items-center justify-center gap-1 rounded-xl px-0.5 text-[9px] font-semibold leading-tight sm:text-[10px] ${activeModule === item.id ? "bg-emerald-50 text-emerald-800" : "text-slate-500 hover:bg-slate-50"}`}><Icon name={item.icon} size={17} /><span className="truncate">{({ overview: "Home", irrigation: "Water", "crop-health": "Health", treatments: "IPM", growth: "Growth", assistant: "Ask" } as Record<ModuleId, string>)[item.id]}</span></button>)}
        </div>
      </nav>
    </div>
  );
}
