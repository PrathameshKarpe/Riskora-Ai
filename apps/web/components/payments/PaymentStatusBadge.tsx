import { cn, paymentStatusColor } from "@/lib/utils/format";

export function PaymentStatusBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
        paymentStatusColor(status)
      )}
    >
      {status}
    </span>
  );
}
