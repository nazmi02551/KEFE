import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/democratic_emergency_safeguard_models.dart';

void main() {
  group('Democratic Emergency & State-of-Exception Safeguard (CAP-113)', () {
    test('ADR-0245 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0245-democratic-emergency-safeguard.md');
      final contract = File('../../docs/contracts/democratic-emergency-safeguard.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-EMERGENCY-001'));
      expect(contract.readAsStringSync(), contains('PROPORTIONATE_SUNSET_BOUNDED'));
    });

    test('DemocraticEmergencyModel instantiates properly', () {
      const model = DemocraticEmergencyModel(
        decreeId: 'emg_1',
        emergencyJurisdiction: 'Deprem Afet Bölgesi',
        safeguardStatus: EmergencySafeguardStatusModel.proportionateSunsetBounded,
        proportionalityScore: 0.94,
        remainingSunsetDays: 45,
      );

      expect(model.proportionalityScore, 0.94);
      expect(model.remainingSunsetDays, 45);
      expect(model.safeguardStatus, EmergencySafeguardStatusModel.proportionateSunsetBounded);
    });

    test('InternalAlphaStrings contains Democratic Emergency localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.emergencyEyebrow, contains('OLAĞANÜSTÜ HAL'));
      expect(tr.emergencyStProportionate, contains('Ölçülü ve Süre Sınırlı'));

      const en = KefeStrings(Locale('en'));
      expect(en.emergencyEyebrow, contains('DEMOCRATIC EMERGENCY'));
      expect(en.emergencyStProportionate, contains('Proportionate & Sunset-Bounded'));
    });
  });
}
