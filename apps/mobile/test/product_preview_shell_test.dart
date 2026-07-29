import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview_app.dart';
import 'package:kefe_mobile/core/design/product_preview_visual_mode.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';

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

  testWidgets(
    'Product Preview opens on rich Explore and navigates to Radar',
    (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(
              PreviewDecisionRepository(),
            ),
            productPreviewVisualModeProvider.overrideWithValue(true),
          ],
          child: const ProductPreviewApp(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Bugün dünya\nneyi tartıyor?'), findsOneWidget);
      expect(find.text('Trend tartımlar'), findsOneWidget);
      expect(find.text('Radar'), findsOneWidget);

      await tester.tap(find.text('Radar'));
      await tester.pumpAndSettle();

      expect(find.text('Dünya şu an\nneyi tartışıyor?'), findsOneWidget);
      expect(find.textContaining('Canlı trend verisi değil'), findsOneWidget);
    },
  );

  testWidgets(
    'Product Preview Case shows hero hierarchy, signature balance and commit-gated result',
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
      expect(find.text('Olay özeti'), findsOneWidget);
      expect(find.byKey(const ValueKey('reveal-card')), findsNothing);

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

      await tester.scrollUntilVisible(
        find.byKey(const ValueKey('reveal-card')),
        300,
        scrollable: find.byType(Scrollable).last,
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('reveal-card')), findsOneWidget);
      expect(
        find.byKey(const ValueKey('reveal-personal-decision')),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('reveal-gap-insight')), findsOneWidget);
      expect(find.text('KEFE UÇURUMU'), findsOneWidget);
      expect(find.byKey(const ValueKey('perspective-section')), findsOneWidget);
    },
  );
}
