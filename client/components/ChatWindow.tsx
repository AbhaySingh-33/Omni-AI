"use client";
import { useEffect, useRef, useState } from "react";
import { Message } from "@/lib/types";

const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";

function Timestamp({ date }: { date: Date | string }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  const dateObj = typeof date === "string" ? new Date(date) : date;
  return (
    <p className="text-white/15 text-[11px]">
      {mounted ? dateObj.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
    </p>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      onClick={copy}
      className="opacity-0 group-hover:opacity-100 transition-all p-1.5 rounded-lg hover:bg-white/8 text-white/25 hover:text-white/60"
      title="Copy"
    >
      {copied ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      )}
    </button>
  );
}

function SpeakButton({ text }: { text: string }) {
  const [loading, setLoading] = useState(false);
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const speak = async () => {
    if (playing && audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setPlaying(false);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => { setPlaying(false); URL.revokeObjectURL(url); };
      audio.onerror = () => { setPlaying(false); URL.revokeObjectURL(url); };
      setPlaying(true);
      await audio.play();
    } catch { setPlaying(false); }
    finally { setLoading(false); }
  };

  return (
    <button
      onClick={speak}
      className="opacity-0 group-hover:opacity-100 transition-all p-1.5 rounded-lg hover:bg-white/8 text-white/25 hover:text-white/60"
      title={playing ? "Stop" : "Speak"}
    >
      {loading ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 3v2"/><path d="M12 19v2"/><path d="M3 12h2"/><path d="M19 12h2"/></svg>
      ) : playing ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 5 6 9H2v6h4l5 4Z"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
      )}
    </button>
  );
}

interface ChatWindowProps {
  messages: Message[];
  loading: boolean;
  historyLoading: boolean;
}

