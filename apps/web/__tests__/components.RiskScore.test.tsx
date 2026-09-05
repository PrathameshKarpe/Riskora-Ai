/**
 * RiskScore component tests.
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import { RiskScore } from "@/components/ui/RiskScore";

describe("RiskScore", () => {
  it("renders score and risk level badge", () => {
    render(<RiskScore score={91} level="HIGH" />);
    expect(screen.getByText("91")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
  });

  it("clamps score to 0-100", () => {
    render(<RiskScore score={150} level="CRITICAL" />);
    expect(screen.getByText("100")).toBeInTheDocument();
  });

  it("renders the progress bar by default", () => {
    render(<RiskScore score={75} level="HIGH" />);
    const bar = screen.getByRole("progressbar");
    expect(bar).toBeInTheDocument();
    expect(bar).toHaveAttribute("aria-valuenow", "75");
  });

  it("does not render progress bar when showBar=false", () => {
    render(<RiskScore score={75} level="HIGH" showBar={false} />);
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  it("renders large size correctly", () => {
    render(<RiskScore score={55} level="MEDIUM" size="lg" />);
    expect(screen.getByText("55")).toBeInTheDocument();
    expect(screen.getByText("/ 100")).toBeInTheDocument();
  });
});
