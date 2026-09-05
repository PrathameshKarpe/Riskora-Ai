"use client";

import { Suspense, useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { PageSpinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { StatusBadge } from "@/components/ui/RiskBadge";
import { getTransactions } from "@/lib/api/client";
import {
  formatCurrency,
  formatRelativeTime,
  formatTimestamp,
} from "@/lib/utils/format";
import type { TransactionStatus } from "@/lib/types";

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "",                 label: "All Statuses" },
  { value: "RECEIVED",         label: "Received" },
  { value: "INVESTIGATING",    label: "Investigating" },
  { value: "PENDING_REVIEW",   label: "Pending Review" },
  { value: "APPROVE",          label: "Approved" },
  { value: "BLOCK",            label: "Blocked" },
  { value: "HOLD",             label: "Hold" },
];

function TransactionsContent() {
  const searchParams = useSearchParams();
  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [statusFilter, setStatusFilter] = useState("");

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["transactions"],
    queryFn: () => getTransactions(500),
    refetchInterval: 30_000,
  });

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.filter((tx) => {
      const q = search.toLowerCase();
      const matchSearch =
        !q ||
        tx.external_id.toLowerCase().includes(q) ||
        tx.merchant.toLowerCase().includes(q) ||
        tx.payment_method.toLowerCase().includes(q) ||
        String(tx.id).includes(q);
      const matchStatus = !statusFilter || tx.status === statusFilter;
      return matchSearch && matchStatus;
    });
  }, [data, search, statusFilter]);

  return (
    <DashboardShell title="Transactions">
      <div className="space-y-4">
        {/* Toolbar */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative flex-1 min-w-48">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none"
              fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803 7.5 7.5 0 0015.803 15.803z" />
            </svg>
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by ID, merchant, payment method..."
              aria-label="Search transactions"
              className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded bg-white text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label="Filter by status"
            className="px-3 py-2 text-sm border border-slate-200 rounded bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <span className="text-xs text-slate-400 whitespace-nowrap">
            {filtered.length} result{filtered.length !== 1 ? "s" : ""}
          </span>
        </div>

        {/* Table */}
        <div className="bg-white rounded-lg border border-slate-200 overflow-x-auto">
          {isLoading ? (
            <PageSpinner />
          ) : isError ? (
            <ErrorState
              title="Unable to load transactions"
              onRetry={refetch}
            />
          ) : filtered.length === 0 ? (
            <EmptyState
              title="No transactions found"
              description={
                search || statusFilter
                  ? "Try adjusting your search or filter."
                  : "No transactions have been created yet."
              }
            />
          ) : (
            <table className="w-full text-xs" role="table">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="px-5 py-3 text-left font-medium text-slate-500">Transaction</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500">Amount</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500">Merchant</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500">Method</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500">Status</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500">Time</th>
                  <th className="px-5 py-3 text-left font-medium text-slate-500">Action</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((tx) => (
                  <tr
                    key={tx.id}
                    className="border-b border-slate-50 hover:bg-slate-50/60 transition-colors"
                  >
                    <td className="px-5 py-3">
                      <span className="font-mono text-slate-800 font-medium">{tx.external_id}</span>
                      <span className="block text-slate-400 text-[10px]">#{tx.id}</span>
                    </td>
                    <td className="px-5 py-3 font-semibold text-slate-900 tabular-nums">
                      {formatCurrency(tx.amount, tx.currency)}
                    </td>
                    <td className="px-5 py-3 text-slate-600 max-w-[140px] truncate" title={tx.merchant}>
                      {tx.merchant}
                    </td>
                    <td className="px-5 py-3 text-slate-500">{tx.payment_method}</td>
                    <td className="px-5 py-3">
                      <StatusBadge status={tx.status as TransactionStatus} />
                    </td>
                    <td className="px-5 py-3 text-slate-400" title={formatTimestamp(tx.created_at)}>
                      {formatRelativeTime(tx.created_at)}
                    </td>
                    <td className="px-5 py-3">
                      <Link
                        href={`/dashboard/transactions/${tx.id}`}
                        className="text-blue-600 hover:text-blue-700 font-medium"
                      >
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

export default function TransactionsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[40vh]">
          <PageSpinner />
        </div>
      }
    >
      <TransactionsContent />
    </Suspense>
  );
}
