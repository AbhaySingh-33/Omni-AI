"use client";
import { useCallback, useEffect, useState } from "react";

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

interface KGSearchRow {
  entity: string;
  type: string;
  relationships: { relation: string; target: string }[];
}

interface KGOverview {
  mode: "overview";
  entities: KGEntity[];
  relations: KGRelation[];
}

interface KGSearch {
  mode: "search";
  query: string;
  rows: KGSearchRow[];
}

interface KGDocument {
  mode: "document";
  doc_id: string;
  entities: KGEntity[];
  relations: KGRelation[];
}

type KGResponse = KGOverview | KGSearch | KGDocument;

export function useKnowledgeGraph(token: string | null) {
  const [data, setData] = useState<KGResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const authHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const fetchKG = useCallback(async (params: { q?: string; limit?: number; docId?: string } = {}) => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const search = new URLSearchParams();
      if (params.q) search.set("q", params.q);
      if (params.docId) search.set("doc_id", params.docId);
      search.set("limit", String(params.limit ?? 20));

      const res = await fetch(`${AI_ENGINE_URL}/kg/inspect?${search.toString()}`, {
        headers: authHeaders,
      });
      if (!res.ok) throw new Error(`KG fetch failed: ${res.status}`);
      const json = (await res.json()) as KGResponse;
      setData(json);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load KG";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;
    fetchKG();
  }, [token, fetchKG]);

  return { data, loading, error, refresh: fetchKG };
}
