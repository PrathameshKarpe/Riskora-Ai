import type { RiskLevel, TransactionStatus } from "@/lib/types";

export function formatCurrency(amount: number, currency = "INR"): string {
  if (currency === "INR") {
    return `₹${amount.toLocaleString("en-IN")}`;
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatRelativeTime(isoString: string): string {
  const now = Date.now();
  const then = new Date(isoString).getTime();
  const diff = Math.floor((now - then) / 1000);

  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export function formatTimestamp(isoString: string): string {
  return new Date(isoString).toLocaleString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export function formatTime(isoString: string): string {
  return new Date(isoString).toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function riskLevelColor(level: RiskLevel): string {
  switch (level) {
    case "LOW":      return "text-emerald-700 bg-emerald-50 border-emerald-200";
    case "MEDIUM":   return "text-amber-700 bg-amber-50 border-amber-200";
    case "HIGH":     return "text-orange-700 bg-orange-50 border-orange-200";
    case "CRITICAL": return "text-red-700 bg-red-50 border-red-200";
    default:         return "text-slate-600 bg-slate-100 border-slate-200";
  }
}

export function riskLevelDot(level: RiskLevel): string {
  switch (level) {
    case "LOW":      return "bg-emerald-500";
    case "MEDIUM":   return "bg-amber-500";
    case "HIGH":     return "bg-orange-500";
    case "CRITICAL": return "bg-red-500";
    default:         return "bg-slate-400";
  }
}

export function statusColor(status: TransactionStatus): string {
  switch (status) {
    case "RECEIVED":             return "text-slate-600 bg-slate-100 border-slate-200";
    case "INVESTIGATING":        return "text-blue-700 bg-blue-50 border-blue-200";
    case "PENDING_REVIEW":       return "text-amber-700 bg-amber-50 border-amber-200";
    case "APPROVE":              return "text-emerald-700 bg-emerald-50 border-emerald-200";
    case "BLOCK":                return "text-red-700 bg-red-50 border-red-200";
    case "HOLD":                 return "text-orange-700 bg-orange-50 border-orange-200";
    case "INVESTIGATION_FAILED": return "text-red-700 bg-red-100 border-red-300";
    default:                     return "text-slate-600 bg-slate-100 border-slate-200";
  }
}

export function riskScoreBar(score: number): string {
  if (score >= 85) return "bg-red-500";
  if (score >= 60) return "bg-orange-500";
  if (score >= 30) return "bg-amber-500";
  return "bg-emerald-500";
}

export function severityIcon(severity: string): string {
  switch (severity?.toUpperCase()) {
    case "CRITICAL":
    case "HIGH":   return "🔴";
    case "MEDIUM": return "🟠";
    case "LOW":    return "🟡";
    default:       return "⚪";
  }
}

export function eventTypeLabel(eventType: string): string {
  return eventType
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(" ");
}

// ── Payment formatting (Phase 6) ─────────────────────────────────────────────

/** Convert paise → rupees and format as ₹ currency string. */
export function formatMinorCurrency(amountMinor: number, currency = "INR"): string {
  return formatCurrency(amountMinor / 100, currency);
}

export function paymentStatusColor(status: string): string {
  switch (status) {
    case "CREATED":    return "text-slate-600 bg-slate-100 border-slate-200";
    case "AUTHORIZED": return "text-blue-700 bg-blue-50 border-blue-200";
    case "CAPTURED":   return "text-emerald-700 bg-emerald-50 border-emerald-200";
    case "FAILED":     return "text-red-700 bg-red-50 border-red-200";
    default:           return "text-slate-600 bg-slate-100 border-slate-200";
  }
}

export function decisionColor(decision: string | null): string {
  if (!decision) return "text-slate-400";
  switch (decision) {
    case "APPROVE": return "text-emerald-700";
    case "BLOCK":   return "text-red-700";
    case "HOLD":    return "text-orange-700";
    case "REVIEW":  return "text-amber-700";
    default:        return "text-slate-600";
  }
}
