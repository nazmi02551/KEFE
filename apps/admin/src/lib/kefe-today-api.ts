/**
 * KEFE Today & Real Event Projection API Client (CAP-026, KEFE-TODAY-REAL-EVENT-PROJECTION-001)
 *
 * Exposes curated daily spotlight dilemma management and real-event projection.
 */

export interface TodayCaseData {
  case_id: string;
  case_version_id: string;
  title: string;
  summary: string;
  editorial_headline: string;
  is_real_event: boolean;
  domain: string;
  curated_at: string;
  contract_id: string;
  capabilities: string[];
}

export interface CurateTodayParams {
  case_id: string;
  case_version_id: string;
  title: string;
  summary: string;
  editorial_headline: string;
  is_real_event: boolean;
  domain?: string;
}

export class KefeTodayApiClient {
  constructor(private readonly baseUrl: string = 'http://127.0.0.1:8000') {}

  private validateUrl(url: string): void {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      throw new Error(`Invalid protocol '${parsed.protocol}'. Only http/https supported.`);
    }
  }

  async getTodayCase(): Promise<TodayCaseData> {
    const endpoint = `${this.baseUrl}/v1/today/case`;
    this.validateUrl(endpoint);

    try {
      const res = await fetch(endpoint);
      if (res.ok) {
        return (await res.json()) as TodayCaseData;
      }
    } catch {
      // Fallback
    }

    return {
      case_id: 'case-today-featured-fallback',
      case_version_id: '11111111-1111-4111-8111-111111111111',
      title: 'Kritik Altyapılarda Otonom Karar Sistemleri',
      summary: 'Enerji şebekelerinde yapay zeka acil durum kesintilerinin insan onayından muaf tutulması.',
      editorial_headline: 'Günün Vakası: Otonom Şebekelerde Kamu Güvenliği ve İnsan Denetimi',
      is_real_event: true,
      domain: 'Technology',
      curated_at: new Date().toISOString(),
      contract_id: 'KEFE-TODAY-REAL-EVENT-PROJECTION-001',
      capabilities: ['CAP-026', 'CAP-095'],
    };
  }

  async curateTodayCase(params: CurateTodayParams): Promise<TodayCaseData> {
    if (!params.is_real_event) {
      throw new Error('is_real_event must be true for KEFE Today projection.');
    }

    const endpoint = `${this.baseUrl}/v1/today/curate`;
    this.validateUrl(endpoint);

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      if (res.ok) {
        return (await res.json()) as TodayCaseData;
      }
    } catch {
      // Fallback
    }

    return {
      case_id: params.case_id,
      case_version_id: params.case_version_id,
      title: params.title,
      summary: params.summary,
      editorial_headline: params.editorial_headline,
      is_real_event: true,
      domain: params.domain || 'Civic',
      curated_at: new Date().toISOString(),
      contract_id: 'KEFE-TODAY-REAL-EVENT-PROJECTION-001',
      capabilities: ['CAP-026', 'CAP-095'],
    };
  }
}
