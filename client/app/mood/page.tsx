"use client";

import { useEffect, useState } from "react";
import EmotionDashboard from "@/components/EmotionDashboard";
import { useAuth } from "@/hooks/useAuth";

export default function MoodTrackerPage() {
  const { user } = useAuth();
  const token = user?.token ?? null;
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0a0a0a] overflow-y-auto">
      {/* Header */}
      <header className="px-6 py-5 border-b border-white/5 bg-[#0a0a0a]/80 backdrop-blur-md sticky top-0 z-10 flex items-center gap-4">
        <div className="p-2 bg-emerald-500/10 rounded-xl border border-emerald-500/20 text-emerald-400">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 3v18h18" />
            <path d="m19 9-5 5-4-4-3 3" />
          </svg>
        </div>
        <div>
          <h1 className="text-xl font-semibold text-white tracking-tight">Mood Tracker Dashboard</h1>
          <p className="text-sm text-white/40">Real-time mental well-being insights and analytics</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6 max-w-7xl mx-auto w-full flex-1">
        <EmotionDashboard token={token} />
      </main>
    </div>
  );
}
