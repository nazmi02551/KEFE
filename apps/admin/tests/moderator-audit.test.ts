import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { ModeratorAuditApiClient } from '../src/lib/moderator-audit-api';

describe('Moderator Action Audit Log Client (CAP-067)', () => {
  const client = new ModeratorAuditApiClient();

  it('logs a moderation action with policy reference and cryptographic hash', async () => {
    const entry = await client.logAction({
      target_resource_id: 'reason-888',
      moderator_id: 'mod-editorial-01',
      action_type: 'REASON_REMOVED_POLICY_BREACH',
      policy_rule_reference: 'KEFE-SEC-001/4.1',
      justification_text: 'Ad-hominem insult violating civic deliberation policy.',
    });

    assert.equal(entry.contract_id, 'KEFE-MOD-AUDIT-001');
    assert.equal(entry.capability_id, 'CAP-067');
    assert.equal(entry.action_type, 'REASON_REMOVED_POLICY_BREACH');
    assert.equal(entry.moderator_id, 'mod-editorial-01');
    assert.ok(entry.action_hash.length >= 16);
    assert.ok(entry.audit_id.length >= 4);
  });

  it('fails if justification_text is under 10 characters', async () => {
    await assert.rejects(
      async () => {
        await client.logAction({
          target_resource_id: 'reason-889',
          moderator_id: 'mod-1',
          action_type: 'FLAG_DISMISSED_VALID',
          policy_rule_reference: 'KEFE-SEC-001',
          justification_text: 'Short',
        });
      },
      { message: /justification_text must be at least 10 characters long/ }
    );
  });

  it('lists audit logs filtered by action type', async () => {
    const logs = await client.listAuditLogs('FLAG_DISMISSED_VALID');
    assert.ok(Array.isArray(logs));
    assert.ok(logs.length >= 1);
    assert.equal(logs[0].contract_id, 'KEFE-MOD-AUDIT-001');
  });
});
