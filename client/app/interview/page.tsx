"use client";
import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import AuthPage from "@/components/AuthPage";
import { useAuth } from "@/hooks/useAuth";
import ResumeBuilder from "@/components/interview/ResumeBuilder";
import MockInterview from "@/components/interview/MockInterview";
import InterviewQuestions from "@/components/interview/InterviewQuestions";
import InterviewDashboard from "@/components/interview/InterviewDashboard";

type Tab = "dashboard" | "resume" | "questions" | "mock";

export default function InterviewPage() {
  const { user, loading: authLoading, error: authError, login, register, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");

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

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: "dashboard", label: "Dashboard", icon: "📊" },
    { id: "resume", label: "Resume", icon: "📄" },
    { id: "questions", label: "Questions", icon: "❓" },
    { id: "mock", label: "Mock Interview", icon: "🎤" },
  ];

  return (
    <div className="flex h-screen bg-[#0a0a0a] text-white overflow-hidden">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        uploadCount={0}
        token={user?.token ?? null}
      />

      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
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
            <h1 className="text-sm font-medium text-white/80">Interview Prep</h1>
            <p className="text-xs text-white/30">Your AI-powered job interview coach</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs text-purple-400/70 bg-purple-400/10 border border-purple-400/20 px-2.5 py-1 rounded-full">
              <span className="text-sm">💼</span>
              Career Mode
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

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-[#0d0d0d] overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                  : "text-white/50 hover:text-white hover:bg-white/5 border border-transparent"
              }`}
            >
              <span>{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {activeTab === "dashboard" && <InterviewDashboard token={user.token} />}
          {activeTab === "resume" && <ResumeBuilder token={user.token} />}
          {activeTab === "questions" && <InterviewQuestions token={user.token} />}
          {activeTab === "mock" && <MockInterview token={user.token} />}
        </div>
      </div>
    </div>
  );
}
