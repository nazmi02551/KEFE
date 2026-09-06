import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/impact_evidence_models.dart';

void main() {
  group('Impact Evidence & Artifact Verification (CAP-053)', () {
    test('ADR-0194 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0194-impact-evidence.md');
      final contract = File('../../docs/contracts/impact-evidence.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-IMPACT-EVIDENCE-001'));
      expect(contract.readAsStringSync(), contains('OFFICIAL_GAZETTE_DECREE'));
    });

    test('ImpactEvidenceModel instantiates properly', () {
      const model = ImpactEvidenceModel(
        evidenceId: 'evi_1',
        actionId: 'act_1',
        evidenceType: ImpactEvidenceTypeModel.officialGazetteDecree,
        evidenceTitle: 'Resmi Gazete İlanı',
        sourceUrl: 'https://resmigazete.gov.tr/ilan.pdf',
        sha256Digest: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        verificationStatus: EvidenceVerificationStatusModel.verifiedAuthentic,
      );

      expect(model.evidenceTitle, 'Resmi Gazete İlanı');
      expect(model.verificationStatus, EvidenceVerificationStatusModel.verifiedAuthentic);
    });

    test('InternalAlphaStrings contains Impact Evidence localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.impactEviEyebrow, contains('SOMUT ETKİ KANITI'));
      expect(tr.impactEviStatusVerified, contains('DOĞRULANMIŞ ÖZGÜN'));

      const en = KefeStrings(Locale('en'));
      expect(en.impactEviEyebrow, contains('IMPACT EVIDENCE'));
      expect(en.impactEviStatusVerified, contains('VERIFIED AUTHENTIC'));
    });
  });
}
