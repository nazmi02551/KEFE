export type ContextDriftType =
  | "LEGAL_REFORM"
  | "FACTUAL_UPDATE"
  | "ASSUMPTION_CHANGED"
  | "SUPERSEDED_BASELINE";

export type DriftRecommendedAction =
  | "CONTINUE_WITH_AWARENESS"
  | "REVIEW_AMENDMENT"
  | "CASE_SUPERSEDED";

export interface ContextDriftNoticeResponse {
  notice_id: string;
  case_version_id: string;
  drift_type: ContextDriftType;
  effective_date: string;
  summary: string;
  recommended_action: DriftRecommendedAction;
  source_reference_url?: string | null;
  created_at: string;
}

export interface PublishDriftNoticeRequest {
  drift_type: ContextDriftType;
  summary: string;
  recommended_action: DriftRecommendedAction;
  source_reference_url?: string | null;
}

export interface DemographicShiftVector {
  demographic_segment: string;
  support_delta_percentage: number;
  confidence_interval: number;
}

export interface LiveRadarResponse {
  case_version_id: string;
  deliberation_velocity_index: number;
  live_participant_count: number;
  primary_consensus_momentum: string;
  shift_vectors: DemographicShiftVector[];
  has_active_context_drift: boolean;
  pulse_updated_at: string;
}

export class RadarLiveApiClient {
  private baseUrl: string;
  private inMemoryNotices: Map<string, ContextDriftNoticeResponse[]>;

  constructor(baseUrl = "") {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.inMemoryNotices = new Map();
  }

  async publishDriftNotice(
    caseVersionId: string,
    req: PublishDriftNoticeRequest
  ): Promise<ContextDriftNoticeResponse> {
    if (!req.summary || req.summary.trim().length < 10) {
      throw new Error("summary must have at least 10 characters");
    }

    if (this.baseUrl) {
      try {
        const res = await fetch(
          `${this.baseUrl}/v1/cases/${caseVersionId}/drift-notices`,
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

    const notice: ContextDriftNoticeResponse = {
      notice_id: `notice_${Date.now()}`,
      case_version_id: caseVersionId,
      drift_type: req.drift_type,
      effective_date: new Date().toISOString(),
      summary: req.summary,
      recommended_action: req.recommended_action,
      source_reference_url: req.source_reference_url,
      created_at: new Date().toISOString(),
    };

    const existing = this.inMemoryNotices.get(caseVersionId) || [];
    existing.push(notice);
    this.inMemoryNotices.set(caseVersionId, existing);
    return notice;
  }

  async getDriftNotices(
    caseVersionId: string
  ): Promise<ContextDriftNoticeResponse[]> {
    if (this.baseUrl) {
      try {
        const res = await fetch(
          `${this.baseUrl}/v1/cases/${caseVersionId}/drift-notices`
        );
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }

    return (
      this.inMemoryNotices.get(caseVersionId) || [
        {
          notice_id: "notice_sample_01",
          case_version_id: caseVersionId,
          drift_type: "LEGAL_REFORM",
          effective_date: "2026-09-10T12:00:00Z",
          summary: "İlgili yasa maddesi TBMM genel kurulunda güncellenmiştir.",
          recommended_action: "CONTINUE_WITH_AWARENESS",
          source_reference_url: "https://resmigazete.gov.tr/2026/09/10",
          created_at: "2026-09-10T12:05:00Z",
        },
      ]
    );
  }

  async getLiveRadar(caseVersionId: string): Promise<LiveRadarResponse> {
    if (this.baseUrl) {
      try {
        const res = await fetch(
          `${this.baseUrl}/v1/cases/${caseVersionId}/live-radar`
        );
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }

    const notices = this.inMemoryNotices.get(caseVersionId) || [];
    return {
      case_version_id: caseVersionId,
      deliberation_velocity_index: 0.74,
      live_participant_count: 1840,
      primary_consensus_momentum: "MODERATE_EXPANSION",
      shift_vectors: [
        {
          demographic_segment: "Genç Yetişkin (18-29)",
          support_delta_percentage: 4.2,
          confidence_interval: 0.92,
        },
        {
          demographic_segment: "Kentsel Sakinler",
          support_delta_percentage: -2.1,
          confidence_interval: 0.88,
        },
        {
          demographic_segment: "Sektör Temsilcileri",
          support_delta_percentage: 1.8,
          confidence_interval: 0.85,
        },
      ],
      has_active_context_drift: notices.length > 0,
      pulse_updated_at: new Date().toISOString(),
    };
  }
}
