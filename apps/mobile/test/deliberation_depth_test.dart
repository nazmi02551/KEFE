import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/deliberation_depth_models.dart';

void main() {
  group('Deliberation Depth & Reflection Score (CAP-118)', () {
    test('ADR-0205 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0205-deliberation-depth.md');
      final contract = File('../../docs/contracts/deliberation-depth.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-DELIB-DEPTH-001'));
      expect(contract.readAsStringSync(), contains('PROFOUND_DELIBERATION'));
    });

    test('DeliberationDepthModel instantiates properly', () {
      const model = DeliberationDepthModel(
        caseVersionId: 'case-1',
        deliberationDepthScore: 1.0,
        depthLevel: DepthLevelModel.profoundDeliberation,
        argumentsInspectedCount: 8,
        evidenceItemsVerifiedCount: 4,
        counterViewsExploredCount: 3,
      );

      expect(model.deliberationDepthScore, 1.0);
      expect(model.depthLevel, DepthLevelModel.profoundDeliberation);
    });

    test('InternalAlphaStrings contains Deliberation Depth localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.delibDepthEyebrow, contains('MÜZAKERE DERİNLİĞİ'));
      expect(tr.delibDepthLevelProfound, contains('Derinlemesine'));

      const en = KefeStrings(Locale('en'));
      expect(en.delibDepthEyebrow, contains('DELIBERATION DEPTH'));
      expect(en.delibDepthLevelProfound, contains('Profound'));
    });
  });
}
