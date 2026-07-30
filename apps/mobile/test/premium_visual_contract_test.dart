import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('migrated Decision Journey surfaces avoid dark-only surface tokens', () {
    final contractFile = File(
      '../../docs/contracts/premium-visual-localization-slice1.v1.json',
    );
    expect(contractFile.existsSync(), isTrue);

    final contract = jsonDecode(contractFile.readAsStringSync())
        as Map<String, Object?>;
    final visual = contract['visual_system']! as Map<String, Object?>;
    final governed = (visual['governed_files']! as List<Object?>)
        .cast<String>();
    const forbidden = <String>[
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
      final mobilePrefix = 'apps/mobile/';
      expect(repositoryPath.startsWith(mobilePrefix), isTrue);
      final file = File(repositoryPath.substring(mobilePrefix.length));
      expect(file.existsSync(), isTrue, reason: repositoryPath);
      final source = file.readAsStringSync();

      for (final token in forbidden) {
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

  test('slice contract keeps product/runtime inference boundaries closed', () {
    final contract = jsonDecode(
          File(
            '../../docs/contracts/premium-visual-localization-slice1.v1.json',
          ).readAsStringSync(),
        )
        as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;

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
  });
}
