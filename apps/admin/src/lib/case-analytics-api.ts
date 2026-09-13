/**
 * Admin Studio — Case Deliberation Analytics API Client
 *
 * Implements typed API clients for deliberation analytics endpoints mounted in
 * case_analytics_router.py:
 * - Quality Checklist (CAP-075)
 * - Consensus / Divergence Classification (CAP-039)
 * - Expert-Public Epistemic Gap Analysis (CAP-041)
 * - Incentive Map Analysis (CAP-022)
 * - Normative Philosophical Models (CAP-019)
 * - Perspective Clusters (CAP-033)
 * - Policy Simulations & Parameter Tuning (CAP-017)
 * - Process Analysis (CAP-021)
 * - Responsibility & Accountability Matrix (CAP-020)
 * - Privacy-Safe Segment Distributions (CAP-036)
 * - Stakeholder Distributions (CAP-037)
 *
 * Invariants:
 * - Read-only analytical introspection; no user profile mutations or scoring.
 * - Minimum k-anonymity (n >= 30) for demographic distributions.
 * - Strict base URL validation preventing credential leakage.
 */

import { AdminApiError } from "@/src/lib/admin-api";

export interface QualityChecklistCriterion {
  code: string;
  name: string;
  is_met: boolean;
  score: number;
  threshold: number;
  details: string;
}

export interface QualityChecklistReport {
  case_version_id: string;
  overall_status: "PASSED" | "PROVISIONAL" | "FAILED";
  overall_score: number;
  criteria: QualityChecklistCriterion[];
  evaluated_at: string;
}

export interface ConsensusDivergenceReport {
  case_version_id: string;
  classification: "BROAD_CONSENSUS" | "BIPOLAR_DIVERGENCE" | "FRAGMENTED_PLURALITY" | "LEANING_MAJORITY";
  leading_share: number;
  margin_of_divergence: number;
  label_tr: string;
  label_en: string;
  description_tr: string;
  description_en: string;
}

export interface ExpertPublicGapReport {
  case_version_id: string;
  gap_classification: "CONVERGENT" | "TECHNICAL_TRANSLATION_GAP" | "NORMATIVE_VALUE_DIVERGENCE" | "TRUST_DEFICIT_SKEPTICISM";
  gap_score: number;
  expert_consensus_share: number;
  public_consensus_share: number;
  friction_points: string[];
  divergence_drivers: string[];
}

export interface IncentiveMapItem {
  actor_group?: string;
  stakeholder_group?: string;
  core_incentive?: string;
  incentive_type?: string;
  alignment_status?: string;
  intensity_score?: number;
  unintended_behavior?: string;
  perverse_incentive_risk?: string;
  rent_seeking_score?: number;
  mitigation_lever?: string;
}

export interface IncentiveMapReport {
  case_version_id: string;
  map_id?: string;
  alignment_index?: number;
  perverse_incentive_risk?: string;
  primary_driver?: string;
  mitigation_mechanism?: string;
  incentives?: IncentiveMapItem[];
  incentive_nodes?: IncentiveMapItem[];
}

export interface NormativeEvaluation {
  option_code: string;
  dominant_philosophy: "UTILITARIAN_MAX_WELFARE" | "DEONTOLOGICAL_CATEGORICAL_RIGHTS" | "RAWLSIAN_MAXIMIN_EQUITY" | "VIRTUE_ETHICS_CHARACTER";
  utilitarian_score: number;
  deontological_score: number;
  rawlsian_score: number;
  virtue_score: number;
}

export interface NormativeModelsReport {
  case_version_id: string;
  evaluations: NormativeEvaluation[];
  philosophies_explained_tr: Record<string, string>;
  philosophies_explained_en: Record<string, string>;
}

export interface PerspectiveClusterItem {
  cluster_id: string;
  case_version_id: string;
  archetype: "NEAR_CONSENSUS" | "OPPOSING_PRINCIPLE" | "BRIDGE_SYNTHESIS";
  core_thesis: string;
  argument_count: number;
  support_percentage: number;
}

