/**
 * API client unit tests — mock fetch, verify request construction.
 */

// Mock global fetch before any imports
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock sessionStorage
Object.defineProperty(window, "sessionStorage", {
  value: {
    getItem: jest.fn(() => null),
    setItem: jest.fn(),
    removeItem: jest.fn(),
  },
  writable: true,
});

import {
  getDashboardMetrics,
  getTransaction,
  getTransactions,
  login,
  startInvestigation,
} from "@/lib/api/client";

function mockOk(data: unknown) {
  mockFetch.mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () => Promise.resolve(data),
  } as Response);
}

function mockError(status: number, detail: string) {
  mockFetch.mockResolvedValueOnce({
    ok: false,
    status,
    json: () => Promise.resolve({ detail }),
  } as Response);
}

beforeEach(() => {
  mockFetch.mockClear();
});

describe("login()", () => {
  it("posts to /api/v1/auth/login and returns AuthUser", async () => {
    mockOk({ access_token: "tok123", token_type: "bearer", email: "admin@riskora.local", role: "ADMIN" });
    const user = await login({ email: "admin@riskora.local" });
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/auth/login",
      expect.objectContaining({ method: "POST" })
    );
    expect(user.email).toBe("admin@riskora.local");
    expect(user.role).toBe("ADMIN");
    expect(user.access_token).toBe("tok123");
  });

  it("throws ApiClientError on 401", async () => {
    mockError(401, "Invalid credentials");
    await expect(login({ email: "bad@example.com" })).rejects.toMatchObject({
      status: 401,
    });
  });
});

describe("getTransactions()", () => {
  it("fetches /api/v1/transactions with limit param", async () => {
    mockOk([]);
    await getTransactions(50);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/transactions?limit=50",
      expect.any(Object)
    );
  });

  it("returns an array", async () => {
    const txList = [{ id: 1, external_id: "TX-001" }];
    mockOk(txList);
    const result = await getTransactions();
    expect(Array.isArray(result)).toBe(true);
    expect(result[0].id).toBe(1);
  });
});

describe("getTransaction()", () => {
  it("fetches /api/v1/transactions/{id}", async () => {
    mockOk({ id: 42, external_id: "TX-042" });
    await getTransaction(42);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/transactions/42",
      expect.any(Object)
    );
  });
});

describe("getDashboardMetrics()", () => {
  it("fetches /api/v1/dashboard/metrics", async () => {
    mockOk({ total_transactions: 10, suspicious_transactions: 3, pending_reviews: 1 });
    const m = await getDashboardMetrics();
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/dashboard/metrics",
      expect.any(Object)
    );
    expect(m.total_transactions).toBe(10);
  });
});

describe("startInvestigation()", () => {
  it("posts to /api/v1/transactions/{id}/investigate", async () => {
    mockOk({ investigation_id: 1, status: "COMPLETED" });
    await startInvestigation(5);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/v1/transactions/5/investigate",
      expect.objectContaining({ method: "POST" })
    );
  });
});

describe("ApiClientError handling", () => {
  it("extracts detail message from JSON error response", async () => {
    mockError(404, "Transaction does not exist.");
    try {
      await getTransaction(9999);
      fail("Should have thrown");
    } catch (err: unknown) {
      const e = err as { status: number; message: string };
      expect(e.status).toBe(404);
      expect(e.message).toContain("Transaction does not exist");
    }
  });
});
