"use client";
import Sidebar from "@/components/Sidebar";
import AuthPage from "@/components/AuthPage";
import KnowledgeGraphPanel from "@/components/KnowledgeGraphPanel";
import { useAuth } from "@/hooks/useAuth";
import { useState } from "react";

export default function KnowledgeGraphPage() {
  const { user, loading, error, login, register } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (!user) {
    return (
      <AuthPage
        onAuth={(email, password, isRegister) =>
          isRegister ? register(email, password) : login(email, password)
        }
        loading={loading}
        error={error}
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
        <header className="flex items-center gap-3 px-4 py-4 border-b border-white/5 bg-[#0a0a0a] flex-shrink-0">
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
            <h1 className="text-sm font-medium text-white/80">Knowledge Graph</h1>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto px-4 py-6">
            <KnowledgeGraphPanel token={user?.token ?? null} isFullPage={true} />
        </main>
      </div>
    </div>
  );
}
