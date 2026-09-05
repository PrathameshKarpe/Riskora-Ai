"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import type { Evidence } from "@/lib/types";

interface Props {
  evidence: Evidence[];
}

export function EvidencePanel({ evidence }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Supporting Evidence</CardTitle>
        <p className="text-xs text-slate-400 mt-0.5">
          Retrieved from internal risk policy knowledge base via RAG
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {evidence.length === 0 ? (
          <p className="text-xs text-slate-400 py-2">
            No relevant evidence retrieved. No anomaly signals were detected
            that required policy citation.
          </p>
        ) : (
          evidence.map((ev, i) => (
            <div
              key={i}
              className="rounded-lg border border-slate-100 bg-slate-50/50 p-4"
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <div>
                  <p className="text-xs font-semibold text-slate-800">{ev.section}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    Source: <span className="font-mono">{ev.source}</span>
                  </p>
                </div>
                <div className="shrink-0 text-right">
                  <span className="text-xs font-semibold text-blue-700">
                    {Math.round(ev.relevance_score * 100)}%
                  </span>
                  <p className="text-[10px] text-slate-400">Relevance</p>
                </div>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">{ev.content}</p>
              {ev.metadata && Object.keys(ev.metadata).length > 0 && (
                <div className="mt-2 flex gap-2 flex-wrap">
                  {Object.entries(ev.metadata).map(([k, v]) => (
                    <span
                      key={k}
                      className="text-[10px] bg-white border border-slate-200 rounded px-1.5 py-0.5 text-slate-500"
                    >
                      {k}: {String(v)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
