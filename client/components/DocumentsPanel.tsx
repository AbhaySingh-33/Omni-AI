"use client";
import { useState } from "react";
import { DocInfo } from "@/hooks/useDocuments";

interface DocumentsPanelProps {
  docs: DocInfo[];
  totalChunks: number;
  loading: boolean;
  deleting: string | null;
  onDelete: (doc_id: string) => void;
}

export default function DocumentsPanel({ docs, totalChunks, loading, deleting, onDelete }: DocumentsPanelProps) {
  const [confirmId, setConfirmId] = useState<string | null>(null);

  const handleDelete = (doc_id: string) => {
    if (confirmId === doc_id) {
      onDelete(doc_id);
      setConfirmId(null);
    } else {
      setConfirmId(doc_id);
    }
  };

  return (
    <div className="px-4 py-4 border-t border-white/5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-white/30 text-xs font-medium uppercase tracking-widest">
          RAG Documents
        </p>
        {totalChunks > 0 && (
          <span className="text-white/20 text-xs">{totalChunks} chunks</span>
        )}
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-white/20 text-xs py-1">
          <span className="w-3 h-3 border border-white/20 border-t-white/50 rounded-full animate-spin" />
          Loading…
        </div>
      )}

      {!loading && docs.length === 0 && (
        <p className="text-white/15 text-xs leading-relaxed">
          No PDFs ingested yet. Attach a PDF below to enable document search.
        </p>
      )}

      {!loading && docs.length > 0 && (
        <div className="space-y-1.5">
          {docs.map((doc) => {
            const isDeleting = deleting === doc.doc_id;
            const isConfirming = confirmId === doc.doc_id;

            return (
              <div
                key={doc.doc_id}
                className={`flex items-center gap-2 px-2.5 py-2 rounded-lg border transition-all ${
                  isConfirming
                    ? "bg-red-500/10 border-red-500/25"
                    : "bg-emerald-500/5 border-emerald-500/10"
                }`}
              >
                <span className="text-emerald-400 flex-shrink-0 text-xs">📄</span>

                <div className="min-w-0 flex-1">
                  <p
                    className="text-emerald-300/80 text-xs font-medium truncate"
                    title={doc.filename}
                  >
                    {doc.filename}
                  </p>
                  <p className="text-white/20 text-xs">
                    {isConfirming ? (
                      <span className="text-red-400/70">Click ✕ again to confirm</span>
                    ) : (
                      `${doc.chunks} chunks`
                    )}
                  </p>
                </div>

                {/* Cancel confirm on blur */}
                {isConfirming && (
                  <button
                    onClick={() => setConfirmId(null)}
                    className="text-white/20 hover:text-white/50 text-xs transition-colors flex-shrink-0"
                    title="Cancel"
                  >
                    ↩
                  </button>
                )}

                <button
                  onClick={() => handleDelete(doc.doc_id)}
                  disabled={isDeleting}
                  title={isConfirming ? "Confirm delete" : "Remove from RAG"}
                  className={`flex-shrink-0 w-5 h-5 flex items-center justify-center rounded transition-all disabled:opacity-30 ${
                    isConfirming
                      ? "text-red-400 hover:text-red-300"
                      : "text-white/15 hover:text-red-400 hover:bg-red-500/10"
                  }`}
                >
                  {isDeleting ? (
                    <span className="w-3 h-3 border border-white/20 border-t-red-400 rounded-full animate-spin" />
                  ) : (
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  )}
                </button>
              </div>
            );
          })}
        </div>
      )}

      {docs.length > 0 && (
        <p className="text-white/15 text-xs mt-3 leading-relaxed">
          All documents are searched together on every query.
        </p>
      )}
    </div>
  );
}