export interface PerspectiveClustersReport {
  case_version_id: string;
  total_arguments_clustered: number;
  clusters: PerspectiveClusterItem[];
}

export interface PolicySimulationResult {
  simulation_id: string;
  case_version_id: string;
  policy_knob_name: string;
  knob_value: number;
  fiscal_score: number;
  social_score: number;
  environmental_score: number;
  equilibrium_state: string;
}

export interface ProcessStageItem {
  stage_key: string;
  stage_title: string;
  is_completed: boolean;
  duration_days: number;
  has_public_input: boolean;
  notes?: string;
}

export interface ProcessAnalysisReport {
  case_version_id: string;
  analysis_id?: string;
  current_stage?: string;
  procedural_integrity_score?: number;
  transparency_level?: string;
  public_participation_status?: string;
  oversight_body?: string;
  procedural_bottleneck?: string | null;
  stages?: ProcessStageItem[];
  procedural_fairness_score?: number;
  stakeholder_inclusion_score?: number;
  institutional_transparency_score?: number;
  deliberation_verdict?: string;
}

export interface ActorResponsibilityItem {
  actor_key: string;
  actor_name: string;
  responsibility_share: number;
  duty_nature: string;
  jurisdiction_scope: string;
  accountability_mechanism?: string;
}

export interface ResponsibilityAnalysisReport {
  case_version_id: string;
  analysis_id?: string;
  clarity_score?: number;
  has_accountability_gap?: boolean;
  legal_redress_channel?: string;
  gap_explanation?: string | null;
  actor_allocations?: ActorResponsibilityItem[];
  duty_bearers?: Array<{
    institution: string;
    accountability_tier: string;
    statutory_mandate: string;
  }>;
}

export interface SegmentDistributionCohort {
  cohort_name?: string;
  cohort_label?: string;
  cohort_type?: string;
  sample_count?: number;
  sample_size?: number;
  choice_distribution?: Record<string, number>;
  option_shares?: Record<string, number>;
  primary_choice?: string | null;
  is_suppressed: boolean;
  suppression_reason?: string | null;
  entropy_score?: number;
}

export interface SegmentDistributionReport {
  case_version_id: string;
  k_anonymity_floor?: number;
  minimum_sample_threshold?: number;
  overall_sample_size?: number;
  cohorts?: SegmentDistributionCohort[];
  segments?: SegmentDistributionCohort[];
  privacy_guarantees?: {
    k_anonymity_threshold: number;
    no_individual_profiling: boolean;
    differential_privacy_noise_applied: boolean;
  };
}

export interface StakeholderDistributionGroup {
  role?: "DIRECTLY_IMPACTED" | "FRONTLINE_PRACTITIONERS" | "COMMERCIAL_ENTERPRISES" | "REGULATORY_OVERSIGHT" | "CIVIC_COMMUNITY" | string;
  category?: string;
  name?: string;
  representation_percentage?: number;
  participant_count?: number;
  sample_share?: number;
  cohesion_score?: number;
  cohesion_index?: number;
  dominant_preference?: string;
  primary_choice?: string;
  option_shares?: Record<string, number>;
  divergence_from_overall_points?: number;
}

export interface StakeholderDistributionReport {
  case_version_id: string;
  total_stakeholders_represented?: number;
  active_categories_count?: number;
  pluralism_score?: number;
  stakeholder_groups?: StakeholderDistributionGroup[];
  stakeholder_distributions?: StakeholderDistributionGroup[];
}

export interface BudgetTradeoffReport {
  tradeoff_id: string;
  case_version_id: string;
  healthcare_pct: number;
  education_pct: number;
  infrastructure_pct: number;
  green_transition_pct: number;
  unallocated_pct: number;
  tradeoff_profile: "HEALTH_EDUCATION_PRIORITY" | "INFRASTRUCTURE_GROWTH" | "ECOLOGICAL_TRANSITION" | "BALANCED_ALLOCATION";
}

