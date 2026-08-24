import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

class _TodayPreviewDecisionRepository extends PreviewDecisionRepository {
  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async {
    final cases = await super.fetchExploreCases(limit: limit);
    return cases
        .map(
          (item) => DecisionCaseSummary(
            id: item.id,
            versionId: item.versionId,
            title: item.title,
            summary: item.summary,
            format: item.format,
            domain: item.domain,
            risk: item.risk,
            isRealEvent: item.format == 'CIVIC',
          ),
        )
        .toList(growable: false);
  }
}

void useTurkishLocale(WidgetTester tester) {
  tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);
}

void main() {
  testWidgets(
    'experience hub surfaces Dilemma, truthful Today empty state, community, Sports CALL and Atlas state',
    (tester) async {
      useTurkishLocale(tester);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(
              PreviewDecisionRepository(),
            ),
            decisionDraftStoreProvider.overrideWithValue(
              MemoryDecisionDraftStore(),
            ),
          ],
          child: const KefeApp(initialLocation: '/experiences'),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('experience-hub')), findsOneWidget);
      expect(find.byKey(const ValueKey('experience-dilemma')), findsOneWidget);
      expect(find.text('İkilemler'), findsOneWidget);
      expect(find.text('Son koltuk kime verilmeli?'), findsWidgets);

      final todayEmpty = find.byKey(
        const ValueKey('experience-today-empty'),
      );
      expect(todayEmpty, findsOneWidget);
      expect(find.text('KEFE Today'), findsOneWidget);
      expect(
        find.descendant(of: todayEmpty, matching: find.byType(FilledButton)),
        findsNothing,
      );

      expect(
        find.byKey(const ValueKey('experience-community')),
        findsOneWidget,
      );
      expect(find.text('Birlikte tart'), findsOneWidget);
      expect(find.text('Önce kendi kararımı ver'), findsOneWidget);
      expect(
        find.byKey(const ValueKey('experience-sports-call')),
        findsOneWidget,
      );
      expect(
        find.text('Bu pozisyonda penaltı kararı doğru muydu?'),
        findsOneWidget,
      );

      final atlas = find.byKey(const ValueKey('experience-atlas'));
      expect(atlas, findsOneWidget);
      expect(
        find.descendant(of: atlas, matching: find.byType(FilledButton)),
        findsNothing,
      );
      expect(
        find.byKey(const ValueKey('experience-truth-note')),
        findsOneWidget,
      );
    },
  );

  testWidgets('Dilemma enters the canonical blind-first Case journey', (
    tester,
  ) async {
    useTurkishLocale(tester);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(
            PreviewDecisionRepository(),
          ),
          decisionDraftStoreProvider.overrideWithValue(
            MemoryDecisionDraftStore(),
          ),
        ],
        child: const KefeApp(initialLocation: '/experiences'),
      ),
    );
    await tester.pumpAndSettle();

    final action = find.text('Bir ikilemi tart');
    await tester.ensureVisible(action);
    await tester.tap(action);
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
    expect(find.text('Son koltuk kime verilmeli?'), findsOneWidget);
    expect(find.byKey(const ValueKey('commit-button')), findsOneWidget);
    expect(find.byKey(const ValueKey('post-commit-journey')), findsNothing);
  });

  testWidgets(
    'Today enters canonical Case journey only for explicitly real-event metadata',
    (tester) async {
      useTurkishLocale(tester);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(
              _TodayPreviewDecisionRepository(),
            ),
            decisionDraftStoreProvider.overrideWithValue(
              MemoryDecisionDraftStore(),
            ),
          ],
          child: const KefeApp(initialLocation: '/experiences'),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('experience-today')), findsOneWidget);
      expect(
        find.text('Kamu sözleşmeleri varsayılan olarak herkese açık olmalı mı?'),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey('experience-today-empty')),
        findsNothing,
      );

      final action = find.text('Gerçek olay vakasını tart');
      await tester.ensureVisible(action);
      await tester.tap(action);
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
      expect(
        find.text('Kamu sözleşmeleri varsayılan olarak herkese açık olmalı mı?'),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('commit-button')), findsOneWidget);
      expect(find.byKey(const ValueKey('post-commit-journey')), findsNothing);
    },
  );

  testWidgets(
    'community entry starts with the canonical blind-first Case journey',
    (tester) async {
      useTurkishLocale(tester);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(
              PreviewDecisionRepository(),
            ),
            decisionDraftStoreProvider.overrideWithValue(
              MemoryDecisionDraftStore(),
            ),
          ],
          child: const KefeApp(initialLocation: '/experiences'),
        ),
      );
      await tester.pumpAndSettle();

      final action = find.text('Önce kendi kararımı ver');
      await tester.ensureVisible(action);
      await tester.tap(action);
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
      expect(find.byKey(const ValueKey('commit-button')), findsOneWidget);
      expect(find.byKey(const ValueKey('post-commit-journey')), findsNothing);
      expect(find.byKey(const ValueKey('consensus-section')), findsNothing);
    },
  );

  testWidgets('Sports CALL enters the canonical Case journey', (tester) async {
    useTurkishLocale(tester);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(
            PreviewDecisionRepository(),
          ),
          decisionDraftStoreProvider.overrideWithValue(
            MemoryDecisionDraftStore(),
          ),
        ],
        child: const KefeApp(initialLocation: '/experiences'),
      ),
    );
    await tester.pumpAndSettle();

    final action = find.text('Kararını ver');
    await tester.ensureVisible(action);
    await tester.tap(action);
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
    expect(
      find.text('Bu pozisyonda penaltı kararı doğru muydu?'),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('commit-button')), findsOneWidget);
  });
}
