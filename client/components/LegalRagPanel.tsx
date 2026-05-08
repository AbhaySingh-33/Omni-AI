"use client";

import { FormEvent, useMemo, useState } from "react";
import { useLegalRag } from "@/hooks/useLegalRag";

interface LegalRagPanelProps {
  token: string;
}

export default function LegalRagPanel({ token }: LegalRagPanelProps) {
  const {
    documents,
    loadingDocs,
    uploading,
    querying,
    deletingDocId,
    uploadLegalPdf,
    queryLegalRag,
    deleteLegalDoc,
  } = useLegalRag(token);

  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [queryMeta, setQueryMeta] = useState<{
    used_candidates: number;
    context_nodes: number;
    references: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const canAsk = useMemo(() => question.trim().length > 3 && !querying, [question, querying]);

  const onUpload = async (event: FormEvent<HTMLInputElement>) => {
    const input = event.currentTarget;
    const file = input.files?.[0];
    if (!file) return;

    setError(null);
    setSuccess(null);
    try {
      const result = await uploadLegalPdf(file);
      setSuccess(`Indexed ${result.filename} (${result.nodes} nodes, ${result.references} references)`);
      if (!selectedDocId) {
        setSelectedDocId(result.doc_id || "");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      input.value = "";
    }
  };

  const onAsk = async () => {
    const trimmed = question.trim();
    if (!trimmed) return;

    setError(null);
    setSuccess(null);
    try {
      const data = await queryLegalRag(trimmed, selectedDocId || undefined);
      setAnswer(data.answer || "");
      setQueryMeta({
        used_candidates: data.used_candidates,
        context_nodes: data.context_nodes,
        references: data.references,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    }
  };

  const onDelete = async (doc_id: string) => {
    setError(null);
    setSuccess(null);
    try {
      await deleteLegalDoc(doc_id);
      setSuccess("Document removed from legal graph");
      if (selectedDocId === doc_id) {
        setSelectedDocId("");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-[360px_1fr] gap-6 h-full">
      <section className="rounded-2xl border border-cyan-500/20 bg-[#0f1418] p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-cyan-300 tracking-wide">Legal Corpus</h2>
          {loadingDocs && <span className="text-xs text-white/40">Refreshing...</span>}
        </div>

        <label className="block text-xs text-white/50 mb-2">Upload Legal PDF</label>
        <input
          type="file"
          accept="application/pdf"
          onInput={onUpload}
          disabled={uploading}
          className="block w-full text-xs text-white/70 file:mr-3 file:rounded-lg file:border file:border-cyan-400/30 file:bg-cyan-500/10 file:px-3 file:py-1.5 file:text-cyan-200 file:text-xs hover:file:bg-cyan-500/20"
        />
        {uploading && <p className="text-xs text-cyan-300/80 mt-2">Indexing PDF into hierarchical legal graph...</p>}

        <div className="mt-5">
          <label className="block text-xs text-white/50 mb-2">Query Scope</label>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="w-full rounded-lg bg-[#121a20] border border-white/10 text-sm text-white/80 px-3 py-2"
          >
            <option value="">All legal docs</option>
            {documents.map((doc) => (
              <option key={doc.doc_id} value={doc.doc_id}>
                {doc.filename}
              </option>
            ))}
          </select>
        </div>

        <div className="mt-5 space-y-2 max-h-[50vh] overflow-y-auto pr-1">
          {documents.length === 0 && !loadingDocs && (
            <p className="text-xs text-white/35">No legal documents uploaded yet.</p>
          )}
          {documents.map((doc) => {
            const deleting = deletingDocId === doc.doc_id;
            return (
              <div key={doc.doc_id} className="rounded-lg border border-white/10 bg-black/20 px-3 py-2">
                <p className="text-xs font-medium text-white/85 truncate" title={doc.filename}>
                  {doc.filename}
                </p>
                <p className="text-[11px] text-white/45 mt-1">
                  {doc.page_count} pages • {doc.nodes} nodes
                </p>
                <button
                  onClick={() => void onDelete(doc.doc_id)}
                  disabled={deleting}
                  className="mt-2 text-[11px] text-rose-300/80 hover:text-rose-200 disabled:opacity-50"
                >
                  {deleting ? "Deleting..." : "Delete"}
                </button>
              </div>
            );
          })}
        </div>
      </section>

      <section className="rounded-2xl border border-cyan-500/20 bg-linear-to-b from-[#111821] to-[#0b1118] p-5 flex flex-col min-h-[70vh]">
        <h2 className="text-base font-semibold text-white/90">Vectorless Legal RAG</h2>
        <p className="text-xs text-white/45 mt-1">
          Uses hierarchical tree traversal + references. This page calls only /legal-rag endpoints.
        </p>

        <div className="mt-4">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about section/rule/act definitions and cross-references..."
            rows={5}
            className="w-full rounded-xl bg-[#0b0f14] border border-white/10 text-sm text-white px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
          />
          <div className="mt-3 flex items-center gap-3">
            <button
              onClick={() => void onAsk()}
              disabled={!canAsk}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-cyan-500/20 text-cyan-200 border border-cyan-400/30 hover:bg-cyan-500/30 disabled:opacity-40"
            >
              {querying ? "Traversing graph..." : "Ask Legal RAG"}
            </button>
            {queryMeta && (
              <span className="text-xs text-white/45">
                seeds: {queryMeta.used_candidates} • nodes: {queryMeta.context_nodes} • refs: {queryMeta.references}
              </span>
            )}
          </div>
        </div>

        {error && <p className="mt-4 text-sm text-rose-300/90">{error}</p>}
        {success && <p className="mt-4 text-sm text-emerald-300/90">{success}</p>}

        <div className="mt-5 flex-1 rounded-xl border border-white/10 bg-black/20 p-4 overflow-y-auto">
          {answer ? (
            <pre className="whitespace-pre-wrap wrap-break-word text-sm leading-relaxed text-white/85 font-sans">{answer}</pre>
          ) : (
            <p className="text-sm text-white/35">Your legal answer will appear here after query execution.</p>
          )}
        </div>
      </section>
    </div>
  );
}
