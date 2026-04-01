"use client";

import { useState, useEffect, useMemo } from "react";
import { useEmotion, EmotionTrendEntry, EmotionAnalytics } from "@/hooks/useEmotion";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";
import { AlertCircle, TrendingUp, Activity, CheckCircle, BrainCircuit } from "lucide-react";

// --- Configuration ---
const EMOTION_EMOJI: Record<string, string> = {
  joy: "😊", sadness: "😢", anger: "😠", fear: "😨",
  anxiety: "😰", stress: "😫", self_doubt: "😔",
  hopelessness: "🥀", neutral: "😐",
};

const EMOTION_LABEL: Record<string, string> = {
  joy: "Joyful", sadness: "Sad", anger: "Angry", fear: "Fearful",
  anxiety: "Anxious", stress: "Stressed", self_doubt: "Self-Doubt",
  hopelessness: "Hopeless", neutral: "Neutral",
};

const RISK_CONFIG: Record<string, { color: string; bg: string; border: string; label: string }> = {
  low:      { color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20", label: "Low Risk" },
  moderate: { color: "text-yellow-400",  bg: "bg-yellow-500/10",  border: "border-yellow-500/20",  label: "Moderate" },
  high:     { color: "text-orange-400",  bg: "bg-orange-500/10",  border: "border-orange-500/20",  label: "High Risk" },
  critical: { color: "text-red-400",     bg: "bg-red-500/10",     border: "border-red-500/20",     label: "Critical" },
};

const MOOD_SCORES: Record<string, number> = {
  joy: 90, neutral: 60, stress: 35, anxiety: 30,
  fear: 25, sadness: 20, anger: 20, self_doubt: 15, hopelessness: 5
};

const INTENSITY_BAR: Record<string, number> = {
  low: 25, moderate: 50, high: 75, severe: 100,
};

// --- Custom Chart Tooltip ---
function CustomTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-[#111] border border-white/10 rounded-xl p-3 shadow-xl backdrop-blur-md">
        <p className="text-white/40 text-xs mb-1">
          {new Date(label).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
        </p>
        <div className="flex items-center gap-2">
          <span className="text-xl">{EMOTION_EMOJI[data.emotion] || "😐"}</span>
          <span className="text-sm text-white font-medium">{EMOTION_LABEL[data.emotion] || data.emotion}</span>
        </div>
        <p className="text-emerald-400 text-xs mt-1.5 font-medium">Mood Score: {data.score}</p>
      </div>
    );
  }
  return null;
}

// --- Main Dashboard Component ---
interface EmotionDashboardProps {
  token: string | null;
  refreshTrigger?: number;
}

