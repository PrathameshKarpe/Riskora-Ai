import React from "react";
import { render, screen } from "@testing-library/react";
import { BehavioralSignals } from "@/components/investigation/BehavioralSignals";

const signals = [
  { signal: "amount_anomaly",  severity: "HIGH",   explanation: "Transaction significantly exceeds normal behavior." },
  { signal: "new_device",      severity: "HIGH",   explanation: "Device has not previously been associated with the customer." },
  { signal: "new_location",    severity: "MEDIUM", explanation: "Transaction from an unusual location." },
];

describe("BehavioralSignals", () => {
  it("renders the section heading", () => {
    render(<BehavioralSignals signals={signals} />);
    expect(screen.getByText("Why Is This Transaction Risky?")).toBeInTheDocument();
  });

  it("renders each signal name", () => {
    render(<BehavioralSignals signals={signals} />);
    expect(screen.getByText(/amount anomaly/i)).toBeInTheDocument();
    expect(screen.getByText(/new device/i)).toBeInTheDocument();
  });

  it("renders explanations", () => {
    render(<BehavioralSignals signals={signals} />);
    expect(screen.getByText(/exceeds normal behavior/i)).toBeInTheDocument();
  });

  it("renders severity icons", () => {
    render(<BehavioralSignals signals={signals} />);
    // HIGH signals get 🔴, MEDIUM gets 🟠
    const icons = screen.getAllByText("🔴");
    expect(icons.length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText("🟠").length).toBeGreaterThanOrEqual(1);
  });

  it("renders nothing when signals array is empty", () => {
    const { container } = render(<BehavioralSignals signals={[]} />);
    expect(container.firstChild).toBeNull();
  });
});
