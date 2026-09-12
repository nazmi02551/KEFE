import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { UserDiscoveryApiClient } from '../src/lib/user-discovery-api';

describe('User-Controlled Discovery Profile Client (CAP-077)', () => {
  const client = new UserDiscoveryApiClient();

  it('retrieves default discovery profile with agency parameters', async () => {
    const profile = await client.getProfile('test-actor-101');
    assert.equal(profile.user_id, 'test-actor-101');
    assert.ok(Array.isArray(profile.preferred_domains));
    assert.ok(profile.preferred_domains.length >= 1);
    assert.ok(['INTRODUCTORY', 'BALANCED', 'DEEP_DELIBERATION'].includes(profile.complexity_level));
    assert.ok(profile.diversification_boost >= 0.0 && profile.diversification_boost <= 1.0);
  });

  it('updates discovery profile with customized preferences', async () => {
    const updated = await client.updateProfile('test-actor-102', {
      preferred_domains: ['ENVIRONMENT', 'JUSTICE'],
      complexity_level: 'DEEP_DELIBERATION',
      freshness_preference: 'CURRENT_EVENTS',
      real_event_preference: 'REAL_EVENTS_FIRST',
      diversification_boost: 0.85,
    });

    assert.equal(updated.user_id, 'test-actor-102');
    assert.equal(updated.complexity_level, 'DEEP_DELIBERATION');
    assert.equal(updated.real_event_preference, 'REAL_EVENTS_FIRST');
    assert.equal(updated.diversification_boost, 0.85);
  });

  it('rejects invalid diversification boost values outside [0, 1]', async () => {
    await assert.rejects(
      async () => {
        await client.updateProfile('test-actor-103', {
          preferred_domains: ['CIVIC'],
          complexity_level: 'BALANCED',
          freshness_preference: 'BALANCED',
          real_event_preference: 'BALANCED',
          diversification_boost: 1.5,
        });
      },
      { message: /diversification_boost must be between 0.0 and 1.0/ }
    );
  });
});
