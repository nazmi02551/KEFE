import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';

void useTurkishLocale(WidgetTester tester) {
  tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);
}

void main() {
  testWidgets('experience hub surfaces real Sports CALL and truthful Atlas state', (
    tester,
  ) async {
    useTurkishLocale(tester);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(PreviewDecisionRepository()),
          decisionDraftStoreProvider.overrideWithValue(MemoryDecisionDraftStore()),
        ],
        child: const KefeApp(initialLocation: '/experiences'),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('experience-hub')), findsOneWidget);
    expect(find.byKey(const ValueKey('experience-sports-call')), findsOneWidget);
    expect(find.text('Bu pozisyonda penaltı kararı doğru muydu?'), findsOneWidget);

    final atlas = find.byKey(const ValueKey('experience-atlas'));
    expect(atlas, findsOneWidget);
    expect(
      find.descendant(of: atlas, matching: find.byType(FilledButton)),
      findsNothing,
    );
    expect(find.byKey(const ValueKey('experience-truth-note')), findsOneWidget);
  });

  testWidgets('Sports CALL enters the canonical Case journey', (tester) async {
    useTurkishLocale(tester);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(PreviewDecisionRepository()),
          decisionDraftStoreProvider.overrideWithValue(MemoryDecisionDraftStore()),
        ],
        child: const KefeApp(initialLocation: '/experiences'),
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.text('Kararını ver'));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
    expect(find.text('Bu pozisyonda penaltı kararı doğru muydu?'), findsOneWidget);
    expect(find.byKey(const ValueKey('commit-button')), findsOneWidget);
  });
}
