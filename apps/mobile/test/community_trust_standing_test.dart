import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/community_trust_standing_models.dart';

void main() {
  group('Community Trust Score & Contribution Standing (CAP-070)', () {
    test('ADR-0203 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0203-community-trust-standing.md');
      final contract = File('../../docs/contracts/community-trust-standing.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-TRUST-STANDING-001'));
      expect(contract.readAsStringSync(), contains('EXEMPLARY_CONTRIBUTOR'));
    });

    test('CommunityTrustStandingModel instantiates properly', () {
      const model = CommunityTrustStandingModel(
        userPseudonymId: 'usr_1',
        trustScore: 0.95,
        standingTier: StandingTierModel.exemplaryContributor,
        bridgeArgumentCount: 5,
        verifiedWeighCount: 20,
        infractionCount: 0,
      );

      expect(model.trustScore, 0.95);
      expect(model.standingTier, StandingTierModel.exemplaryContributor);
    });

    test('InternalAlphaStrings contains Community Trust Standing localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.trustStandEyebrow, contains('TOPLULUK GÜVEN'));
      expect(tr.trustStandTierExemplary, contains('Örnek Sivil'));

      const en = KefeStrings(Locale('en'));
      expect(en.trustStandEyebrow, contains('COMMUNITY TRUST'));
      expect(en.trustStandTierExemplary, contains('Exemplary Civic'));
    });
  });
}
