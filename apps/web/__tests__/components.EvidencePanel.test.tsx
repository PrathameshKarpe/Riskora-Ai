import React from "react";
import { render, screen } from "@testing-library/react";
import { EvidencePanel } from "@/components/investigation/EvidencePanel";

const mockEvidence = [
  {
    source:          "velocity-risk.md",
    section:         "Velocity Risk Policy",
    content:         "High transaction velocity is an elevated-risk indicator.",
    relevance_score: 0.94,
    metadata:        { category: "velocity" },
  },
];

describe("EvidencePanel", () => {
  it("renders evidence section and source", () => {
    render(<EvidencePanel evidence={mockEvidence} />);
    expect(screen.getByText("Velocity Risk Policy")).toBeInTheDocument();
    expect(screen.getByText(/velocity-risk\.md/)).toBeInTheDocument();
  });

  it("renders relevance score", () => {
    render(<EvidencePanel evidence={mockEvidence} />);
    expect(screen.getByText("94%")).toBeInTheDocument();
  });

  it("renders evidence content", () => {
    render(<EvidencePanel evidence={mockEvidence} />);
    expect(screen.getByText(/elevated-risk indicator/)).toBeInTheDocument();
  });

  it("renders metadata tags", () => {
    render(<EvidencePanel evidence={mockEvidence} />);
    expect(screen.getByText(/category: velocity/i)).toBeInTheDocument();
  });

  it("shows empty state when no evidence", () => {
    render(<EvidencePanel evidence={[]} />);
    expect(screen.getByText(/no relevant evidence retrieved/i)).toBeInTheDocument();
  });

  it("renders multiple evidence items", () => {
    const multi = [
      { ...mockEvidence[0], section: "Section A" },
      { ...mockEvidence[0], section: "Section B" },
    ];
    render(<EvidencePanel evidence={multi} />);
    expect(screen.getByText("Section A")).toBeInTheDocument();
    expect(screen.getByText("Section B")).toBeInTheDocument();
  });
});
