"use client";
import { useCallback, useEffect } from "react";
import { Message } from "@/lib/types";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { 
  setMessages, addMessage, setChatLoading, setHistoryLoading, 
  setChatError, clearMessages as clearMessagesAction,
  setSessions, setActiveSessionId
} from "@/store/slices/chatSlice";

const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";

function toUserFacingError(err: unknown): string {
  if (!(err instanceof Error)) return "Something went wrong";
  const msg = err.message || "";
  if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
    return `Cannot connect to AI engine at ${AI_ENGINE_URL}. Please ensure backend server is running.`;
  }
  if (msg.includes("Server error: 401")) {
    return "Your session expired. Please login again.";
  }
  return msg;
}

function normalizeAgent(raw: unknown): Message["agent"] | undefined {
  if (typeof raw !== "string") return undefined;
  const normalized = raw.toLowerCase().trim().replace(/_agent$/, "");
  const aliasMap: Record<string, Message["agent"]> = {
    tool: "tools", tools: "tools",
    reason: "reasoning", reasoning: "reasoning",
    research: "research", memory: "memory",
    router: "router", interview: "interview", finish: "router",
  };
  return aliasMap[normalized];
}

export function useChat(token: string | null) {
  const dispatch = useAppDispatch();
  const chatState = useAppSelector((state) => state.chat);
  const messages = chatState?.messages ?? [];
  const sessions = chatState?.sessions ?? [];
  const activeSessionId = chatState?.activeSessionId ?? null;
  const loading = chatState?.loading ?? false;
  const historyLoading = chatState?.historyLoading ?? false;
  const error = chatState?.error ?? null;

  const authHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const fetchSessions = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${AI_ENGINE_URL}/history/sessions`, { headers: authHeaders, credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        dispatch(setSessions(data.sessions || []));
        return data.sessions || [];
      }
    } catch {
      // silently fail
    }
    return [];
  }, [token, dispatch]);

  const loadSession = useCallback(async (sessionId: string) => {
    if (!token) return;
    dispatch(setHistoryLoading(true));
    dispatch(setActiveSessionId(sessionId));
    try {
      const res = await fetch(`${AI_ENGINE_URL}/history/${sessionId}`, { headers: authHeaders, credentials: "include" });
      if (!res.ok) return;
      const data = await res.json();
      const loaded: Message[] = (data.messages ?? []).map(
        (m: { role: "user" | "assistant"; content: string; agent?: string }, i: number) => ({ 
          id: `history-${i}`, role: m.role, content: m.content,
          timestamp: new Date().toISOString(), agent: normalizeAgent(m.agent), fromHistory: true 
        })
      );
      dispatch(setMessages(loaded));
    } catch {
    } finally {
      dispatch(setHistoryLoading(false));
    }
  }, [token, dispatch]);

  const startNewChat = useCallback(() => {
    const newId = crypto.randomUUID();
    dispatch(setActiveSessionId(newId));
    dispatch(clearMessagesAction());
  }, [dispatch]);

  // Initial load
  useEffect(() => {
    if (!token) { dispatch(setHistoryLoading(false)); return; }
    if (activeSessionId && messages.length > 0) { dispatch(setHistoryLoading(false)); return; } // avoid reload

    const init = async () => {
      const loadedSessions = await fetchSessions();
      if (loadedSessions.length > 0) {
        // load latest session
        loadSession(loadedSessions[0].id);
      } else {
        startNewChat();
        dispatch(setHistoryLoading(false));
      }
    };
    init();
  }, [token]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    let currentSessionId = activeSessionId;
    if (!currentSessionId) {
      currentSessionId = crypto.randomUUID();
      dispatch(setActiveSessionId(currentSessionId));
    }

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content, timestamp: new Date().toISOString() };
    dispatch(addMessage(userMsg));
    dispatch(setChatLoading(true));
    dispatch(setChatError(null));

    try {
      const res = await fetch(`${AI_ENGINE_URL}/chat`, {
        method: "POST",
        credentials: "include",
        headers: authHeaders,
        body: JSON.stringify({ message: content, session_id: currentSessionId }),
      });
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      dispatch(addMessage({
        id: crypto.randomUUID(), role: "assistant", content: data.response,
        timestamp: new Date().toISOString(), agent: normalizeAgent(data.agent), emotion: data.emotion || undefined,
      }));
      // trigger fetch sessions in background to update title if it's a new chat
      fetchSessions();
    } catch (err) {
      const msg = toUserFacingError(err);
      dispatch(setChatError(msg));
      dispatch(addMessage({ id: crypto.randomUUID(), role: "assistant", content: `⚠️ ${msg}`, timestamp: new Date().toISOString() }));
    } finally {
      dispatch(setChatLoading(false));
    }
  }, [token, dispatch, activeSessionId, fetchSessions]);

  const deleteChatHistory = useCallback(async (sessionId: string) => {
    if (!token) return;
    try {
      const res = await fetch(`${AI_ENGINE_URL}/history/${sessionId}`, {
        method: "DELETE",
        credentials: "include",
        headers: authHeaders,
      });
      if (!res.ok) throw new Error("Failed to delete history on server.");
      await fetchSessions();
      if (activeSessionId === sessionId) {
        startNewChat();
      }
    } catch (err) {
      console.error(err);
    }
  }, [token, dispatch, activeSessionId, fetchSessions, startNewChat]);

  return { 
    messages, sessions, activeSessionId, loading, historyLoading, error, 
    sendMessage, startNewChat, loadSession, deleteChatHistory 
  };
}
