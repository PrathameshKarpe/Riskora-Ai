"use client";

import { cn, formatTime } from "@/lib/utils/format";
import type { Investigation } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";

const PIPELINE_STEPS = [
  { key: "TRANSACTION_RECEIVED",        label: "Transaction Received",   agent: "system" },
  { key: "ML_RISK_CALCULATED",          label: "ML Risk Calculated",     agent: "ml" },
  { key: "BEHAVIOR_ANALYSIS_COMPLETED", label: "Behavior Agent",         agent: "behavior" },
  { key: "INVESTIGATION_STARTED",       label: "Investigation Agent",    agent: "investigation" },
  { key: "EVIDENCE_RETRIEVED",          label: "Evidence / RAG Agent",   agent: "evidence" },
  { key: "DECISION_GENERATED",          label: "Decision Agent",         agent: "decision" },
  { key: "POLICY_EVALUATED",            label: "Policy Engine",          agent: "policy" },
];

interface Props {
  investigation: Investigation;
}

export function InvestigationTimeline({ investigation }: Props) {
  const auditEventKeys = new Set<string>();
  // We infer completed steps from the investigation structure rather than
  // having a separate audit fetch here. The agents array tells us what ran.
  const agentNames = new Set(investigation.agents.map((a) => a.agent_name));

  function isStepDone(key: string): boolean {
    if (key === "TRANSACTION_RECEIVED") return true;
    if (key === "ML_RISK_CALCULATED") return investigation.risk != null;
    if (key === "BEHAVIOR_ANALYSIS_COMPLETED") return investigation.behavioral_signals.length > 0 || investigation.status === "COMPLETED";
    if (key === "INVESTIGATION_STARTED") return investigation.status === "COMPLETED" || investigation.status === "FAILED";
    if (key === "EVIDENCE_RETRIEVED") return investigation.evidence.length > 0 || investigation.status === "COMPLETED";
    if (key === "DECISION_GENERATED") return investigation.decision != null;
    if (key === "POLICY_EVALUATED") return investigation.decision != null;
    return false;
  }

  function getStepDetail(key: string): string | null {
    if (key === "ML_RISK_CALCULATED" && investigation.risk) {
      return `Score: ${investigation.risk.final_score.toFixed(0)} · ${investigation.risk.risk_level}`;
    }
    if (key === "BEHAVIOR_ANALYSIS_COMPLETED") {
      const count = investigation.behavioral_signals.length;
      return count > 0 ? `${count} signal${count !== 1 ? "s" : ""} detected` : "No anomaly signals";
    }
    if (key === "EVIDENCE_RETRIEVED") {
      const count = investigation.evidence.length;
      return count > 0 ? `${count} evidence item${count !== 1 ? "s" : ""} retrieved` : "No relevant evidence";
    }
    if (key === "DECISION_GENERATED" && investigation.decision) {
      return `Recommendation: ${investigation.decision.recommendation}`;
    }
    if (key === "POLICY_EVALUATED" && investigation.decision) {
      return `Action: ${investigation.decision.policy_action}`;
    }
    if (key === "INVESTIGATION_STARTED") {
      return investigation.summary ?? null;
    }
    return null;
  }

  const isComplete = investigation.status === "COMPLETED";
  const humanReviewPending = investigation.decision?.requires_human_review ?? false;

  const steps = [
    ...PIPELINE_STEPS,
    {
      key: "HUMAN_REVIEW",
      label: "Human Review",
      agent: "reviewer",
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI Investigation Timeline</CardTitle>
        <p className="text-xs text-slate-400 mt-0.5">
          {investigation.status === "COMPLETED"
            ? "Investigation completed"
            : investigation.status === "RUNNING"
            ? "Investigation in progress..."
            : "Investigation failed"}
        </p>
      </CardHeader>
      <CardContent className="pt-2">
        <ol className="relative" aria-label="Investigation pipeline steps">
          {steps.map((step, idx) => {
            const isHumanReview = step.key === "HUMAN_REVIEW";
            const done = isHumanReview ? false : isStepDone(step.key);
            const detail = isHumanReview ? null : getStepDetail(step.key);
            const isLast = idx === steps.length - 1;
            const pending = isHumanReview && humanReviewPending;

            return (
              <li key={step.key} className="flex gap-4 pb-5">
                {/* Connector line */}
                <div className="flex flex-col items-center">
                  <div
                    className={cn(
                      "h-5 w-5 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5",
                      done
                        ? "bg-blue-600 border-blue-600"
                        : pending
                        ? "bg-amber-500 border-amber-500"
                        : "bg-white border-slate-200"
                    )}
                  >
                    {done && (
                      <svg className="h-2.5 w-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                    {pending && (
                      <div className="h-2 w-2 rounded-full bg-white animate-pulse" />
                    )}
                  </div>
                  {!isLast && (
                    <div className={cn("w-px flex-1 mt-1", done ? "bg-blue-200" : "bg-slate-100")} />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 pb-0 min-w-0">
                  <p
                    className={cn(
                      "text-xs font-medium",
                      done ? "text-slate-800" : pending ? "text-amber-700" : "text-slate-400"
                    )}
                  >
                    {step.label}
                    {pending && (
                      <span className="ml-2 text-[10px] font-normal bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded border border-amber-200">
                        Awaiting analyst
                      </span>
                    )}
                  </p>
                  {detail && (
                    <p className="text-[11px] text-slate-500 mt-0.5 truncate" title={detail}>
                      {detail}
                    </p>
                  )}
                </div>
              </li>
            );
          })}
        </ol>

        {isComplete && investigation.completed_at && (
          <div className="mt-1 pt-3 border-t border-slate-100 text-[11px] text-slate-400 flex justify-between">
            <span>Started: {formatTime(investigation.started_at)}</span>
            <span>Completed: {formatTime(investigation.completed_at)}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
