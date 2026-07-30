import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview_app.dart';
import 'package:kefe_mobile/core/design/product_preview_visual_mode.dart';
import 'package:kefe_mobile/features/consensus/application/consensus_controller.dart';
import 'package:kefe_mobile/features/consensus/data/preview_consensus_repository.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';
import 'package:kefe_mobile/features/media_presentation/application/case_media_provider.dart';
import 'package:kefe_mobile/features/media_presentation/data/preview_case_media_repository.dart';
import 'package:kefe_mobile/features/progress/application/progress_controller.dart';
import 'package:kefe_mobile/features/progress/data/preview_progress_repository.dart';

void main() {
  test(
    'production enables Consensus without importing preview Consensus data',
    () {
      final productionMain = File('lib/main.dart').readAsStringSync();
      expect(
        productionMain,
        contains('consensusExperienceEnabledProvider.overrideWithValue(true)'),
      );
      expect(productionMain, isNot(contains('preview_consensus_repository')));
      expect(productionMain, isNot(contains('PreviewConsensusRepository')));
    },
  );

  testWidgets(
    'post-commit Consensus hides distribution until participation then reveals EXPOSED WE data',
    (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(
              PreviewDecisionRepository(),
            ),
            decisionDraftStoreProvider.overrideWithValue(
              MemoryDecisionDraftStore(),
            ),
            consensusExperienceEnabledProvider.overrideWithValue(true),
            consensusRepositoryProvider.overrideWithValue(
              PreviewConsensusRepository(),
            ),
            caseMediaRepositoryProvider.overrideWithValue(
              const PreviewCaseMediaRepository(),
            ),
            progressRepositoryProvider.overrideWithValue(
              PreviewProgressRepository(),
            ),
            productPreviewVisualModeProvider.overrideWithValue(true),
          ],
          child: const ProductPreviewApp(),
        ),
      );
      await tester.pumpAndSettle();

      final caseCard = find.byKey(
        const ValueKey('explore-case-11111111-1111-4111-8111-111111111111'),
      );
      await tester.scrollUntilVisible(
        caseCard,
        280,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.ensureVisible(caseCard);
      await tester.pumpAndSettle();
      await tester.tap(caseCard);
      await tester.pumpAndSettle();

      final option = find.byKey(
        const ValueKey('option-Öncelikli ihtiyacı olana'),
      );
      await tester.scrollUntilVisible(
        option,
        320,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.ensureVisible(option);
      await tester.pumpAndSettle();
      await tester.tap(option);
      await tester.pumpAndSettle();

      final commit = find.byKey(const ValueKey('commit-button'));
      await tester.scrollUntilVisible(
        commit,
        320,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.ensureVisible(commit);
      await tester.pumpAndSettle();
      expect(tester.widget<FilledButton>(commit).onPressed, isNotNull);
      await tester.tap(commit);
      await tester.pumpAndSettle();

      final consensus = find.byKey(const ValueKey('consensus-section'));
      await tester.scrollUntilVisible(
        consensus,
        360,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.ensureVisible(consensus);
      await tester.pumpAndSettle();

      expect(consensus, findsOneWidget);
      expect(find.text('Konsensüs Kartı'), findsOneWidget);
      expect(find.textContaining('EXPOSED'), findsWidgets);
      expect(
        find.byKey(const ValueKey('consensus-methodology-note')),
        findsNothing,
      );

      final stance = find.byKey(const ValueKey('consensus-stance-AGREE'));
      await tester.ensureVisible(stance);
      await tester.pumpAndSettle();
      await tester.tap(stance);
      await tester.pump();
      final reason = find.byKey(const ValueKey('consensus-reason-FAIRNESS'));
      await tester.ensureVisible(reason);
      await tester.pumpAndSettle();
      await tester.tap(reason);
      await tester.pump();

      final submit = find.byKey(const ValueKey('consensus-submit'));
      await tester.ensureVisible(submit);
      await tester.pumpAndSettle();
      expect(tester.widget<FilledButton>(submit).onPressed, isNotNull);
      await tester.tap(submit);
      await tester.pumpAndSettle();

      expect(
        find.byKey(const ValueKey('consensus-methodology-note')),
        findsOneWidget,
      );
      expect(find.text('KONSENSÜS DAĞILIMI'), findsOneWidget);
      expect(find.textContaining('Signal değildir'), findsOneWidget);
      expect(find.textContaining('n=413'), findsOneWidget);
    },
  );
}
