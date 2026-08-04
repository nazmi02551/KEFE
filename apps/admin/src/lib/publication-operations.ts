import type { CaseBuilderVersion } from "@/src/lib/contracts";

export type PublicationQueueState = "APPROVED" | "PUBLISHED";
export type PublicationDecision = "PUBLISH" | "WITHDRAW";

export interface PublicationQueueItem {
  version_id: string;
  case_id: string;
  version_no: number;
  state: PublicationQueueState;
  title: string;
  content_risk: string;
  primary_domain_code: string;
  content_locale: string;
  flow_template_code: string;
  flow_template_version_no: number;
  created_at: string;
  published_at: string | null;
}

export interface PublicationQueuePage {
  items: PublicationQueueItem[];
  next_offset: number | null;
}

export interface PublicationFilters {
  state?: PublicationQueueState;
  limit?: number;
  offset?: number;
  content_risk?: string;
  primary_domain_code?: string;
}

export interface PublicationAuditSummary {
  audit_id: string;
  actor_ref: string;
  command: string;
  previous_state: string | null;
  new_state: string;
  rationale: string | null;
  occurred_at: string;
}

export interface PublicationPin {
  content_configuration_id: string | null;
  content_configuration_version_no: number | null;
  flow_template_code: string | null;
  flow_template_version_no: number | null;
  entry_step_code: string | null;
}

export interface PublicationDetail {
  version: CaseBuilderVersion;
  pin: PublicationPin;
  approval: PublicationAuditSummary | null;
  publication: PublicationAuditSummary | null;
}

export interface PublicationValidationFailure {
  code: string;
  detail: string;
  path: string | null;
}

export interface PublicationPreflight {
  version_id: string;
  eligible: boolean;
  validation_failures: PublicationValidationFailure[];
  prospective_content_configuration_id: string | null;
  prospective_content_configuration_version_no: number | null;
  prospective_flow_template_code: string | null;
  prospective_flow_template_version_no: number | null;
  prospective_entry_step_code: string | null;
  advisory_only: true;
}

export interface PublicationDecisionRequest {
  decision: PublicationDecision;
  acknowledge_immutable?: boolean;
  rationale?: string | null;
}

export interface PublicationDecisionResponse {
  decision: PublicationDecision;
  version: CaseBuilderVersion;
  pin: PublicationPin;
}

export interface PublishEligibilityInput {
  detail: PublicationDetail | null;
  preflight: PublicationPreflight | null;
  confirmed: boolean;
  csrfToken: string;
}

export function canPublish({
  detail,
  preflight,
  confirmed,
  csrfToken
}: PublishEligibilityInput): boolean {
  return Boolean(
    detail?.version.state === "APPROVED" &&
      preflight?.version_id === detail.version.id &&
      preflight.eligible &&
      preflight.advisory_only &&
      confirmed &&
      csrfToken.trim()
  );
}

export function canWithdraw(input: {
  detail: PublicationDetail | null;
  rationale: string;
  csrfToken: string;
}): boolean {
  return Boolean(
    input.detail?.version.state === "PUBLISHED" &&
      input.rationale.trim() &&
      input.csrfToken.trim()
  );
}

export function publishRequest(): PublicationDecisionRequest {
  return {
    decision: "PUBLISH",
    acknowledge_immutable: true
  };
}

export function withdrawRequest(rationale: string): PublicationDecisionRequest {
  return {
    decision: "WITHDRAW",
    rationale: rationale.trim()
  };
}

export function preflightFingerprint(preflight: PublicationPreflight): string {
  return [
    preflight.version_id,
    preflight.prospective_content_configuration_id ?? "none",
    String(preflight.prospective_content_configuration_version_no ?? "none"),
    preflight.prospective_flow_template_code ?? "none",
    String(preflight.prospective_flow_template_version_no ?? "none")
  ].join(":");
}