export interface HistoricalRetrospectiveReport {
  retrospective_id: string;
  case_version_id: string;
  historical_era: "ANCIENT_CLASSICAL" | "INDUSTRIAL_ERA" | "TWENTIETH_CENTURY" | "CONTEMPORARY_CRISIS";
  historical_year: number;
  historical_event_name: string;
  actual_historical_decision: string;
  historical_consequence_summary: string;
}

export interface ObserveModeSessionReport {
  session_id: string;
  case_version_id: string;
  exploration_mode: "OBSERVE_ONLY" | "STUDY_AND_LEARN" | "TRANSITION_TO_WEIGH";
  is_binding_vote: boolean;
  viewed_argument_count: number;
  viewed_evidence_count: number;
}

export interface CommunityProposalItem {
  proposal_id: string;
  proposed_title: string;
  proposed_context: string;
  curation_state: "DRAFT_SUBMITTED" | "COMMUNITY_PEER_REVIEW" | "EDITORIAL_APPROVED" | "REJECTED_WITH_REASON";
  neutrality_score: number;
  supporter_count: number;
}

export interface BlindVariantsReport {
  case_version_id: string;
  blind_mode: "ACTOR_BLIND" | "OUTCOME_BLIND" | "IDENTITY_BLIND";
  blinded_prompt: string;
  real_identity_revealed: string;
  neutrality_score: number;
  capability_id: string;
}

export interface PrincipleFirstReport {
  case_version_id: string;
  primary_principle: "COLLECTIVE_WELLBEING" | "PROCEDURAL_JUSTICE" | "INDIVIDUAL_LIBERTY" | "EGALITARIAN_FAIRNESS";
  secondary_principle: "COLLECTIVE_WELLBEING" | "PROCEDURAL_JUSTICE" | "INDIVIDUAL_LIBERTY" | "EGALITARIAN_FAIRNESS";
  consistency_score: number;
  reflection_prompt: string;
  capability_id: string;
}

export interface DecisionReceiptReport {
  receipt_id: string;
  case_version_id: string;
  committed_choice: string;
  integrity_digest: string;
  timestamp_utc: string;
  capability_id: string;
}

export interface OutcomeTriangleReport {
  case_version_id: string;
  option_code: string;
  rules_weight: number;
  empathy_weight: number;
  utility_weight: number;
  dominant_archetype: "RULES_FIRST" | "EMPATHY_FIRST" | "UTILITY_FIRST" | "BALANCED_TRIAD";
  capability_id: string;
}

export interface InsufficientInfoBreakdownItem {
  code: string;
  count: number;
  percentage: number;
  description_tr: string;
}

export interface InsufficientInfoReport {
  case_version_id: string;
  contract_id: string;
  capabilities: string[];
  total_opt_outs: number;
  breakdown: InsufficientInfoBreakdownItem[];
  preserves_commit_first_isolation: boolean;
}

export interface RoleFlipReport {
  case_version_id: string;
  initial_role: string;
  flipped_role: string;
  flipped_scenario_prompt: string;
  perspective_shift_score: number;
  capability_id: string;
}

export interface CounterfactualConditionItem {
  condition_type: string;
  description: string;
}

export interface ChangeMindInquiryReport {
  case_version_id: string;
  flexibility_class: "HIGHLY_EPISTEMIC_OPEN" | "CONDITIONALLY_OPEN" | "CATEGORICAL_ABSOLUTE";
  selected_conditions: CounterfactualConditionItem[];
  capability_id: string;
}

export interface BridgeArgumentReportItem {
  bridge_id: string;
  case_version_id: string;
  synthesis_thesis: string;
  connecting_values: string[];
  cross_group_support_rate: number;
  sample_size: number;
  capability_id: string;
}

