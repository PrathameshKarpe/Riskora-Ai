"use client";

import type { AuthUser } from "@/lib/types";

const KEY = "riskora_auth";

export function saveAuth(user: AuthUser): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(KEY, JSON.stringify(user));
}

export function loadAuth(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function clearAuth(): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(KEY);
}

export function getToken(): string | null {
  return loadAuth()?.access_token ?? null;
}
