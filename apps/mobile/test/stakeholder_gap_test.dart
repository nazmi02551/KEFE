import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

void main() {
  group('Stakeholder Gap Disclosure (CAP-038)', () {
    test('ADR-0147 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0147-stakeholder-gap-disclosure.md');
      final contract = File('../../docs/contracts/stakeholder-gap-disclosure.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-STAKEHOLDER-GAP-DISCLOSURE-001'));
      expect(contract.readAsStringSync(), contains('DIRECTLY_AFFECTED'));
    });

    test('StakeholderGapSegment model instantiates properly', () {
      const segment = StakeholderGapSegment(
        segmentKey: 'DIRECTLY_AFFECTED',
        label: 'Doğrudan Etkilenenler',
        distributions: {'A': 0.70, 'B': 0.30},
        gapPoints: 15,
        sampleSize: 150,
      );

      expect(segment.segmentKey, 'DIRECTLY_AFFECTED');
      expect(segment.gapPoints, 15);
      expect(segment.sampleSize, 150);

      const reveal = RevealResult(
        layer: 'TRUSTED',
        sampleSize: 1200,
        confidence: 'HIGH',
        values: {'A': 0.55, 'B': 0.45},
        stakeholderGaps: [segment],
      );

      expect(reveal.stakeholderGaps.length, 1);
      expect(reveal.stakeholderGaps.first.label, 'Doğrudan Etkilenenler');
    });

    test('InternalAlphaStrings contains Stakeholder Gap localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.stakeholderEyebrow, contains('PAYDAŞ'));
      expect(tr.stakeholderTitle, contains('nasıl tarttı'));
      expect(tr.stakeholderSampleInfo(120), 'n=120');

      const en = KefeStrings(Locale('en'));
      expect(en.stakeholderEyebrow, contains('STAKEHOLDER'));
      expect(en.stakeholderTitle, contains('different groups'));
      expect(en.stakeholderSampleInfo(120), 'n=120');
    });
  });
}