export default function EmotionDashboard({ token, refreshTrigger }: EmotionDashboardProps) {
  const { analytics, loading, error, refresh, acknowledgeAlert } = useEmotion(token);

  useEffect(() => {
    if (refreshTrigger && refreshTrigger > 0) {
      const timer = setTimeout(() => refresh(), 1500); 
      return () => clearTimeout(timer);
    }
  }, [refreshTrigger, refresh]);

  if (loading && !analytics) {
    return (
      <div className="flex items-center justify-center p-12 min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
          <p className="text-white/40 font-medium text-sm animate-pulse">Loading mood insights...</p>
        </div>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="flex items-center justify-center p-12 min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <AlertCircle className="w-10 h-10 text-white/20" />
          <p className="text-white/30 text-sm">{error ? `Error: ${error}` : "No emotion data available yet."}</p>
        </div>
      </div>
    );
  }

  const current = analytics.current_emotion;
  const hasData = current !== null;
  const alerts = analytics.alerts || [];

  // Transform trend data for recharts
  const chartData = analytics.trend?.map((entry) => {
    return {
      date: entry.created_at,
      score: MOOD_SCORES[entry.emotion] || 50,
      emotion: entry.emotion,
      confidence: entry.confidence,
    };
  }) || [];

  const isRecentNegative = hasData && current && ["sadness", "anger", "fear", "anxiety", "stress", "self_doubt", "hopelessness"].includes(current.emotion);
  
  if (!hasData) {
    return (
      <div className="flex items-center justify-center p-12 min-h-[60vh]">
        <div className="flex flex-col items-center gap-3 text-center bg-[#111] p-12 rounded-3xl border border-white/5">
          <BrainCircuit className="w-12 h-12 text-white/10 mb-2" />
          <p className="text-white/80 font-medium text-lg">Start your journey</p>
          <p className="text-white/40 text-sm max-w-sm">
            Chat with the AI to begin tracking your mood and detecting mental well-being trends.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      
      {/* Overview Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Current Mood Card */}
        <div className="lg:col-span-2 relative overflow-hidden bg-linear-to-br from-[#111] to-[#0a0a0a] rounded-3xl p-6 border border-white/5 shadow-2xl flex flex-col justify-between group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-[80px] -mr-20 -mt-20 pointer-events-none group-hover:bg-emerald-500/20 transition-all duration-700" />
          
          <div className="relative z-10 flex items-start justify-between">
            <div>
              <p className="text-white/30 uppercase tracking-widest text-xs font-semibold mb-4">Current Mood</p>
              <div className="flex items-center gap-4">
                <span className="text-5xl drop-shadow-lg scale-110">{EMOTION_EMOJI[current.emotion] || "😐"}</span>
                <div>
                  <h2 className="text-3xl font-bold text-white tracking-tight">
                    {EMOTION_LABEL[current.emotion] || current.emotion}
                  </h2>
                  <p className="text-sm font-medium text-white/40 mt-1 capitalize">
                    Intensity: {current.intensity || "Low"}
                  </p>
                </div>
              </div>
            </div>

            {current.risk_level && current.risk_level !== "low" && (
              <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full border shadow-sm backdrop-blur-md ${
                  RISK_CONFIG[current.risk_level]?.color || ""
                } ${RISK_CONFIG[current.risk_level]?.bg || ""} ${
                  RISK_CONFIG[current.risk_level]?.border || ""
                }`}
              >
                <Activity className="w-4 h-4" />
                <span className="text-sm font-semibold tracking-wide">
                  {RISK_CONFIG[current.risk_level]?.label || current.risk_level}
                </span>
              </div>
            )}
            {(!current.risk_level || current.risk_level === "low") && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 shadow-sm backdrop-blur-md">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm font-semibold tracking-wide">Low Risk</span>
              </div>
            )}
          </div>

          <div className="mt-8 relative z-10">
            <div className="flex items-center justify-between text-xs text-white/30 mb-2 font-medium">
              <span>Low</span>
              <span>Moderate</span>
              <span>High</span>
              <span>Severe</span>
            </div>
            <div className="h-2.5 bg-black/40 rounded-full overflow-hidden border border-white/5 shadow-inner">
              <div
                className="h-full rounded-full transition-all duration-1000 ease-out"
                style={{
                  width: `${INTENSITY_BAR[current.intensity] || 25}%`,
                  backgroundImage:
                    current.intensity === "severe"
                      ? "linear-gradient(to right, #f97316, #ef4444)"
                      : current.intensity === "high"
                      ? "linear-gradient(to right, #eab308, #f97316)"
                      : current.intensity === "moderate"
                      ? "linear-gradient(to right, #34d399, #eab308)"
                      : "linear-gradient(to right, #059669, #34d399)",
                }}
              />
            </div>
          </div>
        </div>

        {/* Alerts Pane */}
        <div className="bg-[#111] rounded-3xl p-6 border border-white/5 shadow-2xl flex flex-col h-full lg:min-h-[220px]">
          <div className="flex flex-row items-center justify-between mb-4">
            <p className="text-white/30 uppercase tracking-widest text-xs font-semibold">Active Alerts</p>
            <div className="bg-white/5 p-1.5 rounded-lg border border-white/5">
               <AlertCircle className="w-4 h-4 text-white/30" />
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-1 space-y-3 custom-scrollbar">
            {alerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center text-white/30 py-4">
                <CheckCircle className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-sm">No active alerts</p>
                <p className="text-xs mt-1">Status looking good</p>
              </div>
            ) : (
              alerts.map((alert) => {
                const cfg = RISK_CONFIG[alert.risk_level] || RISK_CONFIG.moderate;
                return (
                  <div
                    key={alert.id}
                    className={`flex items-start gap-3 p-3 rounded-xl border relative shadow-sm hover:shadow-md transition-shadow ${cfg.bg} ${cfg.border}`}
                  >
                    <div className="mt-0.5"><AlertCircle className={`w-4 h-4 ${cfg.color}`} /></div>
                    <div className="flex-1 min-w-0 pr-6">
                      <p className={`text-sm font-semibold tracking-wide ${cfg.color}`}>
                        {alert.alert_type === "crisis" ? "Crisis Detected" : alert.alert_type === "risk_escalation" ? "Risk Increasing" : "Trend Alert"}
                      </p>
                      <p className="text-xs text-white/60 mt-1 leading-relaxed">{alert.details}</p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        acknowledgeAlert(alert.id);
                      }}
                      className="absolute top-2 right-2 text-white/30 hover:text-white/70 hover:bg-white/10 p-1.5 rounded-lg transition-colors"
                      title="Dismiss alert"
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>

      </div>

      {/* Analytics Chart */}
      {chartData.length > 1 && (
        <div className="bg-[#111] rounded-3xl p-6 border border-white/5 shadow-2xl h-[400px] flex flex-col relative overflow-hidden">
          <div className="flex items-center justify-between mb-8 z-10">
            <div>
              <p className="text-white/30 uppercase tracking-widest text-xs font-semibold mb-1">Emotion Progression</p>
              <h3 className="text-lg font-medium text-white tracking-tight flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-white/40" />
                7-Day Trend Analysis
              </h3>
            </div>
            {/* Soft decorative background glow */}
            <div className="absolute -top-32 -left-32 w-64 h-64 bg-emerald-500/5 rounded-full blur-[100px] pointer-events-none" />
          </div>

          <div className="flex-1 min-h-0 z-10 w-full relative -ml-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={isRecentNegative ? "#f97316" : "#10b981"} stopOpacity={0.4} />
                    <stop offset="95%" stopColor={isRecentNegative ? "#f97316" : "#10b981"} stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(val) => {
                    const d = new Date(val);
                    return `${d.getMonth()+1}/${d.getDate()}`;
                  }}
                  tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  dy={10}
                />
                <YAxis 
                  domain={[0, 100]} 
                  tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  dx={-10}
                  tickFormatter={(val) => {
                     if(val === 100) return "Joy";
                     if(val === 50) return "Neutral";
                     if(val === 0) return "Crisis";
                     return "";
                  }}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1 }} />
                <Area 
                  type="monotone" 
                  dataKey="score" 
                  stroke={isRecentNegative ? "#f97316" : "#10b981"} 
                  strokeWidth={3}
                  fillOpacity={1} 
                  fill="url(#colorScore)" 
                  animationDuration={1500}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Historic Logs Preview */}
      {analytics.history && analytics.history.length > 0 && (
        <div className="bg-[#111] rounded-3xl p-6 border border-white/5 shadow-2xl overflow-hidden mb-6">
          <p className="text-white/30 uppercase tracking-widest text-xs font-semibold mb-6">Recent Records</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {analytics.history.slice(0, 8).map((hist, idx) => (
              <div key={idx} className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors cursor-default group">
                <div className="w-10 h-10 rounded-full bg-black/40 flex items-center justify-center text-xl group-hover:scale-110 transition-transform">
                  {EMOTION_EMOJI[hist.emotion] || "😐"}
                </div>
                <div>
                  <p className="text-sm font-semibold text-white/90">{EMOTION_LABEL[hist.emotion] || hist.emotion}</p>
                  <p className="text-xs text-white/40 mt-0.5">{new Date(hist.date).toLocaleDateString()}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
