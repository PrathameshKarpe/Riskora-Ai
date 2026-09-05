"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { PageSpinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { RiskBadge, StatusBadge } from "@/components/ui/RiskBadge";
import { getTransactions } from "@/lib/api/client";
import { formatCurrency, formatRelativeTime } from "@/lib/utils/format";

// Show all transactions that have been through an investigation
export default function InvestigationsPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["transactions"],
    queryFn: () => getTransactions(500),
    refetchInterval: 30_000,
  });

  const investigated = (data ?? []).filter((tx) =>
    [
      "INVESTIGATING",
      "PENDING_REVIEW",
      "APPROVE",
      "BLOCK",
      "HOLD",
      "INVESTIGATION_FAILED",
    ].includes(tx.status)
  );

  return (
    <DashboardShell title="Investigations">
      <div className="space-y-4">
        <p className="text-xs text-slate-500">
          All transactions that have entered the AI investigation pipeline.
        </p>

        <div className="bg-white rounded-lg border border-slate-200 overflow-x-auto">
          {isLoading ? (
            <PageSpinner />
          ) : isError ? (
            <ErrorState title="Unable to load investigations" onRetry={refetch} />
          ) : investigated.length === 0 ? (
            <EmptyState
              title="No investigations yet"
              description="Investigate a transaction to see it here."
              action={
                <Link href="/dashboard/transactions" className="text-xs text-blue-600 hover:text-blue-700">
                  View Transactions →
                </Link>
              }
            />
          ) : (
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="px-5 py-3 text-left font-medium text-slate-500">Transaction</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500">Amount</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500">Merchant</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500">Status</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500">Time</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500">Action</th>
                </tr>
              </thead>
              <tbody>
                {investigated.map((tx) => (
                  <tr key={tx.id} className="border-b border-slate-50 hover:bg-slate-50/60 transition-colors">
                    <td className="px-5 py-3">
                      <span className="font-mono font-medium text-slate-800">{tx.external_id}</span>
                      <span className="block text-slate-400 text-[10px]">#{tx.id}</span>
                    </td>
                    <td className="px-5 py-3 font-semibold text-slate-900 tabular-nums">
                      {formatCurrency(tx.amount, tx.currency)}
                    </td>
                    <td className="px-5 py-3 text-slate-600 max-w-[140px] truncate">{tx.merchant}</td>
                    <td className="px-5 py-3">
                      <StatusBadge status={tx.status} />
                    </td>
                    <td className="px-5 py-3 text-slate-400">{formatRelativeTime(tx.created_at)}</td>
                    <td className="px-5 py-3">
                      <Link href={`/dashboard/transactions/${tx.id}`} className="text-blue-600 hover:text-blue-700 font-medium">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}