export interface StakeholderGapReport {
  case_version_id: string;
  segment_key: string;
  target_option: string;
  gap_points: number;
  sample_size: number;
  segment_distributions: Record<string, number>;
  k_anonymity_satisfied: boolean;
  capability_id: string;
}

export interface DivergenceDriverItem {
  driver_type: string;
  share_percentage: number;
  explanation: string;
}

export interface DivergenceAnatomyReport {
  case_version_id: string;
  primary_driver: string;
  drivers: DivergenceDriverItem[];
  capability_id: string;
}

// CAP-018: Threshold Sensitivity Analysis
export interface SensitivityCurvePoint {
  parameter_value: number;
  acceptance_rate: number;
}

export interface ThresholdAnalysisReport {
  case_version_id: string;
  parameter_name: string;
  unit: string;
  tipping_point_threshold: number;
  curve_points: SensitivityCurvePoint[];
}

// CAP-023: Stakeholder Impact Matrix
export interface StakeholderImpactItem {
  stakeholder_group: string;
  impact_type: string;
  impact_score: number;
  description: string;
}

export interface StakeholderImpactReport {
  case_version_id: string;
  option_code: string;
  net_equity_score: number;
  impact_items: StakeholderImpactItem[];
}

// CAP-013: Blind Temporal Retest / Temporal Drift
export interface TemporalDriftReport {
  case_version_id: string;
  initial_option_code: string;
  retest_option_code: string;
  time_elapsed_days: number;
  is_shifted: boolean;
  confidence_delta: number;
  drift_nature: "STABLE_CONVICTION" | "MATURED_REVISION" | "EXPLORATORY_SHIFT" | "REINFORCED_CERTAINTY";
  capability_id: string;
}

// CAP-014: Decision Fatigue / Healthy Pacing Guard
export interface DecisionFatigueReport {
  session_id: string;
  consecutive_weigh_count: number;
  session_duration_minutes: number;
  pacing_status: "OPTIMAL_PACING" | "PACING_RECOMMENDED" | "REST_INTERVAL_ACTIVE";
  gentle_recommendation_prompt: string;
  capability_id: string;
}

export class CaseAnalyticsApiClient {
  private readonly baseUrl: string;

