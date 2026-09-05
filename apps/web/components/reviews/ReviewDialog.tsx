"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Dialog } from "@/components/ui/Dialog";
import { Button } from "@/components/ui/Button";
import { approveTransaction, blockTransaction, holdTransaction } from "@/lib/api/client";
import type { ReviewDecision, RiskLevel } from "@/lib/types";
import { cn } from "@/lib/utils/format";

interface Props {
  open: boolean;
  onClose: () => void;
  transactionId: number;
  transactionExtId: string;
  decision: ReviewDecision;
  riskScore?: number;
  riskLevel?: RiskLevel;
  onSuccess: () => void;
}

const DECISION_CONFIG: Record<ReviewDecision, { label: string; color: string; variant: "primary" | "danger" | "outline" }> = {
  APPROVE: { label: "Confirm Approve", color: "text-emerald-700", variant: "primary" },
  BLOCK:   { label: "Confirm Block",   color: "text-red-700",     variant: "danger" },
  HOLD:    { label: "Confirm Hold",    color: "text-amber-700",   variant: "outline" },
};

export function ReviewDialog({
  open, onClose, transactionId, transactionExtId, decision, riskScore, riskLevel, onSuccess,
}: Props) {
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const config = DECISION_CONFIG[decision];

  const mutation = useMutation({
    mutationFn: async () => {
      if (!reason.trim()) throw new Error("A reason is required.");
      const payload = { reason: reason.trim() };
      if (decision === "APPROVE") return approveTransaction(transactionId, payload);
      if (decision === "BLOCK")   return blockTransaction(transactionId, payload);
      return holdTransaction(transactionId, payload);
    },
    onSuccess: () => {
      setReason("");
      setError("");
      onSuccess();
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  function handleClose() {
    if (!mutation.isPending) {
      setReason("");
      setError("");
      onClose();
    }
  }

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      title={`${config.label.replace("Confirm ", "Confirm ")} Transaction`}
    >
      <div className="space-y-4">
        {/* Summary */}
        <div className="bg-slate-50 rounded-lg p-4 text-xs space-y-2">
          <div className="flex justify-between">
            <span className="text-slate-500">Transaction</span>
            <span className="font-mono font-semibold text-slate-800">{transactionExtId}</span>
          </div>
          {riskScore != null && (
            <div className="flex justify-between">
              <span className="text-slate-500">Risk Score</span>
              <span className="font-semibold">{riskScore.toFixed(0)} / 100{riskLevel ? ` — ${riskLevel}` : ""}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-slate-500">Action</span>
            <span className={cn("font-bold", config.color)}>{decision}</span>
          </div>
        </div>

        <p className="text-xs text-slate-500">
          This action will be permanently recorded in the audit trail.
        </p>

        {/* Reason */}
        <div>
          <label htmlFor="review-reason" className="block text-xs font-medium text-slate-700 mb-1.5">
            Reason <span className="text-red-500">*</span>
          </label>
          <textarea
            id="review-reason"
            rows={3}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Describe the basis for your decision..."
            className="w-full text-xs rounded border border-slate-200 px-3 py-2 text-slate-700 placeholder-slate-400 resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
            maxLength={2000}
            aria-required="true"
            aria-describedby={error ? "review-error" : undefined}
          />
          <p className="text-right text-[10px] text-slate-400 mt-0.5">{reason.length}/2000</p>
        </div>

        {error && (
          <p id="review-error" className="text-xs text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
            {error}
          </p>
        )}

        <div className="flex justify-end gap-2 pt-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClose}
            disabled={mutation.isPending}
          >
            Cancel
          </Button>
          <Button
            variant={config.variant}
            size="sm"
            onClick={() => mutation.mutate()}
            loading={mutation.isPending}
            aria-label={config.label}
          >
            {config.label}
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
