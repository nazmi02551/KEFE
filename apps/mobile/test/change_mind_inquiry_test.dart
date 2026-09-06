import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/change_mind_inquiry_models.dart';

void main() {
  group('What Would Change My Mind Engine (CAP-010)', () {
    test('ADR-0174 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0174-what-would-change-my-mind-engine.md');
      final contract = File('../../docs/contracts/what-would-change-my-mind.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-CHANGE-MIND-001'));
      expect(contract.readAsStringSync(), contains('EMPIRICAL_DATA_THRESHOLD'));
    });

    test('ChangeMindInquiryModel instantiates properly', () {
      const model = ChangeMindInquiryModel(
        caseVersionId: 'case-1',
        selectedConditions: [
          SelectedCounterfactualConditionModel(
            conditionType: CounterfactualConditionTypeModel.empiricalDataThreshold,
            description: 'Kaza oranında %20 düşüş kanıtlanırsa.',
          ),
        ],
        flexibilityClass: EpistemicFlexibilityClassModel.conditionallyFlexible,
      );

      expect(model.selectedConditions.length, 1);
      expect(model.flexibilityClass, EpistemicFlexibilityClassModel.conditionallyFlexible);
    });

    test('InternalAlphaStrings contains Change Mind localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.changeMindEyebrow, contains('FİKRİMİ NE DEĞİŞTİRİRDİ'));
      expect(tr.changeMindClassOpen, contains('Yüksek Epistemik Esneklik'));

      const en = KefeStrings(Locale('en'));
      expect(en.changeMindEyebrow, contains('EPISTEMIC FLEXIBILITY'));
      expect(en.changeMindClassOpen, contains('Epistemically Open'));
    });
  });
}
