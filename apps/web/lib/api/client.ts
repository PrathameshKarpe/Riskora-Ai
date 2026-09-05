import type {
  AuditEvent,
  AuthUser,
  DashboardMetrics,
  Investigation,
  LoginRequest,
  LoginResponse,
  Payment,
  PaymentConfig,
  PaymentOrderRequest,
  PaymentOrderResponse,
  PaymentVerifyRequest,
  PaymentVerifyResponse,
  Review,
  ReviewRequest,
  RiskDistribution,
  Transaction,
  TransactionCreate,
} from "@/lib/types";

// The Next.js rewrite proxies /api/* → FastAPI, so we don't expose the
// backend URL to the browser directly.
const BASE = "";

class ApiClientError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // Attach stored JWT if available (client-side only)
  const authToken =
    token ??
    (typeof window !== "undefined"
      ? ((): string | null => {
          try {
            const raw = sessionStorage.getItem("riskora_auth");
            return raw ? JSON.parse(raw).access_token : null;
          } catch {
            return null;
          }
        })()
      : null);

  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }

  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      ...options,
      headers,
      cache: "no-store",
    });
  } catch (err) {
    // Network-level failure (backend down, DNS, CORS block, aborted…)
    throw new ApiClientError(
      0,
      "Cannot reach the Riskora API. Please check that the backend is running.",
      err instanceof Error ? err.message : String(err)
    );
  }

  const rawBody = await readBodyOnce(res);

  if (!res.ok) {
    let detail: unknown = rawBody;
    let message = `HTTP ${res.status}`;

    if (rawBody) {
      try {
        const parsed: unknown = JSON.parse(rawBody);
        if (parsed && typeof parsed === "object") {
          detail = parsed;
          const d = parsed as { detail?: unknown };
          if (d.detail !== undefined) {
            // FastAPI validation errors return detail as an array
            if (Array.isArray(d.detail)) {
              message = d.detail
                .map((e) =>
                  typeof e === "object" && e !== null && "msg" in e
                    ? String((e as { msg: unknown }).msg)
                    : String(e)
                )
                .join("; ");
            } else {
              message = String(d.detail);
            }
          }
        }
      } catch {
        // Plain-text error body — keep it as the message when non-empty
        message = rawBody.slice(0, 300);
      }
    }

    // Friendlier messages for common auth/permission statuses
    if (res.status === 401) {
      message = message.startsWith("HTTP") ? "Authentication required. Please sign in again." : message;
    } else if (res.status === 403) {
      message = message.startsWith("HTTP") ? "You do not have permission to perform this action." : message;
    }

    throw new ApiClientError(res.status, message, detail);
  }

  // 204 No Content or empty body
  if (res.status === 204 || rawBody === "") {
    return undefined as unknown as T;
  }

  try {
    return JSON.parse(rawBody) as T;
  } catch {
    // Successful status but non-JSON body — surface it instead of crashing
    throw new ApiClientError(
      res.status,
      "The API returned a response that is not valid JSON.",
      rawBody.slice(0, 300)
    );
  }
}

// Read the body exactly once. Real Responses expose text(); some test
// mocks only expose json(). Either way the body is consumed a single
// time, which prevents "body stream already read" errors.
async function readBodyOnce(res: Response): Promise<string> {
  try {
    if (typeof res.text === "function") {
      return await res.text();
    }
    const data: unknown = await res.json();
    return typeof data === "string" ? data : JSON.stringify(data);
  } catch {
    return "";
  }
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export async function login(payload: LoginRequest): Promise<AuthUser> {
  const data = await request<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return {
    email: data.email,
    role: data.role,
    access_token: data.access_token,
  };
}

// ── Health ────────────────────────────────────────────────────────────────────

export async function getHealth() {
  return request<{ status: string; service: string }>("/health");
}

export async function getHealthDb() {
  return request<{ status: string; database: string }>("/health/db");
}

// ── Transactions ─────────────────────────────────────────────────────────────

export async function getTransactions(limit = 100): Promise<Transaction[]> {
  return request<Transaction[]>(`/api/v1/transactions?limit=${limit}`);
}

export async function getTransaction(id: number): Promise<Transaction> {
  return request<Transaction>(`/api/v1/transactions/${id}`);
}

export async function createTransaction(
  payload: TransactionCreate
): Promise<Transaction> {
  return request<Transaction>("/api/v1/transactions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ── Investigations ────────────────────────────────────────────────────────────

export async function startInvestigation(
  transactionId: number
): Promise<Investigation> {
  return request<Investigation>(
    `/api/v1/transactions/${transactionId}/investigate`,
    { method: "POST" }
  );
}

export async function getInvestigation(
  investigationId: number
): Promise<Investigation> {
  return request<Investigation>(`/api/v1/investigations/${investigationId}`);
}

export async function getTransactionInvestigation(
  transactionId: number
): Promise<Investigation> {
  return request<Investigation>(
    `/api/v1/transactions/${transactionId}/investigation`
  );
}

// ── Reviews ───────────────────────────────────────────────────────────────────

export async function getReviews(): Promise<Review[]> {
  return request<Review[]>("/api/v1/reviews");
}

export async function getTransactionReviews(
  transactionId: number
): Promise<Review[]> {
  return request<Review[]>(`/api/v1/reviews/${transactionId}`);
}

export async function approveTransaction(
  transactionId: number,
  payload: ReviewRequest
): Promise<Review> {
  return request<Review>(`/api/v1/reviews/${transactionId}/approve`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function blockTransaction(
  transactionId: number,
  payload: ReviewRequest
): Promise<Review> {
  return request<Review>(`/api/v1/reviews/${transactionId}/block`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function holdTransaction(
  transactionId: number,
  payload: ReviewRequest
): Promise<Review> {
  return request<Review>(`/api/v1/reviews/${transactionId}/hold`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ── Audit ─────────────────────────────────────────────────────────────────────

export async function getAuditTrail(
  transactionId: number
): Promise<AuditEvent[]> {
  return request<AuditEvent[]>(`/api/v1/audit/${transactionId}`);
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  return request<DashboardMetrics>("/api/v1/dashboard/metrics");
}

export async function getRiskDistribution(): Promise<RiskDistribution> {
  return request<RiskDistribution>("/api/v1/dashboard/risk-distribution");
}

export async function getRecentTransactions(): Promise<Transaction[]> {
  return request<Transaction[]>("/api/v1/dashboard/recent-transactions");
}

export async function getPendingReviewCount(): Promise<number> {
  return request<number>("/api/v1/dashboard/pending-reviews");
}

export { ApiClientError };

// ── Payments (Phase 6 — Razorpay Test Mode) ───────────────────────────────────
// All payment calls go to the FastAPI backend.
// The Key Secret and Webhook Secret are backend-only and never appear here.

export async function getPaymentConfig(): Promise<PaymentConfig> {
  return request<PaymentConfig>("/api/v1/payments/config");
}

export async function createPaymentOrder(
  payload: PaymentOrderRequest
): Promise<PaymentOrderResponse> {
  return request<PaymentOrderResponse>("/api/v1/payments/orders", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function verifyPayment(
  payload: PaymentVerifyRequest
): Promise<PaymentVerifyResponse> {
  return request<PaymentVerifyResponse>("/api/v1/payments/verify", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listPayments(limit = 100): Promise<Payment[]> {
  return request<Payment[]>(`/api/v1/payments?limit=${limit}`);
}

export async function getPaymentForTransaction(
  transactionId: number
): Promise<Payment> {
  return request<Payment>(`/api/v1/payments/transaction/${transactionId}`);
}
