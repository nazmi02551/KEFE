import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';

void main() {
  group('Open Methodology Disclosure per Result/Signal (CAP-074)', () {
    test('ADR-0148 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0148-open-methodology-disclosure.md');
      final contract = File('../../docs/contracts/open-methodology-disclosure.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-OPEN-METHODOLOGY-DISCLOSURE-001'));
      expect(contract.readAsStringSync(), contains('engine_version'));
    });

    test('InternalAlphaStrings contains Open Methodology localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.methodologySheetTitle, contains('Metodoloji'));
      expect(tr.methodologyEngine('v1.0'), contains('KEFE'));
      expect(tr.methodologySafeguardCommitFirst, contains('Commit First'));
      expect(tr.methodologySafeguardNoProfiling, contains('Profilleme Yapılmaz'));

      const en = KefeStrings(Locale('en'));
      expect(en.methodologySheetTitle, contains('Methodology'));
      expect(en.methodologyEngine('v1.0'), contains('KEFE'));
      expect(en.methodologySafeguardCommitFirst, contains('Commit First'));
      expect(en.methodologySafeguardNoProfiling, contains('No Profiling'));
    });

    test('open_methodology_sheet.dart contains modal and safeguard components', () {
      final source = File('lib/features/decision/presentation/open_methodology_sheet.dart').readAsStringSync();

      expect(source, contains("ValueKey('open-methodology-sheet')"));
      expect(source, contains("ValueKey('methodology-close-button')"));
      expect(source, contains('_SafeguardRow'));
      expect(source, contains('_MetricBadge'));
    });
  });
}