function formatContent(text: string) {
  text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  text = text.replace(/`([^`]+)`/g, '<code class="bg-white/10 px-1.5 py-0.5 rounded-md text-sm font-mono text-violet-300">$1</code>');
  text = text.replace(
    /```[\w]*\n?([\s\S]*?)```/g,
    '<pre class="bg-black/50 border border-white/8 rounded-xl p-4 my-3 overflow-x-auto text-sm font-mono text-emerald-300 whitespace-pre-wrap">$1</pre>'
  );
  text = text.replace(/^[-•]\s(.+)/gm, '<li class="ml-4 list-disc">$1</li>');
  text = text.replace(/^\d+\.\s(.+)/gm, '<li class="ml-4 list-decimal">$1</li>');
  text = text.replace(/\n/g, "<br/>");
  return text;
}

const agentMeta: Record<string, { label: string; icon: string; gradient: string; glow: string }> = {
  reasoning: { label: "Reasoning", icon: "🧠", gradient: "from-blue-500/20 to-blue-600/10", glow: "border-blue-500/25 text-blue-300" },
  research:  { label: "Research",  icon: "🔍", gradient: "from-emerald-500/20 to-emerald-600/10", glow: "border-emerald-500/25 text-emerald-300" },
  tools:     { label: "Tools",     icon: "🛠️", gradient: "from-amber-500/20 to-amber-600/10", glow: "border-amber-500/25 text-amber-300" },
  memory:    { label: "Memory",    icon: "💾", gradient: "from-rose-500/20 to-rose-600/10", glow: "border-rose-500/25 text-rose-300" },
  router:    { label: "Router",    icon: "⚡", gradient: "from-violet-500/20 to-violet-600/10", glow: "border-violet-500/25 text-violet-300" },
  interview: { label: "Interview", icon: "💼", gradient: "from-purple-500/20 to-purple-600/10", glow: "border-purple-500/25 text-purple-300" },
};

const emotionEmoji: Record<string, string> = {
  joy: "😊", sadness: "😢", anger: "😠", fear: "😨",
  anxiety: "😰", stress: "😫", self_doubt: "😔", hopelessness: "🥀",
};

const emotionColor: Record<string, string> = {
  joy: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  sadness: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  anger: "text-red-400 bg-red-500/10 border-red-500/20",
  fear: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
  anxiety: "text-orange-400 bg-orange-500/10 border-orange-500/20",
  stress: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  self_doubt: "text-indigo-400 bg-indigo-500/10 border-indigo-500/20",
  hopelessness: "text-rose-400 bg-rose-500/10 border-rose-500/20",
};

function UserMessage({ message }: { message: Message }) {
  return (
    <div className="flex justify-end group message-appear">
      <div className="max-w-[75%] lg:max-w-[60%]">
        <div
          className="text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed"
          style={{
            background: "linear-gradient(135deg, rgba(124,58,237,0.8), rgba(37,99,235,0.8))",
            boxShadow: "0 4px 20px rgba(124,58,237,0.2)",
            border: "1px solid rgba(124,58,237,0.3)",
          }}
        >
          {message.content}
        </div>
        <div className="flex justify-end items-center gap-1 mt-1">
          <CopyButton text={message.content} />
          <Timestamp date={message.timestamp} />
        </div>
      </div>
    </div>
  );
}

function AssistantMessage({ message }: { message: Message }) {
  const meta = message.agent ? agentMeta[message.agent] : null;

  return (
    <div className="flex gap-3 group message-appear">
      <div
        className="w-8 h-8 rounded-xl flex items-center justify-center text-sm flex-shrink-0 mt-1"
        style={{
          background: "linear-gradient(135deg, rgba(124,58,237,0.2), rgba(37,99,235,0.2))",
          border: "1px solid rgba(124,58,237,0.2)",
          boxShadow: "0 0 12px rgba(124,58,237,0.1)",
        }}
      >
        ✦
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-2 flex-wrap">
          {meta && (
            <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border font-medium bg-gradient-to-r ${meta.gradient} ${meta.glow}`}>
              <span>{meta.icon}</span>
              <span>{meta.label}</span>
            </span>
          )}
          {message.emotion && emotionEmoji[message.emotion.detected] && (
            <span
              className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border font-medium ${
                emotionColor[message.emotion.detected] || "text-white/40 bg-white/5 border-white/10"
              }`}
              title={`${message.emotion.detected} · ${message.emotion.intensity}`}
            >
              <span>{emotionEmoji[message.emotion.detected]}</span>
              <span className="capitalize">{message.emotion.detected.replace("_", " ")}</span>
            </span>
          )}
        </div>
        <div
          className="rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-white/85 leading-relaxed"
          style={{
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          <div dangerouslySetInnerHTML={{ __html: formatContent(message.content) }} />
        </div>
        <div className="flex items-center gap-0.5 mt-1">
          <SpeakButton text={message.content} />
          <CopyButton text={message.content} />
          <Timestamp date={message.timestamp} />
        </div>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-3 message-appear">
      <div
        className="w-8 h-8 rounded-xl flex items-center justify-center text-sm flex-shrink-0"
        style={{
          background: "linear-gradient(135deg, rgba(124,58,237,0.2), rgba(37,99,235,0.2))",
          border: "1px solid rgba(124,58,237,0.2)",
        }}
      >
        ✦
      </div>
      <div
        className="rounded-2xl rounded-tl-sm px-4 py-3"
        style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
      >
        <div className="flex gap-1.5 items-center h-4">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-violet-400/60 animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function HistorySkeleton() {
  return (
    <div className="space-y-5 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className={`flex ${i % 2 === 0 ? "justify-end" : "gap-3"}`}>
          {i % 2 !== 0 && <div className="w-8 h-8 rounded-xl bg-white/5 flex-shrink-0" />}
          <div className={`space-y-1.5 ${i % 2 === 0 ? "items-end flex flex-col" : ""}`}>
            <div className={`h-9 rounded-2xl bg-white/5 ${i % 2 === 0 ? "w-48" : "w-64"}`} />
            <div className="h-3 w-10 rounded bg-white/5" />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState() {
  const suggestions = [
    { icon: "💡", text: "What can you help me with?" },
    { icon: "🌐", text: "Search the web for latest AI news" },
    { icon: "📄", text: "Summarize my uploaded documents" },
    { icon: "💬", text: "What did we talk about last time?" },
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full gap-8 px-4">
      <div className="text-center space-y-4">
        <div
          className="w-20 h-20 rounded-3xl flex items-center justify-center text-3xl mx-auto float"
          style={{
            background: "linear-gradient(135deg, rgba(124,58,237,0.3), rgba(37,99,235,0.3))",
            border: "1px solid rgba(124,58,237,0.3)",
            boxShadow: "0 0 40px rgba(124,58,237,0.2), 0 0 80px rgba(124,58,237,0.05)",
          }}
        >
          ✦
        </div>
        <div>
          <h2 className="text-white text-2xl font-bold gradient-text">How can I help?</h2>
          <p className="text-white/35 text-sm mt-2 max-w-xs mx-auto leading-relaxed">
            A team of AI agents ready to reason, research, and take action for you.
          </p>
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
        {suggestions.map((s) => (
          <button
            key={s.text}
            className="text-left px-4 py-3 rounded-xl text-white/45 text-sm hover:text-white/80 transition-all hover:-translate-y-0.5"
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.07)",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.background = "rgba(124,58,237,0.08)";
              (e.currentTarget as HTMLElement).style.borderColor = "rgba(124,58,237,0.2)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)";
              (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.07)";
            }}
          >
            <span className="mr-2">{s.icon}</span>{s.text}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function ChatWindow({ messages, loading, historyLoading }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  if (historyLoading) {
    return <div className="flex-1 overflow-y-auto px-4 py-6"><HistorySkeleton /></div>;
  }

  const historyMsgs = messages.filter((m) => (m as Message & { fromHistory?: boolean }).fromHistory);
  const sessionMsgs = messages.filter((m) => !(m as Message & { fromHistory?: boolean }).fromHistory);
  const hasHistory = historyMsgs.length > 0;
  const hasSession = sessionMsgs.length > 0;

  if (!hasHistory && !hasSession && !loading) return <EmptyState />;

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5">
      {hasHistory && (
        <>
          <div className="flex items-center gap-3 py-1">
            <div className="flex-1 h-px bg-white/5" />
            <span className="text-white/15 text-xs px-2 flex-shrink-0">Previous conversations</span>
            <div className="flex-1 h-px bg-white/5" />
          </div>
          {historyMsgs.map((msg) =>
            msg.role === "user" ? <UserMessage key={msg.id} message={msg} /> : <AssistantMessage key={msg.id} message={msg} />
          )}
        </>
      )}

      {hasHistory && (hasSession || loading) && (
        <div className="flex items-center gap-3 py-2">
          <div className="flex-1 h-px bg-white/5" />
          <span className="text-white/20 text-xs px-2 flex-shrink-0">Current session</span>
          <div className="flex-1 h-px bg-white/5" />
        </div>
      )}

      {sessionMsgs.map((msg) =>
        msg.role === "user" ? <UserMessage key={msg.id} message={msg} /> : <AssistantMessage key={msg.id} message={msg} />
      )}

      {loading && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}
