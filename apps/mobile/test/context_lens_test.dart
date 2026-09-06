import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/context_lens_models.dart';

void main() {
  group('Context Lens Neutral Background Engine (CAP-097)', () {
    test('ADR-0167 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0167-context-lens-neutral-background-engine.md');
      final contract = File('../../docs/contracts/context-lens.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-CONTEXT-LENS-001'));
      expect(contract.readAsStringSync(), contains('LEGAL_FRAMEWORK'));
    });

    test('ContextLensModel instantiates properly', () {
      const model = ContextLensModel(
        caseVersionId: 'case-1',
        pillars: [
          ContextLensPillarModel(
            pillarType: LensPillarTypeModel.legalFramework,
            title: 'Belediye Kanunu',
            content: 'Büyükşehir belediyelerinin toplu taşıma hizmetlerini düzenleme yetkisi.',
            sourceCitation: '5393 Sayılı Kanun',
          ),
        ],
      );

      expect(model.pillars.length, 1);
      expect(model.pillars.first.pillarType, LensPillarTypeModel.legalFramework);
    });

    test('InternalAlphaStrings contains Context Lens localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.lensSheetTitle, contains('Bağlam'));
      expect(tr.lensPillarLegal, contains('Hukuki'));

      const en = KefeStrings(Locale('en'));
      expect(en.lensSheetTitle, contains('Context'));
      expect(en.lensPillarLegal, contains('Legal'));
    });
  });
}
