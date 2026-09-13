import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { SourceDiversityApiClient } from '../src/lib/source-diversity-api';

describe('Source Diversity Indicator Client (CAP-071)', () => {
  const client = new SourceDiversityApiClient();

  it('retrieves default source diversity breakdown for case version', async () => {
    const data = await client.getSourceDiversity('case-uuid-101');
    assert.equal(data.case_version_id, 'case-uuid-101');
    assert.ok(data.total_sources >= 1);
    assert.ok(['HIGH_DIVERSITY', 'BALANCED_DIVERSITY', 'LIMITED_DIVERSITY'].includes(data.diversity_level));
    assert.ok(Array.isArray(data.category_breakdown));
    assert.ok(data.category_breakdown.length > 0);
  });

  it('evaluates source diversity with custom pluralistic categories', async () => {
    const data = await client.evaluateSourceDiversity('case-uuid-102', [
      'ACADEMIC_SCIENTIFIC',
      'OFFICIAL_GOVERNMENT',
      'CIVIC_INDEPENDENT',
      'MAINSTREAM_JOURNALISM',
      'TECHNICAL_INDUSTRY',
    ]);
    assert.equal(data.total_sources, 5);
    assert.equal(data.diversity_level, 'HIGH_DIVERSITY');
    assert.equal(data.category_breakdown.length, 5);
    assert.equal(data.category_breakdown[0].percentage, 20.0);
  });

  it('evaluates limited diversity when monopolistic single category provided', async () => {
    const data = await client.evaluateSourceDiversity('case-uuid-103', [
      'MAINSTREAM_JOURNALISM',
      'MAINSTREAM_JOURNALISM',
    ]);
    assert.equal(data.total_sources, 2);
    assert.equal(data.diversity_level, 'LIMITED_DIVERSITY');
    assert.equal(data.category_breakdown.length, 1);
    assert.equal(data.category_breakdown[0].percentage, 100.0);
  });
});
