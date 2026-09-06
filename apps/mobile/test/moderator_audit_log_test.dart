import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/moderator_audit_log_models.dart';

void main() {
  group('Moderator Action Audit Log & Transparency (CAP-067)', () {
    test('ADR-0201 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0201-moderator-audit-log.md');
      final contract = File('../../docs/contracts/moderator-audit-log.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-MOD-AUDIT-001'));
      expect(contract.readAsStringSync(), contains('REASON_REMOVED_POLICY_BREACH'));
    });

    test('ModeratorAuditLogModel instantiates properly', () {
      const model = ModeratorAuditLogModel(
        auditId: 'aud_1',
        targetResourceId: 'rsn_1',
        moderatorId: 'mod_1',
        actionType: ModerationActionTypeModel.reasonRemovedPolicyBreach,
        policyRuleReference: 'TOS-4.2',
        justificationText: 'Kural ihlali gerekçesiyle kaldırıldı.',
        actionHash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        createdAtUtc: '2026-09-01T15:00:00Z',
      );

      expect(model.moderatorId, 'mod_1');
      expect(model.actionType, ModerationActionTypeModel.reasonRemovedPolicyBreach);
    });

    test('InternalAlphaStrings contains Moderator Audit Log localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.modAuditEyebrow, contains('MODERASYON DENETİM'));
      expect(tr.modAuditActionRemove, contains('İçerik Kaldırıldı'));

      const en = KefeStrings(Locale('en'));
      expect(en.modAuditEyebrow, contains('MODERATION AUDIT'));
      expect(en.modAuditActionRemove, contains('Content Removed'));
    });
  });
}
