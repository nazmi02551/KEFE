import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/conflict_interest_lobbying_radar_models.dart';

void main() {
  group('Conflict-of-Interest & Lobbying Transparency Radar (CAP-104)', () {
    test('ADR-0236 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0236-conflict-interest-lobbying-radar.md');
      final contract = File('../../docs/contracts/conflict-interest-lobbying-radar.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-LOBBY-RADAR-001'));
      expect(contract.readAsStringSync(), contains('CLEAN_INDEPENDENT_DISCLOSURE'));
    });

    test('LobbyingRadarModel instantiates properly', () {
      const model = LobbyingRadarModel(
        radarId: 'rdr_1',
        organizationId: 'org_1',
        exposureLevel: LobbyingExposureLevelModel.cleanIndependentDisclosure,
        transparencyIndex: 0.98,
        declaredFundingAmountUsd: 0.0,
        primaryBenefactorSector: 'Bağımsız Yurttaş Bağışları',
      );

      expect(model.transparencyIndex, 0.98);
      expect(model.declaredFundingAmountUsd, 0.0);
      expect(model.exposureLevel, LobbyingExposureLevelModel.cleanIndependentDisclosure);
    });

    test('InternalAlphaStrings contains Lobbying Radar localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.lobbyRdrEyebrow, contains('ÇIKAR ÇATIŞMASI'));
      expect(tr.lobbyRdrLvlClean, contains('Temiz Bağımsız'));

      const en = KefeStrings(Locale('en'));
      expect(en.lobbyRdrEyebrow, contains('CONFLICT-OF-INTEREST'));
      expect(en.lobbyRdrLvlClean, contains('Clean Independent'));
    });
  });
}
