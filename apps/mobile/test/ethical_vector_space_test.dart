import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/ethical_vector_space_models.dart';

void main() {
  group('Multi-Dimensional Ethical Vector Space (CAP-096)', () {
    test('ADR-0211 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0211-ethical-vector-space.md');
      final contract = File('../../docs/contracts/ethical-vector-space.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-ETH-VECTOR-001'));
      expect(contract.readAsStringSync(), contains('DEONTOLOGICAL_RIGHTS'));
    });

    test('EthicalVectorSpaceModel instantiates properly', () {
      const model = EthicalVectorSpaceModel(
        caseVersionId: 'case-1',
        utilitarianWeight: 0.45,
        deontologicalWeight: 0.90,
        communitarianWeight: 0.60,
        intergenerationalWeight: 0.70,
        dominantAttractor: DominantMoralAttractorModel.deontologicalRights,
      );

      expect(model.deontologicalWeight, 0.90);
      expect(model.dominantAttractor, DominantMoralAttractorModel.deontologicalRights);
    });

    test('InternalAlphaStrings contains Ethical Vector localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.ethVecEyebrow, contains('ETİK HARİTALAMA'));
      expect(tr.ethVecDomDeontological, contains('Ödev'));

      const en = KefeStrings(Locale('en'));
      expect(en.ethVecEyebrow, contains('ETHICAL VECTOR'));
      expect(en.ethVecDomDeontological, contains('Deontological'));
    });
  });
}
