"use client";
import { useState, useEffect, useCallback } from "react";
import { useAppDispatch } from "@/store/hooks";
import { forceLogout } from "@/store/authUtils";

const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";

export interface EmotionEntry {
  date: string;
  emotion: string;
  confidence: number;
  had_crisis: boolean;
  message_count: number;
}

export interface EmotionTrendEntry {
  scores: Record<string, number>;
  confidence: number;
  emotion: string;
  created_at: string;
}

export interface EmotionAlert {
  id: number;
  alert_type: string;
  risk_level: string;
  details: string;
  created_at: string;
}

export interface CurrentEmotion {
  emotion: string;
  confidence: number;
  intensity: string;
  risk_level: string;
  is_crisis: boolean;
  created_at: string;
}

export interface EmotionAnalytics {
  current_emotion: CurrentEmotion | null;
  history: EmotionEntry[];
  trend: EmotionTrendEntry[];
  alerts: EmotionAlert[];
}

export function useEmotion(token: string | null) {
  const dispatch = useAppDispatch();
  const [analytics, setAnalytics] = useState<EmotionAnalytics | null>(null);
  const [loading, setLoading] = useState(true); // default to true
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/emotion/analytics`, {
        credentials: "include",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        forceLogout(dispatch);
        return;
      }
      if (!res.ok) throw new Error(`Error: ${res.status}`);
      const data: EmotionAnalytics = await res.json();
      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load emotion data");
    } finally {
      setLoading(false);
    }
  }, [token]);

  const acknowledgeAlert = useCallback(async (alertId: number) => {
    if (!token) return;
    try {
      const res = await fetch(`${AI_ENGINE_URL}/emotion/alerts/${alertId}/acknowledge`, {
        method: "POST",
        credentials: "include",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        forceLogout(dispatch);
        return;
      }
      // Refresh analytics after acknowledging
      fetchAnalytics();
    } catch {
      // silently fail
    }
  }, [token, fetchAnalytics, dispatch]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return { analytics, loading, error, refresh: fetchAnalytics, acknowledgeAlert };
}
