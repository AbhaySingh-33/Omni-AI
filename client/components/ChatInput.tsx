"use client";
import { useState, useRef, KeyboardEvent, useCallback } from "react";
import { useUpload } from "@/hooks/useUpload";

interface ChatInputProps {
  onSend: (message: string) => void;
  loading: boolean;
  onClear: () => void;
  onUploadSuccess: () => void;
  token: string | null;
}

export default function ChatInput({ onSend, loading, onClear, onUploadSuccess, token }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { status: uploadStatus, fileName, message: uploadMessage, uploadPdf } = useUpload(token, onUploadSuccess);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || loading) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) uploadPdf(file);
      e.target.value = "";
    },
    [uploadPdf]
  );

  const uploadIdle = uploadStatus === "idle";
  const uploadBusy = uploadStatus === "uploading";

  return (
    <div className="px-4 pb-5 pt-3 border-t border-white/5 bg-[#0a0a0a]">
      <div className="max-w-3xl mx-auto space-y-2">
        {!uploadIdle && (
          <div
            className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs border transition-all ${
              uploadStatus === "uploading"
                ? "bg-violet-500/10 border-violet-500/20 text-violet-300"
                : uploadStatus === "success"
                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"
                : "bg-red-500/10 border-red-500/20 text-red-300"
            }`}
          >
            {uploadBusy && (
              <span className="w-3 h-3 border-2 border-violet-400/30 border-t-violet-400 rounded-full animate-spin flex-shrink-0" />
            )}
            {uploadStatus === "success" && <span>OK</span>}
            {uploadStatus === "error" && <span>ERR</span>}
            <span className="truncate">
              {uploadBusy
                ? `Ingesting "${fileName}" into RAG...`
                : uploadMessage}
            </span>
          </div>
        )}

        <div className="flex items-end gap-3 bg-white/5 border border-white/10 rounded-2xl px-4 py-3 focus-within:border-violet-500/50 focus-within:bg-white/7 transition-all">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadBusy}
            title="Attach PDF for RAG"
            className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-xl text-white/30 hover:text-violet-400 hover:bg-violet-500/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="12" y1="18" x2="12" y2="12" />
              <line x1="9" y1="15" x2="15" y2="15" />
            </svg>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={handleFileChange}
          />

          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder="Ask anything... or attach a PDF to search it"
            rows={1}
            disabled={loading}
            className="flex-1 bg-transparent text-white/85 placeholder-white/25 text-sm resize-none outline-none leading-relaxed max-h-40 disabled:opacity-50"
          />

          <div className="flex items-center gap-2 flex-shrink-0">
            {value.length > 0 && (
              <button
                onClick={() => { setValue(""); if (textareaRef.current) textareaRef.current.style.height = "auto"; }}
                className="text-white/25 hover:text-white/50 transition-colors text-xs"
              >
                X
              </button>
            )}
            <button
              onClick={handleSend}
              disabled={!value.trim() || loading}
              className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-600 to-blue-600 flex items-center justify-center text-white text-sm disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-90 transition-all shadow-lg shadow-violet-500/20"
            >
              {loading ? (
                <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              )}
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between px-1">
          <p className="text-white/20 text-xs">
            <kbd className="bg-white/10 px-1 rounded text-white/30">Enter</kbd> send .{" "}
            <kbd className="bg-white/10 px-1 rounded text-white/30">Shift+Enter</kbd> newline .{" "}
            <span className="text-white/15">PDF to RAG</span>
          </p>
          <button onClick={onClear} className="text-white/20 hover:text-white/40 text-xs transition-colors">
            Clear chat
          </button>
        </div>
      </div>
    </div>
  );
}