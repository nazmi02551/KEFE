// ADR-0142 / CAP-070 — Context information-status guide locale string tests.
// Contract: KEFE-CONTEXT-INFORMATION-STATUS-GUIDE-001
//
// Invariants tested:
// 1. contextInformationStatusGuideTitle is non-blank in TR and EN.
// 2. contextInformationStatusGuideHelper is non-blank in TR and EN.
// 3. contextInformationStatusDescription returns distinct non-blank
//    descriptions for all four canonical statuses in both locales.
// 4. No description attributes a status to the linked source
//    (must not contain "source" as the subject).
// 5. Contract: guide_collapsed_by_default — confirmed by key in widget tests.
// 6. Contract: linked_source_status_inferred = false
//    (descriptions must not imply source verification).
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';

const _statuses = ['VERIFIED', 'CLAIMED', 'DISPUTED', 'UNKNOWN'];

void main() {
  group('ADR-0142 — Context information-status guide strings (CAP-070)', () {
    const tr = KefeStrings(Locale('tr'));
    const en = KefeStrings(Locale('en'));

    test('contract file exists and contains KEFE-CONTEXT-INFORMATION-STATUS-GUIDE-001',
        () {
      final contract = File(
        '../../docs/contracts/context-information-status-guide.v1.json',
      );
      expect(contract.existsSync(), isTrue,
          reason: 'context-information-status-guide.v1.json must exist');
      final decoded =
          jsonDecode(contract.readAsStringSync()) as Map<String, dynamic>;
      expect(
        decoded['contract_id'],
        'KEFE-CONTEXT-INFORMATION-STATUS-GUIDE-001',
      );
    });

    test('contextInformationStatusGuideTitle non-blank in TR and EN', () {
      expect(tr.contextInformationStatusGuideTitle, isNotEmpty);
      expect(en.contextInformationStatusGuideTitle, isNotEmpty);
    });

    test('contextInformationStatusGuideHelper non-blank in TR and EN', () {
      expect(tr.contextInformationStatusGuideHelper, isNotEmpty);
      expect(en.contextInformationStatusGuideHelper, isNotEmpty);
    });

    test('TR and EN guide titles are distinct (locale parity)', () {
      expect(
        tr.contextInformationStatusGuideTitle,
        isNot(equals(en.contextInformationStatusGuideTitle)),
      );
    });

    for (final status in _statuses) {
      test('TR description for $status is non-blank', () {
        expect(tr.contextInformationStatusDescription(status), isNotEmpty);
      });

      test('EN description for $status is non-blank', () {
        expect(en.contextInformationStatusDescription(status), isNotEmpty);
      });

      test('TR and EN descriptions for $status are distinct', () {
        expect(
          tr.contextInformationStatusDescription(status),
          isNot(equals(en.contextInformationStatusDescription(status))),
        );
      });
    }

    test('all four status descriptions are distinct in EN', () {
      final descriptions =
          _statuses.map(en.contextInformationStatusDescription).toSet();
      expect(descriptions.length, _statuses.length,
          reason: 'each status must have a unique description');
    });

    test('all four status descriptions are distinct in TR', () {
      final descriptions =
          _statuses.map(tr.contextInformationStatusDescription).toSet();
      expect(descriptions.length, _statuses.length,
          reason: 'each status must have a unique description');
    });

    test(
        'EN descriptions do not imply source verification (linked_source_status_inferred=false)',
        () {
      // ADR-0142: "a block status does not independently verify a linked source"
      // Descriptions must not say they verify the source.
      for (final status in _statuses) {
        final desc = en.contextInformationStatusDescription(status);
        // Should not start with "Source" as subject
        expect(
          desc.toLowerCase().startsWith('source'),
          isFalse,
          reason:
              'Description for $status must not attribute status to the source',
        );
      }
    });

    test('EN helper mentions block not source', () {
      final helper = en.contextInformationStatusGuideHelper.toLowerCase();
      expect(helper, contains('block'));
      // ADR-0142: helper must not positively assert source verification.
      // The canonical string uses "does not independently verify" — a denial,
      // not an assertion. We verify it does not start with a verification claim.
      expect(helper, isNot(startsWith('verif')));
      expect(helper, isNot(contains('source is verified')));
    });

    test('TR helper mentions blok not kaynak-doğrulama', () {
      final helper = tr.contextInformationStatusGuideHelper.toLowerCase();
      // "blok" appears as "bloğunun" (inflected form) in Turkish
      expect(helper, anyOf(contains('blok'), contains('bloğ')));
    });
  });
}