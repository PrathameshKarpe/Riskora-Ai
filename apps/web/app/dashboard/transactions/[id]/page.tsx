"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { PageSpinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/ErrorState";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { RiskScore } from "@/components/ui/RiskScore";
import { RiskBadge, StatusBadge } from "@/components/ui/RiskBadge";
import { Dialog } from "@/components/ui/Dialog";
import { ReviewDialog } from "@/components/reviews/ReviewDialog";
import { InvestigationTimeline } from "@/components/investigation/InvestigationTimeline";
import { EvidencePanel } from "@/components/investigation/EvidencePanel";
import { AgentFindings } from "@/components/investigation/AgentFindings";
import { DecisionPanel } from "@/components/investigation/DecisionPanel";
import { BehavioralSignals } from "@/components/investigation/BehavioralSignals";
import { PaymentPanel } from "@/components/payments/PaymentPanel";
import {
  getTransaction,
  getTransactionInvestigation,
  startInvestigation,
} from "@/lib/api/client";
import {
  formatCurrency,
  formatTimestamp,
} from "@/lib/utils/format";
import type { ReviewDecision } from "@/lib/types";

export default function TransactionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const txId = Number(id);
  const qc = useQueryClient();

  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [reviewDecision, setReviewDecision] = useState<ReviewDecision>("APPROVE");

  const txQ = useQuery({
    queryKey: ["transactions", txId],
    queryFn: () => getTransaction(txId),
    enabled: !!txId,
  });

  const invQ = useQuery({
    queryKey: ["investigations", "tx", txId],
    queryFn: () => getTransactionInvestigation(txId),
    enabled: !!txId,
    retry: false,
  });

  const investigateMutation = useMutation({
    mutationFn: () => startInvestigation(txId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["investigations", "tx", txId] });
      qc.invalidateQueries({ queryKey: ["transactions", txId] });
    },
  });

  const tx = txQ.data;
  const inv = invQ.data;

  const canInvestigate =
    tx &&
    !["INVESTIGATING"].includes(tx.status) &&
    !invQ.data;

  function openReview(decision: ReviewDecision) {
    setReviewDecision(decision);
    setReviewDialogOpen(true);
  }

  function onReviewComplete() {
    setReviewDialogOpen(false);
    qc.invalidateQueries({ queryKey: ["transactions", txId] });
    qc.invalidateQueries({ queryKey: ["investigations", "tx", txId] });
  }

  if (txQ.isLoading) return <DashboardShell><PageSpinner /></DashboardShell>;
  if (txQ.isError || !tx) {
    return (
      <DashboardShell title="Transaction">
        <ErrorState title="Transaction not found" onRetry={() => txQ.refetch()} />
      </DashboardShell>
    );
  }

  return (
    <DashboardShell title={`Transaction ${tx.external_id}`}>
      <div className="space-y-5 max-w-6xl">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Link href="/dashboard/transactions" className="hover:text-blue-600">Transactions</Link>
          <span>/</span>
          <span className="text-slate-600 font-mono">{tx.external_id}</span>
        </div>

        {/* Header row */}
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-lg font-semibold text-slate-900 font-mono mb-1">{tx.external_id}</h1>
            <div className="flex items-center gap-2 flex-wrap">
              <StatusBadge status={tx.status} />
              <span className="text-xs text-slate-400">{formatTimestamp(tx.created_at)}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {canInvestigate && (
              <Button
                onClick={() => investigateMutation.mutate()}
                loading={investigateMutation.isPending}
                variant="primary"
                size="sm"
              >
                Run Investigation
              </Button>
            )}
            {tx.status === "PENDING_REVIEW" && (
              <>
                <Button size="sm" variant="outline" onClick={() => openReview("APPROVE")}>
                  Approve
                </Button>
                <Button size="sm" variant="outline" onClick={() => openReview("HOLD")}>
                  Hold
                </Button>
                <Button size="sm" variant="danger" onClick={() => openReview("BLOCK")}>
                  Block
                </Button>
              </>
            )}
            <Link
              href={`/dashboard/audit?tx=${txId}`}
              className="text-xs text-slate-500 hover:text-blue-600 border border-slate-200 rounded px-3 py-1.5 bg-white transition-colors"
            >
              Audit Trail
            </Link>
          </div>
        </div>

        {investigateMutation.isError && (
          <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-4 py-3">
            Investigation failed: {(investigateMutation.error as Error)?.message}
          </div>
        )}

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Left column */}
          <div className="lg:col-span-1 space-y-5">
            {/* Transaction summary */}
            <Card>
              <CardHeader><CardTitle>Transaction Details</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {[
                  { label: "Amount",         value: formatCurrency(tx.amount, tx.currency), mono: false },
                  { label: "Currency",       value: tx.currency },
                  { label: "Merchant",       value: tx.merchant },
                  { label: "Payment Method", value: tx.payment_method },
                  { label: "Device",         value: tx.device_id ?? "—" },
                  { label: "Location",       value: tx.location ?? "—" },
                ].map(({ label, value, mono }) => (
                  <div key={label} className="flex justify-between text-xs">
                    <span className="text-slate-500">{label}</span>
                    <span className={`font-medium text-slate-800 text-right ${mono === false ? "" : "font-mono"}`}>
                      {value}
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Risk assessment */}
            {inv?.risk && (
              <Card>
                <CardHeader><CardTitle>Risk Assessment</CardTitle></CardHeader>
                <CardContent>
                  <RiskScore
                    score={inv.risk.final_score}
                    level={inv.risk.risk_level}
                    size="lg"
                  />
                  <div className="mt-4 space-y-2 text-xs">
                    {[
                      { label: "ML Score",       value: inv.risk.ml_score.toFixed(1) },
                      { label: "Behavioral Risk", value: inv.risk.behavioral_risk },
                      { label: "Final Score",     value: inv.risk.final_score.toFixed(1) },
                      { label: "Model",           value: inv.risk.model_version },
                    ].map(({ label, value }) => (
                      <div key={label} className="flex justify-between">
                        <span className="text-slate-500">{label}</span>
                        <span className="font-medium text-slate-700">{value}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Behavioral signals */}
            {inv && inv.behavioral_signals.length > 0 && (
              <BehavioralSignals signals={inv.behavioral_signals} />
            )}

            {/* Razorpay payment panel — shown only when a payment exists */}
            <PaymentPanel transactionId={txId} />
          </div>

          {/* Right column */}
          <div className="lg:col-span-2 space-y-5">
            {invQ.isLoading ? (
              <Card>
                <CardContent className="py-12">
                  <PageSpinner />
                </CardContent>
              </Card>
            ) : !inv ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-sm text-slate-500 mb-4">
                    This transaction has not been investigated yet.
                  </p>
                  {canInvestigate && (
                    <Button
                      onClick={() => investigateMutation.mutate()}
                      loading={investigateMutation.isPending}
                    >
                      Run AI Investigation
                    </Button>
                  )}
                </CardContent>
              </Card>
            ) : (
              <>
                {/* Investigation timeline */}
                <InvestigationTimeline investigation={inv} />

                {/* Agent findings */}
                <AgentFindings agents={inv.agents} />

                {/* Evidence */}
                <EvidencePanel evidence={inv.evidence} />

                {/* Decision */}
                <DecisionPanel decision={inv.decision} />

                {/* Human review panel */}
                {tx.status === "PENDING_REVIEW" && (
                  <Card className="border-amber-200 bg-amber-50/30">
                    <CardHeader>
                      <CardTitle className="text-amber-800">Human Review Required</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-xs text-amber-700 mb-4">
                        {inv.decision?.explanation ?? "This transaction requires analyst review before a final decision."}
                      </p>
                      <div className="flex gap-2 flex-wrap">
                        <Button variant="primary" size="sm" onClick={() => openReview("APPROVE")}>
                          Approve
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => openReview("HOLD")}>
                          Hold
                        </Button>
                        <Button variant="danger" size="sm" onClick={() => openReview("BLOCK")}>
                          Block
                        </Button>
                      </div>
                      <p className="text-[10px] text-amber-600 mt-3">
                        The Policy Engine is authoritative. Your decision will be recorded in the audit trail.
                      </p>
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Review dialog */}
      <ReviewDialog
        open={reviewDialogOpen}
        onClose={() => setReviewDialogOpen(false)}
        transactionId={txId}
        transactionExtId={tx.external_id}
        decision={reviewDecision}
        riskScore={inv?.risk?.final_score}
        riskLevel={inv?.risk?.risk_level}
        onSuccess={onReviewComplete}
      />
    </DashboardShell>
  );
}
