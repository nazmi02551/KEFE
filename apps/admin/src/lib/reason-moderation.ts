export type ReasonModerationQueueKind = "PENDING" | "REPORTED";
export type ReasonModerationDecision = "ALLOWED" | "BLOCKED";
export type ReasonReportCode =
  | "ABUSE"
  | "PERSONAL_DATA"
  | "MISLEADING"
  | "OTHER";

export interface ReasonModerationItem {
  reason_id: string;
  case_version_id: string;
  tags: string[];
  body: string | null;
  moderation_state: string;
  created_at: string;
  updated_at: string;
  report_count: number;
  report_counts_by_code: Record<string, number>;
  latest_reported_at: string | null;
  candidate_at: string;
}

export interface ReasonModerationQueuePage {
  items: ReasonModerationItem[];
  next_offset: number | null;
}

export interface ReasonModerationFilters {
  kind?: ReasonModerationQueueKind;
  limit?: number;
  offset?: number;
  case_version_id?: string;
  report_code?: ReasonReportCode;
}

export interface ReasonModerationAuditEntry {
  audit_id: string;
  reason_id: string;
  actor_ref: string;
  previous_state: string;
  decided_state: string;
  rationale: string;
  created_at: string;
}

export interface ReasonModerationAuditTrail {
  items: ReasonModerationAuditEntry[];
}

export interface ReasonModerationDecisionRequest {
  state: ReasonModerationDecision;
  rationale: string;
  confirm_reason_id: string;
}

export interface ReasonModerationDecisionResponse {
  reason: ReasonModerationItem;
  audit: ReasonModerationAuditEntry;
}

export function moderationDecisionRequest(input: {
  reasonId: string;
  state: ReasonModerationDecision;
  rationale: string;
}): ReasonModerationDecisionRequest {
  return {
    state: input.state,
    rationale: input.rationale.trim(),
    confirm_reason_id: input.reasonId
  };
}

export function canSubmitModeration(input: {
  reason: ReasonModerationItem | null;
  state: ReasonModerationDecision;
  rationale: string;
  confirmationReasonId: string;
  confirmed: boolean;
  csrfToken: string;
}): boolean {
  const rationaleLength = input.rationale.trim().length;
  return Boolean(
    input.reason &&
      input.state &&
      rationaleLength >= 10 &&
      rationaleLength <= 1000 &&
      input.confirmationReasonId === input.reason.reason_id &&
      input.confirmed &&
      input.csrfToken.trim()
  );
}

export function reportSummary(item: ReasonModerationItem): string[] {
  return Object.entries(item.report_counts_by_code)
    .filter(([, count]) => Number.isInteger(count) && count > 0)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([code, count]) => `${code}: ${count}`);
}

export function boundedReasonText(value: unknown, fallback: string): string {
  if (typeof value !== "string") return fallback;
  const compact = value.replace(/\s+/g, " ").trim();
  return compact.slice(0, 500) || fallback;
}
