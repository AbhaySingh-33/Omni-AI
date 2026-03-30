"use client";
import { useCallback, useEffect } from "react";
import { Message } from "@/lib/types";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setMessages, addMessage, setChatLoading, setHistoryLoading, setChatError, clearMessages as clearMessagesAction } from "@/store/slices/chatSlice";

const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";

export function useChat(token: string | null) {
  const dispatch = useAppDispatch();
  const { messages, loading, historyLoading, error } = useAppSelector((state) => state.chat);

  const authHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  useEffect(() => {
    if (!token) { dispatch(setHistoryLoading(false)); return; }
    if (messages.length > 0) { dispatch(setHistoryLoading(false)); return; } // avoid reload if persisted

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
        dispatch(setMessages(loaded));
      } catch {
        // silently fail
      } finally {
        dispatch(setHistoryLoading(false));
      }
    };
    loadHistory();
  }, [token, dispatch, messages.length]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content, timestamp: new Date() };
    dispatch(addMessage(userMsg));
    dispatch(setChatLoading(true));
    dispatch(setChatError(null));

    try {
      const res = await fetch(`${AI_ENGINE_URL}/chat`, {
        method: "POST",
        headers: authHeaders,
        body: JSON.stringify({ message: content }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      dispatch(addMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
        agent: data.agent ?? undefined,
      }));
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Something went wrong";  
      dispatch(setChatError(msg));
      dispatch(addMessage({ id: crypto.randomUUID(), role: "assistant", content: `\u26a0\ufe0f ${msg}`, timestamp: new Date() }));
    } finally {
      dispatch(setChatLoading(false));
    }
  }, [token, dispatch]);

  const clearMessages = useCallback(() => dispatch(clearMessagesAction()), [dispatch]);

  return { messages, loading, historyLoading, error, sendMessage, clearMessages };
}
