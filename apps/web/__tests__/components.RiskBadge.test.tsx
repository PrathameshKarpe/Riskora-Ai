import React from "react";
import { render, screen } from "@testing-library/react";
import { RiskBadge, StatusBadge } from "@/components/ui/RiskBadge";

describe("RiskBadge", () => {
  it.each([["LOW"], ["MEDIUM"], ["HIGH"], ["CRITICAL"]])(
    "renders %s risk level",
    (level) => {
      render(<RiskBadge level={level as "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"} />);
      expect(screen.getByText(level)).toBeInTheDocument();
    }
  );
});

describe("StatusBadge", () => {
  it("renders RECEIVED status", () => {
    render(<StatusBadge status="RECEIVED" />);
    expect(screen.getByText("RECEIVED")).toBeInTheDocument();
  });

  it("renders PENDING REVIEW status with space-replaced underscore", () => {
    render(<StatusBadge status="PENDING_REVIEW" />);
    expect(screen.getByText("PENDING REVIEW")).toBeInTheDocument();
  });

  it("renders BLOCK status", () => {
    render(<StatusBadge status="BLOCK" />);
    expect(screen.getByText("BLOCK")).toBeInTheDocument();
  });
});
