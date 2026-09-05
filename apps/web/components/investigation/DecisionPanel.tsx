"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import type { Decision } from "@/lib/types";
import { cn } from "@/lib/utils/format";

function actionColor(action: string): string {
  switch (action) {
    case "APPROVE":       return "text-emerald-700 bg-emerald-50 border-emerald-200";
    case "BLOCK":         return "text-red-700 bg-red-50 border-red-200";
    case "HUMAN_REVIEW":  return "text-amber-700 bg-amber-50 border-amber-200";
    case "HOLD":          return "text-orange-700 bg-orange-50 border-orange-200";
    default:              return "text-slate-600 bg-slate-50 border-slate-200";
  }
}

interface Props {
  decision: Decision | null;
}

export function DecisionPanel({ decision }: Props) {
  if (!decision) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* AI recommendation */}
      <Card>
        <CardHeader>
          <CardTitle>AI Recommendation</CardTitle>
          <p className="text-[10px] text-slate-400 mt-0.5">
            From Decision Agent — not the final authority
          </p>
        </CardHeader>
        <CardContent>
          <div
            className={cn(
              "inline-flex items-center px-3 py-1.5 rounded-lg border text-sm font-bold mb-3",
              actionColor(decision.recommendation)
            )}
          >
            {decision.recommendation}
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">
            {decision.explanation}
          </p>
        </CardContent>
      </Card>

      {/* Policy engine */}
      <Card>
        <CardHeader>
          <CardTitle>Policy Engine</CardTitle>
          <p className="text-[10px] text-slate-400 mt-0.5">
            Deterministic — this is the authoritative action
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-1">Action</p>
            <div
              className={cn(
                "inline-flex items-center px-3 py-1.5 rounded-lg border text-sm font-bold",
                actionColor(decision.policy_action)
              )}
            >
              {decision.policy_action}
            </div>
          </div>

          {decision.requires_human_review && (
            <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2">
              Human review required before final action.
            </div>
          )}

          {decision.reason_codes.length > 0 && (
            <div>
              <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-1">Reason Codes</p>
              <div className="flex flex-wrap gap-1">
                {decision.reason_codes.map((code) => (
                  <span
                    key={code}
                    className="text-[10px] font-mono bg-slate-100 text-slate-600 border border-slate-200 rounded px-1.5 py-0.5"
                  >
                    {code}
                  </span>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
