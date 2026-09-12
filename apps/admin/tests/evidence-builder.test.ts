import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { EvidenceBuilderApiClient } from '../src/lib/evidence-builder-api';

describe('Evidence Builder API Client (CAP-098)', () => {
  const client = new EvidenceBuilderApiClient();

  it('creates and binds structured evidence with verifiable URL', async () => {
    const record = await client.createEvidence({
      case_version_id: 'case-cv-101',
      category: 'ACADEMIC_PEER_REVIEWED',
      title: 'Algorithmic Civics Peer-Reviewed Paper',
      publisher: 'Oxford Academic Press',
      source_url: 'https://academic.example.com/paper/42',
    });

    assert.equal(record.contract_id, 'KEFE-EVIDENCE-BUILDER-001');
    assert.equal(record.capability_id, 'CAP-098');
    assert.equal(record.title, 'Algorithmic Civics Peer-Reviewed Paper');
    assert.equal(record.category, 'ACADEMIC_PEER_REVIEWED');
    assert.equal(record.verification_status, 'UNVERIFIED');
  });

  it('fails to create evidence if both source_url and doi_or_doc_ref are missing', async () => {
    await assert.rejects(
      async () => {
        await client.createEvidence({
          case_version_id: 'case-cv-102',
          category: 'INVESTIGATIVE_JOURNALISM',
          title: 'Unreferenced Investigative Report',
          publisher: 'Unknown Media',
        });
      },
      { message: /Either source_url or doi_or_doc_ref must be provided/ }
    );
  });

  it('lists case evidence records and verifies an item', async () => {
    const list = await client.listCaseEvidence('case-cv-101');
    assert.ok(Array.isArray(list));
    assert.ok(list.length >= 1);

    const verified = await client.verifyEvidence(
      list[0].evidence_id,
      'EXPERT_AUDITED',
      'auditor-1',
      'Verified against primary archives.'
    );
    assert.equal(verified.verification_status, 'EXPERT_AUDITED');
  });
});
