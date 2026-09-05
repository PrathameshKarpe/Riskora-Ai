"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { PageSpinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/ErrorState";
import { RiskBadge, StatusBadge } from "@/components/ui/RiskBadge";
import {
  getDashboardMetrics,
  getRecentTransactions,
  getRiskDistribution,
} from "@/lib/api/client";
import { formatCurrency, formatRelativeTime } from "@/lib/utils/format";
import type { RiskLevel } from "@/lib/types";
import { RiskDistributionChart } from "@/components/charts/RiskDistributionChart";

function MetricCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string | number | React.ReactNode;
  sub?: string;
  accent?: string;
}) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">{label}</p>
      <div className={`text-2xl font-bold tabular-nums ${accent ?? "text-slate-900"}`}>
        {value}
      </div>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const metricsQ = useQuery({
    queryKey: ["dashboard", "metrics"],
    queryFn: getDashboardMetrics,
    refetchInterval: 30_000,
  });
  const recentQ = useQuery({
    queryKey: ["dashboard", "recent"],
    queryFn: getRecentTransactions,
    refetchInterval: 30_000,
  });
  const distQ = useQuery({
    queryKey: ["dashboard", "risk-distribution"],
    queryFn: getRiskDistribution,
    refetchInterval: 30_000,
  });

  const m = metricsQ.data;
  const recent = recentQ.data ?? [];
  const dist = distQ.data ?? {};

  return (
    <DashboardShell title="Overview">
      {metricsQ.isLoading ? (
        <PageSpinner />
      ) : metricsQ.isError ? (
        <ErrorState
          title="Unable to load dashboard metrics"
          message="The API may be unavailable. Check that the FastAPI server is running."
          onRetry={() => metricsQ.refetch()}
        />
      ) : (
        <div className="space-y-6">
          {/* Pipeline architecture banner */}
          <div className="bg-slate-900 rounded-lg p-4 text-xs font-mono text-slate-400 flex items-center gap-2 overflow-x-auto whitespace-nowrap">
            <span className="text-blue-400 font-semibold">ML DETECTS</span>
            <span className="text-slate-600">→</span>
            <span className="text-purple-400 font-semibold">AI INVESTIGATES</span>
            <span className="text-slate-600">→</span>
            <span className="text-amber-400 font-semibold">RAG PROVIDES EVIDENCE</span>
            <span className="text-slate-600">→</span>
            <span className="text-orange-400 font-semibold">POLICY CONTROLS</span>
            <span className="text-slate-600">→</span>
            <span className="text-emerald-400 font-semibold">HUMAN APPROVES</span>
            <span className="text-slate-600">→</span>
            <span className="text-slate-300 font-semibold">AUDIT RECORDS</span>
          </div>

          {/* Top metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              label="Total Transactions"
              value={m?.total_transactions ?? 0}
              sub="All time"
            />
            <MetricCard
              label="Suspicious"
              value={m?.suspicious_transactions ?? 0}
              sub="HIGH or CRITICAL risk"
              accent="text-orange-600"
            />
            <MetricCard
              label="Pending Review"
              value={m?.pending_reviews ?? 0}
              sub="Awaiting analyst decision"
              accent="text-amber-600"
            />
            <MetricCard
              label="Prevented Loss"
              value={
                m?.estimated_prevented_loss != null
                  ? formatCurrency(m.estimated_prevented_loss)
                  : "N/A"
              }
              sub="Estimated blocked value"
              accent="text-emerald-600"
            />
          </div>

          {/* Secondary metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              label="Fraud Detection Rate"
              value={m?.fraud_detection_rate != null ? `${(m.fraud_detection_rate * 100).toFixed(1)}%` : "N/A"}
              sub="From completed investigations"
            />
            <MetricCard
              label="False Positive Rate"
              value={m?.false_positive_rate != null ? `${(m.false_positive_rate * 100).toFixed(1)}%` : "N/A"}
              sub="Approved after review"
            />
            <MetricCard
              label="Blocked"
              value={m?.blocked_transactions ?? 0}
              sub="Transactions blocked"
              accent="text-red-600"
            />
            <MetricCard
              label="Approved"
              value={m?.approved_transactions ?? 0}
              sub="Transactions approved"
              accent="text-emerald-600"
            />
          </div>

          {/* Chart + Recent */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Risk distribution chart */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle>Risk Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {distQ.isLoading ? (
                  <PageSpinner />
                ) : Object.keys(dist).length === 0 ? (
                  <p className="text-xs text-slate-400 py-4 text-center">
                    No risk assessments yet.
                  </p>
                ) : (
                  <RiskDistributionChart data={dist as Record<RiskLevel, number>} />
                )}
              </CardContent>
            </Card>

            {/* Recent transactions */}
            <Card className="lg:col-span-2">
              <CardHeader className="flex items-center justify-between">
                <CardTitle>Recent Transactions</CardTitle>
                <Link
                  href="/dashboard/transactions"
                  className="text-xs text-blue-600 hover:text-blue-700"
                >
                  View all →
                </Link>
              </CardHeader>
              <div className="overflow-x-auto">
                {recentQ.isLoading ? (
                  <PageSpinner />
                ) : recent.length === 0 ? (
                  <p className="text-xs text-slate-400 text-center py-8">
                    No transactions yet.
                  </p>
                ) : (
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-slate-100">
                        <th className="px-5 py-2.5 text-left font-medium text-slate-500">ID</th>
                        <th className="px-5 py-2.5 text-left font-medium text-slate-500">Amount</th>
                        <th className="px-5 py-2.5 text-left font-medium text-slate-500">Merchant</th>
                        <th className="px-5 py-2.5 text-left font-medium text-slate-500">Status</th>
                        <th className="px-5 py-2.5 text-left font-medium text-slate-500">Time</th>
                        <th className="px-5 py-2.5 text-left font-medium text-slate-500"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {recent.slice(0, 8).map((tx) => (
                        <tr
                          key={tx.id}
                          className="border-b border-slate-50 hover:bg-slate-50 transition-colors"
                        >
                          <td className="px-5 py-3 font-mono text-slate-700">
                            {tx.external_id}
                          </td>
                          <td className="px-5 py-3 font-medium text-slate-900 tabular-nums">
                            {formatCurrency(tx.amount, tx.currency)}
                          </td>
                          <td className="px-5 py-3 text-slate-600 max-w-[120px] truncate">
                            {tx.merchant}
                          </td>
                          <td className="px-5 py-3">
                            <StatusBadge status={tx.status} />
                          </td>
                          <td className="px-5 py-3 text-slate-400">
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
            </Card>
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
