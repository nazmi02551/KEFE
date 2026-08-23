import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:kefe_mobile/app/product_preview_app.dart';
import 'package:kefe_mobile/core/design/product_preview_visual_mode.dart';
import 'package:kefe_mobile/core/preferences/app_preferences.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';
import 'package:kefe_mobile/features/media_presentation/application/case_media_provider.dart';
import 'package:kefe_mobile/features/media_presentation/data/preview_case_media_repository.dart';
import 'package:kefe_mobile/features/privacy/application/privacy_controller.dart';
import 'package:kefe_mobile/features/privacy/data/preview_privacy_repository.dart';
import 'package:kefe_mobile/features/progress/application/progress_controller.dart';
import 'package:kefe_mobile/features/progress/data/preview_progress_repository.dart';
import 'package:kefe_mobile/features/saved_cases/application/saved_cases_controller.dart';
import 'package:kefe_mobile/features/saved_cases/data/saved_case_store.dart';
import 'package:kefe_mobile/features/sharing/application/share_controller.dart';
import 'package:kefe_mobile/features/sharing/data/preview_share_repository.dart';

ProviderScope _previewScope({
  required MemoryAppPreferencesStore preferences,
  MemorySavedCaseStore? savedCases,
  bool privacy = false,
  bool sharing = false,
}) {
  return ProviderScope(
    overrides: [
      appPreferencesStoreProvider.overrideWithValue(preferences),
      decisionRepositoryProvider.overrideWithValue(PreviewDecisionRepository()),
      decisionDraftStoreProvider.overrideWithValue(MemoryDecisionDraftStore()),
      caseMediaRepositoryProvider.overrideWithValue(
        const PreviewCaseMediaRepository(),
      ),
      progressRepositoryProvider.overrideWithValue(PreviewProgressRepository()),
      savedCaseStoreProvider.overrideWithValue(
        savedCases ?? MemorySavedCaseStore(),
      ),
      productPreviewVisualModeProvider.overrideWithValue(true),
      if (privacy) ...[
        privacyExperienceEnabledProvider.overrideWithValue(true),
        privacyRepositoryProvider.overrideWithValue(PreviewPrivacyRepository()),
      ],
      if (sharing) ...[
        shareExperienceEnabledProvider.overrideWithValue(true),
        shareRepositoryProvider.overrideWithValue(PreviewShareRepository()),
      ],
    ],
    child: const ProductPreviewApp(),
  );
}

Future<void> _openSettings(WidgetTester tester) async {
  await tester.tap(find.text('My KEFE'));
  await tester.pumpAndSettle();
  await tester.tap(find.byKey(const ValueKey('open-preview-settings')));
  await tester.pumpAndSettle();
}

Future<void> _scrollTo(WidgetTester tester, Finder finder) async {
  await tester.scrollUntilVisible(
    finder,
    300,
    scrollable: find.byType(Scrollable).last,
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets(
    'locale and theme switch persist through the shared preference store',
    (tester) async {
      final preferences = MemoryAppPreferencesStore(
        const AppPreferencesState(
          locale: AppLocalePreference.tr,
          theme: AppThemePreference.system,
          loaded: true,
        ),
      );

      await tester.pumpWidget(
        _previewScope(preferences: preferences, privacy: true),
      );
      await tester.pumpAndSettle();

      expect(find.text('Keşfet'), findsOneWidget);
      await _openSettings(tester);

      await tester.tap(find.text('English'));
      await tester.pumpAndSettle();
      expect(preferences.value.locale, AppLocalePreference.en);
      expect(find.text('Settings'), findsOneWidget);

      await tester.tap(find.text('Dark'));
      await tester.pumpAndSettle();
      expect(preferences.value.theme, AppThemePreference.dark);
      expect(
        Theme.of(tester.element(find.byType(Scaffold).first)).brightness,
        Brightness.dark,
      );

      final privacyEntry = find.byKey(
        const ValueKey('settings-privacy-entry'),
      );
      await _scrollTo(tester, privacyEntry);
      await tester.tap(privacyEntry);
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('privacy-controls')), findsOneWidget);
    },
  );

  testWidgets(
    'Explore save continuity and Weigh Commit Reveal survive together',
    (tester) async {
      final preferences = MemoryAppPreferencesStore(
        const AppPreferencesState(
          locale: AppLocalePreference.tr,
          theme: AppThemePreference.light,
          loaded: true,
        ),
      );
      final savedCases = MemorySavedCaseStore();
      const caseId = PreviewDecisionRepository.caseId;

      await tester.pumpWidget(
        _previewScope(preferences: preferences, savedCases: savedCases),
      );
      await tester.pumpAndSettle();

      final save = find.byKey(const ValueKey('save-case-$caseId'));
      await tester.ensureVisible(save);
      await tester.tap(save);
      await tester.pumpAndSettle();

      await tester.tap(find.text('Aktivite'));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('saved-cases-section')), findsOneWidget);
      final savedCase = find.byKey(const ValueKey('open-saved-case-$caseId'));
      expect(savedCase, findsOneWidget);
      await tester.ensureVisible(savedCase);
      await tester.tap(savedCase);
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('reveal-card')), findsNothing);
      final option = find.byKey(
        const ValueKey('option-Öncelikli ihtiyacı olana'),
      );
      await _scrollTo(tester, option);
      await tester.tap(option);
      await tester.pumpAndSettle();

      final commit = find.byKey(const ValueKey('commit-button'));
      await _scrollTo(tester, commit);
      await tester.tap(commit);
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('reveal-card')), findsOneWidget);
    },
  );

  testWidgets(
    'shared Case deep link remains Blind First before receiver Commit',
    (tester) async {
      final preferences = MemoryAppPreferencesStore(
        const AppPreferencesState(
          locale: AppLocalePreference.en,
          theme: AppThemePreference.system,
          loaded: true,
        ),
      );

      await tester.pumpWidget(
        _previewScope(preferences: preferences, sharing: true),
      );
      await tester.pumpAndSettle();

      final routerContext = tester.element(
        find.byKey(const ValueKey('primary-navigation')),
      );
      GoRouter.of(routerContext).go('/share/inbound-phone-acceptance');
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('public-share-weigh')), findsOneWidget);
      expect(find.byKey(const ValueKey('reveal-card')), findsNothing);
      expect(find.text('A KEFE case was shared'), findsOneWidget);

      await tester.tap(find.byKey(const ValueKey('public-share-weigh')));
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
      expect(find.byKey(const ValueKey('reveal-card')), findsNothing);
    },
  );
}
