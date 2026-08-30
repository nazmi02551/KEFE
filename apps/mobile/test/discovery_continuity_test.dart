import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview_app.dart';
import 'package:kefe_mobile/core/design/product_preview_visual_mode.dart';
import 'package:kefe_mobile/core/preferences/app_preferences.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';
import 'package:kefe_mobile/features/media_presentation/application/case_media_provider.dart';
import 'package:kefe_mobile/features/media_presentation/data/preview_case_media_repository.dart';
import 'package:kefe_mobile/features/progress/application/progress_controller.dart';
import 'package:kefe_mobile/features/progress/data/preview_progress_repository.dart';
import 'package:kefe_mobile/features/saved_cases/application/saved_cases_controller.dart';
import 'package:kefe_mobile/features/saved_cases/data/saved_case_store.dart';

const caseId = '11111111-1111-4111-8111-111111111111';

MemoryAppPreferencesStore _turkishPreferences() {
  return MemoryAppPreferencesStore(
    const AppPreferencesState(
      locale: AppLocalePreference.tr,
      theme: AppThemePreference.system,
      loaded: true,
    ),
  );
}

void main() {
  testWidgets('searches, filters, saves and continues a Case from Activity', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          appPreferencesStoreProvider.overrideWithValue(_turkishPreferences()),
          decisionRepositoryProvider.overrideWithValue(
            PreviewDecisionRepository(),
          ),
          decisionDraftStoreProvider.overrideWithValue(
            MemoryDecisionDraftStore(),
          ),
          caseMediaRepositoryProvider.overrideWithValue(
            const PreviewCaseMediaRepository(),
          ),
          progressRepositoryProvider.overrideWithValue(
            PreviewProgressRepository(),
          ),
          savedCaseStoreProvider.overrideWithValue(MemorySavedCaseStore()),
          productPreviewVisualModeProvider.overrideWithValue(true),
        ],
        child: const ProductPreviewApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('explore-search-field')), findsOneWidget);
    expect(find.byKey(const ValueKey('domain-filter-all')), findsOneWidget);

    await tester.enterText(
      find.byKey(const ValueKey('explore-search-field')),
      'kamusal yasam seffaflik',
    );
    await tester.pumpAndSettle();

    expect(
      find.byKey(
        const ValueKey('explore-case-11111111-1111-4111-8111-111111111114'),
      ),
      findsOneWidget,
    );
    expect(find.text('1 vaka bulundu'), findsOneWidget);

    await tester.enterText(
      find.byKey(const ValueKey('explore-search-field')),
      'son koltuk',
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('explore-case-$caseId')), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('save-case-$caseId')));
    await tester.pumpAndSettle();

    final container = ProviderScope.containerOf(
      tester.element(find.byType(ProductPreviewApp)),
      listen: false,
    );
    expect(
      container.read(savedCasesControllerProvider).contains(caseId),
      isTrue,
    );

    await tester.tap(find.byKey(const ValueKey('saved-only-filter')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('explore-case-$caseId')), findsOneWidget);

    await tester.enterText(
      find.byKey(const ValueKey('explore-search-field')),
      'eşleşmeyen ifade',
    );
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('explore-no-results')), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('clear-explore-filters')));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Aktivite'));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('activity-screen')), findsOneWidget);
    expect(find.byKey(const ValueKey('saved-cases-section')), findsOneWidget);
    expect(find.text('Son koltuk kime verilmeli?'), findsWidgets);
    expect(
      find.byKey(const ValueKey('open-saved-case-$caseId')),
      findsOneWidget,
    );

    await tester.tap(find.byKey(const ValueKey('open-saved-case-$caseId')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
  });
}
