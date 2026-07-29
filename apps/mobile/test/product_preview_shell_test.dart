import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview_app.dart';
import 'package:kefe_mobile/core/design/product_preview_visual_mode.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';
import 'package:kefe_mobile/features/media_presentation/application/case_media_provider.dart';
import 'package:kefe_mobile/features/media_presentation/data/preview_case_media_repository.dart';
import 'package:kefe_mobile/features/progress/application/progress_controller.dart';
import 'package:kefe_mobile/features/progress/data/preview_progress_repository.dart';

void main() {
  test('preview catalog contains multiple domains and cases', () async {
    final repository = PreviewDecisionRepository();
    final cases = await repository.fetchExploreCases();

    expect(cases.length, greaterThanOrEqualTo(5));
    expect(
      cases.map((item) => item.domain).toSet().length,
      greaterThanOrEqualTo(5),
    );
  });

  test('production entrypoint never imports preview-only repositories', () {
    final productionMain = File('lib/main.dart').readAsStringSync();
    expect(productionMain, isNot(contains('preview_case_media_repository')));
    expect(productionMain, isNot(contains('PreviewCaseMediaRepository')));
    expect(productionMain, isNot(contains('preview_progress_repository')));
    expect(productionMain, isNot(contains('PreviewProgressRepository')));
  });

  testWidgets(
    'Product Preview opens on rich Explore with media and navigates to Radar',
    (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(
              PreviewDecisionRepository(),
            ),
            caseMediaRepositoryProvider.overrideWithValue(
              const PreviewCaseMediaRepository(),
            ),
            productPreviewVisualModeProvider.overrideWithValue(true),
          ],
          child: const ProductPreviewApp(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Bugün dünya\nneyi tartıyor?'), findsOneWidget);
      expect(find.text('Radar'), findsOneWidget);
      expect(
        find.byKey(
          const ValueKey(
            'case-media-EXPLORE_CARD-22222222-2222-4222-8222-222222222222',
          ),
        ),
        findsOneWidget,
      );

      await tester.scrollUntilVisible(
        find.text('Trend tartımlar'),
        260,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.pumpAndSettle();
      expect(find.text('Trend tartımlar'), findsOneWidget);

      await tester.tap(find.text('Radar'));
      await tester.pumpAndSettle();

      expect(find.text('Dünya şu an\nneyi tartışıyor?'), findsOneWidget);
      expect(find.textContaining('Canlı trend verisi değil'), findsOneWidget);
    },
  );

  testWidgets(
    'Product Preview media keeps the Case hero and Commit semantics intact',
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
            caseMediaRepositoryProvider.overrideWithValue(
              const PreviewCaseMediaRepository(),
            ),
            productPreviewVisualModeProvider.overrideWithValue(true),
          ],
          child: const ProductPreviewApp(),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(
        find.byKey(
          const ValueKey(
            'explore-case-11111111-1111-4111-8111-111111111111',
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
      expect(find.text('KARAR YOLCULUĞU'), findsOneWidget);
      expect(
        find.byKey(
          const ValueKey(
            'case-media-CASE_HERO-22222222-2222-4222-8222-222222222222',
          ),
        ),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('reveal-card')), findsNothing);

      await tester.scrollUntilVisible(
        find.text('Olay özeti'),
        260,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.pumpAndSettle();
      expect(find.text('Olay özeti'), findsOneWidget);

      await tester.scrollUntilVisible(
        find.byKey(const ValueKey('kefe-balance-visual')),
        320,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.pumpAndSettle();

      expect(find.text('KARAR'), findsOneWidget);
      expect(find.byKey(const ValueKey('kefe-balance-visual')), findsOneWidget);

      final option = find.byKey(
        const ValueKey('option-Öncelikli ihtiyacı olana'),
      );
      await tester.tap(option);
      await tester.pumpAndSettle();

      await tester.scrollUntilVisible(
        find.byKey(const ValueKey('reason-card')),
        260,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.pumpAndSettle();
      expect(find.text('GEREKÇELER'), findsOneWidget);

      await tester.scrollUntilVisible(
        find.byKey(const ValueKey('commit-button')),
        260,
        scrollable: find.byType(Scrollable).last,
      );
      final commit = find.byKey(const ValueKey('commit-button'));
      await tester.tap(commit);
      await tester.pumpAndSettle();

      final container = ProviderScope.containerOf(
        tester.element(find.byType(ProductPreviewApp)),
        listen: false,
      );
      expect(container.read(decisionControllerProvider).reveal, isNotNull);
    },
  );

  testWidgets(
    'My KEFE is repository-driven descriptive journey data',
    (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(
              PreviewDecisionRepository(),
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

      await tester.tap(find.text('Profil'));
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('my-kefe-journey')), findsOneWidget);
      expect(
        find.byKey(const ValueKey('my-kefe-preview-notice')),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('my-kefe-weigh-count')), findsOneWidget);
      expect(find.byKey(const ValueKey('my-kefe-update-count')), findsOneWidget);
      expect(
        find.byKey(const ValueKey('my-kefe-reflection-count')),
        findsOneWidget,
      );

      await tester.scrollUntilVisible(
        find.byKey(const ValueKey('my-kefe-domain-activity')),
        280,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.pumpAndSettle();
      expect(
        find.byKey(const ValueKey('my-kefe-domain-activity')),
        findsOneWidget,
      );

      await tester.scrollUntilVisible(
        find.byKey(const ValueKey('my-kefe-recent-journeys')),
        300,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.pumpAndSettle();
      expect(
        find.text(
          'Çocuklar uçakta ebeveynleriyle ücretsiz yan yana oturmalı mı?',
        ),
        findsOneWidget,
      );
      expect(find.text('1 yeniden tartım'), findsWidgets);
      expect(find.text('Yansıma tamamlandı'), findsWidgets);

      await tester.scrollUntilVisible(
        find.byKey(const ValueKey('my-kefe-no-inference-note')),
        320,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.pumpAndSettle();
      expect(
        find.byKey(const ValueKey('my-kefe-no-inference-note')),
        findsOneWidget,
      );
      expect(find.textContaining('neden-sonuç çıkarımı yapmaz'), findsOneWidget);
      expect(find.textContaining('empatin yüksek'), findsNothing);
    },
  );
}
