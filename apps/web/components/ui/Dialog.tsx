"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils/format";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  className?: string;
}

export function Dialog({ open, onClose, title, children, className }: DialogProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      {/* Panel */}
      <div
        ref={ref}
        className={cn(
          "relative bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-md mx-4 p-6",
          className
        )}
      >
        <h2 id="dialog-title" className="text-base font-semibold text-slate-900 mb-4">
          {title}
        </h2>
        {children}
      </div>
    </div>
  );
}
