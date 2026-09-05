"use client";

import { Suspense, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { PageSpinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import { getAuditTrail } from "@/lib/api/client";
import { eventTypeLabel, formatTime, formatTimestamp } from "@/lib/utils/format";

const EVENT_ICONS: Record<string, string> = {
  TRANSACTION_RECEIVED:        "📥",
  INVESTIGATION_STARTED:       "🔍",
  ML_RISK_CALCULATED:          "🤖",
  BEHAVIOR_ANALYSIS_COMPLETED: "📊",
  EVIDENCE_RETRIEVED:          "📚",
  DECISION_GENERATED:          "⚖️",
  POLICY_EVALUATED:            "🛡️",
  AUDIT_RECORDED:              "📋",
  HUMAN_REVIEW_STARTED:        "👤",
  REVIEWER_DECISION:           "✅",
  FINAL_ACTION:                "🏁",
};

function EventCard({
  event,
}: {
  event: {
    id: number;
    event_type: string;
    actor: string;
    payload: Record<string, unknown>;
    timestamp: string;
  };
}) {
  const [expanded, setExpanded] = useState(false);
  const icon = EVENT_ICONS[event.event_type] ?? "•";

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center text-sm shrink-0">
          {icon}
        </div>
        <div className="w-px flex-1 bg-slate-100 mt-1" />
      </div>
      <div className="flex-1 pb-5 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="text-xs font-semibold text-slate-800">
              {eventTypeLabel(event.event_type)}
            </p>
            <p className="text-[10px] text-slate-400 mt-0.5">
              {formatTime(event.timestamp)} · {event.actor}
            </p>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-[10px] text-slate-400 hover:text-slate-600 shrink-0"
            aria-label={expanded ? "Hide payload" : "Show payload"}
          >
            {expanded ? "Hide" : "Details"}
          </button>
        </div>

        {/* Key payload summary */}
        {!expanded && Object.keys(event.payload).length > 0 && (
          <div className="mt-1 text-[11px] text-slate-500">
            {Object.entries(event.payload)
              .filter(([k]) => !["audit_events", "errors"].includes(k))
              .slice(0, 3)
              .map(([k, v]) => (
                <span key={k} className="mr-3">
                  <span className="text-slate-400">{k}:</span>{" "}
                  <span className="font-medium text-slate-600">
                    {typeof v === "object" ? "…" : String(v).substring(0, 40)}
                  </span>
                </span>
              ))}
          </div>
        )}

        {expanded && (
          <pre className="mt-2 text-[10px] bg-slate-50 rounded border border-slate-100 p-3 overflow-x-auto text-slate-600 whitespace-pre-wrap font-mono">
            {JSON.stringify(event.payload, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}

function AuditTrailContent() {
  const searchParams = useSearchParams();
  const [txIdInput, setTxIdInput] = useState(searchParams.get("tx") ?? "");
  const [submittedTxId, setSubmittedTxId] = useState(
    searchParams.get("tx") ? Number(searchParams.get("tx")) : null
  );

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["audit", submittedTxId],
    queryFn: () => getAuditTrail(submittedTxId!),
    enabled: !!submittedTxId,
  });

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const id = parseInt(txIdInput.trim());
    if (!isNaN(id)) setSubmittedTxId(id);
  }

  return (
    <DashboardShell title="Audit Trail">
      <div className="space-y-5 max-w-3xl">
        {/* Search */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="number"
            value={txIdInput}
            onChange={(e) => setTxIdInput(e.target.value)}
            placeholder="Enter transaction ID..."
            aria-label="Transaction ID"
            className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded bg-white text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <Button type="submit" variant="primary" size="md">
            Load Audit Trail
          </Button>
        </form>

        {/* Results */}
        {!submittedTxId ? (
          <EmptyState
            title="Enter a transaction ID to view its audit trail"
            description="The audit trail records every action taken on a transaction from receipt to final decision."
          />
        ) : isLoading ? (
          <PageSpinner />
        ) : isError ? (
          <ErrorState
            title="Unable to load audit trail"
            message="The transaction may not exist or the API is unavailable."
            onRetry={refetch}
          />
        ) : !data || data.length === 0 ? (
          <EmptyState title="No audit events found for this transaction." />
        ) : (
          <div>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">
                  Transaction #{submittedTxId}
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  {data.length} event{data.length !== 1 ? "s" : ""} · Chronological order
                </p>
              </div>
              <Link
                href={`/dashboard/transactions/${submittedTxId}`}
                className="text-xs text-blue-600 hover:text-blue-700"
              >
                View Transaction →
              </Link>
            </div>

            <div className="bg-white rounded-lg border border-slate-200 p-5">
              {data.map((event, i) => (
                <EventCard key={event.id} event={event} />
              ))}
              {/* Final node */}
              <div className="flex gap-4">
                <div className="h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center text-xs shrink-0">
                  <svg className="h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div className="flex items-center">
                  <p className="text-xs text-slate-500">End of audit trail</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

export default function AuditTrailPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[40vh]">
          <PageSpinner />
        </div>
      }
    >
      <AuditTrailContent />
    </Suspense>
  );
}
