"use client";
import React from "react";
import { useChat } from "@/hooks/useChat";

interface ChatSessionsSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  token: string | null;
}

export default function ChatSessionsSidebar({ isOpen, onClose, token }: ChatSessionsSidebarProps) {
  const { sessions, activeSessionId, startNewChat, loadSession, deleteChatHistory } = useChat(token);
  const safeSessions = Array.isArray(sessions) ? sessions : [];

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden" onClick={onClose} />

      <aside
        className={`
          fixed lg:relative inset-y-0 left-0 z-50 lg:z-auto
          w-64 flex flex-col border-r border-white/5
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
        style={{ background: "rgba(8,8,16,0.97)", backdropFilter: "blur(20px)" }}
      >
        <div className="p-4 border-b border-white/5">
          <button
            onClick={() => { startNewChat(); if (window.innerWidth < 1024) onClose(); }}
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all font-medium text-sm text-white hover:-translate-y-0.5 active:translate-y-0"
            style={{
              background: "linear-gradient(135deg, rgba(124,58,237,0.2), rgba(37,99,235,0.2))",
              border: "1px solid rgba(124,58,237,0.25)",
              boxShadow: "0 4px 12px rgba(124,58,237,0.1)",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.boxShadow = "0 4px 20px rgba(124,58,237,0.2)";
              (e.currentTarget as HTMLElement).style.borderColor = "rgba(124,58,237,0.4)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.boxShadow = "0 4px 12px rgba(124,58,237,0.1)";
              (e.currentTarget as HTMLElement).style.borderColor = "rgba(124,58,237,0.25)";
            }}
          >
            <span className="text-lg leading-none">✦</span>
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {safeSessions.length === 0 ? (
            <div className="text-center p-6 space-y-2">
              <div className="text-2xl opacity-30">💬</div>
              <p className="text-white/25 text-xs">No past sessions yet</p>
            </div>
          ) : (
            safeSessions.map((session) => {
              const isActive = activeSessionId === session.id;
              const date = new Date(session.createdAt);
              const dateStr = date.toLocaleDateString(undefined, { month: "short", day: "numeric" });

              return (
                <div
                  key={session.id}
                  className="group relative flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition-all"
                  style={isActive ? {
                    background: "rgba(124,58,237,0.12)",
                    border: "1px solid rgba(124,58,237,0.2)",
                    boxShadow: "0 0 12px rgba(124,58,237,0.08)",
                  } : {
                    border: "1px solid transparent",
                  }}
                  onClick={() => { loadSession(session.id); if (window.innerWidth < 1024) onClose(); }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.04)";
                      (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.06)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      (e.currentTarget as HTMLElement).style.background = "transparent";
                      (e.currentTarget as HTMLElement).style.borderColor = "transparent";
                    }
                  }}
                >
                  <span className="text-base opacity-50">💬</span>
                  <div className="flex-1 min-w-0 pr-6">
                    <p className={`text-sm font-medium truncate ${isActive ? "text-violet-200" : "text-white/55"}`}>
                      {session.title}
                    </p>
                    <p className="text-[10px] text-white/25 mt-0.5">{dateStr}</p>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteChatHistory(session.id); }}
                    className="absolute right-2 opacity-0 group-hover:opacity-100 p-1.5 hover:bg-rose-500/15 text-rose-400/50 hover:text-rose-400 rounded-lg transition-all"
                    title="Delete session"
                  >
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                  </button>
                </div>
              );
            })
          )}
        </div>
      </aside>
    </>
  );
}
