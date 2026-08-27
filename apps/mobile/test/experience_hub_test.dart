import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/core/preferences/app_preferences.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';

void useTurkishLocale(WidgetTester tester) {
  tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);
}

MemoryAppPreferencesStore turkishPreferences() {
  return MemoryAppPreferencesStore(
    const AppPreferencesState(
      locale: AppLocalePreference.tr,
      theme: AppThemePreference.system,
      loaded: true,
    ),
  );
}

Finder experienceScrollable() => find.descendant(
  of: find.byKey(const ValueKey('experience-hub')),
  matching: find.byType(Scrollable),
);

Future<void> revealExperience(WidgetTester tester, Finder target) async {
  // The hub lazily builds off-screen cards, so assertions must reveal their target.
  await tester.scrollUntilVisible(
    target,
    280,
    scrollable: experienceScrollable(),
  );
  await tester.pumpAndSettle();
}

Future<void> revealCaseControl(WidgetTester tester, Finder target) async {
  await tester.scrollUntilVisible(
    target,
    280,
    scrollable: find.byType(Scrollable).last,
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'experience hub surfaces Dilemma, community, Sports CALL and truthful Atlas state',
    (tester) async {
      useTurkishLocale(tester);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            appPreferencesStoreProvider.overrideWithValue(turkishPreferences()),
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

      final dilemma = find.byKey(const ValueKey('experience-dilemma'));
      await revealExperience(tester, dilemma);
      expect(dilemma, findsOneWidget);
      expect(find.text('İkilemler'), findsOneWidget);
      expect(find.textContaining('Son koltuk kime verilmeli?'), findsWidgets);

      final community = find.byKey(const ValueKey('experience-community'));
      await revealExperience(tester, community);
      expect(community, findsOneWidget);
      expect(find.text('Birlikte tart'), findsOneWidget);
      expect(find.text('Önce kendi kararımı ver'), findsOneWidget);

      final sports = find.byKey(const ValueKey('experience-sports-call'));
      await revealExperience(tester, sports);
      expect(sports, findsOneWidget);
      expect(
        find.descendant(
          of: sports,
          matching: find.textContaining(
            'Bu pozisyonda penaltı kararı doğru muydu?',
          ),
        ),
        findsOneWidget,
      );

      final atlas = find.byKey(const ValueKey('experience-atlas'));
      await revealExperience(tester, atlas);
      expect(atlas, findsOneWidget);
      expect(
        find.descendant(of: atlas, matching: find.byType(FilledButton)),
        findsNothing,
      );

      final truth = find.byKey(const ValueKey('experience-truth-note'));
      await revealExperience(tester, truth);
      expect(truth, findsOneWidget);
    },
  );

  testWidgets('Dilemma enters the canonical blind-first Case journey', (
    tester,
  ) async {
    useTurkishLocale(tester);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          appPreferencesStoreProvider.overrideWithValue(turkishPreferences()),
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

    final dilemma = find.byKey(const ValueKey('experience-dilemma'));
    await revealExperience(tester, dilemma);
    final action = find.descendant(
      of: dilemma,
      matching: find.byType(FilledButton),
    );
    expect(action, findsOneWidget);
    await tester.tap(action);
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
    expect(find.text('Son koltuk kime verilmeli?'), findsOneWidget);
    await revealCaseControl(
      tester,
      find.byKey(const ValueKey('commit-button')),
    );
    expect(find.byKey(const ValueKey('commit-button')), findsOneWidget);
    expect(find.byKey(const ValueKey('post-commit-journey')), findsNothing);
  });

  testWidgets(
    'community entry starts with the canonical blind-first Case journey',
    (tester) async {
      useTurkishLocale(tester);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            appPreferencesStoreProvider.overrideWithValue(turkishPreferences()),
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

      final community = find.byKey(const ValueKey('experience-community'));
      await revealExperience(tester, community);
      final action = find.descendant(
        of: community,
        matching: find.byType(FilledButton),
      );
      expect(action, findsOneWidget);
      await tester.tap(action);
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
      await revealCaseControl(
        tester,
        find.byKey(const ValueKey('commit-button')),
      );
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
          appPreferencesStoreProvider.overrideWithValue(turkishPreferences()),
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

    final sports = find.byKey(const ValueKey('experience-sports-call'));
    await revealExperience(tester, sports);
    final action = find.descendant(
      of: sports,
      matching: find.byType(FilledButton),
    );
    expect(action, findsOneWidget);
    await tester.tap(action);
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
    expect(
      find.text('Bu pozisyonda penaltı kararı doğru muydu?'),
      findsOneWidget,
    );
    await revealCaseControl(
      tester,
      find.byKey(const ValueKey('commit-button')),
    );
    expect(find.byKey(const ValueKey('commit-button')), findsOneWidget);
  });
}
