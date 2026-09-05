import React from "react";
import { render, screen } from "@testing-library/react";
import { DecisionPanel } from "@/components/investigation/DecisionPanel";

const mockDecision = {
  recommendation:      "HOLD",
  policy_action:       "HUMAN_REVIEW",
  requires_human_review: true,
  reason_codes:        ["HIGH_AMOUNT_ANOMALY", "NEW_DEVICE"],
  explanation:         "Multiple independent risk indicators detected.",
};

describe("DecisionPanel", () => {
  it("renders AI recommendation", () => {
    render(<DecisionPanel decision={mockDecision} />);
    expect(screen.getByText("AI Recommendation")).toBeInTheDocument();
    expect(screen.getByText("HOLD")).toBeInTheDocument();
  });

  it("renders policy action", () => {
    render(<DecisionPanel decision={mockDecision} />);
    expect(screen.getByText("HUMAN_REVIEW")).toBeInTheDocument();
  });

  it("shows human review notice when required", () => {
    render(<DecisionPanel decision={mockDecision} />);
    expect(screen.getByText(/human review required/i)).toBeInTheDocument();
  });

  it("renders reason codes as badges", () => {
    render(<DecisionPanel decision={mockDecision} />);
    expect(screen.getByText("HIGH_AMOUNT_ANOMALY")).toBeInTheDocument();
    expect(screen.getByText("NEW_DEVICE")).toBeInTheDocument();
  });

  it("renders the explanation text", () => {
    render(<DecisionPanel decision={mockDecision} />);
    expect(screen.getByText("Multiple independent risk indicators detected.")).toBeInTheDocument();
  });

  it("renders nothing when decision is null", () => {
    const { container } = render(<DecisionPanel decision={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("distinguishes AI recommendation from Policy Engine authority", () => {
    render(<DecisionPanel decision={mockDecision} />);
    expect(screen.getByText(/not the final authority/i)).toBeInTheDocument();
    expect(screen.getByText(/authoritative action/i)).toBeInTheDocument();
  });
});
