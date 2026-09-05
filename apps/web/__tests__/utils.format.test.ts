import {
  cn,
  eventTypeLabel,
  formatCurrency,
  formatRelativeTime,
  riskLevelColor,
  riskScoreBar,
  severityIcon,
  statusColor,
} from "@/lib/utils/format";

describe("formatCurrency", () => {
  it("formats INR amounts with ₹ symbol", () => {
    expect(formatCurrency(48500, "INR")).toContain("₹");
    expect(formatCurrency(48500, "INR")).toContain("48,500");
  });

  it("formats USD amounts", () => {
    const result = formatCurrency(1000, "USD");
    expect(result).toContain("1,000");
  });
});

describe("riskLevelColor", () => {
  it("returns emerald for LOW", () => {
    expect(riskLevelColor("LOW")).toContain("emerald");
  });
  it("returns amber for MEDIUM", () => {
    expect(riskLevelColor("MEDIUM")).toContain("amber");
  });
  it("returns orange for HIGH", () => {
    expect(riskLevelColor("HIGH")).toContain("orange");
  });
  it("returns red for CRITICAL", () => {
    expect(riskLevelColor("CRITICAL")).toContain("red");
  });
});

describe("riskScoreBar", () => {
  it("returns red for score >= 85", () => {
    expect(riskScoreBar(91)).toContain("red");
    expect(riskScoreBar(85)).toContain("red");
  });
  it("returns orange for HIGH range", () => {
    expect(riskScoreBar(70)).toContain("orange");
  });
  it("returns amber for MEDIUM range", () => {
    expect(riskScoreBar(45)).toContain("amber");
  });
  it("returns emerald for LOW range", () => {
    expect(riskScoreBar(10)).toContain("emerald");
  });
});

describe("statusColor", () => {
  it("returns red for BLOCK", () => {
    expect(statusColor("BLOCK")).toContain("red");
  });
  it("returns emerald for APPROVE", () => {
    expect(statusColor("APPROVE")).toContain("emerald");
  });
  it("returns amber for PENDING_REVIEW", () => {
    expect(statusColor("PENDING_REVIEW")).toContain("amber");
  });
});

describe("severityIcon", () => {
  it("returns red circle for HIGH/CRITICAL", () => {
    expect(severityIcon("HIGH")).toBe("🔴");
    expect(severityIcon("CRITICAL")).toBe("🔴");
  });
  it("returns orange circle for MEDIUM", () => {
    expect(severityIcon("MEDIUM")).toBe("🟠");
  });
  it("returns yellow for LOW", () => {
    expect(severityIcon("LOW")).toBe("🟡");
  });
});

describe("eventTypeLabel", () => {
  it("converts underscore event types to title case", () => {
    expect(eventTypeLabel("ML_RISK_CALCULATED")).toBe("Ml Risk Calculated");
    expect(eventTypeLabel("POLICY_EVALUATED")).toBe("Policy Evaluated");
  });
});

describe("cn", () => {
  it("joins class names", () => {
    expect(cn("a", "b", "c")).toBe("a b c");
  });
  it("filters falsy values", () => {
    expect(cn("a", false, null, undefined, "b")).toBe("a b");
  });
  it("returns empty string for all falsy", () => {
    expect(cn(false, null, undefined)).toBe("");
  });
});

describe("formatRelativeTime", () => {
  it("returns seconds for recent timestamps", () => {
    const recent = new Date(Date.now() - 30_000).toISOString();
    expect(formatRelativeTime(recent)).toMatch(/\d+s ago/);
  });
  it("returns minutes for older timestamps", () => {
    const old = new Date(Date.now() - 5 * 60_000).toISOString();
    expect(formatRelativeTime(old)).toMatch(/\d+m ago/);
  });
});
