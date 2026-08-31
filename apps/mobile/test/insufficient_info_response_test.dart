import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/core/localization/internal_alpha_strings.dart';
import 'package:mobile/core/localization/kefe_strings.dart';

void main() {
  group('Insufficient information and missing options response contract & structure (CAP-011)', () {
    test('contract file exists and is valid JSON', () {
      final contractFile = File(
        '../../docs/contracts/insufficient-info-response.v1.json',
      );
      expect(contractFile.existsSync(), isTrue);
      expect(
        contractFile.readAsStringSync(),
        contains('KEFE-INSUFFICIENT-INFO-RESPONSE-001'),
      );
      expect(
        contractFile.readAsStringSync(),
        contains('OPT_OUT_INSUFFICIENT_INFO'),
      );
      expect(
        contractFile.readAsStringSync(),
        contains('OPT_OUT_MISSING_OPTIONS'),
      );
    });

    test('ADR-0146 exists', () {
      final adrFile = File(
        '../../docs/adr/0146-insufficient-info-and-missing-options-response.md',
      );
      expect(adrFile.existsSync(), isTrue);
      expect(
        adrFile.readAsStringSync(),
        contains('Non-coercive Insufficient Information and Missing Options Response'),
      );
    });

    test('question_input.dart contains opt-out buttons and keys', () {
      final source = File(
        'lib/features/decision/presentation/question_input.dart',
      ).readAsStringSync();

      expect(source, contains("ValueKey('option-OPT_OUT_INSUFFICIENT_INFO')"));
      expect(source, contains("ValueKey('option-OPT_OUT_MISSING_OPTIONS')"));
      expect(source, contains('_AlternativeResponseFooter'));
      expect(source, contains('_OptOutButton'));
    });

    test('InternalAlphaStrings contains Turkish and English opt-out strings', () {
      const en = KefeStrings(Locale('en'));
      expect(en.decisionOptOutInsufficientInfo, contains('Not enough information'));
      expect(en.decisionOptOutMissingOptions, contains('Options are missing'));
      expect(en.decisionOptOutTitle, contains('ALTERNATIVE RESPONSES'));

      const tr = KefeStrings(Locale('tr'));
      expect(tr.decisionOptOutInsufficientInfo, contains('Yeterli bilgim yok'));
      expect(tr.decisionOptOutMissingOptions, contains('Seçenekler eksik'));
      expect(tr.decisionOptOutTitle, contains('ALTERNATİF YANITLAR'));
    });
  });
}
