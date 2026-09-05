/**
 * PaymentStatusBadge component tests.
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import { PaymentStatusBadge } from "@/components/payments/PaymentStatusBadge";

describe("PaymentStatusBadge", () => {
  it.each([["CREATED"], ["AUTHORIZED"], ["CAPTURED"], ["FAILED"]])(
    "renders %s status",
    (status) => {
      render(<PaymentStatusBadge status={status} />);
      expect(screen.getByText(status)).toBeInTheDocument();
    }
  );

  it("applies emerald class for CAPTURED", () => {
    const { container } = render(<PaymentStatusBadge status="CAPTURED" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("emerald");
  });

  it("applies red class for FAILED", () => {
    const { container } = render(<PaymentStatusBadge status="FAILED" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("red");
  });

  it("applies blue class for AUTHORIZED", () => {
    const { container } = render(<PaymentStatusBadge status="AUTHORIZED" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("blue");
  });
});
