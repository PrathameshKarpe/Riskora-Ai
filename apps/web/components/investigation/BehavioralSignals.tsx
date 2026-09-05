"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { severityIcon } from "@/lib/utils/format";
import type { BehavioralSignal } from "@/lib/types";

interface Props {
  signals: BehavioralSignal[];
}

export function BehavioralSignals({ signals }: Props) {
  if (!signals.length) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Why Is This Transaction Risky?</CardTitle>
        <p className="text-xs text-slate-400 mt-0.5">Behavioral signals from AI analysis</p>
      </CardHeader>
      <CardContent className="space-y-3">
        {signals.map((sig, i) => {
          const signal = sig as { signal?: string; severity?: string; explanation?: string; value?: unknown; source?: string };
          const signalName = signal.signal ?? String(Object.values(sig)[0] ?? "Signal");
          const severity = signal.severity ?? "MEDIUM";
          const explanation = signal.explanation ?? "";

          return (
            <div
              key={i}
              className="flex gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100"
            >
              <span className="text-base shrink-0 mt-0.5">{severityIcon(severity)}</span>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-800 capitalize">
                  {signalName.replace(/_/g, " ")}
                </p>
                {explanation && (
                  <p className="text-[11px] text-slate-500 mt-0.5">{explanation}</p>
                )}
                {signal.value != null && (
                  <p className="text-[10px] text-slate-400 mt-0.5 font-mono">
                    value: {String(signal.value)}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
