import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/counter_argument_models.dart';

void main() {
  group('Counter-Argument and Refutation Mapper (CAP-043)', () {
    test('ADR-0181 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0181-counter-argument-and-refutation-mapper.md');
      final contract = File('../../docs/contracts/counter-argument-mapper.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-COUNTER-ARGUMENT-001'));
      expect(contract.readAsStringSync(), contains('DIRECT_EMPIRICAL_REBUTTAL'));
    });

    test('ArgumentRefutationLinkModel instantiates properly', () {
      const model = ArgumentRefutationLinkModel(
        refutationId: 'ref-1',
        sourceArgumentId: 'arg-2',
        targetArgumentId: 'arg-1',
        refutationType: RefutationTypeModel.directEmpiricalRebuttal,
        refutationStrength: 0.85,
        rebuttalThesis: 'TÜİK 2026 verileri ile çürütülmüştür.',
      );

      expect(model.refutationType, RefutationTypeModel.directEmpiricalRebuttal);
      expect(model.refutationStrength, 0.85);
    });

    test('InternalAlphaStrings contains Rebuttal localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.rebuttalEyebrow, contains('DİYALEKTİK'));
      expect(tr.rebuttalTypeEmpirical, contains('Doğrudan Olgusal'));

      const en = KefeStrings(Locale('en'));
      expect(en.rebuttalEyebrow, contains('DIALECTICAL'));
      expect(en.rebuttalTypeEmpirical, contains('Empirical'));
    });
  });
}
