"use client";
import { useState } from "react";

interface AuthPageProps {
  onAuth: (email: string, password: string, isRegister: boolean) => void;
  loading: boolean;
  error: string | null;
}

export default function AuthPage({ onAuth, loading, error }: AuthPageProps) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    onAuth(email, password, isRegister);
  };

  return (
    <div className="flex h-screen bg-animated items-center justify-center px-4 relative overflow-hidden">
      {/* Background orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-blue-600/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-emerald-600/5 rounded-full blur-[80px] pointer-events-none" />

      <div className="w-full max-w-sm space-y-8 scale-in">
        {/* Logo */}
        <div className="text-center space-y-4">
          <div className="relative inline-block">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 via-purple-500 to-blue-500 flex items-center justify-center text-2xl mx-auto shadow-2xl glow-violet float">
              ✦
            </div>
          </div>
          <div>
            <h1 className="text-white text-2xl font-bold tracking-tight gradient-text">OmniAI</h1>
            <p className="text-white/40 text-sm mt-1">Your multi-agent AI assistant</p>
          </div>
        </div>

        {/* Card */}
        <div className="glass-strong rounded-2xl p-6 space-y-4 shadow-2xl">
          <div className="text-center mb-2">
            <h2 className="text-white font-semibold text-lg">
              {isRegister ? "Create account" : "Welcome back"}
            </h2>
            <p className="text-white/30 text-xs mt-1">
              {isRegister ? "Join OmniAI today" : "Sign in to continue"}
            </p>
          </div>

          <form onSubmit={submit} className="space-y-3">
            <div className="relative group">
              <input
                type="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-white/5 border border-white/10 group-hover:border-white/20 focus:border-violet-500/60 focus:bg-white/8 rounded-xl px-4 py-3 text-sm text-white placeholder-white/25 transition-all"
                style={{ outline: "none" }}
              />
            </div>
            <div className="relative group">
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full bg-white/5 border border-white/10 group-hover:border-white/20 focus:border-violet-500/60 focus:bg-white/8 rounded-xl px-4 py-3 text-sm text-white placeholder-white/25 transition-all"
                style={{ outline: "none" }}
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2.5 fade-in-up">
                <span className="text-red-400 text-xs">⚠</span>
                <p className="text-red-400/90 text-xs">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full relative overflow-hidden bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 disabled:opacity-50 text-white rounded-xl py-3 text-sm font-semibold transition-all shadow-lg shadow-violet-500/20 hover:shadow-violet-500/30 hover:-translate-y-0.5 active:translate-y-0"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Please wait…
                </span>
              ) : (
                isRegister ? "Create account →" : "Sign in →"
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-white/30 text-sm">
          {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="text-violet-400 hover:text-violet-300 font-medium transition-colors"
          >
            {isRegister ? "Sign in" : "Sign up"}
          </button>
        </p>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-2">
          {["🧠 Reasoning", "🔍 Research", "🛠️ Tools", "💾 Memory"].map((f) => (
            <span key={f} className="text-xs text-white/20 bg-white/5 border border-white/8 px-2.5 py-1 rounded-full">
              {f}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
