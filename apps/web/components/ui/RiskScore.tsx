import { cn, riskScoreBar } from "@/lib/utils/format";
import type { RiskLevel } from "@/lib/types";
import { RiskBadge } from "./RiskBadge";

interface RiskScoreProps {
  score: number;
  level: RiskLevel;
  showBar?: boolean;
  size?: "sm" | "md" | "lg";
}

export function RiskScore({ score, level, showBar = true, size = "md" }: RiskScoreProps) {
  const clamped = Math.max(0, Math.min(100, Math.round(score)));

  if (size === "sm") {
    return (
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold text-slate-900 tabular-nums">{clamped}</span>
        <RiskBadge level={level} />
      </div>
    );
  }

  if (size === "lg") {
    return (
      <div>
        <div className="flex items-end gap-2 mb-1">
          <span className="text-4xl font-bold text-slate-900 tabular-nums leading-none">{clamped}</span>
          <span className="text-sm text-slate-400 mb-1">/ 100</span>
        </div>
        <RiskBadge level={level} />
        {showBar && (
          <div className="mt-3 h-2 w-full bg-slate-100 rounded-full overflow-hidden">
            <div
              className={cn("h-full rounded-full transition-all", riskScoreBar(clamped))}
              style={{ width: `${clamped}%` }}
              role="progressbar"
              aria-valuenow={clamped}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Risk score: ${clamped} out of 100`}
            />
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-baseline gap-1 mb-1">
        <span className="text-2xl font-bold text-slate-900 tabular-nums">{clamped}</span>
        <span className="text-xs text-slate-400">/ 100</span>
      </div>
      <RiskBadge level={level} />
      {showBar && (
        <div className="mt-2 h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
          <div
            className={cn("h-full rounded-full", riskScoreBar(clamped))}
            style={{ width: `${clamped}%` }}
            role="progressbar"
            aria-valuenow={clamped}
            aria-valuemin={0}
            aria-valuemax={100}
          />
        </div>
      )}
    </div>
  );
}
