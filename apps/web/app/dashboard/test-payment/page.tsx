"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PageSpinner, Spinner } from "@/components/ui/Spinner";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { PaymentStatusBadge } from "@/components/payments/PaymentStatusBadge";
import {
  createPaymentOrder,
  getPaymentConfig,
  listPayments,
  verifyPayment,
} from "@/lib/api/client";
import {
  cn,
  decisionColor,
  formatMinorCurrency,
  formatRelativeTime,
  riskLevelColor,
} from "@/lib/utils/format";
import type { PaymentOrderResponse, PaymentScenario } from "@/lib/types";

// ── Scenario selector ─────────────────────────────────────────────────────────

const SCENARIOS: {
  value: PaymentScenario;
  label: string;
  amount: number;
  description: string;
  expectedRisk: string;
  expectedDecision: string;
  color: string;
}[] = [
  {
    value: "LOW",
    label: "Low Risk",
    amount: 15000,         // ₹150 in paise
    description: "Normal retail purchase from a known device and location.",
    expectedRisk: "LOW",
    expectedDecision: "APPROVE",
    color: "border-emerald-200 bg-emerald-50/40",
  },
  {
    value: "HIGH",
    label: "High Risk",
    amount: 4850000,       // ₹48 500 in paise
    description: "High velocity, new device, new location, amount anomaly.",
    expectedRisk: "HIGH",
    expectedDecision: "HUMAN REVIEW",
    color: "border-orange-200 bg-orange-50/40",
  },
  {
    value: "CRITICAL",
    label: "Critical Risk",
    amount: 20000000,      // ₹2 00 000 in paise
    description: "Multiple fraud indicators: impossible travel, fraud history, very high velocity.",
    expectedRisk: "CRITICAL",
    expectedDecision: "BLOCK",
    color: "border-red-200 bg-red-50/40",
  },
];

// ── Checkout flow state ───────────────────────────────────────────────────────

type CheckoutStep =
  | { phase: "idle" }
  | { phase: "ordering" }
  | { phase: "awaiting_payment"; order: PaymentOrderResponse }
  | { phase: "verifying"; order: PaymentOrderResponse }
  | { phase: "done"; transactionId: number; riskStatus: string; decision: string | null };

