export type BotDefenseState =
  | "ORGANIC_CITIZEN_AUTHENTIC"
  | "SUSPECTED_BOT_COORDINATION"
  | "ISOLATED_QUARANTINE_SWARM";

export type QuarantineStatus = "ACTIVE" | "RESOLVED" | "WHITELISTED";

export type AgendaPriorityTier =
  | "NATIONAL_URGENCY_SPIKE"
  | "REGIONAL_EMERGENT_TOPIC"
  | "MONITORED_INCUBATION";

export interface ClusterInspectionRequest {
  cluster_id: string;
  target_case_id: string;
  synthetic_probability_score: number;
  quarantined_bot_payloads_count: number;
  semantic_entropy_index: number;
}

export interface ClusterInspectionResponse {
  cluster_id: string;
  target_case_id: string;
  defense_state: BotDefenseState;
  synthetic_probability_score: number;
  quarantined_bot_payloads_count: number;
  semantic_entropy_index: number;
  is_quarantined: boolean;
  inspected_at: string;
}

export interface AgendaThresholdEvaluationRequest {
  topic_id: string;
  topic_title: string;
  resonance_velocity_index: number;
  viewpoint_diversity_entropy: number;
}

export interface AgendaThresholdEvaluationResponse {
  topic_id: string;
  topic_title: string;
  priority_tier: AgendaPriorityTier;
  resonance_velocity_index: number;
  viewpoint_diversity_entropy: number;
  is_featured_on_national_ballot: boolean;
  evaluated_at: string;
}

export interface QuarantineClusterRecord {
  cluster_id: string;
  target_case_id: string;
  defense_state: BotDefenseState;
  synthetic_probability_score: number;
  quarantined_bot_payloads_count: number;
  semantic_entropy_index: number;
  quarantine_status: QuarantineStatus;
  updated_at: string;
}

const DEFAULT_CLUSTERS: QuarantineClusterRecord[] = [
  {
    cluster_id: "bot_cls_001",
    target_case_id: "case_ai_001",
    defense_state: "ISOLATED_QUARANTINE_SWARM",
    synthetic_probability_score: 0.94,
    quarantined_bot_payloads_count: 1450,
    semantic_entropy_index: 0.12,
    quarantine_status: "ACTIVE",
    updated_at: "2026-09-12T12:00:00Z",
  },
  {
    cluster_id: "bot_cls_002",
    target_case_id: "case_edu_002",
    defense_state: "SUSPECTED_BOT_COORDINATION",
    synthetic_probability_score: 0.65,
    quarantined_bot_payloads_count: 180,
    semantic_entropy_index: 0.38,
    quarantine_status: "ACTIVE",
    updated_at: "2026-09-12T15:30:00Z",
  },
  {
    cluster_id: "bot_cls_003",
    target_case_id: "case_health_003",
    defense_state: "ORGANIC_CITIZEN_AUTHENTIC",
    synthetic_probability_score: 0.15,
    quarantined_bot_payloads_count: 0,
    semantic_entropy_index: 0.82,
    quarantine_status: "WHITELISTED",
    updated_at: "2026-09-12T16:45:00Z",
  },
];

export class TrustIntegrityApiClient {
  private baseUrl: string;
  private inMemoryClusters: Map<string, QuarantineClusterRecord>;

  constructor(baseUrl = "") {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
    this.inMemoryClusters = new Map(
      DEFAULT_CLUSTERS.map((c) => [c.cluster_id, { ...c }])
    );
  }

  async inspectCluster(
    req: ClusterInspectionRequest
  ): Promise<ClusterInspectionResponse> {
    if (!req.cluster_id || req.cluster_id.trim().length < 2) {
      throw new Error("cluster_id must have at least 2 characters");
    }
    if (
      req.synthetic_probability_score < 0 ||
      req.synthetic_probability_score > 1
    ) {
      throw new Error("synthetic_probability_score must be between 0.0 and 1.0");
    }
    if (req.semantic_entropy_index < 0 || req.semantic_entropy_index > 1) {
      throw new Error("semantic_entropy_index must be between 0.0 and 1.0");
    }

    if (this.baseUrl) {
      try {
        const res = await fetch(`${this.baseUrl}/v1/trust/shield/inspect`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(req),
        });
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback to local evaluation
      }
    }

