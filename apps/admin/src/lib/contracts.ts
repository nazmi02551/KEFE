export type ProposalReviewState =
  | "PENDING"
  | "ACCEPTED"
  | "REJECTED"
  | "CHANGES_REQUESTED";

export type ProposalReviewDecision = Exclude<ProposalReviewState, "PENDING">;

export interface AdminSession {
  admin_subject_id: string;
  session_id: string;
  roles: string[];
  direct_capabilities: string[];
  authenticated_at: string;
  mfa_satisfied_at: string | null;
  step_up_at: string | null;
  expires_at: string;
}

export interface ProposalReviewSummary {
  proposal_review_decision_id: string;
  decision: ProposalReviewDecision;
  reviewer_ref: string;
  decided_at: string;
  rationale: string | null;
  reason_code: string | null;
  policy_version: string | null;
  risk_policy_version: string | null;
}

export interface ProposalQueueItem {
  proposal_id: string;
  proposal_kind: string;
  payload_schema_ref: string;
  payload_schema_version: string;
  payload_hash: string;
  run_id: string;
  stage_execution_id: string;
  input_artifact_kind: string;
  input_artifact_id: string;
  pipeline_code: string;
  pipeline_version: string;
  locale: string | null;
  jurisdiction_code: string | null;
  proposal_taxonomy_version: string | null;
  proposal_configuration_version: string | null;
  proposal_methodology_version: string | null;
  run_taxonomy_version: string | null;
  run_methodology_version: string | null;
  confidence: number | null;
  risk_code: string | null;
  ai_execution_ref: string | null;
  provenance_ref: string | null;
  supersedes_proposal_id: string | null;
  created_at: string;
  review_state: ProposalReviewState;
  review: ProposalReviewSummary | null;
}

export interface ProposalDetail extends ProposalQueueItem {
  payload: Record<string, unknown>;
}

export interface ProposalQueuePage {
  items: ProposalQueueItem[];
  next_cursor: string | null;
}

export interface ProposalFilters {
  limit?: number;
  cursor?: string;
  review_state?: ProposalReviewState;
  proposal_kind?: string;
  risk_code?: string;
  run_id?: string;
  pipeline_code?: string;
}

export interface ProposalReviewRequest {
  decision: ProposalReviewDecision;
  rationale?: string;
  reason_code?: string;
  policy_version?: string;
  risk_policy_version?: string;
}

export interface ProposalReviewResponse extends ProposalReviewSummary {
  proposal_id: string;
}

export interface CandidateBundleRequest {
  source_brief_review_decision_id: string;
  slug: string;
  title: string;
  summary: string;
  base_format_code: string;
  primary_domain_code: string;
  content_risk: string;
  issue_code: string;
  issue_title: string;
  question_stable_code: string;
  question_prompt: string;
  response_options: string[];
  flow_template_code: string;
  flow_template_version_no: number;
  content_locale: string;
  market_scope: string;
  country_codes: string[];
  required_review_modes: string[];
  is_fact_bearing: boolean;
  is_real_event: boolean;
  context_title: string;
  cultural_context_note?: string | null;
  legal_context_note?: string | null;
}

export interface CandidateBundleResponse {
  candidate_seed_artifact_id: string;
  run_id: string;
  decision_problem_proposal_id: string;
  question_draft_proposal_id: string;
  candidate_case_proposal_id: string;
  run_state: string;
  proposal_review_state: "PENDING";
}

export interface EditorialProjectionRequest {
  proposal_review_decision_id: string;
  profile_code: string;
  profile_version: number;
  idempotency_key: string;
  explicit_flow_template_code?: string | null;
  explicit_flow_template_version?: number | null;
}

export interface EditorialProjectionResponse {
  projection_record_id: string;
  candidate_proposal_id: string;
  proposal_review_decision_id: string;
  profile_code: string;
  profile_version: number;
  authoring_case_id: string;
  authoring_case_version_id: string;
  lifecycle_state: "DRAFT";
  replayed: boolean;
  created_at: string;
}
