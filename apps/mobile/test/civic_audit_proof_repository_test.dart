import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/civic_audit_proof_repository_models.dart';

void main() {
  group('Independent Civic Audit Report & Proof Repository (CAP-107)', () {
    test('ADR-0239 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0239-civic-audit-proof-repository.md');
      final contract = File('../../docs/contracts/civic-audit-proof-repository.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-AUDIT-REPO-001'));
      expect(contract.readAsStringSync(), contains('PEER_ATTESTED_CORROBORATED'));
    });

    test('CivicAuditReportModel instantiates properly', () {
      const model = CivicAuditReportModel(
        reportId: 'aud_1',
        investigationTitle: 'İmar Planı Değişikliği ve Yeşil Alan Dönüşüm Raporu',
        verificationStatus: AuditVerificationStatusModel.peerAttestedCorroborated,
        peerAttestationSignaturesCount: 5,
        evidentiaryRigorScore: 0.96,
        contentHashDigest: 'sha256:4a8b7c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b',
      );

      expect(model.peerAttestationSignaturesCount, 5);
      expect(model.evidentiaryRigorScore, 0.96);
      expect(model.verificationStatus, AuditVerificationStatusModel.peerAttestedCorroborated);
    });

    test('InternalAlphaStrings contains Civic Audit localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.civicRepoEyebrow, contains('YURTTAŞ DENETİM'));
      expect(tr.civicRepoStAttested, contains('Hakem Onaylı'));

      const en = KefeStrings(Locale('en'));
      expect(en.civicRepoEyebrow, contains('CIVIC AUDIT'));
      expect(en.civicRepoStAttested, contains('Peer-Attested'));
    });
  });
}
