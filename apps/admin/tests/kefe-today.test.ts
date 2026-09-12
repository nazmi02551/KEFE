import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { KefeTodayApiClient } from '../src/lib/kefe-today-api';

describe('KEFE Today & Real Event Projection Client (CAP-026)', () => {
  const client = new KefeTodayApiClient();

  it('fetches active featured today case with is_real_event true', async () => {
    const data = await client.getTodayCase();
    assert.equal(data.contract_id, 'KEFE-TODAY-REAL-EVENT-PROJECTION-001');
    assert.ok(data.capabilities.includes('CAP-026'));
    assert.equal(data.is_real_event, true);
    assert.ok(data.title.length >= 5);
    assert.ok(data.editorial_headline.length >= 5);
  });

  it('curates a new today spotlight case', async () => {
    const curated = await client.curateTodayCase({
      case_id: 'case-curated-test-01',
      case_version_id: '22222222-2222-4222-8222-222222222222',
      title: 'Yapay Zeka ve Yargısal Bağımsızlık',
      summary: 'Hakim kararlarında yapay zeka öneri sistemlerinin zorunlu bağlayıcılığı tartışması.',
      editorial_headline: 'Günün Hukuk İkilemi: Algoritmik Adalet',
      is_real_event: true,
      domain: 'Justice',
    });

    assert.equal(curated.case_id, 'case-curated-test-01');
    assert.equal(curated.is_real_event, true);
    assert.equal(curated.domain, 'Justice');
  });

  it('rejects curation when is_real_event is false', async () => {
    await assert.rejects(
      async () => {
        await client.curateTodayCase({
          case_id: 'case-invalid-02',
          case_version_id: '22222222-2222-4222-8222-222222222222',
          title: 'Hypothetical Dilemma',
          summary: 'A completely fictional scenario.',
          editorial_headline: 'Fiction',
          is_real_event: false,
        });
      },
      { message: /is_real_event must be true for KEFE Today projection/ }
    );
  });
});
