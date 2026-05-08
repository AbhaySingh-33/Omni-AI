"use client";

import { useCallback, useEffect, useState } from "react";

const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";

export interface LegalRagDocument {
  doc_id: string;
  filename: string;
  page_count: number;
  nodes: number;
  updated_at?: number;
}

export interface LegalRagQueryResponse {
  status: string;
  answer: string;
  used_candidates: number;
  context_nodes: number;
  references: number;
  acts: Array<{ name: string; description?: string; source_url?: string }>;
  web_enriched: Array<{ name: string; description?: string; source_url?: string }>;
}

export function useLegalRag(token: string | null) {
  const [documents, setDocuments] = useState<LegalRagDocument[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [querying, setQuerying] = useState(false);
  const [deletingDocId, setDeletingDocId] = useState<string | null>(null);

  const getAuthHeaders = useCallback(() => {
    return token ? { Authorization: `Bearer ${token}` } : undefined;
  }, [token]);

  const readJsonSafe = async (res: Response) => {
    try {
      return await res.json();
    } catch {
      return null;
    }
  };

  const fetchDocuments = useCallback(async () => {
    if (!token) {
      setDocuments([]);
      return;
    }

    setLoadingDocs(true);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/legal-rag/documents`, {
        headers: getAuthHeaders(),
        credentials: "include",
      });
      const data = await readJsonSafe(res);
      if (!res.ok) {
        // Keep this non-throwing because it runs inside an effect.
        if (res.status === 401) {
          setDocuments([]);
          return;
        }
        throw new Error((data as { detail?: string } | null)?.detail || "Failed to fetch legal documents");
      }
      setDocuments(Array.isArray(data?.documents) ? data.documents : []);
    } catch {
      // Silent by design to avoid noisy unhandled promise rejections.
      setDocuments([]);
    } finally {
      setLoadingDocs(false);
    }
  }, [token, getAuthHeaders]);

  const uploadLegalPdf = useCallback(
    async (file: File) => {
      if (!token) throw new Error("Not authenticated");
      setUploading(true);
      try {
        const form = new FormData();
        form.append("file", file);

        const res = await fetch(`${AI_ENGINE_URL}/legal-rag/upload`, {
          method: "POST",
          headers: getAuthHeaders(),
          credentials: "include",
          body: form,
        });
        const data = await readJsonSafe(res);
        if (!res.ok) throw new Error(data?.detail || "Legal upload failed");

        await fetchDocuments();
        return data;
      } finally {
        setUploading(false);
      }
    },
    [token, getAuthHeaders, fetchDocuments]
  );

  const queryLegalRag = useCallback(
    async (question: string, doc_id?: string) => {
      if (!token) throw new Error("Not authenticated");
      setQuerying(true);
      try {
        const payload: { question: string; doc_id?: string } = { question };
        if (doc_id) payload.doc_id = doc_id;

        const res = await fetch(`${AI_ENGINE_URL}/legal-rag/query`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            ...(getAuthHeaders() ?? {}),
          },
          body: JSON.stringify(payload),
        });
        const data = await readJsonSafe(res);
        if (!res.ok) throw new Error(data?.detail || "Legal query failed");
        return data as LegalRagQueryResponse;
      } finally {
        setQuerying(false);
      }
    },
    [token, getAuthHeaders]
  );

  const deleteLegalDoc = useCallback(
    async (doc_id: string) => {
      if (!token) throw new Error("Not authenticated");
      setDeletingDocId(doc_id);
      try {
        const res = await fetch(`${AI_ENGINE_URL}/legal-rag/documents/${doc_id}`, {
          method: "DELETE",
          headers: getAuthHeaders(),
          credentials: "include",
        });
        const data = await readJsonSafe(res);
        if (!res.ok) throw new Error(data?.detail || "Delete failed");
        setDocuments((prev) => prev.filter((d) => d.doc_id !== doc_id));
      } finally {
        setDeletingDocId(null);
      }
    },
    [token, getAuthHeaders]
  );

  useEffect(() => {
    fetchDocuments().catch(() => {
      // Defensive catch; fetchDocuments should already absorb effect-time errors.
    });
  }, [fetchDocuments]);

  return {
    documents,
    loadingDocs,
    uploading,
    querying,
    deletingDocId,
    fetchDocuments,
    uploadLegalPdf,
    queryLegalRag,
    deleteLegalDoc,
  };
}
