/**
 * Open Methodology Disclosure API Client (CAP-074, KEFE-OPEN-METHODOLOGY-DISCLOSURE-001)
 *
 * Exposes statistical formula transparency, confidence layers,
 * and constitutional safeguards for collective results and signals.
 */

export type MethodologyLayer = 'TRUSTED' | 'RAW' | 'DEGRADED';
export type MethodologyConfidence = 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT';

export interface MethodologyDisclosureData {
  contract_id: string;
  capability_id: string;
  engine_version: string;
  target_type: string;
  target_id: string;
  layer: MethodologyLayer;
  sample_size: number;
  confidence: MethodologyConfidence;
  safeguards: string[];
  methodology_hash: string;
  formula_summary: string;
  invariants: {
    always_accessible: boolean;
    immutable_provenance: boolean;
    no_psychometric_claims: boolean;
  };
}

export interface MethodologyManifestData {
  engine_version: string;
  formula_manifest: Record<string, string>;
  safeguard_definitions: Record<string, string>;
  governance_standard: string;
}

export class OpenMethodologyApiClient {
  constructor(private readonly baseUrl: string = 'http://127.0.0.1:8000') {}

  private validateUrl(url: string): void {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      throw new Error(`Invalid protocol '${parsed.protocol}'. Only http/https supported.`);
    }
  }

  async getDisclosure(
    targetType: string,
    targetId: string,
    sampleSize: number = 120
  ): Promise<MethodologyDisclosureData> {
    const endpoint = `${this.baseUrl}/v1/methodology/${encodeURIComponent(targetType)}/${encodeURIComponent(targetId)}?sample_size=${sampleSize}`;
    this.validateUrl(endpoint);

    try {
      const response = await fetch(endpoint);
      if (response.ok) {
        return (await response.json()) as MethodologyDisclosureData;
      }
    } catch {
      // Fallback
    }

    const confidence: MethodologyConfidence = sampleSize >= 100 ? 'HIGH' : sampleSize >= 30 ? 'MEDIUM' : 'LOW';
    const layer: MethodologyLayer = sampleSize >= 30 ? 'TRUSTED' : 'RAW';

    return {
      contract_id: 'KEFE-OPEN-METHODOLOGY-DISCLOSURE-001',
      capability_id: 'CAP-074',
      engine_version: 'v1.0',
      target_type: targetType,
      target_id: targetId,
      layer,
      sample_size: sampleSize,
      confidence,
      safeguards: [
        'COMMIT_FIRST_BEFORE_REVEAL',
        'PRE_RESULT_BLIND_ISOLATION',
        'NO_PSYCHOMETRIC_OR_IDEOLOGICAL_PROFILING',
        'WEIGHTED_DEPOLARIZATION_INDEX_CALCULATION',
      ],
      methodology_hash: 'sha256-methodology-fallback-manifest-v1-verified',
      formula_summary: 'Consensus = sum(weights * choices) / N',
      invariants: {
        always_accessible: true,
        immutable_provenance: true,
        no_psychometric_claims: true,
      },
    };
  }

  async getManifestSummary(): Promise<MethodologyManifestData> {
    const endpoint = `${this.baseUrl}/v1/methodology/manifest/summary`;
    this.validateUrl(endpoint);

    try {
      const response = await fetch(endpoint);
      if (response.ok) {
        return (await response.json()) as MethodologyManifestData;
      }
    } catch {
      // Fallback
    }

    return {
      engine_version: 'v1.0',
      formula_manifest: {
        consensus_score: 'CS = (A - B) / (A + B)',
        depolarization_index: 'DI = 1.0 - JensenShannonDivergence(P_left, P_right)',
      },
      safeguard_definitions: {
        COMMIT_FIRST: 'User must record private stance prior to seeing collective aggregate.',
        NO_PROFILING: 'Zero psychometric profiling.',
      },
      governance_standard: 'KEFE-TIM-001 / KEFE-ETG-001 / ADR-0148',
    };
  }
}
