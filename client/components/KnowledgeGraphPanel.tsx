"use client";
import { useState } from "react";
import { useKnowledgeGraph } from "@/hooks/useKnowledgeGraph";

interface KnowledgeGraphPanelProps {
  token: string | null;
  isFullPage?: boolean;
}

export default function KnowledgeGraphPanel({ token, isFullPage = false }: KnowledgeGraphPanelProps) {
  const { data, loading, error, refresh } = useKnowledgeGraph(token);
  const [query, setQuery] = useState("");

  const handleSearch = () => {
    const q = query.trim();
    refresh({ q: q || undefined, limit: isFullPage ? 100 : 20 });
  };

  const containerClass = isFullPage 
    ? "h-full w-full flex flex-col"
    : "px-4 py-4 border-t border-white/5";

  return (
    <div className={containerClass}>
      {!isFullPage && (
        <div className="flex items-center justify-between mb-3">
          <p className="text-white/30 text-xs font-medium uppercase tracking-widest">
            Knowledge Graph
          </p>
          <button
            onClick={() => refresh({ limit: 20 })}
            className="text-white/20 text-xs hover:text-white/50 transition-colors"
          >
            Refresh
          </button>
        </div>
      )}

      {isFullPage && (
         <div className="flex items-center gap-4 mb-6">
            <div className="flex-1 flex gap-2">
                <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search entities via vector similarity..."
                className="flex-1 max-w-lg bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white/80 placeholder:text-white/25 focus:outline-none focus:border-emerald-400/40 transition-colors"
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                />
                <button
                onClick={handleSearch}
                className="px-6 py-2 rounded-xl border border-emerald-400/20 text-emerald-300 bg-emerald-400/10 hover:bg-emerald-400/20 transition-colors font-medium text-sm"
                >
                Search
                </button>
            </div>
             <button
            onClick={() => refresh({ limit: 100 })}
            className="px-4 py-2 rounded-lg text-white/40 hover:text-white hover:bg-white/5 transition-colors text-sm"
          >
            Refresh View
          </button>
         </div>
      )}

      {!isFullPage && (
        <div className="flex items-center gap-2 mb-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search entities"
            className="flex-1 bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-white/80 placeholder:text-white/25 focus:outline-none focus:border-emerald-400/40"
          />
          <button
            onClick={handleSearch}
            className="text-xs px-2.5 py-1.5 rounded-lg border border-emerald-400/20 text-emerald-300/80 bg-emerald-400/10 hover:bg-emerald-400/20 transition-colors"
          >
            Search
          </button>
        </div>
      )}

      {loading && (
        <div className="flex items-center gap-2 text-white/20 text-xs py-1">
          <span className="w-3 h-3 border border-white/20 border-t-white/50 rounded-full animate-spin" />
          {isFullPage ? "Loading Knowledge Graph Data..." : "Loading..."}
        </div>
      )}

      {!loading && error && (
        <p className="text-red-400/70 text-xs leading-relaxed">{error}</p>
      )}

      {!loading && !error && !data && (
        <p className="text-white/15 text-xs leading-relaxed">
          No KG data yet. Upload a PDF or ask a question.
        </p>
      )}

      {!loading && !error && data?.mode === "search" && (
        <div className={isFullPage ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" : "space-y-2"}>
          {data.rows.length === 0 && (
            <p className="text-white/15 text-xs">No matching entities.</p>
          )}
          {data.rows.map((row) => (
            <div key={`${row.entity}-${row.type}`} className="bg-white/5 border border-white/10 rounded-lg p-3 hover:border-white/20 transition-colors">
              <div className="flex justify-between items-start mb-2">
                 <p className={`${isFullPage ? 'text-sm' : 'text-xs'} text-emerald-300 font-medium`}>{row.entity}</p>
                 <span className="text-[10px] uppercase tracking-wider text-white/30 bg-white/5 px-2 py-0.5 rounded-full">{row.type}</span>
              </div>
              
              {row.relationships?.length > 0 && (
                <div className="mt-2 space-y-1.5">
                  {row.relationships.map((r, i) => (
                      <p key={i} className="text-[11px] text-white/60 flex items-center gap-1.5">
                        <span className="w-1 h-1 rounded-full bg-emerald-500/50"></span>
                        <span className="text-white/30 italic">{r.relation}</span> 
                        <span className="text-emerald-200/70">{r.target}</span>
                      </p>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {!loading && !error && data?.mode !== "search" && (
        <div className={isFullPage ? "grid grid-cols-1 lg:grid-cols-2 gap-8 flex-1 overflow-y-auto" : "space-y-3"}>
          
          {/* ENTITIES COLUMN */}
          <div className="flex flex-col gap-3">
            <h3 className="text-white/30 text-[11px] uppercase tracking-widest font-semibold flex items-center justify-between">
              Entities <span className="text-white/20 bg-white/5 px-2 py-0.5 rounded-full">{data?.entities?.length || 0}</span>
            </h3>
            
            {data?.entities?.length ? (
              <div className={isFullPage ? "grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2 auto-rows-min" : "space-y-1.5"}>
                {(isFullPage ? data.entities : data.entities.slice(0, 8)).map((e) => (
                  <div key={`${e.name}-${e.type}`} className="flex items-center justify-between bg-white/5 border border-white/10 rounded-lg px-3 py-2 hover:bg-white/10 transition-colors group cursor-default">
                    <span className="text-xs text-white/90 truncate font-medium max-w-[70%]" title={e.name}>{e.name}</span>
                    <span className="text-[10px] text-emerald-400/50 group-hover:text-emerald-400 transition-colors bg-emerald-400/5 px-1.5 py-0.5 rounded">{e.type}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-white/15 text-xs italic">No entities yet.</p>
            )}
          </div>

          {/* RELATIONS COLUMN */}
          <div className="flex flex-col gap-3">
            <h3 className="text-white/30 text-[11px] uppercase tracking-widest font-semibold flex items-center justify-between">
              Recent Relations <span className="text-white/20 bg-white/5 px-2 py-0.5 rounded-full">{data?.relations?.length || 0}</span>
            </h3>

            {data?.relations?.length ? (
              <div className={isFullPage ? "grid grid-cols-1 gap-2 auto-rows-min" : "space-y-1.5"}>
                {(isFullPage ? data.relations : data.relations.slice(0, 8)).map((r, idx) => (
                  <div key={`${r.source}-${r.relation}-${r.target}-${idx}`} className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 flex items-center gap-3 hover:border-white/20 transition-colors group">
                    <div className="flex-1 min-w-0 flex items-center gap-2 justify-end text-right">
                         <span className="text-xs text-emerald-200/90 truncate" title={r.source}>{r.source}</span>
                    </div>
                    
                    <div className="flex flex-col items-center min-w-[80px]">
                        <span className="text-[9px] text-white/30 uppercase tracking-wider mb-0.5">{r.relation}</span>
                        <div className="w-full h-px bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
                    </div>

                    <div className="flex-1 min-w-0 flex items-center gap-2">
                        <span className="text-xs text-emerald-200/90 truncate" title={r.target}>{r.target}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-white/15 text-xs italic">No relations yet.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
