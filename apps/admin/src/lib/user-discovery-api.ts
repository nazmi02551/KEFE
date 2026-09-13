/**
 * User-Controlled Discovery Profile API Client (CAP-077, KEFE-USER-DISCOVERY-001)
 *
 * Implements user-governed exploration profiles, non-engagement maximization,
 * and diversity boost configurations.
 */

export type DomainPreference =
  | 'CIVIC'
  | 'TECHNOLOGY'
  | 'BIOETHICS'
  | 'ENVIRONMENT'
  | 'JUSTICE'
  | 'ECONOMIC';

export type ComplexityLevel =
  | 'INTRODUCTORY'
  | 'BALANCED'
  | 'DEEP_DELIBERATION';

export type FreshnessPreference =
  | 'CURRENT_EVENTS'
  | 'BALANCED'
  | 'TIMELESS_FOUNDATIONS';

export type RealEventPreference =
  | 'REAL_EVENTS_FIRST'
  | 'BALANCED'
  | 'HYPOTHETICALS_FIRST';

export interface UserDiscoveryProfileData {
  user_id: string;
  preferred_domains: DomainPreference[];
  complexity_level: ComplexityLevel;
  freshness_preference: FreshnessPreference;
  real_event_preference: RealEventPreference;
  diversification_boost: number;
  updated_at: string;
}

export interface UpdateDiscoveryProfileParams {
  preferred_domains: DomainPreference[];
  complexity_level: ComplexityLevel;
  freshness_preference: FreshnessPreference;
  real_event_preference: RealEventPreference;
  diversification_boost: number;
}

export class UserDiscoveryApiClient {
  constructor(private readonly baseUrl: string = 'http://127.0.0.1:8000') {}

  private validateUrl(url: string): void {
    const parsed = new URL(url);
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      throw new Error(`Invalid protocol '${parsed.protocol}'. Only http/https supported.`);
    }
  }

  async getProfile(userId: string = 'guest-current-actor'): Promise<UserDiscoveryProfileData> {
    const endpoint = `${this.baseUrl}/v1/discovery/profile?user_id=${encodeURIComponent(userId)}`;
    this.validateUrl(endpoint);

    try {
      const res = await fetch(endpoint);
      if (res.ok) {
        return (await res.json()) as UserDiscoveryProfileData;
      }
    } catch {
      // Fallback
    }

    return {
      user_id: userId,
      preferred_domains: ['CIVIC', 'TECHNOLOGY'],
      complexity_level: 'BALANCED',
      freshness_preference: 'BALANCED',
      real_event_preference: 'BALANCED',
      diversification_boost: 0.5,
      updated_at: new Date().toISOString(),
    };
  }

  async updateProfile(
    userId: string,
    params: UpdateDiscoveryProfileParams
  ): Promise<UserDiscoveryProfileData> {
    if (params.diversification_boost < 0.0 || params.diversification_boost > 1.0) {
      throw new Error('diversification_boost must be between 0.0 and 1.0.');
    }

    const endpoint = `${this.baseUrl}/v1/discovery/profile?user_id=${encodeURIComponent(userId)}`;
    this.validateUrl(endpoint);

    try {
      const res = await fetch(endpoint, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      if (res.ok) {
        return (await res.json()) as UserDiscoveryProfileData;
      }
    } catch {
      // Fallback
    }

    return {
      user_id: userId,
      preferred_domains: params.preferred_domains,
      complexity_level: params.complexity_level,
      freshness_preference: params.freshness_preference,
      real_event_preference: params.real_event_preference,
      diversification_boost: params.diversification_boost,
      updated_at: new Date().toISOString(),
    };
  }
}
