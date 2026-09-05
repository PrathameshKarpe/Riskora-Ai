"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/context";
import { Button } from "@/components/ui/Button";
import type { Role } from "@/lib/types";

const DEMO_ACCOUNTS = [
  { email: "admin@riskora.local",    role: "ADMIN" as Role,        label: "Admin" },
  { email: "analyst@riskora.local",  role: "RISK_ANALYST" as Role, label: "Risk Analyst" },
  { email: "reviewer@riskora.local", role: "REVIEWER" as Role,     label: "Reviewer" },
];

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("admin@riskora.local");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login({ email: email.trim() });
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex flex-col justify-between w-1/2 p-14 bg-slate-900 border-r border-slate-800">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-blue-600 flex items-center justify-center">
            <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <span className="text-white font-bold text-lg">Riskora AI</span>
        </div>

        <div>
          <h2 className="text-3xl font-bold text-white mb-4 leading-tight">
            AI-powered fraud<br />detection at scale.
          </h2>
          <p className="text-slate-400 text-sm leading-relaxed max-w-sm">
            Multi-agent investigation, RAG evidence retrieval, deterministic
            policy engine, and complete audit trail — all in one platform.
          </p>
        </div>

        <div className="space-y-3">
          {[
            { label: "ML Detection",      desc: "RandomForest fraud probability scoring" },
            { label: "AI Investigation",  desc: "LangGraph multi-agent analysis pipeline" },
            { label: "Policy Engine",     desc: "Deterministic rule enforcement" },
            { label: "Human Review",      desc: "Analyst workflow with full audit trail" },
          ].map((item) => (
            <div key={item.label} className="flex items-start gap-3">
              <div className="mt-0.5 h-4 w-4 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center shrink-0">
                <div className="h-1.5 w-1.5 rounded-full bg-blue-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-300">{item.label}</p>
                <p className="text-xs text-slate-500">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="h-7 w-7 rounded bg-blue-600 flex items-center justify-center">
              <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            </div>
            <span className="text-white font-bold">Riskora AI</span>
          </div>

          <div className="mb-8">
            <h1 className="text-xl font-semibold text-white mb-1">Sign in</h1>
            <p className="text-sm text-slate-400">Risk Operations Dashboard</p>
          </div>

          {/* Demo quick-select */}
          <div className="mb-6">
            <p className="text-[10px] uppercase tracking-widest text-slate-600 mb-2">Demo accounts</p>
            <div className="flex gap-2">
              {DEMO_ACCOUNTS.map((acc) => (
                <button
                  key={acc.email}
                  type="button"
                  onClick={() => setEmail(acc.email)}
                  className={`flex-1 py-1.5 text-xs rounded border transition-colors ${
                    email === acc.email
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-slate-800 text-slate-400 border-slate-700 hover:border-slate-500 hover:text-slate-200"
                  }`}
                >
                  {acc.label}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-xs font-medium text-slate-400 mb-1.5">
                Email address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@riskora.local"
                className="w-full px-3 py-2 text-sm bg-slate-800 border border-slate-700 text-white rounded placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                autoComplete="email"
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 text-red-400 text-xs bg-red-900/20 border border-red-800/40 rounded px-3 py-2">
                <svg className="h-3.5 w-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                {error}
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              loading={loading}
              aria-label="Sign in to Riskora AI"
            >
              Sign in
            </Button>
          </form>

          <p className="mt-6 text-[10px] text-slate-600 text-center">
            Development mode — any email is accepted.
          </p>
        </div>
      </div>
    </div>
  );
}