    let defense_state: BotDefenseState = "ORGANIC_CITIZEN_AUTHENTIC";
    if (
      req.synthetic_probability_score >= 0.8 &&
      req.semantic_entropy_index < 0.25
    ) {
      defense_state = "ISOLATED_QUARANTINE_SWARM";
    } else if (req.synthetic_probability_score >= 0.4) {
      defense_state = "SUSPECTED_BOT_COORDINATION";
    }

    const is_quarantined = defense_state === "ISOLATED_QUARANTINE_SWARM";
    const record: QuarantineClusterRecord = {
      cluster_id: req.cluster_id.trim(),
      target_case_id: req.target_case_id.trim(),
      defense_state,
      synthetic_probability_score: Math.round(req.synthetic_probability_score * 100) / 100,
      quarantined_bot_payloads_count: req.quarantined_bot_payloads_count,
      semantic_entropy_index: Math.round(req.semantic_entropy_index * 100) / 100,
      quarantine_status: is_quarantined ? "ACTIVE" : "WHITELISTED",
      updated_at: new Date().toISOString(),
    };

    if (is_quarantined) {
      this.inMemoryClusters.set(record.cluster_id, record);
    }

    return {
      ...record,
      is_quarantined,
      inspected_at: record.updated_at,
    };
  }

  async evaluateAgenda(
    req: AgendaThresholdEvaluationRequest
  ): Promise<AgendaThresholdEvaluationResponse> {
    if (!req.topic_title || req.topic_title.trim().length < 5) {
      throw new Error("topic_title must have at least 5 characters");
    }

    if (this.baseUrl) {
      try {
        const res = await fetch(`${this.baseUrl}/v1/trust/agenda/evaluate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(req),
        });
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }

    const combined =
      0.6 * req.resonance_velocity_index + 0.4 * req.viewpoint_diversity_entropy;
    let priority_tier: AgendaPriorityTier = "MONITORED_INCUBATION";
    let is_featured = false;

    if (combined >= 0.75) {
      priority_tier = "NATIONAL_URGENCY_SPIKE";
      is_featured = true;
    } else if (combined >= 0.45) {
      priority_tier = "REGIONAL_EMERGENT_TOPIC";
      is_featured = false;
    }

    return {
      topic_id: req.topic_id.trim(),
      topic_title: req.topic_title.trim(),
      priority_tier,
      resonance_velocity_index: Math.round(req.resonance_velocity_index * 100) / 100,
      viewpoint_diversity_entropy: Math.round(req.viewpoint_diversity_entropy * 100) / 100,
      is_featured_on_national_ballot: is_featured,
      evaluated_at: new Date().toISOString(),
    };
  }

  async listClusters(): Promise<QuarantineClusterRecord[]> {
    if (this.baseUrl) {
      try {
        const res = await fetch(`${this.baseUrl}/v1/trust/clusters`);
        if (res.ok) {
          return await res.json();
        }
      } catch {
        // Fallback
      }
    }
    return Array.from(this.inMemoryClusters.values());
  }

  async updateClusterStatus(
    cluster_id: string,
    new_status: QuarantineStatus
  ): Promise<QuarantineClusterRecord> {
    const cluster = this.inMemoryClusters.get(cluster_id);
    if (!cluster) {
      throw new Error(`Cluster ${cluster_id} not found`);
    }
    const updated: QuarantineClusterRecord = {
      ...cluster,
      quarantine_status: new_status,
      updated_at: new Date().toISOString(),
    };
    this.inMemoryClusters.set(cluster_id, updated);
    return updated;
  }
}
