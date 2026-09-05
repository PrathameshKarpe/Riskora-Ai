"use client";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="text-red-400 mb-3 text-3xl">⚠</div>
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {message && <p className="text-xs text-slate-500 mt-1 max-w-sm">{message}</p>}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 text-xs font-medium text-blue-600 hover:text-blue-700 underline-offset-2 hover:underline"
        >
          Retry
        </button>
      )}
    </div>
  );
}
