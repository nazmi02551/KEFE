import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/evidence_builder_models.dart';

void main() {
  group('Evidence Builder and Verification Engine (CAP-098)', () {
    test('ADR-0168 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0168-evidence-builder-and-verification-engine.md');
      final contract = File('../../docs/contracts/evidence-builder.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-EVIDENCE-BUILDER-001'));
      expect(contract.readAsStringSync(), contains('ACADEMIC_PEER_REVIEWED'));
    });

    test('StructuredEvidenceItemModel instantiates properly', () {
      final item = StructuredEvidenceItemModel(
        evidenceId: 'ev-1',
        caseVersionId: 'case-1',
        category: EvidenceCategoryModel.academicPeerReviewed,
        title: 'Kentsel Ulaşım Analizi',
        publisher: 'İktisat Dergisi',
        verificationStatus: EvidenceVerificationStatusModel.expertAudited,
        createdAt: DateTime.now().toUtc(),
      );

      expect(item.evidenceId, 'ev-1');
      expect(item.category, EvidenceCategoryModel.academicPeerReviewed);
      expect(item.verificationStatus, EvidenceVerificationStatusModel.expertAudited);
    });

    test('InternalAlphaStrings contains Evidence localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.evidenceCategoryAcademic, contains('Akademik'));
      expect(tr.evidenceStatusExpert, contains('Uzman'));

      const en = KefeStrings(Locale('en'));
      expect(en.evidenceCategoryAcademic, contains('Academic'));
      expect(en.evidenceStatusExpert, contains('Expert'));
    });
  });
}
