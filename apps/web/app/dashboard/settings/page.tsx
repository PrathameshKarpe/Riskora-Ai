"use client";

import { useQuery } from "@tanstack/react-query";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { useAuth } from "@/lib/auth/context";
import { getHealth, getHealthDb } from "@/lib/api/client";
import { cn } from "@/lib/utils/format";

function StatusDot({ ok }: { ok: boolean }) {
  return (
    <span
      className={cn(
        "inline-block h-2 w-2 rounded-full",
        ok ? "bg-emerald-500" : "bg-red-500"
      )}
    />
  );
}

export default function SettingsPage() {
  const { user, logout } = useAuth();

  const healthQ = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    retry: false,
  });
  const dbQ = useQuery({
    queryKey: ["health", "db"],
    queryFn: getHealthDb,
    retry: false,
  });

  const apiOk = healthQ.data?.status === "ok";
  const dbOk  = dbQ.data?.database === "ok";

  return (
    <DashboardShell title="Settings">
      <div className="space-y-5 max-w-2xl">
        {/* Account */}
        <Card>
          <CardHeader><CardTitle>Account</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Email</span>
              <span className="font-medium text-slate-800">{user?.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Role</span>
              <span className="font-medium text-slate-800">{user?.role}</span>
            </div>
            <div className="pt-2">
              <button
                onClick={logout}
                className="text-xs text-red-600 hover:text-red-700 font-medium"
              >
                Sign out
              </button>
            </div>
          </CardContent>
        </Card>

        {/* System status */}
        <Card>
          <CardHeader><CardTitle>System Status</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">FastAPI Backend</span>
              <div className="flex items-center gap-2">
                <StatusDot ok={apiOk} />
                <span className={apiOk ? "text-emerald-700" : "text-red-600"}>
                  {healthQ.isLoading ? "Checking..." : apiOk ? "Operational" : "Unavailable"}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">PostgreSQL</span>
              <div className="flex items-center gap-2">
                <StatusDot ok={dbOk} />
                <span className={dbOk ? "text-emerald-700" : "text-red-600"}>
                  {dbQ.isLoading ? "Checking..." : dbOk ? "Connected" : "Unavailable"}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Environment */}
        <Card>
          <CardHeader><CardTitle>Environment</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-xs">
            {[
              { label: "API URL",     value: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000" },
              { label: "Mode",        value: process.env.NODE_ENV },
              { label: "Version",     value: "Phase 5 — Risk Operations Dashboard" },
            ].map(({ label, value }) => (
              <div key={label} className="flex justify-between">
                <span className="text-slate-500">{label}</span>
                <span className="font-mono text-slate-700">{value}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* About */}
        <Card>
          <CardHeader><CardTitle>About Riskora AI</CardTitle></CardHeader>
          <CardContent className="text-xs text-slate-600 space-y-2">
            <p>
              Riskora AI is a prototype payment-risk investigation platform built for the Razorpay AI Buildathon.
            </p>
            <p className="text-slate-400">
              Phase 1–4: ML fraud detection, LangGraph multi-agent investigation, RAG evidence retrieval, deterministic policy engine, FastAPI + PostgreSQL backend.
            </p>
            <p className="text-slate-400">
              Phase 5: Next.js risk operations dashboard.
            </p>
            <p className="text-red-400 mt-3">
              This is a test/prototype environment. Use synthetic data only.
            </p>
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  );
}
