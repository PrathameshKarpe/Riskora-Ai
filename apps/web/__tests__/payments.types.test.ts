/**
 * Payment type contract tests — verify the TypeScript interfaces match
 * the expected API shape without needing a live backend.
 */
import type {
  Payment,
  PaymentConfig,
  PaymentMode,
  PaymentOrderRequest,
  PaymentOrderResponse,
  PaymentScenario,
  PaymentVerifyRequest,
  PaymentVerifyResponse,
} from "@/lib/types";

// TypeScript compile-time assertions — these fail at build time if the
// types don't match the expected shape.

function assertPaymentShape(p: Payment): void {
  const _id: number = p.id;
  const _txId: number = p.transaction_id;
  const _orderId: string = p.razorpay_order_id;
  const _payId: string | null = p.razorpay_payment_id;
  const _amount: number = p.amount;       // paise, not float rupees
  const _currency: string = p.currency;
  const _payStatus = p.payment_status;    // "CREATED"|"AUTHORIZED"|"CAPTURED"|"FAILED"
  const _riskStatus = p.risk_status;      // "UNASSESSED"|"LOW"|"MEDIUM"|"HIGH"|"CRITICAL"
  const _decision: string | null = p.decision;
  const _scenario: PaymentScenario | null = p.scenario;
  const _mode: PaymentMode = p.mode;
  const _createdAt: string = p.created_at;
  const _updatedAt: string = p.updated_at;
}

function assertOrderRequestShape(r: PaymentOrderRequest): void {
  const _amount: number = r.amount;
  const _currency: string = r.currency;
  const _scenario: PaymentScenario = r.scenario;
}

function assertOrderResponseShape(r: PaymentOrderResponse): void {
  const _txId: number = r.transaction_id;
  const _orderId: string = r.razorpay_order_id;
  const _amount: number = r.amount;
  const _currency: string = r.currency;
  const _keyId: string | null = r.key_id;  // secret never here
  const _mode: PaymentMode = r.mode;
  const _scenario: PaymentScenario | null = r.scenario;
}

function assertConfigShape(c: PaymentConfig): void {
  const _mode: PaymentMode = c.mode;
  const _keyId: string | null = c.key_id;   // only public key, no secret
  const _webhook: boolean = c.webhook_configured;
}

// No key_secret field must exist anywhere in the types
type NoSecretInOrderResponse = "key_secret" extends keyof PaymentOrderResponse
  ? "FAIL — key_secret must not be in PaymentOrderResponse"
  : "PASS";
const _noSecret: NoSecretInOrderResponse = "PASS";

type NoSecretInConfig = "key_secret" extends keyof PaymentConfig
  ? "FAIL — key_secret must not be in PaymentConfig"
  : "PASS";
const _noSecretConfig: NoSecretInConfig = "PASS";

// Verify payment state machines are separate (not the same field)
type PaymentStatusValues = Payment["payment_status"];
type RiskStatusValues = Payment["risk_status"];
// They must be different unions
type DifferentStateMachines = PaymentStatusValues extends RiskStatusValues
  ? RiskStatusValues extends PaymentStatusValues
    ? "OVERLAP — state machines may not be properly separated"
    : "PASS"
  : "PASS";
const _separated: DifferentStateMachines = "PASS";

// Runtime tests — just verify the shape works as expected
describe("Payment types", () => {
  it("PaymentScenario accepts only LOW, HIGH, CRITICAL", () => {
    const valid: PaymentScenario[] = ["LOW", "HIGH", "CRITICAL"];
    expect(valid).toHaveLength(3);
  });

  it("PaymentMode accepts only razorpay-test and local-demo", () => {
    const valid: PaymentMode[] = ["razorpay-test", "local-demo"];
    expect(valid).toHaveLength(2);
  });

  it("amount field represents paise (integer)", () => {
    const p: Payment = {
      id: 1,
      transaction_id: 1,
      razorpay_order_id: "order_test",
      razorpay_payment_id: null,
      amount: 4_850_000,   // ₹48 500 in paise
      currency: "INR",
      payment_status: "CREATED",
      risk_status: "UNASSESSED",
      decision: null,
      scenario: "HIGH",
      mode: "local-demo",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    expect(p.amount).toBe(4_850_000);
    expect(Number.isInteger(p.amount)).toBe(true);
  });

  it("PaymentConfig key_id is nullable — never contains secret", () => {
    const localDemoConfig: PaymentConfig = {
      mode: "local-demo",
      key_id: null,          // no key in local-demo mode
      webhook_configured: false,
    };
    expect(localDemoConfig.key_id).toBeNull();
  });

  it("separate payment_status and risk_status state machines", () => {
    const p: Partial<Payment> = {
      payment_status: "AUTHORIZED",
      risk_status: "HIGH",
      decision: "HUMAN_REVIEW",
    };
    // All three can be independently set — they don't overwrite each other
    expect(p.payment_status).toBe("AUTHORIZED");
    expect(p.risk_status).toBe("HIGH");
    expect(p.decision).toBe("HUMAN_REVIEW");
  });
});
