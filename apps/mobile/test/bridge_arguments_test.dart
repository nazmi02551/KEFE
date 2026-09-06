import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/bridge_argument_models.dart';

void main() {
  group('Bridge Arguments and Shared Ground Engine (CAP-034)', () {
    test('ADR-0161 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0161-bridge-arguments-and-shared-ground-engine.md');
      final contract = File('../../docs/contracts/bridge-arguments.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-BRIDGE-ARGUMENTS-001'));
      expect(contract.readAsStringSync(), contains('connecting_values'));
    });

    test('BridgeArgumentItemModel instantiates properly', () {
      final item = BridgeArgumentItemModel(
        id: 'bridge-1',
        caseVersionId: 'case-v1',
        synthesisThesis: 'Şeffaflık ve güvenlik dengeli denetimle sağlanır.',
        connectingValues: ['seffaflik', 'guvenlik'],
        crossGroupSupportRate: 0.55,
        sampleSize: 120,
        createdAt: DateTime.now().toUtc(),
      );

      expect(item.id, 'bridge-1');
      expect(item.crossGroupSupportRate, 0.55);
      expect(item.sampleSize, 120);
    });

    test('InternalAlphaStrings contains Bridge Argument localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.bridgeEyebrow, contains('ORTAK ZEMİN'));
      expect(tr.bridgeCrossSupport(55, 120), contains('%55'));

      const en = KefeStrings(Locale('en'));
      expect(en.bridgeEyebrow, contains('SHARED GROUND'));
      expect(en.bridgeCrossSupport(55, 120), contains('55%'));
    });
  });
}
