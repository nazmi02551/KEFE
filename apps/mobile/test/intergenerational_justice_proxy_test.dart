import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/intergenerational_justice_proxy_models.dart';

void main() {
  group('Intergenerational Justice & Planetary Rights Proxy (CAP-112)', () {
    test('ADR-0244 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0244-intergenerational-justice-proxy.md');
      final contract = File('../../docs/contracts/intergenerational-justice-proxy.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-FUTURE-001'));
      expect(contract.readAsStringSync(), contains('REGENERATIVE_FUTURE_STEWARDSHIP'));
    });

    test('IntergenerationalJusticeModel instantiates properly', () {
      const model = IntergenerationalJusticeModel(
        proxyId: 'prx_1',
        policyDomain: 'Su Havzaları',
        impactStatus: IntergenerationalImpactStatusModel.regenerativeFutureStewardship,
        stewardshipEquityIndex: 0.91,
        planetaryBoundaryHeadroomScore: 0.85,
      );

      expect(model.stewardshipEquityIndex, 0.91);
      expect(model.planetaryBoundaryHeadroomScore, 0.85);
      expect(model.impactStatus, IntergenerationalImpactStatusModel.regenerativeFutureStewardship);
    });

    test('InternalAlphaStrings contains Intergenerational Justice localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.futureProxyEyebrow, contains('GELECEK NESİLLER'));
      expect(tr.futureProxyStRegenerative, contains('Yenileyici Gezegen Emaneti'));

      const en = KefeStrings(Locale('en'));
      expect(en.futureProxyEyebrow, contains('INTERGENERATIONAL JUSTICE'));
      expect(en.futureProxyStRegenerative, contains('Regenerative 50-Year'));
    });
  });
}
