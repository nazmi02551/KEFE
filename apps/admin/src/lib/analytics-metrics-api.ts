export interface NorthStarResponse {
  window_start: string;
  window_end: string;
  meaningful_weigh_count: number;
  weekly_active_weighers: number;
  distinct_cases_weighed: number;
}

export interface FunnelStageItem {
  stage_name: string;
  stage_count: number;
  conversion_from_start_rate: number;
  drop_off_from_previous_rate: number;
}

export interface ActivationFunnelResponse {
  window_start: string;
  window_end: string;
  total_sessions: number;
  stages: FunnelStageItem[];
}

export interface QualityResilienceResponse {
  window_start: string;
  window_end: string;
  total_exposed_sessions: number;
  stable_decisions_count: number;
  shifted_decisions_count: number;
  resilience_index: number;
  attitude_shift_rate: number;
}

export type BridgeEfficacyState =
  | "HIGH_DEPOLARIZATION"
  | "MODERATE_BRIDGE_RESONANCE"
  | "PERSISTENT_POLARIZATION";

export interface DepolarizationEvaluationRequest {
  case_version_id: string;
  pre_deliberation_distance: number;
  post_deliberation_distance: number;
}

export interface DepolarizationEvaluationResponse {
  case_version_id: string;
  pre_deliberation_distance: number;
  post_deliberation_distance: number;
  depolarization_score: number;
  bridge_efficacy_state: BridgeEfficacyState;
  evaluated_at: string;
}

export class AnalyticsMetricsApiClient {
  private baseUrl: string;

  constructor(baseUrl = "") {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  async getNorthStar(windowDays = 7): Promise<NorthStarResponse> {
    if (this.baseUrl) {
      try {
        const res = await fetch(
          `${this.baseUrl}/v1/analytics/north-star?window_days=${windowDays}`
        );
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }

    const now = new Date();
    const start = new Date(now.getTime() - windowDays * 24 * 60 * 60 * 1000);
    return {
      window_start: start.toISOString(),
      window_end: now.toISOString(),
      meaningful_weigh_count: 3840,
      weekly_active_weighers: 1240,
      distinct_cases_weighed: 18,
    };
  }

  async getActivationFunnel(windowDays = 7): Promise<ActivationFunnelResponse> {
    if (this.baseUrl) {
      try {
        const res = await fetch(
          `${this.baseUrl}/v1/analytics/funnel?window_days=${windowDays}`
        );
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }

    const now = new Date();
    const start = new Date(now.getTime() - windowDays * 24 * 60 * 60 * 1000);
    return {
      window_start: start.toISOString(),
      window_end: now.toISOString(),
      total_sessions: 5000,
      stages: [
        {
          stage_name: "WEIGH_STARTED",
          stage_count: 5000,
          conversion_from_start_rate: 1.0,
          drop_off_from_previous_rate: 0.0,
        },
        {
          stage_name: "DECISION_COMMITTED",
          stage_count: 4200,
          conversion_from_start_rate: 0.84,
          drop_off_from_previous_rate: 0.16,
        },
        {
          stage_name: "RESULT_REVEALED",
          stage_count: 3840,
          conversion_from_start_rate: 0.768,
          drop_off_from_previous_rate: 0.0857,
        },
        {
          stage_name: "PERSPECTIVE_VIEWED",
          stage_count: 3100,
          conversion_from_start_rate: 0.62,
          drop_off_from_previous_rate: 0.1927,
        },
        {
          stage_name: "DECISION_REVISED",
          stage_count: 980,
          conversion_from_start_rate: 0.196,
          drop_off_from_previous_rate: 0.6839,
        },
      ],
    };
  }

  async getQualityMetrics(windowDays = 7): Promise<QualityResilienceResponse> {
    if (this.baseUrl) {
      try {
        const res = await fetch(
          `${this.baseUrl}/v1/analytics/quality?window_days=${windowDays}`
        );
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }

    const now = new Date();
    const start = new Date(now.getTime() - windowDays * 24 * 60 * 60 * 1000);
    return {
      window_start: start.toISOString(),
      window_end: now.toISOString(),
      total_exposed_sessions: 3100,
      stable_decisions_count: 2120,
      shifted_decisions_count: 980,
      resilience_index: 0.6839,
      attitude_shift_rate: 0.3161,
    };
  }

  async evaluateDepolarization(
    req: DepolarizationEvaluationRequest
  ): Promise<DepolarizationEvaluationResponse> {
    if (
      req.pre_deliberation_distance < 0 ||
      req.pre_deliberation_distance > 1 ||
      req.post_deliberation_distance < 0 ||
      req.post_deliberation_distance > 1
    ) {
      throw new Error("Distances must be in [0.0, 1.0]");
    }

    if (this.baseUrl) {
      try {
        const res = await fetch(
          `${this.baseUrl}/v1/analytics/depolarization/evaluate`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(req),
          }
        );
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }

    let score = 0.0;
    if (req.pre_deliberation_distance > 0) {
      const reduction =
        req.pre_deliberation_distance - req.post_deliberation_distance;
      score = Math.max(0.0, reduction / req.pre_deliberation_distance);
    }

    let state: BridgeEfficacyState = "PERSISTENT_POLARIZATION";
    if (score >= 0.5) {
      state = "HIGH_DEPOLARIZATION";
    } else if (score >= 0.2) {
      state = "MODERATE_BRIDGE_RESONANCE";
    }

    return {
      case_version_id: req.case_version_id,
      pre_deliberation_distance: Math.round(req.pre_deliberation_distance * 100) / 100,
      post_deliberation_distance: Math.round(req.post_deliberation_distance * 100) / 100,
      depolarization_score: Math.round(score * 100) / 100,
      bridge_efficacy_state: state,
      evaluated_at: new Date().toISOString(),
    };
  }
}
