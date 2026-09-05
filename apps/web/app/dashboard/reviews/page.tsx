"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { PageSpinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/RiskBadge";
import { ReviewDialog } from "@/components/reviews/ReviewDialog";
import { getTransactions, getReviews, getTransactionInvestigation } from "@/lib/api/client";
import { formatCurrency, formatRelativeTime, formatTimestamp } from "@/lib/utils/format";
import type { ReviewDecision, Transaction } from "@/lib/types";

function PriorityBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    CRITICAL: "text-red-700 bg-red-50 border-red-200",
    HIGH:     "text-orange-700 bg-orange-50 border-orange-200",
    MEDIUM:   "text-amber-700 bg-amber-50 border-amber-200",
    LOW:      "text-emerald-700 bg-emerald-50 border-emerald-200",
  };
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium border ${colors[level] ?? colors.MEDIUM}`}>
      {level}
    </span>
  );
}

export default function ReviewQueuePage() {
  const qc = useQueryClient();
  const [reviewTx, setReviewTx] = useState<Transaction | null>(null);
  const [reviewDecision, setReviewDecision] = useState<ReviewDecision>("APPROVE");

  const { data: txs, isLoading, isError, refetch } = useQuery({
    queryKey: ["transactions"],
    queryFn: () => getTransactions(500),
    refetchInterval: 15_000,
  });

  const reviewsQ = useQuery({
    queryKey: ["reviews"],
    queryFn: getReviews,
    refetchInterval: 30_000,
  });

  const pending = (txs ?? []).filter((tx) => tx.status === "PENDING_REVIEW");

  function openReview(tx: Transaction, decision: ReviewDecision) {
    setReviewTx(tx);
    setReviewDecision(decision);
  }

  function onReviewDone() {
    setReviewTx(null);
    qc.invalidateQueries({ queryKey: ["transactions"] });
    qc.invalidateQueries({ queryKey: ["reviews"] });
  }

  return (
    <DashboardShell title="Review Queue">
      <div className="space-y-6">
        {/* Pending reviews */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">
                Pending Reviews
                {pending.length > 0 && (
                  <span className="ml-2 inline-flex items-center justify-center h-5 min-w-5 px-1.5 rounded-full bg-amber-500 text-white text-[10px] font-bold">
                    {pending.length}
                  </span>
                )}
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Transactions awaiting analyst decision
              </p>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-slate-200 overflow-x-auto">
            {isLoading ? (
              <PageSpinner />
            ) : isError ? (
              <ErrorState title="Unable to load queue" onRetry={refetch} />
            ) : pending.length === 0 ? (
              <EmptyState
                icon="✓"
                title="No pending reviews"
                description="All transactions have been processed."
              />
            ) : (
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50">
                    <th className="px-5 py-3 text-left font-medium text-slate-500">Transaction</th>
                    <th className="px-5 py-3 text-left font-medium text-slate-500">Amount</th>
                    <th className="px-5 py-3 text-left font-medium text-slate-500">Merchant</th>
                    <th className="px-5 py-3 text-left font-medium text-slate-500">Waiting Since</th>
                    <th className="px-5 py-3 text-left font-medium text-slate-500">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pending.map((tx) => (
                    <tr
                      key={tx.id}
                      className="border-b border-slate-50 hover:bg-slate-50/60 transition-colors"
                    >
                      <td className="px-5 py-3">
                        <Link
                          href={`/dashboard/transactions/${tx.id}`}
                          className="font-mono font-medium text-blue-700 hover:text-blue-800"
                        >
                          {tx.external_id}
                        </Link>
                        <span className="block text-slate-400 text-[10px]">#{tx.id}</span>
                      </td>
                      <td className="px-5 py-3 font-semibold text-slate-900 tabular-nums">
                        {formatCurrency(tx.amount, tx.currency)}
                      </td>
                      <td className="px-5 py-3 text-slate-600 max-w-[160px] truncate" title={tx.merchant}>
                        {tx.merchant}
                      </td>
                      <td className="px-5 py-3 text-slate-400" title={formatTimestamp(tx.created_at)}>
                        {formatRelativeTime(tx.created_at)}
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-1.5">
                          <Link
                            href={`/dashboard/transactions/${tx.id}`}
                            className="text-xs text-blue-600 hover:text-blue-700 font-medium px-2 py-1 border border-slate-200 rounded bg-white"
                          >
                            Review
                          </Link>
                          <button
                            onClick={() => openReview(tx, "APPROVE")}
                            className="text-xs text-emerald-700 hover:text-emerald-800 font-medium px-2 py-1 border border-emerald-200 rounded bg-emerald-50 hover:bg-emerald-100 transition-colors"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => openReview(tx, "BLOCK")}
                            className="text-xs text-red-700 hover:text-red-800 font-medium px-2 py-1 border border-red-200 rounded bg-red-50 hover:bg-red-100 transition-colors"
                          >
                            Block
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Recent decisions */}
        <div>
          <h2 className="text-sm font-semibold text-slate-900 mb-4">Recent Decisions</h2>
          <div className="bg-white rounded-lg border border-slate-200 overflow-x-auto">
            {reviewsQ.isLoading ? (
              <PageSpinner />
            ) : (reviewsQ.data ?? []).length === 0 ? (
              <EmptyState title="No review decisions yet" />
            ) : (
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50">
                    <th className="px-5 py-3 text-left font-medium text-slate-500">Transaction</th>
                    <th className="px-5 py-3 text-left font-medium text-slate-500">Decision</th>
                    <th className="px-5 py-3 text-left font-medium text-slate-500">Reason</th>
                    <th className="px-5 py-3 text-left font-medium text-slate-500">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {(reviewsQ.data ?? []).slice(0, 20).map((review) => (
                    <tr key={review.id} className="border-b border-slate-50">
                      <td className="px-5 py-3">
                        <Link
                          href={`/dashboard/transactions/${review.transaction_id}`}
                          className="font-mono text-blue-700 hover:text-blue-800"
                        >
                          #{review.transaction_id}
                        </Link>
                      </td>
                      <td className="px-5 py-3">
                        <StatusBadge status={review.decision as "APPROVE" | "BLOCK" | "HOLD"} />
                      </td>
                      <td className="px-5 py-3 text-slate-600 max-w-[280px] truncate" title={review.reason}>
                        {review.reason}
                      </td>
                      <td className="px-5 py-3 text-slate-400">
                        {formatRelativeTime(review.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>

      {reviewTx && (
        <ReviewDialog
          open={!!reviewTx}
          onClose={() => setReviewTx(null)}
          transactionId={reviewTx.id}
          transactionExtId={reviewTx.external_id}
          decision={reviewDecision}
          onSuccess={onReviewDone}
        />
      )}
    </DashboardShell>
  );
}