  public constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000") {
    const trimmed = baseUrl.trim().replace(/\/+$/, "");
    if (!trimmed.startsWith("http://localhost") && !trimmed.startsWith("http://127.0.0.1") && !trimmed.startsWith("https://")) {
      throw new AdminApiError("INVALID_BASE_URL", "Insecure or invalid API base URL", 400);
    }
    this.baseUrl = trimmed;
  }

  private async getJson<T>(path: string): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const res = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new AdminApiError("GET_FAILED", `GET ${path} failed (${res.status}): ${text}`, res.status);
    }

    return (await res.json()) as T;
  }

  private async postJson<T>(path: string, body: unknown): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new AdminApiError("POST_FAILED", `POST ${path} failed (${res.status}): ${text}`, res.status);
    }

    return (await res.json()) as T;
  }

  public async getQualityChecklist(caseVersionId: string): Promise<QualityChecklistReport> {
    return this.getJson<QualityChecklistReport>(`/v1/cases/${caseVersionId}/quality-checklist`);
  }

  public async getConsensusDivergence(caseVersionId: string, distributionJson?: string): Promise<ConsensusDivergenceReport> {
    const query = distributionJson ? `?distribution_json=${encodeURIComponent(distributionJson)}` : "";
    return this.getJson<ConsensusDivergenceReport>(`/v1/cases/${caseVersionId}/consensus-divergence${query}`);
  }

  public async getExpertPublicGap(caseVersionId: string): Promise<ExpertPublicGapReport> {
    return this.getJson<ExpertPublicGapReport>(`/v1/cases/${caseVersionId}/expert-public-gap`);
  }

  public async getIncentiveMap(caseVersionId: string): Promise<IncentiveMapReport> {
    return this.getJson<IncentiveMapReport>(`/v1/cases/${caseVersionId}/incentive-map`);
  }

  public async getNormativeModels(caseVersionId: string): Promise<NormativeModelsReport> {
    return this.getJson<NormativeModelsReport>(`/v1/cases/${caseVersionId}/normative-models`);
  }

  public async getPerspectiveClusters(caseVersionId: string): Promise<PerspectiveClustersReport> {
    return this.getJson<PerspectiveClustersReport>(`/v1/cases/${caseVersionId}/perspective-clusters`);
  }

  public async getDefaultPolicySimulation(caseVersionId: string): Promise<PolicySimulationResult> {
    return this.getJson<PolicySimulationResult>(`/v1/cases/${caseVersionId}/policy-simulations`);
  }

  public async evaluatePolicySimulation(
    caseVersionId: string,
    policyKnobName: string,
    knobValue: number
  ): Promise<PolicySimulationResult> {
    if (knobValue < 0 || knobValue > 100) {
      throw new AdminApiError("INVALID_KNOB_VALUE", "knobValue must be between 0.0 and 100.0", 400);
    }
    if (policyKnobName.trim().length < 3) {
      throw new AdminApiError("INVALID_KNOB_NAME", "policyKnobName must have at least 3 characters", 400);
    }
    return this.postJson<PolicySimulationResult>(`/v1/cases/${caseVersionId}/policy-simulations/evaluate`, {
      policy_knob_name: policyKnobName.trim(),
      knob_value: knobValue,
    });
  }

  public async getProcessAnalysis(caseVersionId: string): Promise<ProcessAnalysisReport> {
    return this.getJson<ProcessAnalysisReport>(`/v1/cases/${caseVersionId}/process-analysis`);
  }

  public async getResponsibilityAnalysis(caseVersionId: string): Promise<ResponsibilityAnalysisReport> {
    return this.getJson<ResponsibilityAnalysisReport>(`/v1/cases/${caseVersionId}/responsibility-analysis`);
  }

  public async getSegmentDistributions(caseVersionId: string): Promise<SegmentDistributionReport> {
    return this.getJson<SegmentDistributionReport>(`/v1/cases/${caseVersionId}/segment-distributions`);
  }

  public async getStakeholderDistributions(caseVersionId: string): Promise<StakeholderDistributionReport> {
    return this.getJson<StakeholderDistributionReport>(`/v1/cases/${caseVersionId}/stakeholder-distributions`);
  }

  public async getBudgetTradeoff(caseVersionId: string): Promise<BudgetTradeoffReport> {
    return this.getJson<BudgetTradeoffReport>(`/v1/cases/${caseVersionId}/budget-tradeoff`);
  }

  public async evaluateBudgetTradeoff(
    caseVersionId: string,
    allocation: {
      healthcare_pct: number;
      education_pct: number;
      infrastructure_pct: number;
      green_transition_pct: number;
    }
  ): Promise<BudgetTradeoffReport> {
    const total =
      allocation.healthcare_pct +
      allocation.education_pct +
      allocation.infrastructure_pct +
      allocation.green_transition_pct;
    if (total > 100) {
      throw new AdminApiError(
        "INVALID_ALLOCATION",
        `Total budget allocation cannot exceed 100%, got ${total}%`,
        400
      );
    }
    return this.postJson<BudgetTradeoffReport>(
      `/v1/cases/${caseVersionId}/budget-tradeoff/evaluate`,
      allocation
    );
  }

  public async getHistoricalRetrospective(caseVersionId: string): Promise<HistoricalRetrospectiveReport> {
    return this.getJson<HistoricalRetrospectiveReport>(`/v1/cases/${caseVersionId}/historical-retrospective`);
  }

  public async createObserveSession(
    caseVersionId: string,
    explorationMode: string = "OBSERVE_ONLY"
  ): Promise<ObserveModeSessionReport> {
    return this.postJson<ObserveModeSessionReport>(`/v1/cases/${caseVersionId}/observe-session`, {
      exploration_mode: explorationMode,
    });
  }

  public async listCommunityProposals(caseVersionId: string): Promise<CommunityProposalItem[]> {
    return this.getJson<CommunityProposalItem[]>(`/v1/cases/${caseVersionId}/community-proposals`);
  }

  public async createCommunityProposal(
    caseVersionId: string,
    title: string,
    context: string
  ): Promise<CommunityProposalItem> {
    if (title.trim().length < 5) {
      throw new AdminApiError("INVALID_TITLE", "Title must have at least 5 characters", 400);
    }
    if (context.trim().length < 10) {
      throw new AdminApiError("INVALID_CONTEXT", "Context must have at least 10 characters", 400);
    }
    return this.postJson<CommunityProposalItem>(`/v1/cases/${caseVersionId}/community-proposals`, {
      proposed_title: title.trim(),
      proposed_context: context.trim(),
    });
  }

  public async getBlindVariants(caseVersionId: string): Promise<BlindVariantsReport> {
    return this.getJson<BlindVariantsReport>(`/v1/cases/${caseVersionId}/blind-variants`);
  }

  public async getPrincipleFirst(caseVersionId: string): Promise<PrincipleFirstReport> {
    return this.getJson<PrincipleFirstReport>(`/v1/cases/${caseVersionId}/principle-first`);
  }

  public async getDecisionReceipt(caseVersionId: string): Promise<DecisionReceiptReport> {
    return this.getJson<DecisionReceiptReport>(`/v1/cases/${caseVersionId}/decision-receipt`);
  }

  public async getOutcomeTriangle(caseVersionId: string): Promise<OutcomeTriangleReport> {
    return this.getJson<OutcomeTriangleReport>(`/v1/cases/${caseVersionId}/outcome-triangle`);
  }

  public async getInsufficientInfoReport(caseVersionId: string): Promise<InsufficientInfoReport> {
    return this.getJson<InsufficientInfoReport>(`/v1/cases/${caseVersionId}/insufficient-info-report`);
  }

  public async getRoleFlip(caseVersionId: string): Promise<RoleFlipReport> {
    return this.getJson<RoleFlipReport>(`/v1/cases/${caseVersionId}/role-flip`);
  }

  public async getChangeMindInquiry(caseVersionId: string): Promise<ChangeMindInquiryReport> {
    return this.getJson<ChangeMindInquiryReport>(`/v1/cases/${caseVersionId}/change-mind-inquiry`);
  }

  public async getBridgeArguments(caseVersionId: string): Promise<BridgeArgumentReportItem[]> {
    return this.getJson<BridgeArgumentReportItem[]>(`/v1/cases/${caseVersionId}/bridge-arguments`);
  }

  public async getStakeholderGap(
    caseVersionId: string,
    segmentKey: string = "DIRECTLY_AFFECTED",
    targetOption: string = "A"
  ): Promise<StakeholderGapReport> {
    return this.getJson<StakeholderGapReport>(
      `/v1/cases/${caseVersionId}/stakeholder-gap?segment_key=${encodeURIComponent(segmentKey)}&target_option=${encodeURIComponent(targetOption)}`
    );
  }

  public async getDivergenceAnatomy(caseVersionId: string): Promise<DivergenceAnatomyReport> {
    return this.getJson<DivergenceAnatomyReport>(`/v1/cases/${caseVersionId}/divergence-anatomy`);
  }

  public async getThresholdAnalysis(caseVersionId: string): Promise<ThresholdAnalysisReport> {
    return this.getJson<ThresholdAnalysisReport>(`/v1/cases/${caseVersionId}/threshold-analysis`);
  }

  public async getStakeholderImpact(caseVersionId: string, optionCode: string = "A"): Promise<StakeholderImpactReport> {
    return this.getJson<StakeholderImpactReport>(
      `/v1/cases/${caseVersionId}/stakeholder-impact?option_code=${encodeURIComponent(optionCode)}`
    );
  }

  public async getTemporalDrift(caseVersionId: string): Promise<TemporalDriftReport> {
    return this.getJson<TemporalDriftReport>(`/v1/cases/${caseVersionId}/temporal-drift`);
  }

  public async getFatigueGuardStatus(
    sessionId: string = "SESSION-DEFAULT",
    consecutiveWeighCount: number = 6,
    sessionDurationMinutes: number = 24.5
  ): Promise<DecisionFatigueReport> {
    return this.getJson<DecisionFatigueReport>(
      `/v1/cases/fatigue-guard/status?session_id=${encodeURIComponent(sessionId)}&consecutive_weigh_count=${consecutiveWeighCount}&session_duration_minutes=${sessionDurationMinutes}`
    );
  }

  public async evaluateFatigueGuard(
    sessionId: string,
    consecutiveWeighCount: number,
    sessionDurationMinutes: number
  ): Promise<DecisionFatigueReport> {
    if (consecutiveWeighCount < 0) {
      throw new AdminApiError("INVALID_COUNT", "consecutiveWeighCount cannot be negative", 400);
    }
    if (sessionDurationMinutes < 0) {
      throw new AdminApiError("INVALID_DURATION", "sessionDurationMinutes cannot be negative", 400);
    }
    return this.postJson<DecisionFatigueReport>(`/v1/cases/fatigue-guard/evaluate`, {
      session_id: sessionId.trim(),
      consecutive_weigh_count: consecutiveWeighCount,
      session_duration_minutes: sessionDurationMinutes,
    });
  }

  public async getContextLens(caseVersionId: string): Promise<ContextLensReport> {
    return this.getJson<ContextLensReport>(`/v1/cases/${caseVersionId}/context-lens`);
  }

  public async addContextLensPillar(
    caseVersionId: string,
    pillar: ContextLensPillarInput
  ): Promise<{ status: string; pillar: ContextLensPillar }> {
    if (pillar.title.trim().length < 2) {
      throw new AdminApiError("INVALID_TITLE", "Title must have at least 2 characters", 400);
    }
    if (pillar.content.trim().length < 20) {
      throw new AdminApiError("INVALID_CONTENT", "Content must have at least 20 characters", 400);
    }
    return this.postJson<{ status: string; pillar: ContextLensPillar }>(
      `/v1/cases/${caseVersionId}/context-lens/pillars`,
      pillar
    );
  }

  public async getConsensusCircle(caseVersionId: string): Promise<ConsensusCircleReport> {
    return this.getJson<ConsensusCircleReport>(`/v1/cases/${caseVersionId}/consensus-circle`);
  }

  public async evaluateConsensusCircle(
    caseVersionId: string,
    payload: ConsensusCircleInput
  ): Promise<ConsensusCircleReport> {
    return this.postJson<ConsensusCircleReport>(`/v1/cases/${caseVersionId}/consensus-circle`, payload);
  }

  public async getBoardroomDeliberation(caseVersionId: string): Promise<BoardroomReport> {
    return this.getJson<BoardroomReport>(`/v1/cases/${caseVersionId}/boardroom`);
  }

  public async evaluateBoardroomDecision(
    caseVersionId: string,
    payload: BoardroomInput
  ): Promise<BoardroomReport> {
    return this.postJson<BoardroomReport>(`/v1/cases/${caseVersionId}/boardroom`, payload);
  }

  public async getYouthSpace(caseVersionId: string): Promise<YouthSpaceReport> {
    return this.getJson<YouthSpaceReport>(`/v1/cases/${caseVersionId}/youth-space`);
  }

  public async updateYouthSpace(
    caseVersionId: string,
    payload: YouthSpaceInput
  ): Promise<YouthSpaceReport> {
    return this.postJson<YouthSpaceReport>(`/v1/cases/${caseVersionId}/youth-space`, payload);
  }

  public async getCitizenJury(caseVersionId: string): Promise<CitizenJuryReport> {
    return this.getJson<CitizenJuryReport>(`/v1/cases/${caseVersionId}/citizen-jury`);
  }

  public async conveneCitizenJury(
    caseVersionId: string,
    payload: CitizenJuryInput
  ): Promise<CitizenJuryReport> {
    return this.postJson<CitizenJuryReport>(`/v1/cases/${caseVersionId}/citizen-jury`, payload);
  }
}

