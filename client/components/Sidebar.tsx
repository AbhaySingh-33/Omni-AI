"use client";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AgentInfo } from "@/lib/types";
import DocumentsPanel from "@/components/DocumentsPanel";
import { useDocuments } from "@/hooks/useDocuments";

const agents: AgentInfo[] = [
  { id: "router",    label: "Router",    description: "Classifies intent & delegates",   color: "violet",  icon: "⚡" },
  { id: "reasoning", label: "Reasoning", description: "General Q&A via DSPy + Gemini",   color: "blue",    icon: "🧠" },
  { id: "research",  label: "Research",  description: "RAG over your documents",          color: "emerald", icon: "🔍" },
  { id: "tools",     label: "Tools",     description: "Web search, files, terminal",      color: "amber",   icon: "🛠️" },
  { id: "memory",    label: "Memory",    description: "Recalls past conversations",       color: "rose",    icon: "💾" },
  { id: "interview", label: "Interview", description: "Resume & interview prep",          color: "purple",  icon: "💼" },
];

const agentStyle: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  violet:  { bg: "rgba(124,58,237,0.08)",  border: "rgba(124,58,237,0.2)",  text: "#a78bfa", dot: "#7c3aed" },
  blue:    { bg: "rgba(37,99,235,0.08)",   border: "rgba(37,99,235,0.2)",   text: "#93c5fd", dot: "#2563eb" },
  emerald: { bg: "rgba(16,185,129,0.08)",  border: "rgba(16,185,129,0.2)",  text: "#6ee7b7", dot: "#10b981" },
  amber:   { bg: "rgba(245,158,11,0.08)",  border: "rgba(245,158,11,0.2)",  text: "#fcd34d", dot: "#f59e0b" },
  rose:    { bg: "rgba(244,63,94,0.08)",   border: "rgba(244,63,94,0.2)",   text: "#fda4af", dot: "#f43f5e" },
  purple:  { bg: "rgba(168,85,247,0.08)",  border: "rgba(168,85,247,0.2)",  text: "#d8b4fe", dot: "#a855f7" },
};

const navItems = [
  { href: "/",          label: "Chat",            icon: "💬", activeCheck: (p: string) => p === "/" || p === "" },
  { href: "/interview", label: "Interview Prep",  icon: "💼", activeCheck: (p: string) => p?.startsWith("/interview") },
  { href: "/mood",      label: "Mood Tracker",    icon: "📈", activeCheck: (p: string) => p?.startsWith("/mood") },
  { href: "/legal-rag", label: "Legal RAG",       icon: "⚖️", activeCheck: (p: string) => p?.startsWith("/legal-rag") },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  uploadCount: number;
  token: string | null;
}

export default function Sidebar({ isOpen, onClose, uploadCount, token }: SidebarProps) {
  const { docs, totalChunks, loading, deleting, deleteDoc } = useDocuments(token, uploadCount);
  const pathname = usePathname();

  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-20 lg:hidden" onClick={onClose} />
      )}

      <aside
        className={`
          fixed lg:relative inset-y-0 left-0 z-30 lg:z-auto
          w-72 flex flex-col border-r border-white/5
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
        style={{ background: "rgba(8,8,16,0.95)", backdropFilter: "blur(20px)" }}
      >
        {/* Header */}
        <div className="border-b border-white/5">
          <div className="flex items-center gap-3 px-5 py-5">
            <div className="w-9 h-9 rounded-xl overflow-hidden flex-shrink-0 ring-1 ring-violet-500/30" style={{ boxShadow: "0 0 12px rgba(124,58,237,0.2)" }}>
              <Image src="/AI.jpg" alt="OmniAI" width={36} height={36} className="w-full h-full object-cover" priority />
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-wide gradient-text">OmniAI</h1>
              <p className="text-white/25 text-xs">Multi-Agent System</p>
            </div>
          </div>

          {/* Navigation */}
          <div className="px-3 pb-4 space-y-0.5">
            {navItems.map(({ href, label, icon, activeCheck }) => {
              const isActive = activeCheck(pathname ?? "");
              return (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all"
                  style={isActive ? {
                    background: "rgba(124,58,237,0.12)",
                    color: "#c4b5fd",
                    border: "1px solid rgba(124,58,237,0.2)",
                    boxShadow: "0 0 12px rgba(124,58,237,0.08)",
                  } : {
                    color: "rgba(255,255,255,0.4)",
                    border: "1px solid transparent",
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.8)";
                      (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.04)";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.4)";
                      (e.currentTarget as HTMLElement).style.background = "transparent";
                    }
                  }}
                >
                  <span className="text-base opacity-80">{icon}</span>
                  {label}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Agents */}
        <div className="flex-1 overflow-y-auto px-4 py-5 space-y-2">
          <p className="text-white/20 text-xs font-semibold uppercase tracking-widest mb-4 px-1">
            Active Agents
          </p>
          {agents.map((agent) => {
            const s = agentStyle[agent.color];
            return (
              <div
                key={agent.id}
                className="flex items-start gap-3 p-3 rounded-xl transition-all cursor-default"
                style={{ background: s.bg, border: `1px solid ${s.border}` }}
              >
                <span className="text-base mt-0.5">{agent.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium" style={{ color: s.text }}>{agent.label}</span>
                    <span
                      className="w-1.5 h-1.5 rounded-full animate-pulse"
                      style={{ background: s.dot, boxShadow: `0 0 6px ${s.dot}` }}
                    />
                  </div>
                  <p className="text-xs text-white/30 mt-0.5 leading-relaxed">{agent.description}</p>
                </div>
              </div>
            );
          })}
        </div>

        <DocumentsPanel docs={docs} totalChunks={totalChunks} loading={loading} deleting={deleting} onDelete={deleteDoc} />

        <div className="px-5 py-4 border-t border-white/5">
          <div className="flex items-center gap-2 text-xs text-white/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" style={{ boxShadow: "0 0 6px #10b981" }} />
            <span>AI Engine connected</span>
          </div>
        </div>
      </aside>
    </>
  );
}
