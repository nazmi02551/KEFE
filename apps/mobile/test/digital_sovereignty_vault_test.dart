import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/digital_sovereignty_vault_models.dart';

void main() {
  group('Digital Sovereignty & Anti-Data-Colonialism Vault (CAP-110)', () {
    test('ADR-0242 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0242-digital-sovereignty-vault.md');
      final contract = File('../../docs/contracts/digital-sovereignty-vault.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-SOVEREIGNTY-001'));
      expect(contract.readAsStringSync(), contains('SOVEREIGN_RESIDENCY_ENFORCED'));
    });

    test('DigitalSovereigntyModel instantiates properly', () {
      const model = DigitalSovereigntyModel(
        vaultId: 'vlt_1',
        jurisdictionRegion: 'TR-Marmara',
        sovereigntyTier: DigitalSovereigntyTierModel.sovereignResidencyEnforced,
        localResidencyPct: 1.00,
        exfiltrationThreatScore: 0.01,
      );

      expect(model.localResidencyPct, 1.00);
      expect(model.exfiltrationThreatScore, 0.01);
      expect(model.sovereigntyTier, DigitalSovereigntyTierModel.sovereignResidencyEnforced);
    });

    test('InternalAlphaStrings contains Digital Sovereignty localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.sovereigntyEyebrow, contains('DİJİTAL EGEMENLİK'));
      expect(tr.sovereigntyStEnforced, contains('Kriptografik Yerel Egemenlik'));

      const en = KefeStrings(Locale('en'));
      expect(en.sovereigntyEyebrow, contains('DIGITAL SOVEREIGNTY'));
      expect(en.sovereigntyStEnforced, contains('Sovereign Local Residency'));
    });
  });
}
