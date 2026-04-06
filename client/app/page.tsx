"use client";
import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import ChatInput from "@/components/ChatInput";
import ChatSessionsSidebar from "@/components/ChatSessionsSidebar";
import AuthPage from "@/components/AuthPage";
import { useChat } from "@/hooks/useChat";
import { useAuth } from "@/hooks/useAuth";

export default function Home() {
  const { user, loading: authLoading, error: authError, login, register, logout } = useAuth();
  const { messages, loading, historyLoading, sendMessage, startNewChat } = useChat(user?.token ?? null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sessionsOpen, setSessionsOpen] = useState(true); // Automatically open sessions by default on desktop
  const [uploadCount, setUploadCount] = useState(0);

  if (!user) {
    return (
      <AuthPage
        onAuth={(email, password, isRegister) =>
          isRegister ? register(email, password) : login(email, password)
        }
        loading={authLoading}
        error={authError}
      />
    );
  }

  return (
    <div className="flex h-screen bg-[#0a0a0a] text-white overflow-hidden">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        uploadCount={uploadCount}
        token={user?.token ?? null}
      />

      <ChatSessionsSidebar
        isOpen={sessionsOpen}
        onClose={() => setSessionsOpen(false)}
        token={user?.token ?? null}
      />

      <div className="flex flex-col flex-1 min-w-0">
        <header className="flex items-center gap-3 px-4 py-4 border-b border-white/5 bg-[#0a0a0a] flex-shrink-0">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5 text-white/50 transition-colors"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <button
              onClick={() => setSessionsOpen(!sessionsOpen)}
              className="hidden lg:flex w-8 h-8 items-center justify-center rounded-lg hover:bg-white/5 text-white/50 transition-colors"
              title="Toggle Sessions"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
              </svg>
            </button>
            <button
              onClick={() => setSessionsOpen(true)}
              className="lg:hidden w-8 h-8 flex items-center justify-center rounded-lg hover:bg-white/5 text-white/50 transition-colors"
              title="View History"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
          </div>
          <div className="flex-1">
            <h1 className="text-sm font-medium text-white/80">OmniAI</h1>
            <p className="text-xs text-white/30">Multi-agent . Reasoning . Research . Tools . Memory</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-emerald-400/70 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Live
            </div>
            <div className="flex items-center gap-2">
              <span className="text-white/30 text-xs hidden sm:block">{user.email}</span>
              <button
                onClick={logout}
                className="text-xs text-white/30 hover:text-white/70 bg-white/5 hover:bg-white/10 border border-white/8 px-2.5 py-1 rounded-lg transition-all"
              >
                Sign out
              </button>
            </div>
          </div>
        </header>

        <div className="flex flex-col flex-1 min-h-0 max-w-3xl w-full mx-auto">
          <ChatWindow messages={messages} loading={loading} historyLoading={historyLoading} />
          <ChatInput
            onSend={sendMessage}
            loading={loading}
            onClear={startNewChat}
            onUploadSuccess={() => setUploadCount((c) => c + 1)}
            token={user?.token ?? null}
          />
        </div>
      </div>
    </div>
  );
}