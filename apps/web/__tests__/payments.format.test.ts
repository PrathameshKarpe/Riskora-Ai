/**
 * Payment formatting utility tests.
 */
import {
  decisionColor,
  formatMinorCurrency,
  paymentStatusColor,
} from "@/lib/utils/format";

describe("formatMinorCurrency()", () => {
  it("converts paise to rupees and formats with ₹", () => {
    const result = formatMinorCurrency(4_850_000);
    expect(result).toContain("₹");
    expect(result).toContain("48,500");
  });

  it("handles ₹150 (15000 paise)", () => {
    const result = formatMinorCurrency(15_000);
    expect(result).toContain("150");
  });

  it("handles ₹2 00 000 (20000000 paise)", () => {
    const result = formatMinorCurrency(20_000_000);
    expect(result).toContain("2");
  });

  it("zero amount", () => {
    const result = formatMinorCurrency(0);
    expect(result).toContain("₹");
  });
});

describe("paymentStatusColor()", () => {
  it("returns emerald for CAPTURED", () => {
    expect(paymentStatusColor("CAPTURED")).toContain("emerald");
  });

  it("returns blue for AUTHORIZED", () => {
    expect(paymentStatusColor("AUTHORIZED")).toContain("blue");
  });

  it("returns red for FAILED", () => {
    expect(paymentStatusColor("FAILED")).toContain("red");
  });

  it("returns slate for CREATED", () => {
    expect(paymentStatusColor("CREATED")).toContain("slate");
  });

  it("returns slate for unknown status", () => {
    expect(paymentStatusColor("UNKNOWN")).toContain("slate");
  });
});

describe("decisionColor()", () => {
  it("returns emerald for APPROVE", () => {
    expect(decisionColor("APPROVE")).toContain("emerald");
  });

  it("returns red for BLOCK", () => {
    expect(decisionColor("BLOCK")).toContain("red");
  });

  it("returns amber for REVIEW", () => {
    expect(decisionColor("REVIEW")).toContain("amber");
  });

  it("returns orange for HOLD", () => {
    expect(decisionColor("HOLD")).toContain("orange");
  });

  it("returns slate-400 for null", () => {
    expect(decisionColor(null)).toContain("slate");
  });
});
