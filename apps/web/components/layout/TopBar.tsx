"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { useAuth } from "@/lib/auth/context";

export function TopBar({ title }: { title?: string }) {
  const { user } = useAuth();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = search.trim();
    if (!q) return;
    // If it looks like a transaction ID number, go to that transaction
    if (/^\d+$/.test(q)) {
      router.push(`/dashboard/transactions/${q}`);
    } else {
      router.push(`/dashboard/transactions?search=${encodeURIComponent(q)}`);
    }
    setSearch("");
  }

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between h-14 px-6 bg-white border-b border-slate-200 shrink-0">
      <div className="flex items-center gap-4">
        {title && (
          <h1 className="text-sm font-semibold text-slate-900">{title}</h1>
        )}
      </div>

      <div className="flex items-center gap-3">
        {/* Search */}
        <form onSubmit={handleSearch} className="relative hidden sm:block">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400 pointer-events-none"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 15.803 7.5 7.5 0 0015.803 15.803z" />
          </svg>
          <input
            ref={inputRef}
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search transactions..."
            aria-label="Search transactions"
            className="pl-8 pr-4 py-1.5 text-xs rounded border border-slate-200 bg-slate-50 text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:bg-white w-52 transition-colors"
          />
        </form>

        {/* Role badge */}
        {user && (
          <span className="hidden sm:inline-flex items-center gap-1.5 text-xs font-medium text-slate-600">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            {user.role.replace("_", " ")}
          </span>
        )}

        {/* User avatar */}
        {user && (
          <div
            className="h-7 w-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-semibold select-none"
            title={user.email}
            aria-label={`Signed in as ${user.email}`}
          >
            {user.email.charAt(0).toUpperCase()}
          </div>
        )}
      </div>
    </header>
  );
}
