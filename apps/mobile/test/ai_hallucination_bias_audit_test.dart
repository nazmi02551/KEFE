import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/ai_hallucination_bias_audit_models.dart';

void main() {
  group('AI Hallucination & Cognitive Bias Auditing (CAP-091)', () {
    test('ADR-0231 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0231-ai-hallucination-bias-audit.md');
      final contract = File('../../docs/contracts/ai-hallucination-bias-audit.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-AI-AUDIT-001'));
      expect(contract.readAsStringSync(), contains('AUDIT_VERIFIED_GROUNDED'));
    });

    test('AiAuditModel instantiates properly', () {
      const model = AiAuditModel(
        auditId: 'adt_1',
        targetArtifactId: 'art_1',
        status: AiAuditStatusModel.auditVerifiedGrounded,
        groundingConfidenceScore: 0.96,
        biasAsymmetryIndex: 0.08,
        auditFindingsSummary: 'Ampirik temellendirme ve tarafsızlık doğrulandı.',
      );

      expect(model.groundingConfidenceScore, 0.96);
      expect(model.biasAsymmetryIndex, 0.08);
      expect(model.status, AiAuditStatusModel.auditVerifiedGrounded);
    });

    test('InternalAlphaStrings contains AI Audit localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.aiAuditEyebrow, contains('YAPAY ZEKA HALÜSİNASYON'));
      expect(tr.aiAuditStGrounded, contains('Olgusal Temellendirilmiş'));

      const en = KefeStrings(Locale('en'));
      expect(en.aiAuditEyebrow, contains('AI HALLUCINATION'));
      expect(en.aiAuditStGrounded, contains('Factually Grounded'));
    });
  });
}
