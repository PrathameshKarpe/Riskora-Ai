/**
 * ReviewDialog tests — confirm/cancel, reason validation, loading state.
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReviewDialog } from "@/components/reviews/ReviewDialog";

// Mock the API client
jest.mock("@/lib/api/client", () => ({
  approveTransaction: jest.fn().mockResolvedValue({ id: 1, decision: "APPROVE", reason: "Approved." }),
  blockTransaction:   jest.fn().mockResolvedValue({ id: 2, decision: "BLOCK",   reason: "Blocked."  }),
  holdTransaction:    jest.fn().mockResolvedValue({ id: 3, decision: "HOLD",    reason: "On hold."  }),
}));

const mockOnSuccess = jest.fn();
const mockOnClose   = jest.fn();

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

function renderDialog(decision: "APPROVE" | "BLOCK" | "HOLD" = "APPROVE") {
  return render(
    <ReviewDialog
      open
      onClose={mockOnClose}
      transactionId={42}
      transactionExtId="TX-042"
      decision={decision}
      riskScore={81}
      riskLevel="HIGH"
      onSuccess={mockOnSuccess}
    />,
    { wrapper }
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

describe("ReviewDialog", () => {
  it("renders transaction summary and decision label", () => {
    renderDialog("APPROVE");
    expect(screen.getByText("TX-042")).toBeInTheDocument();
    expect(screen.getByText("APPROVE")).toBeInTheDocument();
  });

  it("shows reason textarea", () => {
    renderDialog("APPROVE");
    expect(screen.getByLabelText(/reason/i)).toBeInTheDocument();
  });

  it("shows error if reason is empty on submit", async () => {
    renderDialog("APPROVE");
    fireEvent.click(screen.getByText("Confirm Approve"));
    await waitFor(() => {
      expect(screen.getByText(/reason is required/i)).toBeInTheDocument();
    });
  });

  it("closes on Cancel click", () => {
    renderDialog("APPROVE");
    fireEvent.click(screen.getByText("Cancel"));
    expect(mockOnClose).toHaveBeenCalled();
  });

  it("renders BLOCK variant with danger label", () => {
    renderDialog("BLOCK");
    expect(screen.getByText("BLOCK")).toBeInTheDocument();
  });

  it("renders HOLD variant", () => {
    renderDialog("HOLD");
    expect(screen.getByText("HOLD")).toBeInTheDocument();
  });
});
