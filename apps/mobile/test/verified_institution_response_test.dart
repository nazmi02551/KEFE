import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/verified_institution_response_models.dart';

void main() {
  group('Verified Institution Response Protocol (CAP-049)', () {
    test('ADR-0192 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0192-verified-institution-response.md');
      final contract = File('../../docs/contracts/verified-institution-response.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-INST-RESPONSE-001'));
      expect(contract.readAsStringSync(), contains('OFFICIAL_GOVERNMENT'));
    });

    test('VerifiedInstitutionResponseModel instantiates properly', () {
      const model = VerifiedInstitutionResponseModel(
        responseId: 'resp_1',
        signalId: 'sig_1',
        institutionName: 'Bakanlık',
        institutionType: InstitutionTypeModel.officialGovernment,
        responseBody: 'Resmi yanıt metni.',
        verificationFingerprint: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        respondedAtUtc: '2026-09-01T14:30:00Z',
      );

      expect(model.institutionName, 'Bakanlık');
      expect(model.institutionType, InstitutionTypeModel.officialGovernment);
    });

    test('InternalAlphaStrings contains Verified Institution Response localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.instRespEyebrow, contains('DOĞRULANMIŞ KURUM'));
      expect(tr.instRespVerifiedBadge, contains('RESMİ DOĞRULANMIŞ'));

      const en = KefeStrings(Locale('en'));
      expect(en.instRespEyebrow, contains('VERIFIED INSTITUTION'));
      expect(en.instRespVerifiedBadge, contains('OFFICIALLY VERIFIED'));
    });
  });
}
