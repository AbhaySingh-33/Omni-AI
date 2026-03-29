"use client";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AgentInfo } from "@/lib/types";
import DocumentsPanel from "@/components/DocumentsPanel";
import { useDocuments } from "@/hooks/useDocuments";

const agents: AgentInfo[] = [
  { id: "router", label: "Router", description: "Classifies intent & delegates", color: "violet", icon: "⚡" },
  { id: "reasoning", label: "Reasoning", description: "General Q&A via DSPy + Gemini", color: "blue", icon: "🧠" },
  { id: "research", label: "Research", description: "RAG over your documents", color: "emerald", icon: "🔍" },
  { id: "tools", label: "Tools", description: "Web search, files, terminal", color: "amber", icon: "🛠️" },
  { id: "memory", label: "Memory", description: "Recalls past conversations", color: "rose", icon: "💾" },
];

const colorMap: Record<string, string> = {
  violet: "bg-violet-500/10 text-violet-400 border-violet-500/20",
  blue: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  emerald: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  amber: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  rose: "bg-rose-500/10 text-rose-400 border-rose-500/20",
};

const dotMap: Record<string, string> = {
  violet: "bg-violet-400",
  blue: "bg-blue-400",
  emerald: "bg-emerald-400",
  amber: "bg-amber-400",
  rose: "bg-rose-400",
};

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  uploadCount: number;
  token: string | null;
}

export default function Sidebar({ isOpen, onClose, uploadCount, token }: SidebarProps) {
  const { docs, totalChunks, loading, deleting, deleteDoc } = useDocuments(token, uploadCount);
  const pathname = usePathname();

  // pathname check for active link state
  const isChatActive = pathname === "/" || pathname === "";
  const isKgActive = pathname?.startsWith("/kg");

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-20 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed lg:relative inset-y-0 left-0 z-30 lg:z-auto
          w-72 flex flex-col bg-[#0d0d0d] border-r border-white/5
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        <div className="flex flex-col gap-0 border-b border-white/5 bg-[#0a0a0a]">
            {/* Header / Logo */}
            <div className="flex items-center gap-3 px-5 py-5">
                <div className="w-8 h-8 rounded-lg overflow-hidden flex-shrink-0">
                    <Image
                    src="/AI.jpg"
                    alt="OmniAI Logo"
                    width={32}
                    height={32}
                    className="w-full h-full object-cover"
                    priority
                    />
                </div>
                <div>
                    <h1 className="text-white font-semibold text-sm tracking-wide">OmniAI</h1>
                    <p className="text-white/30 text-xs">Multi-Agent System</p>
                </div>
            </div>

            {/* Navigation Section */}
            <div className="px-3 pb-4 space-y-1">
                <Link 
                    href="/"
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isChatActive 
                        ? "bg-white/10 text-white" 
                        : "text-white/50 hover:text-white hover:bg-white/5"
                    }`}
                >
                    <span className="text-lg opacity-80">💬</span>
                    Chat
                </Link>
                <Link 
                    href="/kg"
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isKgActive 
                        ? "bg-white/10 text-white" 
                        : "text-white/50 hover:text-white hover:bg-white/5"
                    }`}
                >
                    <span className="text-lg opacity-80">🕸️</span>
                    Knowledge Graph
                </Link>
            </div>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-5 space-y-2">
          <p className="text-white/30 text-xs font-medium uppercase tracking-widest mb-4 px-1">
            Active Agents
          </p>
          {agents.map((agent) => (
            <div
              key={agent.id}
              className={`flex items-start gap-3 p-3 rounded-xl border ${colorMap[agent.color]} transition-all`}
            >
              <span className="text-base mt-0.5">{agent.icon}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{agent.label}</span>
                  <span className={`w-1.5 h-1.5 rounded-full ${dotMap[agent.color]} animate-pulse`} />
                </div>
                <p className="text-xs opacity-60 mt-0.5 leading-relaxed">{agent.description}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Removed KnowledgeGraphPanel from here */}

        <DocumentsPanel docs={docs} totalChunks={totalChunks} loading={loading} deleting={deleting} onDelete={deleteDoc} />

        <div className="px-5 py-4 border-t border-white/5">
          <div className="flex items-center gap-2 text-xs text-white/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>AI Engine connected</span>
          </div>
        </div>
      </aside>
    </>
  );
}
