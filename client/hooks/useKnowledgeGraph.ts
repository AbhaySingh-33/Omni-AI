"use client";
import { useCallback, useEffect } from "react";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setKgData, setKgLoading, setKgError } from "@/store/slices/kgSlice";

const AI_ENGINE_URL = process.env.NEXT_PUBLIC_AI_ENGINE_URL || "http://localhost:8000";

export interface KGEntity {
  name: string;
  type: string;
  updated_at?: number;
}

export interface KGRelation {
  source: string;
  relation: string;
  target: string;
  source_type?: string;
  source_id?: string;
  updated_at?: number;
}

export interface KGSearchRow {
  entity: string;
  type: string;
  relationships: { relation: string; target: string }[];
}

export interface KGOverview {
  mode: "overview";
  entities: KGEntity[];
  relations: KGRelation[];
}

export interface KGSearch {
  mode: "search";
  query: string;
  rows: KGSearchRow[];
}

export interface KGDocument {
  mode: "document";
  doc_id: string;
  entities: KGEntity[];
  relations: KGRelation[];
}

export type KGResponse = KGOverview | KGSearch | KGDocument;

export function useKnowledgeGraph(token: string | null) {
  const dispatch = useAppDispatch();
  const { data, loading, error } = useAppSelector((state) => state.kg);

  const authHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const fetchKG = useCallback(async (params: { q?: string; limit?: number; docId?: string } = {}) => {
    if (!token) return;
    dispatch(setKgLoading(true));
    dispatch(setKgError(null));
    try {
      // If there are no ingested documents, clear stale persisted KG state.
      const docsRes = await fetch(`${AI_ENGINE_URL}/documents`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (docsRes.ok) {
        const docsJson = await docsRes.json();
        const docs = docsJson?.documents ?? [];
        if (!Array.isArray(docs) || docs.length === 0) {
          dispatch(setKgData(null));
          return;
        }
      }

      const search = new URLSearchParams();
      if (params.q) search.set("q", params.q);
      if (params.docId) search.set("doc_id", params.docId);
      search.set("limit", String(params.limit ?? 20));

      const res = await fetch(`${AI_ENGINE_URL}/kg/inspect?${search.toString()}`, {
        headers: authHeaders,
      });
      if (!res.ok) throw new Error(`KG fetch failed: ${res.status}`);
      const json = (await res.json()) as KGResponse;
      dispatch(setKgData(json));
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load KG";
      dispatch(setKgError(msg));
    } finally {
      dispatch(setKgLoading(false));
    }
  }, [token, dispatch]);

  useEffect(() => {
    if (!token) return;
    fetchKG();
  }, [token, fetchKG]);

  useEffect(() => {
    if (!token) return;

    const handleDocumentsChanged = () => {
      fetchKG();
    };

    window.addEventListener("omni:documents:changed", handleDocumentsChanged);
    return () => {
      window.removeEventListener("omni:documents:changed", handleDocumentsChanged);
    };
  }, [token, fetchKG]);

  return { data, loading, error, refresh: fetchKG };
}
