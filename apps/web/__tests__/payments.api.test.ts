/**
 * Payment API client tests — mock fetch, verify correct request
 * construction and secret-safety invariants.
 */

const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock sessionStorage with a stored token
Object.defineProperty(window, "sessionStorage", {
  value: {
    getItem: jest.fn((k: string) =>
      k === "riskora_auth"
        ? JSON.stringify({ access_token: "test-tok", email: "a@b.com", role: "ADMIN" })
        : null
    ),
    setItem: jest.fn(),
    removeItem: jest.fn(),
  },
  writable: true,
});

import {
  createPaymentOrder,
  getPaymentConfig,
  getPaymentForTransaction,
  listPayments,
  verifyPayment,
} from "@/lib/api/client";

function mockOk(data: unknown, status = 200) {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    status,
    text: () => Promise.resolve(JSON.stringify(data)),
  } as Response);
}

function mockErr(status: number, detail: string) {
  mockFetch.mockResolvedValueOnce({
    ok: false,
    status,
    text: () => Promise.resolve(JSON.stringify({ detail })),
  } as Response);
}

beforeEach(() => mockFetch.mockClear());

// ── getPaymentConfig ───────────────────────────────────────────────────────

describe("getPaymentConfig()", () => {
  it("calls GET /api/v1/payments/config", async () => {
    mockOk({ mode: "local-demo", key_id: null, webhook_configured: false });
    await getPaymentConfig();
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/payments/config",
      expect.any(Object)
    );
  });

  it("returns mode=local-demo when no credentials", async () => {
    mockOk({ mode: "local-demo", key_id: null, webhook_configured: false });
    const cfg = await getPaymentConfig();
    expect(cfg.mode).toBe("local-demo");
    expect(cfg.key_id).toBeNull();
  });

  it("never has key_secret in response", async () => {
    mockOk({ mode: "local-demo", key_id: null, webhook_configured: false });
    const cfg = await getPaymentConfig();
    expect((cfg as unknown as Record<string, unknown>)["key_secret"]).toBeUndefined();
    expect((cfg as unknown as Record<string, unknown>)["razorpay_key_secret"]).toBeUndefined();
  });
});

// ── createPaymentOrder ─────────────────────────────────────────────────────

describe("createPaymentOrder()", () => {
  it("POSTs to /api/v1/payments/orders", async () => {
    mockOk(
      {
        transaction_id: 42,
        razorpay_order_id: "order_demo1234",
        amount: 4_850_000,
        currency: "INR",
        key_id: null,
        mode: "local-demo",
        scenario: "HIGH",
      },
      201
    );
    const resp = await createPaymentOrder({
      amount: 4_850_000,
      currency: "INR",
      scenario: "HIGH",
    });
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/payments/orders",
      expect.objectContaining({ method: "POST" })
    );
    expect(resp.razorpay_order_id).toBe("order_demo1234");
    expect(resp.transaction_id).toBe(42);
    // key_id must not contain a secret value
    expect(resp.key_id).toBeNull();
  });

  it("amount is in paise (integer)", async () => {
    mockOk({ transaction_id: 1, razorpay_order_id: "o", amount: 15_000, currency: "INR", key_id: null, mode: "local-demo", scenario: "LOW" }, 201);
    const resp = await createPaymentOrder({ amount: 15_000, currency: "INR", scenario: "LOW" });
    expect(resp.amount).toBe(15_000);
    expect(Number.isInteger(resp.amount)).toBe(true);
  });

  it("attaches Authorization header from stored token", async () => {
    mockOk({ transaction_id: 1, razorpay_order_id: "o", amount: 1, currency: "INR", key_id: null, mode: "local-demo", scenario: "LOW" }, 201);
    await createPaymentOrder({ amount: 1, currency: "INR", scenario: "LOW" });
    const call = mockFetch.mock.calls[0];
    const headers = call[1].headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer test-tok");
  });

  it("throws on 422 validation error", async () => {
    mockErr(422, "amount must be > 0");
    await expect(
      createPaymentOrder({ amount: 0, currency: "INR", scenario: "LOW" })
    ).rejects.toMatchObject({ status: 422 });
  });
});

// ── verifyPayment ──────────────────────────────────────────────────────────

describe("verifyPayment()", () => {
  it("POSTs to /api/v1/payments/verify", async () => {
    mockOk({
      verified: true,
      payment: {
        id: 1, transaction_id: 1, razorpay_order_id: "order_x",
        razorpay_payment_id: "pay_abc", amount: 4_850_000, currency: "INR",
        payment_status: "AUTHORIZED", risk_status: "HIGH", decision: "HUMAN_REVIEW",
        scenario: "HIGH", mode: "local-demo",
        created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
      },
      investigation_triggered: true,
    });
    const resp = await verifyPayment({
      razorpay_order_id: "order_x",
      razorpay_payment_id: "pay_abc",
      razorpay_signature: "sig_xyz",
    });
    expect(resp.verified).toBe(true);
    expect(resp.investigation_triggered).toBe(true);
    expect(resp.payment.decision).toBe("HUMAN_REVIEW");
  });

  it("throws ApiClientError on invalid signature (400)", async () => {
    mockErr(400, "Payment signature verification failed.");
    await expect(
      verifyPayment({
        razorpay_order_id: "o",
        razorpay_payment_id: "p",
        razorpay_signature: "bad",
      })
    ).rejects.toMatchObject({ status: 400 });
  });
});

// ── listPayments ───────────────────────────────────────────────────────────

describe("listPayments()", () => {
  it("calls GET /api/v1/payments with limit param", async () => {
    mockOk([]);
    await listPayments(25);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/payments?limit=25",
      expect.any(Object)
    );
  });

  it("returns an array", async () => {
    const items = [
      { id: 1, transaction_id: 1, razorpay_order_id: "o1", razorpay_payment_id: null, amount: 15_000, currency: "INR", payment_status: "CREATED", risk_status: "UNASSESSED", decision: null, scenario: "LOW", mode: "local-demo", created_at: "", updated_at: "" },
    ];
    mockOk(items);
    const result = await listPayments();
    expect(Array.isArray(result)).toBe(true);
    expect(result[0].amount).toBe(15_000);
  });
});

// ── getPaymentForTransaction ───────────────────────────────────────────────

describe("getPaymentForTransaction()", () => {
  it("calls GET /api/v1/payments/transaction/{id}", async () => {
    mockOk({ id: 5, transaction_id: 10, razorpay_order_id: "o", razorpay_payment_id: null, amount: 1, currency: "INR", payment_status: "CREATED", risk_status: "UNASSESSED", decision: null, scenario: null, mode: "local-demo", created_at: "", updated_at: "" });
    await getPaymentForTransaction(10);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/payments/transaction/10",
      expect.any(Object)
    );
  });

  it("throws 404 when no payment for transaction", async () => {
    mockErr(404, "No payment exists for this transaction.");
    await expect(getPaymentForTransaction(99999)).rejects.toMatchObject({ status: 404 });
  });
});
