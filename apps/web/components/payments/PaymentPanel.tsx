"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { getPaymentForTransaction } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { PageSpinner } from "@/components/ui/Spinner";
import { PaymentStatusBadge } from "./PaymentStatusBadge";
import {
  cn,
  decisionColor,
  formatMinorCurrency,
  formatTimestamp,
  riskLevelColor,
} from "@/lib/utils/format";

interface Props {
  transactionId: number;
}

export function PaymentPanel({ transactionId }: Props) {
  const { data: payment, isLoading, isError } = useQuery({
    queryKey: ["payments", "tx", transactionId],
    queryFn: () => getPaymentForTransaction(transactionId),
    retry: false,
  });

  // No payment linked to this transaction — not a Razorpay payment.
  if (!isLoading && (isError || !payment)) return null;

  return (
    <Card className="border-blue-100 bg-blue-50/20">
      <CardHeader className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg className="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
          </svg>
          <CardTitle>Razorpay Payment</CardTitle>
        </div>
        {payment && (
          <span className={cn(
            "text-[10px] font-medium uppercase tracking-wide px-2 py-0.5 rounded border",
            payment.mode === "razorpay-test"
              ? "text-blue-700 bg-blue-100 border-blue-200"
              : "text-slate-600 bg-slate-100 border-slate-200"
          )}>
            {payment.mode === "razorpay-test" ? "Test Mode" : "Local Demo"}
          </span>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <PageSpinner />
        ) : payment ? (
          <div className="space-y-3 text-xs">
            {/* Payment section */}
            <div className="space-y-2">
              <p className="text-[10px] uppercase tracking-widest text-slate-400 font-medium">
                Payment
              </p>
              {[
                { label: "Order ID",    value: payment.razorpay_order_id, mono: true },
                { label: "Payment ID",  value: payment.razorpay_payment_id ?? "—", mono: true },
                { label: "Amount",      value: formatMinorCurrency(payment.amount, payment.currency), mono: false },
                { label: "Currency",    value: payment.currency, mono: false },
              ].map(({ label, value, mono }) => (
                <div key={label} className="flex justify-between">
                  <span className="text-slate-500">{label}</span>
                  <span className={cn("font-medium text-slate-700 text-right max-w-[180px] truncate", mono ? "font-mono text-[10px]" : "")}>
                    {value}
                  </span>
                </div>
              ))}
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Payment Status</span>
                <PaymentStatusBadge status={payment.payment_status} />
              </div>
            </div>

            <div className="border-t border-slate-100 pt-3 space-y-2">
              <p className="text-[10px] uppercase tracking-widest text-slate-400 font-medium">
                Risk &amp; Decision
              </p>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Risk Status</span>
                {payment.risk_status === "UNASSESSED" ? (
                  <span className="text-slate-400 font-medium">UNASSESSED</span>
                ) : (
                  <span className={cn(
                    "inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border",
                    riskLevelColor(payment.risk_status as "LOW" | "MEDIUM" | "HIGH" | "CRITICAL")
                  )}>
                    {payment.risk_status}
                  </span>
                )}
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500">Policy Decision</span>
                <span className={cn("font-bold text-sm", decisionColor(payment.decision))}>
                  {payment.decision ?? "—"}
                </span>
              </div>
              {payment.scenario && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Demo Scenario</span>
                  <span className="font-medium text-slate-600 uppercase">{payment.scenario}</span>
                </div>
              )}
            </div>

            {payment.scenario && (
              <p className="text-[10px] text-slate-400 border-t border-slate-100 pt-2">
                ⚠ Synthetic test data — not real fraud data.
              </p>
            )}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