export interface ContextLensPillar {
  pillar_type: "LEGAL_FRAMEWORK" | "HISTORICAL_CONTEXT" | "SCIENTIFIC_DATA" | "COMPARATIVE_PRACTICE";
  title: string;
  content: string;
  source_citation: string;
  source_url?: string | null;
}

export interface ContextLensReport {
  case_version_id: string;
  pillars: ContextLensPillar[];
}

export interface ContextLensPillarInput {
  pillar_type: "LEGAL_FRAMEWORK" | "HISTORICAL_CONTEXT" | "SCIENTIFIC_DATA" | "COMPARATIVE_PRACTICE";
  title: string;
  content: string;
  source_citation: string;
  source_url?: string | null;
}

export interface ConsensusCircleReport {
  case_version_id: string;
  circle_id: string;
  pact_title: string;
  state: "STAKEHOLDER_DIAMETRIC_IMPASSE" | "INTERMEDIATE_CONCESSION_BARGAINING" | "SYNTHESIS_PACT_RATIFIED";
  stakeholder_groups_count: number;
  mutual_concession_score: number;
  synthesis_covenant_summary: string;
  capability_id: string;
}

export interface ConsensusCircleInput {
  circle_id: string;
  pact_title: string;
  stakeholder_groups_count: number;
  mutual_concession_score: number;
  synthesis_covenant_summary: string;
}

