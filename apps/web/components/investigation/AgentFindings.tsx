"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { cn } from "@/lib/utils/format";
import type { AgentFinding } from "@/lib/types";

const AGENT_LABELS: Record<string, string> = {
  behavior_agent:    "Behavior Agent",
  investigation:     "Investigation Agent",
  evidence_agent:    "Evidence Agent",
  decision_agent:    "Decision Agent",
  audit_agent:       "Audit Agent",
};

interface Props {
  agents: AgentFinding[];
}

export function AgentFindings({ agents }: Props) {
  const grouped = agents.reduce<Record<string, AgentFinding[]>>((acc, a) => {
    if (!acc[a.agent_name]) acc[a.agent_name] = [];
    acc[a.agent_name].push(a);
    return acc;
  }, {});

  const tabs = Object.keys(grouped);
  const [active, setActive] = useState(tabs[0] ?? "");

  if (!agents.length) return null;

  const activeFindings = grouped[active] ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Agent Findings</CardTitle>
      </CardHeader>
      <div className="border-b border-slate-100 px-5 flex gap-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActive(tab)}
            className={cn(
              "text-xs font-medium pb-2.5 pt-1 px-1 border-b-2 whitespace-nowrap transition-colors",
              active === tab
                ? "border-blue-600 text-blue-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            )}
          >
            {AGENT_LABELS[tab] ?? tab.replace(/_/g, " ")}
          </button>
        ))}
      </div>
      <CardContent className="space-y-3">
        {activeFindings.map((finding, i) => {
          const f = finding.finding as Record<string, unknown>;
          return (
            <div key={i} className="text-xs">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-slate-700 capitalize">
                  {finding.status}
                </span>
                {finding.confidence != null && (
                  <span className="text-slate-400">
                    Confidence: {Math.round(finding.confidence * 100)}%
                  </span>
                )}
              </div>
              {Object.entries(f).map(([key, val]) => {
                if (key === "agent") return null;
                if (Array.isArray(val)) {
                  return (
                    <div key={key} className="mb-2">
                      <p className="text-[10px] uppercase tracking-wide text-slate-400 mb-1">
                        {key.replace(/_/g, " ")}
                      </p>
                      <ul className="space-y-1">
                        {(val as unknown[]).map((item, j) => (
                          <li key={j} className="flex gap-2 text-slate-600">
                            <span className="text-slate-300 shrink-0">•</span>
                            <span>
                              {typeof item === "object"
                                ? JSON.stringify(item)
                                : String(item)}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                }
                if (typeof val === "object" && val !== null) return null;
                return (
                  <div key={key} className="flex justify-between py-0.5 border-b border-slate-50 last:border-0">
                    <span className="text-slate-500 capitalize">{key.replace(/_/g, " ")}</span>
                    <span className="text-slate-700 font-medium">{String(val)}</span>
                  </div>
                );
              })}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
