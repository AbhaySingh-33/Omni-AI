"use client";

import { useState } from "react";
import AuthPage from "@/components/AuthPage";
import Sidebar from "@/components/Sidebar";
import LegalRagPanel from "@/components/LegalRagPanel";
import { useAuth } from "@/hooks/useAuth";

export default function LegalRagPage() {
  const { user, loading: authLoading, error: authError, login, register, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

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
        uploadCount={0}
        token={user?.token ?? null}
      />

      <div className="flex flex-col flex-1 min-w-0">
        <header className="flex items-center gap-3 px-4 py-4 border-b border-white/5 bg-[#0a0a0a] shrink-0">
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
          <div className="flex-1">
            <h1 className="text-sm font-medium text-white/80">Legal RAG</h1>
            <p className="text-xs text-white/30">Hierarchical tree + page-indexed graph traversal (vectorless)</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-cyan-400/70 bg-cyan-400/10 border border-cyan-400/20 px-2.5 py-1 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
              Legal Mode
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

        <main className="flex-1 overflow-y-auto px-4 py-6">
          <LegalRagPanel token={user.token} />
        </main>
      </div>
    </div>
  );
}
