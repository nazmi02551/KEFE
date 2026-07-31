import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview_app.dart';
import 'package:kefe_mobile/core/design/product_preview_visual_mode.dart';
import 'package:kefe_mobile/core/preferences/app_preferences.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/application/reflection_completion_provider.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/preview_journey_decision_repository.dart';
import 'package:kefe_mobile/features/decision/data/reflection_completion_store.dart';

const airlineCaseId = '11111111-1111-4111-8111-111111111116';

Future<void> scrollTo(
  WidgetTester tester,
  Finder finder, {
  double delta = 300,
}) async {
  await tester.scrollUntilVisible(
    finder,
    delta,
    scrollable: find.byType(Scrollable).last,
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'Product Preview executes principle, counterview, revision and Reflection journey',
    (tester) async {
      final repository = PreviewJourneyDecisionRepository();
      final preferences = MemoryAppPreferencesStore(
        const AppPreferencesState(
          locale: AppLocalePreference.tr,
          theme: AppThemePreference.system,
          loaded: true,
        ),
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            appPreferencesStoreProvider.overrideWithValue(preferences),
            decisionRepositoryProvider.overrideWithValue(repository),
            decisionDraftStoreProvider.overrideWithValue(
              MemoryDecisionDraftStore(),
            ),
            reflectionCompletionStoreProvider.overrideWithValue(
              MemoryReflectionCompletionStore(),
            ),
            productPreviewVisualModeProvider.overrideWithValue(true),
          ],
          child: const ProductPreviewApp(),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Tartım'));
      await tester.pumpAndSettle();

      final airlineCase = find.byKey(
        const ValueKey('weigh-case-$airlineCaseId'),
      );
      await scrollTo(tester, airlineCase);
      await tester.tap(airlineCase);
      await tester.pumpAndSettle();

      expect(find.text('KARAR YOLCULUĞU'), findsOneWidget);
      expect(find.byKey(const ValueKey('reveal-card')), findsNothing);

      final signatureBalance = find.byKey(
        const ValueKey('signature-balance-hero'),
      );
      await scrollTo(tester, signatureBalance);
      expect(signatureBalance, findsOneWidget);
      expect(find.byKey(const ValueKey('balance-state-neutral')), findsOneWidget);
      expect(find.byKey(const ValueKey('reveal-card')), findsNothing);

      final firstYes = find.byKey(const ValueKey('option-Evet'));
      await scrollTo(tester, firstYes);
      await tester.tap(firstYes);
      await tester.pump();
      expect(
        find.byKey(const ValueKey('balance-state-leftSelected')),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('reveal-card')), findsNothing);

      final firstCommit = find.byKey(const ValueKey('commit-button'));
      await scrollTo(tester, firstCommit);
      await tester.tap(firstCommit);
      await tester.pumpAndSettle();

      expect(find.text('Karşı görüş'), findsOneWidget);
      expect(find.byKey(const ValueKey('reveal-card')), findsNothing);

      final finalNo = find.byKey(const ValueKey('option-Hayır'));
      await scrollTo(tester, finalNo);
      await tester.tap(finalNo);
      await tester.pump();

      final finalCommit = find.byKey(const ValueKey('commit-button'));
      await scrollTo(tester, finalCommit);
      await tester.tap(finalCommit);
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('reveal-card')), findsNothing);

      final reflection = find.byKey(
        const ValueKey('reflection-step-REFLECTION'),
      );
      await scrollTo(tester, reflection);

      expect(reflection, findsOneWidget);
      expect(
        find.byKey(const ValueKey('reflection-journey-graphic')),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('reflection-summary')), findsOneWidget);
      expect(
        find.byKey(const ValueKey('reflection-intervention-summary')),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey('reflection-non-causal-note')),
        findsOneWidget,
      );
    },
  );
}
