"use client";
import { useState, useCallback, useEffect } from "react";
import { useAppDispatch } from "@/store/hooks";
import { forceLogout } from "@/store/authUtils";

export type { DocInfo } from '@/store/slices/docsSlice';
const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";

interface _DocInfo {
  doc_id: string;
  filename: string;
  chunks: number;
}

export function useDocuments(token: string | null, refreshTrigger: number) {
  const dispatch = useAppDispatch();
  const [docs, setDocs] = useState<_DocInfo[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  const fetchDocs = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/documents`, {
        credentials: "include",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        forceLogout(dispatch);
        return;
      }
      const data = await res.json();
      setDocs(data.documents ?? []);
      setTotalChunks(data.total_chunks ?? 0);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  }, [token, dispatch]);

  const deleteDoc = useCallback(async (doc_id: string) => {
    if (!token) return;
    setDeleting(doc_id);
    try {
      const res = await fetch(`${AI_ENGINE_URL}/documents/${doc_id}`, {
        method: "DELETE",
        credentials: "include",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 401) {
        forceLogout(dispatch);
        return;
      }
      if (!res.ok) throw new Error("Delete failed");
      setDocs((prev) => prev.filter((d) => d.doc_id !== doc_id));
      setTotalChunks((prev) => {
        const removed = docs.find((d) => d.doc_id === doc_id)?.chunks ?? 0;
        return Math.max(0, prev - removed);
      });
      window.dispatchEvent(new CustomEvent("omni:documents:changed", { detail: { type: "deleted", doc_id } }));
    } finally {
      setDeleting(null);
    }
  }, [docs, token, dispatch]);

  useEffect(() => { fetchDocs(); }, [fetchDocs, refreshTrigger]);

  return { docs, totalChunks, loading, deleting, deleteDoc, refetch: fetchDocs };
}