export interface BoardroomReport {
  case_version_id: string;
  room_id: string;
  organization_name: string;
  dilemma_scope: "ESG_AND_SUSTAINABILITY" | "CAPITAL_ALLOCATION_AND_MA" | "EXECUTIVE_COMPENSATION" | "CRISIS_MANAGEMENT";
  board_member_count: number;
  fiduciary_consensus_ratio: number;
  esg_alignment_score: number;
  capability_id: string;
}

export interface BoardroomInput {
  room_id: string;
  organization_name: string;
  dilemma_scope: string;
  board_member_count: number;
  votes_in_favor: number;
  esg_alignment_score: number;
}

export interface YouthSpaceReport {
  case_version_id: string;
  space_id: string;
  space_name: string;
  focus_area: "CAMPUS_AND_EDUCATION_POLICY" | "CLIMATE_AND_INTERGENERATIONAL" | "DIGITAL_RIGHTS_AND_AI" | "CIVIC_ENTREPRENEURSHIP";
  institution_or_community: string;
  active_student_count: number;
  consensus_action_count: number;
  capability_id: string;
}

export interface YouthSpaceInput {
  space_id: string;
  space_name: string;
  focus_area: string;
  institution_or_community: string;
  active_student_count: number;
  consensus_action_count: number;
}

export interface CitizenJuryReport {
  case_version_id: string;
  jury_id: string;
  dilemma_title: string;
  stage: "STRATIFIED_PANEL_ASSEMBLY" | "EXPERT_HEARINGS_IN_SESSION" | "CONSENSUS_VERDICT_EMITTED";
  juror_count: number;
  expert_witnesses_count: number;
  verdict_consensus_rate: number;
  reference_adr: string;
}

export interface CitizenJuryInput {
  jury_id: string;
  dilemma_title: string;
  stage: string;
  juror_count: number;
  expert_witnesses_count: number;
  verdict_consensus_rate: number;
}
