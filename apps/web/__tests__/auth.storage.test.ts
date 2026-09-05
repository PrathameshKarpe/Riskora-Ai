/**
 * Auth storage tests — sessionStorage persistence.
 */

// Mock sessionStorage
const store: Record<string, string> = {};
const mockSessionStorage = {
  getItem:    jest.fn((k: string) => store[k] ?? null),
  setItem:    jest.fn((k: string, v: string) => { store[k] = v; }),
  removeItem: jest.fn((k: string) => { delete store[k]; }),
};
Object.defineProperty(window, "sessionStorage", {
  value: mockSessionStorage,
  writable: true,
});

import { clearAuth, loadAuth, saveAuth } from "@/lib/auth/storage";

beforeEach(() => {
  Object.keys(store).forEach((k) => delete store[k]);
  jest.clearAllMocks();
});

describe("saveAuth / loadAuth", () => {
  it("saves and loads an AuthUser", () => {
    const user = { email: "admin@riskora.local", role: "ADMIN" as const, access_token: "tok" };
    saveAuth(user);
    const loaded = loadAuth();
    expect(loaded).toEqual(user);
  });

  it("returns null when nothing is stored", () => {
    expect(loadAuth()).toBeNull();
  });
});

describe("clearAuth", () => {
  it("removes the stored user", () => {
    saveAuth({ email: "a@b.com", role: "REVIEWER" as const, access_token: "x" });
    clearAuth();
    expect(loadAuth()).toBeNull();
  });
});
