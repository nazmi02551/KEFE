import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/system_health_transparency_models.dart';

void main() {
  group('Real-Time Service Health & Incident Transparency (CAP-088)', () {
    test('ADR-0218 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0218-system-health-transparency.md');
      final contract = File('../../docs/contracts/system-health-transparency.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-SYS-HEALTH-001'));
      expect(contract.readAsStringSync(), contains('OPERATIONAL_OPTIMAL'));
    });

    test('SystemHealthModel instantiates properly', () {
      const model = SystemHealthModel(
        subsystemId: 'sub_1',
        subsystemName: 'Kör Tartım Motoru',
        status: SystemHealthStatusModel.operationalOptimal,
        p99LatencyMs: 45,
        uptimePercentage30d: 99.98,
      );

      expect(model.p99LatencyMs, 45);
      expect(model.uptimePercentage30d, 99.98);
    });

    test('InternalAlphaStrings contains System Health localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.sysHealthEyebrow, contains('SİSTEM DURUMU'));
      expect(tr.sysHealthStOptimal, contains('Tüm Sistemler'));

      const en = KefeStrings(Locale('en'));
      expect(en.sysHealthEyebrow, contains('SERVICE HEALTH'));
      expect(en.sysHealthStOptimal, contains('Operational'));
    });
  });
}
