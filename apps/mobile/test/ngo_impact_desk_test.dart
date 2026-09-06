import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/ngo_impact_desk_models.dart';

void main() {
  group('Civil Society & NGO Impact Desk (CAP-037)', () {
    test('ADR-0210 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0210-ngo-impact-desk.md');
      final contract = File('../../docs/contracts/ngo-impact-desk.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-NGO-DESK-001'));
      expect(contract.readAsStringSync(), contains('ENVIRONMENT_AND_CLIMATE'));
    });

    test('NgoImpactDeskModel instantiates properly', () {
      const model = NgoImpactDeskModel(
        campaignId: 'cmp_1',
        ngoName: 'Temiz Hava Derneği',
        advocacyDomain: NgoAdvocacyDomainModel.environmentAndClimate,
        citizenEndorsementCount: 1000,
        institutionalReformsAchieved: 3,
        advocacyEfficacyScore: 0.95,
      );

      expect(model.citizenEndorsementCount, 1000);
      expect(model.advocacyEfficacyScore, 0.95);
    });

    test('InternalAlphaStrings contains NGO Impact Desk localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.ngoDeskEyebrow, contains('SİVİL TOPLUM'));
      expect(tr.ngoDeskDomClimate, contains('Çevre'));

      const en = KefeStrings(Locale('en'));
      expect(en.ngoDeskEyebrow, contains('CIVIL SOCIETY'));
      expect(en.ngoDeskDomClimate, contains('Environment'));
    });
  });
}
