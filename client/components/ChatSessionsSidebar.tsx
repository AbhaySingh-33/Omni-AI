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
      {/* Mobile overlay */}
      <div 
        className="fixed inset-0 bg-black/60 z-40 lg:hidden" 
        onClick={onClose} 
      />
      
      <aside className={`
        fixed lg:relative inset-y-0 left-0 z-50 lg:z-auto
        w-64 flex flex-col bg-[#080808] border-r border-white/5
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
      `}>
        <div className="p-4 border-b border-white/5">
          <button 
            onClick={() => { startNewChat(); if (window.innerWidth < 1024) onClose(); }}
            className="w-full flex items-center gap-3 px-4 py-2.5 bg-white/10 hover:bg-white/15 text-white rounded-xl transition-colors font-medium text-sm border border-white/10 shadow-sm"
          >
            <span className="text-lg leading-none opactity-90">➕</span>
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          {safeSessions.length === 0 ? (
            <div className="text-center p-4">
              <span className="text-white/30 text-xs">No past sessions</span>
            </div>
          ) : (
            safeSessions.map((session) => {
              const isActive = activeSessionId === session.id;
              // Format date nicely
              const date = new Date(session.createdAt);
              const dateStr = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
              
              return (
                <div 
                  key={session.id} 
                  className={`group relative flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                    isActive ? "bg-white/10 text-white" : "hover:bg-white/5 text-white/60 hover:text-white/90"
                  }`}
                  onClick={() => {
                    loadSession(session.id);
                    if (window.innerWidth < 1024) onClose();
                  }}
                >
                  <span className="text-base opacity-70">💬</span>
                  <div className="flex-1 min-w-0 pr-6">
                    <p className="text-sm font-medium truncate">{session.title}</p>
                    <p className="text-[10px] opacity-50 mt-0.5">{dateStr}</p>
                  </div>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteChatHistory(session.id);
                    }}
                    className={`absolute right-2 opacity-0 group-hover:opacity-100 p-1.5 hover:bg-rose-500/20 text-rose-400/70 hover:text-rose-400 rounded-md transition-all ${isActive ? 'bg-black/20' : ''}`}
                    title="Delete session"
                  >
                    🗑️
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
