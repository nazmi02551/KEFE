import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/impact/domain/institution_response_models.dart';

void main() {
  group('Verified Institution Response and Impact Room (CAP-050)', () {
    test('ADR-0149 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0149-verified-institution-response-and-impact-room.md');
      final contract = File('../../docs/contracts/institution-response.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-INSTITUTION-RESPONSE-001'));
      expect(contract.readAsStringSync(), contains('POLICY_CHANGE'));
    });

    test('InstitutionResponseItem model instantiates properly', () {
      final item = InstitutionResponseItem(
        id: 'resp-1',
        caseVersionId: 'case-v1',
        institutionName: 'Ulaştırma Bakanlığı',
        authorityRole: 'Basın Dairesi',
        verificationStatus: AuthorityVerificationStatus.verified,
        responseType: InstitutionResponseType.policyChange,
        statement: 'Tarife düzenlemesi yeniden değerlendirmeye alınmıştır.',
        publishedAt: DateTime.now().toUtc(),
      );

      expect(item.institutionName, 'Ulaştırma Bakanlığı');
      expect(item.verificationStatus, AuthorityVerificationStatus.verified);
      expect(item.responseType, InstitutionResponseType.policyChange);
    });

    test('InternalAlphaStrings contains Institution Response localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.institutionEyebrow, contains('KURUM YANITI'));
      expect(tr.institutionVerifiedBadge, contains('Resmi'));
      expect(tr.institutionTypePolicyChange, contains('Politika'));

      const en = KefeStrings(Locale('en'));
      expect(en.institutionEyebrow, contains('INSTITUTION RESPONSE'));
      expect(en.institutionVerifiedBadge, contains('Official'));
      expect(en.institutionTypePolicyChange, contains('Policy'));
    });
  });
}
