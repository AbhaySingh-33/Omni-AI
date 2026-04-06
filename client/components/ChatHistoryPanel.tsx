"use client";

import { useChat } from "@/hooks/useChat";

interface ChatHistoryPanelProps {
  token: string | null;
}

export default function ChatHistoryPanel({ token }: ChatHistoryPanelProps) {
  const { messages, deleteChatHistory } = useChat(token);

  const getRecentSnippets = () => {
    const userMessages = messages.filter((m) => m.role === "user");
    return userMessages.slice(-3);
  };

  const snippets = getRecentSnippets();

  return (
    <div className="px-5 py-4 border-t border-white/5 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-white/30 text-xs font-medium uppercase tracking-widest px-1">
          Chat History
        </h3>
      </div>
      
      {messages.length === 0 ? (
        <p className="text-white/40 text-xs px-1">No recent interactions.</p>
      ) : (
        <div className="space-y-2">
          {snippets.map((msg) => (
            <div key={msg.id} className="text-xs text-white/50 bg-white/5 p-2 rounded-lg truncate" title={msg.content}>
              {msg.content}
            </div>
          ))}
          <button
            onClick={deleteChatHistory}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 mt-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 hover:border-rose-500/30 rounded-lg text-xs font-medium transition-colors"
          >
            <span>🗑️</span> Clear History
          </button>
        </div>
      )}
    </div>
  );
}
