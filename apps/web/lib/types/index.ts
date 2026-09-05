// ── Auth ─────────────────────────────────────────────────────────────────────

export type Role = "ADMIN" | "RISK_ANALYST" | "REVIEWER";

export interface AuthUser {
  email: string;
  role: Role;
  access_token: string;
}

export interface LoginRequest {
  email: string;
  role?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  email: string;
  role: Role;
}

// ── Transactions ─────────────────────────────────────────────────────────────

export type TransactionStatus =
  | "RECEIVED"
  | "INVESTIGATING"
  | "PENDING_REVIEW"
  | "APPROVE"
  | "BLOCK"
  | "HOLD"
  | "INVESTIGATION_FAILED";

export interface Transaction {
  id: number;
  external_id: string;
  amount: number;
  currency: string;
  merchant: string;
  payment_method: string;
  device_id: string | null;
  location: string | null;
  status: TransactionStatus;
  risk_context: Record<string, unknown>;
  created_at: string;
  user_id?: number | null;
}

export interface TransactionCreate {
  external_id: string;
  amount: number;
  currency: string;
  merchant: string;
  payment_method: string;
  device_id?: string;
  location?: string;
  risk_context?: Record<string, unknown>;
}

// ── Investigations ────────────────────────────────────────────────────────────

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface RiskInfo {
  model_version: string;
  ml_score: number;
  final_score: number;
  risk_level: RiskLevel;
  behavioral_risk: string;
}

export interface BehavioralSignal {
  signal: string;
  severity: string;
  explanation: string;
  value?: number | string | null;
  source?: string;
}

export interface AgentFinding {
  agent_name: string;
  status: string;
  finding: Record<string, unknown>;
  confidence: number | null;
}

export interface Evidence {
  source: string;
  section: string;
  content: string;
  relevance_score: number;
  metadata: Record<string, unknown>;
}

export interface Decision {
  recommendation: string;
  policy_action: string;
  requires_human_review: boolean;
  reason_codes: string[];
  explanation: string;
}

export interface Investigation {
  investigation_id: number;
  transaction_id: number;
  status: "RUNNING" | "COMPLETED" | "FAILED";
  summary: string | null;
  confidence: number | null;
  started_at: string;
  completed_at: string | null;
  risk: RiskInfo | null;
  behavioral_signals: BehavioralSignal[];
  agents: AgentFinding[];
  evidence: Evidence[];
  decision: Decision | null;
}

// ── Reviews ───────────────────────────────────────────────────────────────────

export type ReviewDecision = "APPROVE" | "BLOCK" | "HOLD";

export interface Review {
  id: number;
  transaction_id: number;
  decision: ReviewDecision;
  reason: string;
  reviewer_id: number | null;
  created_at: string;
}

export interface ReviewRequest {
  reason: string;
}

// ── Audit ─────────────────────────────────────────────────────────────────────

export interface AuditEvent {
  id: number;
  transaction_id: number;
  event_type: string;
  actor: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export interface DashboardMetrics {
  total_transactions: number;
  suspicious_transactions: number;
  blocked_transactions: number;
  approved_transactions: number;
  pending_reviews: number;
  fraud_detection_rate: number | null;
  false_positive_rate: number | null;
  estimated_prevented_loss: number | null;
}

export type RiskDistribution = Record<RiskLevel, number>;

// ── API Errors ────────────────────────────────────────────────────────────────

export interface ApiError {
  status: number;
  message: string;
  detail?: unknown;
}

// ── Payments (Phase 6 — Razorpay Test Mode) ───────────────────────────────────

/** Synthetic demo scenario that seeds the ML risk context. */
export type PaymentScenario = "LOW" | "HIGH" | "CRITICAL";

/** Integration mode returned by the backend. */
export type PaymentMode = "razorpay-test" | "local-demo";

/**
 * Payment lifecycle:  CREATED → AUTHORIZED → CAPTURED | FAILED
 * Risk lifecycle:     UNASSESSED → LOW | MEDIUM | HIGH | CRITICAL
 * Decision lifecycle: null → APPROVE | REVIEW | HOLD | BLOCK
 *
 * These are intentionally separate state machines (Phase 6 Step 14).
 * A payment can be AUTHORIZED with HIGH risk and a HUMAN_REVIEW decision
 * without any state overwriting another.
 */
export interface Payment {
  id: number;
  transaction_id: number;
  razorpay_order_id: string;
  razorpay_payment_id: string | null;
  /** Amount in smallest currency unit (paise for INR). */
  amount: number;
  currency: string;
  payment_status: "CREATED" | "AUTHORIZED" | "CAPTURED" | "FAILED";
  risk_status: "UNASSESSED" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  decision: "APPROVE" | "REVIEW" | "HUMAN_REVIEW" | "HOLD" | "BLOCK" | null;
  scenario: PaymentScenario | null;
  mode: PaymentMode;
  created_at: string;
  updated_at: string;
}

export interface PaymentOrderRequest {
  /** Amount in paise (INR smallest unit). */
  amount: number;
  currency: string;
  scenario: PaymentScenario;
}

export interface PaymentOrderResponse {
  transaction_id: number;
  razorpay_order_id: string;
  amount: number;
  currency: string;
  /** Public Razorpay Key ID. Only present in razorpay-test mode. */
  key_id: string | null;
  mode: PaymentMode;
  scenario: PaymentScenario | null;
}

export interface PaymentVerifyRequest {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

export interface PaymentVerifyResponse {
  verified: boolean;
  payment: Payment;
  investigation_triggered: boolean;
}

export interface PaymentConfig {
  mode: PaymentMode;
  /** Only exposed in razorpay-test mode. Never contains the Key Secret. */
  key_id: string | null;
  webhook_configured: boolean;
}
