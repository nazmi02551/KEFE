import 'dart:convert';
import 'dart:io';

import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview/preview_content_localizer.dart';
import 'package:kefe_mobile/core/localization/kefe_content_localizer.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';

void main() {
  test('Perspective slice 3 contract preserves product/runtime boundaries', () {
    final contractFile = File(
      '../../docs/contracts/premium-perspective-slice3.v1.json',
    );
    expect(contractFile.existsSync(), isTrue);

    final contract =
        jsonDecode(contractFile.readAsStringSync()) as Map<String, Object?>;
    final runtime = contract['runtime']! as Map<String, Object?>;
    final invariants = contract['invariants']! as Map<String, Object?>;

    expect(runtime['post_commit_only'], isTrue);
    expect(runtime['retry_perspective_only'], isTrue);
    expect(runtime['answer_replay_on_retry'], isFalse);
    expect(runtime['reason_replay_on_retry'], isFalse);
    expect(runtime['commit_replay_on_retry'], isFalse);
    expect(runtime['reveal_replay_on_retry'], isFalse);
    expect(runtime['perspective_domain_model_change'], isFalse);
    expect(invariants['commit_first'], isTrue);
    expect(invariants['blind_first'], isTrue);
    expect(invariants['case_agnostic_runtime'], isTrue);
    expect(invariants['preview_fixture_is_production_fallback'], isFalse);
    expect(invariants['personality_inference'], isFalse);
    expect(invariants['ideology_inference'], isFalse);
    expect(invariants['psychometric_inference'], isFalse);
    expect(invariants['bias_inference'], isFalse);
    expect(invariants['causal_inference'], isFalse);
    expect(invariants['signal_in_scope'], isFalse);
    expect(invariants['impact_in_scope'], isFalse);
  });

  test('governed Perspective presentation uses semantic visual boundaries', () {
    final source = File(
      'lib/features/decision/presentation/perspective_section.dart',
    ).readAsStringSync();

    expect(source, contains('KefeSurface('));
    expect(source, contains('context.kefeVisual'));
    expect(source, contains('kefeContentLocalizerProvider'));
    expect(source, contains('KefeContentNamespace.perspectiveBody'));
    expect(source, contains('KefeContentNamespace.perspectiveProvenance'));
    expect(
      source,
      contains('KefeContentNamespace.perspectiveMethodologyProvenance'),
    );
    expect(source, isNot(contains('KefeColorTokens.')));
    expect(source, isNot(contains('Color(0xFFAA9CFF)')));
    expect(source, isNot(contains('Color(0xFF8E7CFF)')));
    expect(source, isNot(contains('locale.languageCode')));
  });

  test(
    'Product Preview localizes Perspective display without mutating raw fixture data',
    () async {
      final repository = PreviewDecisionRepository();
      final sessionId = await repository.startSession(
        PreviewDecisionRepository.caseId,
      );
      final raw = await repository.fetchPerspectives(sessionId);
      final rawFirstBody = raw.cards.first.body;
      final rawFirstProvenance = raw.cards.first.provenanceLabel;
      final rawMethodology = raw.methodology.provenanceNote;

      const localizer = PreviewContentLocalizer();
      final body = localizer.text(
        namespace: KefeContentNamespace.perspectiveBody,
        id: raw.cards.first.id,
        locale: const Locale('en', 'US'),
        fallback: rawFirstBody,
      );
      final provenance = localizer.text(
        namespace: KefeContentNamespace.perspectiveProvenance,
        id: raw.cards.first.id,
        locale: const Locale('en', 'US'),
        fallback: rawFirstProvenance,
      );
      final methodology = localizer.text(
        namespace: KefeContentNamespace.perspectiveMethodologyProvenance,
        id: raw.caseVersionId,
        locale: const Locale('en', 'US'),
        fallback: rawMethodology,
      );
      final sampleKind = localizer.text(
        namespace: KefeContentNamespace.perspectiveSampleKind,
        id: raw.methodology.sampleKind,
        locale: const Locale('en', 'US'),
        fallback: raw.methodology.sampleKind,
      );

      expect(
        rawFirstBody,
        'Bu yaklaşım, kararın doğrudan etkilenen kişilere vereceği pratik sonucu öncelemeyi savunuyor.',
      );
      expect(
        body,
        'This perspective prioritizes the practical effect the decision may have on the people directly affected.',
      );
      expect(raw.cards.first.body, rawFirstBody);
      expect(raw.cards.first.provenanceLabel, rawFirstProvenance);
      expect(raw.methodology.provenanceNote, rawMethodology);
      expect(provenance, 'KEFE Preview · Editorial example');
      expect(methodology, 'Fixed editorial demo perspectives for Product Preview.');
      expect(sampleKind, 'Curated fallback');
      expect(
        localizer.text(
          namespace: KefeContentNamespace.perspectiveBody,
          id: raw.cards.first.id,
          locale: const Locale('tr', 'TR'),
          fallback: rawFirstBody,
        ),
        rawFirstBody,
      );
    },
  );
}