export default function TestPaymentPage() {
  const qc = useQueryClient();
  const [scenario, setScenario] = useState<PaymentScenario>("HIGH");
  const [step, setStep] = useState<CheckoutStep>({ phase: "idle" });
  const [error, setError] = useState<string | null>(null);

  // Backend integration mode
  const configQ = useQuery({
    queryKey: ["payment", "config"],
    queryFn: getPaymentConfig,
  });

  // Recent payments list
  const paymentsQ = useQuery({
    queryKey: ["payments"],
    queryFn: () => listPayments(50),
    refetchInterval: 15_000,
  });

  const selectedScenario = SCENARIOS.find((s) => s.value === scenario)!;
  const mode = configQ.data?.mode ?? "local-demo";

  // ── Create order ────────────────────────────────────────────────────────────

  const createOrder = useMutation({
    mutationFn: () =>
      createPaymentOrder({
        amount: selectedScenario.amount,
        currency: "INR",
        scenario,
      }),
    onMutate: () => { setError(null); setStep({ phase: "ordering" }); },
    onSuccess: (order) => {
      if (mode === "razorpay-test" && order.key_id) {
        // Real Razorpay Checkout — open the Razorpay JS modal.
        setStep({ phase: "awaiting_payment", order });
        openRazorpayCheckout(order);
      } else {
        // Local-demo mode: auto-verify with a synthetic HMAC signature.
        setStep({ phase: "verifying", order });
        autoVerifyLocalDemo(order);
      }
    },
    onError: (err: Error) => {
      setError(err.message);
      setStep({ phase: "idle" });
    },
  });

  // ── Razorpay Checkout (real Test Mode) ────────────────────────────────────

  function openRazorpayCheckout(order: PaymentOrderResponse) {
    // Razorpay Checkout JS is loaded via a <script> tag. If it is not yet
    // available the user must refresh — we surface a clear error.
    const Razorpay =
      typeof window !== "undefined"
        ? (window as unknown as Record<string, unknown>)["Razorpay"]
        : undefined;

    if (!Razorpay || typeof Razorpay !== "function") {
      setError(
        "Razorpay Checkout script is not loaded. " +
          "Add <script src='https://checkout.razorpay.com/v1/checkout.js'></script> " +
          "to app/layout.tsx for real Test Mode payments."
      );
      setStep({ phase: "idle" });
      return;
    }

    const rzp = new (Razorpay as new (opts: unknown) => { open(): void; on(e: string, cb: () => void): void })({
      key: order.key_id,
      amount: order.amount,
      currency: order.currency,
      order_id: order.razorpay_order_id,
      name: "Riskora AI",
      description: `Test Payment — ${order.scenario ?? "demo"} scenario`,
      theme: { color: "#2563eb" },
      handler: (response: {
        razorpay_payment_id: string;
        razorpay_order_id: string;
        razorpay_signature: string;
      }) => {
        setStep({ phase: "verifying", order });
        verifyOnServer(order, response.razorpay_payment_id, response.razorpay_signature);
      },
      modal: {
        ondismiss: () => {
          setStep({ phase: "idle" });
          setError("Payment cancelled.");
        },
      },
    });
    rzp.open();
  }

  // ── Local-demo auto-verify ────────────────────────────────────────────────

  async function autoVerifyLocalDemo(order: PaymentOrderResponse) {
    // In local-demo mode the backend signed the order with RAZORPAY_DEMO_SECRET.
    // We call the /payments/verify endpoint which generates the expected
    // HMAC and compares it — a correct local-demo signature is computed and
    // sent to the backend so the same verification code path runs.
    // The signature is generated server-side by the seed script; for the
    // frontend demo we call a GET-free endpoint that returns a pre-signed
    // payment id.
    //
    // Implementation: the backend /payments/verify also accepts a demo
    // flow where the payment_id and signature are generated server-side.
    // We call POST /payments/demo-verify for the local-demo case.
    try {
      const demoVerifyResp = await fetch("/api/v1/payments/demo-verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getStoredToken()}`,
        },
        body: JSON.stringify({ razorpay_order_id: order.razorpay_order_id }),
        cache: "no-store",
      });

      if (!demoVerifyResp.ok) {
        const detail = await demoVerifyResp.json().catch(() => ({}));
        throw new Error(
          (detail as { detail?: { message?: string } }).detail?.message ??
            `Verification failed (${demoVerifyResp.status})`
        );
      }

      const result = await demoVerifyResp.json() as {
        verified: boolean;
        payment: { transaction_id: number; risk_status: string; decision: string | null };
      };
      qc.invalidateQueries({ queryKey: ["payments"] });
      qc.invalidateQueries({ queryKey: ["transactions"] });
      setStep({
        phase: "done",
        transactionId: result.payment.transaction_id,
        riskStatus: result.payment.risk_status,
        decision: result.payment.decision,
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Verification failed.");
      setStep({ phase: "idle" });
    }
  }

  async function verifyOnServer(
    order: PaymentOrderResponse,
    paymentId: string,
    signature: string
  ) {
    try {
      const resp = await verifyPayment({
        razorpay_order_id: order.razorpay_order_id,
        razorpay_payment_id: paymentId,
        razorpay_signature: signature,
      });
      qc.invalidateQueries({ queryKey: ["payments"] });
      qc.invalidateQueries({ queryKey: ["transactions"] });
      setStep({
        phase: "done",
        transactionId: resp.payment.transaction_id,
        riskStatus: resp.payment.risk_status,
        decision: resp.payment.decision,
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Payment verification failed.");
      setStep({ phase: "idle" });
    }
  }

  function getStoredToken(): string {
    try {
      const raw = sessionStorage.getItem("riskora_auth");
      return raw ? JSON.parse(raw).access_token : "";
    } catch {
      return "";
    }
  }

  function reset() {
    setStep({ phase: "idle" });
    setError(null);
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <DashboardShell title="Test Payments">
      <div className="space-y-6 max-w-4xl">

        {/* Mode banner */}
        {configQ.data && (
          <div className={cn(
            "flex items-center justify-between rounded-lg px-4 py-3 border text-xs",
            mode === "razorpay-test"
              ? "bg-blue-50 border-blue-200 text-blue-800"
              : "bg-amber-50 border-amber-200 text-amber-800"
          )}>
            <div className="flex items-center gap-2">
              <span className={cn(
                "h-2 w-2 rounded-full",
                mode === "razorpay-test" ? "bg-blue-500" : "bg-amber-500"
              )} />
              <span className="font-semibold">
                {mode === "razorpay-test" ? "Razorpay Test Mode" : "Local Demo Mode"}
              </span>
              <span className="text-slate-500 hidden sm:inline">
                {mode === "razorpay-test"
                  ? "— Real Razorpay Test Mode API. No live money."
                  : "— Synthetic payments. No Razorpay credentials configured."}
              </span>
            </div>
            {configQ.data.webhook_configured && (
              <span className="text-[10px] px-2 py-0.5 bg-white/60 rounded border border-current">
                Webhooks active
              </span>
            )}
          </div>
        )}

        {/* Synthetic data notice */}
        <div className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded px-4 py-2">
          <span className="font-semibold text-slate-700">⚠ Synthetic test data</span>
          {" — "}All payments on this page use clearly-labeled demo transactions.
          No real money is processed. Results go through the full ML → Agents → Policy pipeline.
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Left: create payment */}
          <div className="space-y-4">
            <Card>
              <CardHeader><CardTitle>Create Test Payment</CardTitle></CardHeader>
              <CardContent className="space-y-4">

                {/* Scenario selector */}
                <div>
                  <p className="text-xs font-medium text-slate-700 mb-2">Demo Scenario</p>
                  <div className="space-y-2">
                    {SCENARIOS.map((s) => (
                      <button
                        key={s.value}
                        type="button"
                        onClick={() => { setScenario(s.value); reset(); }}
                        className={cn(
                          "w-full text-left rounded-lg border p-3 transition-all",
                          scenario === s.value
                            ? s.color + " ring-1 ring-offset-1 ring-blue-400"
                            : "border-slate-200 bg-white hover:bg-slate-50"
                        )}
                        aria-pressed={scenario === s.value}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-semibold text-slate-800">{s.label}</span>
                          <span className="text-xs font-bold text-slate-600 tabular-nums">
                            {formatMinorCurrency(s.amount)}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500">{s.description}</p>
                        <div className="flex gap-2 mt-2">
                          <span className="text-[10px] text-slate-400">
                            Expected: <span className="font-semibold">{s.expectedRisk}</span>
                            {" → "}
                            <span className="font-semibold">{s.expectedDecision}</span>
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Amount display */}
                <div className="flex justify-between text-xs border-t border-slate-100 pt-3">
                  <span className="text-slate-500">Amount (paise)</span>
                  <span className="font-mono font-medium text-slate-700">
                    {selectedScenario.amount.toLocaleString("en-IN")}
                  </span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Display amount</span>
                  <span className="font-semibold text-slate-900">
                    {formatMinorCurrency(selectedScenario.amount)}
                  </span>
                </div>

                {/* Error */}
                {error && (
                  <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
                    {error}
                  </div>
                )}

                {/* Action */}
                {step.phase === "idle" && (
                  <Button
                    variant="primary"
                    className="w-full"
                    onClick={() => createOrder.mutate()}
                    loading={createOrder.isPending}
                    aria-label={`Create ${scenario} risk test payment`}
                  >
                    Create Test Payment
                  </Button>
                )}

                {step.phase === "ordering" && (
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <PageSpinner className="h-4 w-4" />
                    Creating order...
                  </div>
                )}

                {step.phase === "awaiting_payment" && (
                  <div className="text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded px-3 py-2">
                    Razorpay Checkout is open. Complete the test payment in the modal.
                  </div>
                )}

                {step.phase === "verifying" && (
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <PageSpinner className="h-4 w-4" />
                    Verifying payment &amp; running risk pipeline...
                  </div>
                )}

                {step.phase === "done" && (
                  <div className="space-y-3">
                    <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs">
                      <p className="font-semibold text-emerald-800 mb-1">Payment verified ✓</p>
                      <div className="space-y-1 text-emerald-700">
                        <div className="flex justify-between">
                          <span>Risk Status</span>
                          <span className="font-bold">{step.riskStatus}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Policy Decision</span>
                          <span className={cn("font-bold", decisionColor(step.decision))}>
                            {step.decision ?? "—"}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Link
                        href={`/dashboard/transactions/${step.transactionId}`}
                        className="flex-1 text-center text-xs font-medium text-blue-600 hover:text-blue-700 border border-blue-200 rounded px-3 py-2 bg-white hover:bg-blue-50 transition-colors"
                      >
                        View Full Investigation →
                      </Link>
                      <Button variant="outline" size="sm" onClick={reset}>
                        New Payment
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Pipeline architecture */}
            <Card>
              <CardHeader><CardTitle>Payment → Risk Pipeline</CardTitle></CardHeader>
              <CardContent>
                <ol className="space-y-1.5 text-xs text-slate-600">
                  {[
                    ["Payment Created",        "Razorpay Test Mode order"],
                    ["Signature Verified",     "HMAC-SHA256 server-side"],
                    ["ML Risk Scored",         "RandomForest fraud probability"],
                    ["Behavior Analyzed",      "9 behavioral signal checks"],
                    ["AI Investigated",        "LangGraph multi-agent"],
                    ["Evidence Retrieved",     "TF-IDF RAG from policy docs"],
                    ["Decision Generated",     "Decision Agent recommendation"],
                    ["Policy Applied",         "Deterministic Policy Engine"],
                    ["Human Review (if HIGH)", "Analyst approve/block/hold"],
                    ["Audit Recorded",         "Full event trail in PostgreSQL"],
                  ].map(([step, detail], i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="shrink-0 h-4 w-4 rounded-full bg-blue-100 text-blue-700 text-[9px] font-bold flex items-center justify-center mt-0.5">
                        {i + 1}
                      </span>
                      <span>
                        <span className="font-medium text-slate-700">{step}</span>
                        <span className="text-slate-400"> — {detail}</span>
                      </span>
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          </div>

          {/* Right: recent payments */}
          <div>
            <Card>
              <CardHeader className="flex items-center justify-between">
                <CardTitle>Recent Payments</CardTitle>
                <span className="text-xs text-slate-400">
                  {paymentsQ.data?.length ?? 0} total
                </span>
              </CardHeader>
              {paymentsQ.isLoading ? (
                <CardContent><PageSpinner /></CardContent>
              ) : paymentsQ.isError ? (
                <CardContent>
                  <ErrorState title="Unable to load payments" onRetry={() => paymentsQ.refetch()} />
                </CardContent>
              ) : !paymentsQ.data?.length ? (
                <CardContent>
                  <EmptyState
                    title="No payments yet"
                    description="Create a test payment to see results here."
                  />
                </CardContent>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-slate-100 bg-slate-50">
                        <th className="px-4 py-2.5 text-left font-medium text-slate-500">Order</th>
                        <th className="px-4 py-2.5 text-left font-medium text-slate-500">Amount</th>
                        <th className="px-4 py-2.5 text-left font-medium text-slate-500">Status</th>
                        <th className="px-4 py-2.5 text-left font-medium text-slate-500">Risk</th>
                        <th className="px-4 py-2.5 text-left font-medium text-slate-500">Decision</th>
                        <th className="px-4 py-2.5 text-left font-medium text-slate-500"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {paymentsQ.data.map((p) => (
                        <tr key={p.id} className="border-b border-slate-50 hover:bg-slate-50/60 transition-colors">
                          <td className="px-4 py-2.5">
                            <span className="font-mono text-[10px] text-slate-600">
                              {p.razorpay_order_id.slice(-10)}
                            </span>
                            {p.scenario && (
                              <span className="block text-[10px] text-slate-400">{p.scenario}</span>
                            )}
                          </td>
                          <td className="px-4 py-2.5 font-semibold text-slate-800 tabular-nums">
                            {formatMinorCurrency(p.amount, p.currency)}
                          </td>
                          <td className="px-4 py-2.5">
                            <PaymentStatusBadge status={p.payment_status} />
                          </td>
                          <td className="px-4 py-2.5">
                            {p.risk_status === "UNASSESSED" ? (
                              <span className="text-slate-400">—</span>
                            ) : (
                              <span className={cn(
                                "inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold border",
                                riskLevelColor(p.risk_status as "LOW" | "MEDIUM" | "HIGH" | "CRITICAL")
                              )}>
                                {p.risk_status}
                              </span>
                            )}
                          </td>
                          <td className={cn("px-4 py-2.5 font-bold text-xs", decisionColor(p.decision))}>
                            {p.decision ?? "—"}
                          </td>
                          <td className="px-4 py-2.5">
                            <Link
                              href={`/dashboard/transactions/${p.transaction_id}`}
                              className="text-blue-600 hover:text-blue-700 font-medium"
                            >
                              View
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>
    </DashboardShell>
  );
}
