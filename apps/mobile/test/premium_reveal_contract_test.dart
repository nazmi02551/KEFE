import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  final contractFile = File(
    '../../docs/contracts/premium-reveal-slice2.v1.json',
  );

  test('governed Reveal presentation avoids dark-only and locale branching', () {
    expect(contractFile.existsSync(), isTrue);
    final contract = jsonDecode(contractFile.readAsStringSync())
        as Map<String, Object?>;
    final governed = (contract['governed_files']! as List<Object?>)
        .cast<String>();
    const forbiddenTokens = <String>[
      'KefeColorTokens.backgroundDark',
      'KefeColorTokens.surfaceDark',
      'KefeColorTokens.surfaceElevatedDark',
      'KefeColorTokens.surfaceSoftDark',
      'KefeColorTokens.borderDark',
    ];
    const localeBranching = <String>[
      "locale.languageCode == 'tr'",
      'locale.languageCode == "tr"',
      "locale.languageCode == 'en'",
      'locale.languageCode == "en"',
    ];

    for (final repositoryPath in governed) {
      const mobilePrefix = 'apps/mobile/';
      expect(repositoryPath.startsWith(mobilePrefix), isTrue);
      final file = File(repositoryPath.substring(mobilePrefix.length));
      expect(file.existsSync(), isTrue, reason: repositoryPath);
      final source = file.readAsStringSync();

      for (final token in forbiddenTokens) {
        expect(
          source.contains(token),
          isFalse,
          reason: '$repositoryPath still owns dark-only token $token',
        );
      }
      for (final branch in localeBranching) {
        expect(
          source.contains(branch),
          isFalse,
          reason: '$repositoryPath contains presentation locale branching',
        );
      }
    }
  });

  test('Reveal slice keeps inference and pre-Commit boundaries closed', () {
    final contract = jsonDecode(contractFile.readAsStringSync())
        as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;
    final localization = contract['localization']! as Map<String, Object?>;

    expect(invariants['commit_first'], isTrue);
    expect(invariants['blind_first'], isTrue);
    expect(invariants['immutable_case_version'], isTrue);
    expect(invariants['case_agnostic_runtime'], isTrue);
    expect(invariants['preview_production_isolation'], isTrue);
    expect(invariants['preview_fixture_is_production_fallback'], isFalse);
    expect(invariants['signal_in_scope'], isFalse);
    expect(invariants['impact_in_scope'], isFalse);
    expect(invariants['personality_inference'], isFalse);
    expect(invariants['ideology_inference'], isFalse);
    expect(invariants['psychometric_inference'], isFalse);
    expect(invariants['bias_inference'], isFalse);
    expect(invariants['causal_inference'], isFalse);

    expect(localization['raw_selected_option_must_not_change'], isTrue);
    expect(localization['raw_reveal_keys_must_not_change'], isTrue);
  });
}
