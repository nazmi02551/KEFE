import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/depolarization_index_models.dart';

void main() {
  group('Depolarization & Bridge Efficacy Index (CAP-117)', () {
    test('ADR-0204 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0204-depolarization-index.md');
      final contract = File('../../docs/contracts/depolarization-index.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-DEPOLAR-INDEX-001'));
      expect(contract.readAsStringSync(), contains('HIGH_DEPOLARIZATION'));
    });

    test('DepolarizationIndexModel instantiates properly', () {
      const model = DepolarizationIndexModel(
        caseVersionId: 'case-1',
        preDeliberationDistance: 0.80,
        postDeliberationDistance: 0.30,
        depolarizationScore: 0.62,
        bridgeEfficacyState: BridgeEfficacyStateModel.highDepolarization,
      );

      expect(model.depolarizationScore, 0.62);
      expect(model.bridgeEfficacyState, BridgeEfficacyStateModel.highDepolarization);
    });

    test('InternalAlphaStrings contains Depolarization localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.depolarEyebrow, contains('KUTUPLAŞMA AZALTMA'));
      expect(tr.depolarStateHigh, contains('Yakınlaşma'));

      const en = KefeStrings(Locale('en'));
      expect(en.depolarEyebrow, contains('DEPOLARIZATION'));
      expect(en.depolarStateHigh, contains('Convergence'));
    });
  });
}
