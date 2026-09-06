import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/perspective_spectrum_models.dart';

void main() {
  group('Value-Driven Perspective Spectrum (CAP-103)', () {
    test('ADR-0215 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0215-perspective-spectrum.md');
      final contract = File('../../docs/contracts/perspective-spectrum.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-PERSPECT-SPEC-001'));
      expect(contract.readAsStringSync(), contains('EQUALITY_AND_CARE'));
    });

    test('PerspectiveSpectrumModel instantiates properly', () {
      const model = PerspectiveSpectrumModel(
        spectrumId: 'spec_1',
        caseVersionId: 'case_1',
        primaryValueHue: PrimaryValueHueModel.equalityAndCare,
        argumentResonanceCount: 450,
        crossValueBridgeRatio: 0.72,
        coreMoralIntuition: 'Kırılgan kesimlerin korunması.',
      );

      expect(model.crossValueBridgeRatio, 0.72);
      expect(model.primaryValueHue, PrimaryValueHueModel.equalityAndCare);
    });

    test('InternalAlphaStrings contains Perspective Spectrum localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.perspSpecEyebrow, contains('PERSPEKTİF TAYFI'));
      expect(tr.perspSpecValEquality, contains('Eşitlik'));

      const en = KefeStrings(Locale('en'));
      expect(en.perspSpecEyebrow, contains('PERSPECTIVE SPECTRUM'));
      expect(en.perspSpecValEquality, contains('Equality'));
    });
  });
}
