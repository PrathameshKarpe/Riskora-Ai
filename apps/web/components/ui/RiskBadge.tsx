import { riskLevelColor, riskLevelDot, statusColor } from "@/lib/utils/format";
import type { RiskLevel, TransactionStatus } from "@/lib/types";
import { cn } from "@/lib/utils/format";

export function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold border",
        riskLevelColor(level)
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", riskLevelDot(level))} />
      {level}
    </span>
  );
}

export function StatusBadge({ status }: { status: TransactionStatus }) {
  const label = status.replace(/_/g, " ");
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
        statusColor(status)
      )}
    >
      {label}
    </span>
  );
}
