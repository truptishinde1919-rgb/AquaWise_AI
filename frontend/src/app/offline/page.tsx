export default function OfflinePage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4 text-center text-slate-700">
      <div className="max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">AquaWise AI</p>
        <h1 className="mt-3 text-2xl font-bold text-slate-900">You are offline</h1>
        <p className="mt-3 text-sm text-slate-600">
          The dashboard can’t reach the network right now. Reconnect to use live water and crop assessments.
        </p>
      </div>
    </main>
  );
}
