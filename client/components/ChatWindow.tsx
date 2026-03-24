"use client";
import { useEffect, useRef, useState } from "react";
import { Message } from "@/lib/types";

const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";

function Timestamp({ date }: { date: Date }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  return (
    <p className="text-white/20 text-xs">
      {mounted ? date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}
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
      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-md hover:bg-white/10 text-white/30 hover:text-white/70"
      title="Copy"
    >
      {copied ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
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
      if (!res.ok) throw new Error(`TTS error: ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        setPlaying(false);
        URL.revokeObjectURL(url);
      };
      audio.onerror = () => {
        setPlaying(false);
        URL.revokeObjectURL(url);
      };
      setPlaying(true);
      await audio.play();
    } catch {
      setPlaying(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={speak}
      className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded-md hover:bg-white/10 text-white/30 hover:text-white/70"
      title={playing ? "Stop" : "Speak"}
      aria-label={playing ? "Stop speaking" : "Speak message"}
    >
      {loading ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 3v2"/><path d="M12 19v2"/><path d="M3 12h2"/><path d="M19 12h2"/><path d="M5.6 5.6l1.4 1.4"/><path d="M17 17l1.4 1.4"/><path d="M5.6 18.4l1.4-1.4"/><path d="M17 7l1.4-1.4"/></svg>
      ) : playing ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 5 6 9H2v6h4l5 4Z"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
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
  text = text.replace(/`([^`]+)`/g, '<code class="bg-white/10 px-1.5 py-0.5 rounded text-sm font-mono">$1</code>');
  text = text.replace(
    /```[\w]*\n?([\s\S]*?)```/g,
    '<pre class="bg-black/40 border border-white/10 rounded-xl p-4 my-3 overflow-x-auto text-sm font-mono text-emerald-300 whitespace-pre-wrap">$1</pre>'
  );
  text = text.replace(/^[-•]\s(.+)/gm, '<li class="ml-4 list-disc">$1</li>');
  text = text.replace(/^\d+\.\s(.+)/gm, '<li class="ml-4 list-decimal">$1</li>');
  text = text.replace(/\n/g, "<br/>");
  return text;
}

function UserMessage({ message }: { message: Message }) {
  return (
    <div className="flex justify-end group">
      <div className="max-w-[75%] lg:max-w-[60%]">
        <div className="bg-gradient-to-br from-violet-600 to-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed shadow-lg shadow-violet-500/10">
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
  const agentMeta: Record<string, { label: string; icon: string; color: string }> = {
    reasoning: { label: "Reasoning", icon: "🧠", color: "text-blue-400 bg-blue-500/10 border-blue-500/20" },
    research:  { label: "Research",  icon: "🔍", color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" },
    tools:     { label: "Tools",     icon: "🛠️", color: "text-amber-400 bg-amber-500/10 border-amber-500/20" },
    memory:    { label: "Memory",    icon: "💾", color: "text-rose-400 bg-rose-500/10 border-rose-500/20" },
    router:    { label: "Router",    icon: "⚡", color: "text-violet-400 bg-violet-500/10 border-violet-500/20" },
  };
  const meta = message.agent ? agentMeta[message.agent] : null;

  return (
    <div className="flex gap-3 group">
      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500/20 to-blue-500/20 border border-white/10 flex items-center justify-center text-sm flex-shrink-0 mt-1">
        ✦
      </div>
      <div className="flex-1 min-w-0">
        {meta && (
          <div className="flex items-center gap-1.5 mb-1.5">
            <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full border font-medium ${meta.color}`}>
              <span>{meta.icon}</span>
              <span>{meta.label} Agent</span>
            </span>
          </div>
        )}
        <div className="bg-white/5 border border-white/8 rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-white/85 leading-relaxed">
          <div dangerouslySetInnerHTML={{ __html: formatContent(message.content) }} />
        </div>
        <div className="flex items-center gap-1 mt-1">
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
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500/20 to-blue-500/20 border border-white/10 flex items-center justify-center text-sm flex-shrink-0">
        ✦
      </div>
      <div className="bg-white/5 border border-white/8 rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex gap-1.5 items-center h-4">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-white/40 animate-bounce"
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

function SessionDivider() {
  return (
    <div className="flex items-center gap-3 py-2">
      <div className="flex-1 h-px bg-white/5" />
      <span className="text-white/20 text-xs px-2 flex-shrink-0">Current session</span>
      <div className="flex-1 h-px bg-white/5" />
    </div>
  );
}

function EmptyState() {
  const suggestions = [
    "What can you help me with?",
    "Search the web for latest AI news",
    "Summarize my uploaded documents",
    "What did we talk about last time?",
  ];

  return (
    <div className="flex flex-col items-center justify-center h-full gap-8 px-4">
      <div className="text-center space-y-3">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-blue-500 flex items-center justify-center text-2xl mx-auto shadow-2xl shadow-violet-500/30">
          ✦
        </div>
        <h2 className="text-white text-xl font-semibold">How can I help?</h2>
        <p className="text-white/40 text-sm max-w-xs">
          I&apos;m a team of AI agents — ask me anything.
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
        {suggestions.map((s) => (
          <button
            key={s}
            className="text-left px-4 py-3 rounded-xl bg-white/5 border border-white/8 text-white/50 text-sm hover:bg-white/8 hover:text-white/80 hover:border-white/15 transition-all"
          >
            {s}
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
    return (
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <HistorySkeleton />
      </div>
    );
  }

  // Split history messages from current session ones
  const historyMsgs = messages.filter((m) => (m as Message & { fromHistory?: boolean }).fromHistory);
  const sessionMsgs = messages.filter((m) => !(m as Message & { fromHistory?: boolean }).fromHistory);
  const hasHistory = historyMsgs.length > 0;
  const hasSession = sessionMsgs.length > 0;

  if (!hasHistory && !hasSession && !loading) {
    return <EmptyState />;
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5 scrollbar-thin">
      {/* Past history */}
      {hasHistory && (
        <>
          <div className="flex items-center gap-3 py-1">
            <div className="flex-1 h-px bg-white/5" />
            <span className="text-white/15 text-xs px-2 flex-shrink-0">Previous conversations</span>
            <div className="flex-1 h-px bg-white/5" />
          </div>
          {historyMsgs.map((msg) =>
            msg.role === "user" ? (
              <UserMessage key={msg.id} message={msg} />
            ) : (
              <AssistantMessage key={msg.id} message={msg} />
            )
          )}
        </>
      )}

      {/* Divider between history and current session */}
      {hasHistory && (hasSession || loading) && <SessionDivider />}

      {/* Current session */}
      {sessionMsgs.map((msg) =>
        msg.role === "user" ? (
          <UserMessage key={msg.id} message={msg} />
        ) : (
          <AssistantMessage key={msg.id} message={msg} />
        )
      )}

      {loading && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}
