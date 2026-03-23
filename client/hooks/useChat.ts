"use client";
import { useState, useCallback, useEffect } from "react";
import { Message } from "@/lib/types";

const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";

export function useChat(token: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const authHeaders = token
    ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` }
    : { "Content-Type": "application/json" };

  useEffect(() => {
    if (!token) { setHistoryLoading(false); return; }
    const loadHistory = async () => {
      try {
        const res = await fetch(`${AI_ENGINE_URL}/history`, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) return;
        const data = await res.json();
        const loaded: Message[] = (data.messages ?? []).map(
          (m: { role: "user" | "assistant"; content: string }, i: number) => ({
            id: `history-${i}`,
            role: m.role,
            content: m.content,
            timestamp: new Date(),
            fromHistory: true,
          })
        );
        setMessages(loaded);
      } catch {
        // silently fail
      } finally {
        setHistoryLoading(false);
      }
    };
    loadHistory();
  }, [token]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${AI_ENGINE_URL}/chat`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ message: content }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "assistant", content: data.response, timestamp: new Date() }]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Something went wrong";
      setError(msg);
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "assistant", content: `⚠️ ${msg}`, timestamp: new Date() }]);
    } finally {
      setLoading(false);
    }
  }, [token]);

  const clearMessages = useCallback(() => setMessages([]), []);

  return { messages, loading, historyLoading, error, sendMessage, clearMessages };
}
