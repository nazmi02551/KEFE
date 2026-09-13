import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { OpenMethodologyApiClient } from '../src/lib/open-methodology-api';

describe('Open Methodology Disclosure Client (CAP-074)', () => {
  const client = new OpenMethodologyApiClient();

  it('retrieves methodology disclosure with invariants and safeguards', async () => {
    const data = await client.getDisclosure('case', 'case-test-88', 150);
    assert.equal(data.contract_id, 'KEFE-OPEN-METHODOLOGY-DISCLOSURE-001');
    assert.equal(data.capability_id, 'CAP-074');
    assert.equal(data.target_type, 'case');
    assert.equal(data.target_id, 'case-test-88');
    assert.equal(data.confidence, 'HIGH');
    assert.equal(data.layer, 'TRUSTED');
    assert.ok(data.safeguards.length >= 3);
    assert.ok(data.methodology_hash.length > 0);
    assert.equal(data.invariants.no_psychometric_claims, true);
    assert.equal(data.invariants.always_accessible, true);
  });

  it('degrades confidence when sample size is low', async () => {
    const data = await client.getDisclosure('signal', 'sig-test-12', 15);
    assert.equal(data.confidence, 'LOW');
    assert.equal(data.layer, 'RAW');
    assert.equal(data.sample_size, 15);
  });

  it('fetches manifest summary and safeguard definitions', async () => {
    const manifest = await client.getManifestSummary();
    assert.equal(manifest.engine_version, 'v1.0');
    assert.ok(manifest.formula_manifest.consensus_score);
    assert.ok(manifest.safeguard_definitions.COMMIT_FIRST);
    assert.ok(manifest.governance_standard.includes('ADR-0148'));
  });
});
