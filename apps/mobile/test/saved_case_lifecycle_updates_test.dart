import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:kefe_mobile/app/product_preview/preview_content_localizer.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_content_localizer.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/saved_cases/application/saved_cases_controller.dart';
import 'package:kefe_mobile/features/saved_cases/data/saved_case_store.dart';
import 'package:kefe_mobile/features/saved_cases/domain/saved_case.dart';
import 'package:kefe_mobile/features/saved_cases/presentation/saved_cases_section.dart';

void main() {
  test('CAP-079 lifecycle contract keeps the foreground boundary closed', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/saved-case-lifecycle-updates.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['issue'], 389);
    expect(contract['capabilities'], ['CAP-079']);
    expect(contract['surface']['owner'], 'ACTIVITY');
    expect(contract['surface']['foreground_only'], isTrue);
    expect(contract['surface']['background_polling'], isFalse);
    expect(
      contract['detection']['updated_when'],
      'EXACT_CASE_ID_MATCH_AND_CASE_VERSION_ID_DIFFERS',
    );
    expect(
      contract['detection']['catalog_failure'],
      'UNKNOWN_NO_UPDATE_CLAIM',
    );
    expect(contract['acknowledgement']['trigger'], 'OPEN_UPDATED_CASE');
    expect(contract['persistence']['format_change'], isFalse);
    expect(contract['persistence']['migration_required'], isFalse);
    expect(contract['lifecycle']['cap_079_after_slice'], 'IMPLEMENTED_PARTIAL');
  });

  test(
    'acknowledgement preserves saved time and refreshes the snapshot',
    () async {
      final savedAt = DateTime.utc(2026, 8, 20, 12);
      final store = MemorySavedCaseStore([
        _saved(versionId: 'old', savedAt: savedAt),
      ]);
      final container = ProviderContainer(
        overrides: [savedCaseStoreProvider.overrideWithValue(store)],
      );
      addTearDown(container.dispose);

      await container.read(savedCasesControllerProvider.notifier).load();
      await container
          .read(savedCasesControllerProvider.notifier)
          .acknowledgeCurrentVersion(_currentSummary);

      expect(store.items, hasLength(1));
      expect(store.items.single.caseVersionId, _currentSummary.versionId);
      expect(store.items.single.title, _currentSummary.title);
      expect(store.items.single.summary, _currentSummary.summary);
      expect(store.items.single.savedAt, savedAt);
    },
  );

  testWidgets('Activity saved surface reveals and acknowledges an update', (
    tester,
  ) async {
    final savedAt = DateTime.utc(2026, 8, 20, 12);
    final store = MemorySavedCaseStore([
      _saved(versionId: 'old', savedAt: savedAt),
    ]);

    await _pump(
      tester,
      store: store,
      repository: PreviewDecisionRepository(),
      locale: const Locale('tr', 'TR'),
    );
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('saved-cases-update-count')),
      findsOneWidget,
    );
    expect(
      find.byKey(
        const ValueKey(
          'saved-case-update-${PreviewDecisionRepository.caseId}',
        ),
      ),
      findsOneWidget,
    );
    expect(find.text('Vaka güncellendi'), findsOneWidget);
    expect(find.text('Güncel vakayı aç'), findsOneWidget);

    final open = find.byKey(
      const ValueKey(
        'open-saved-case-${PreviewDecisionRepository.caseId}',
      ),
    );
    await tester.ensureVisible(open);
    await tester.tap(open);
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('opened-current-saved-case')),
      findsOneWidget,
    );
    expect(store.items.single.caseVersionId, _currentSummary.versionId);
    expect(store.items.single.savedAt, savedAt);
    expect(tester.takeException(), isNull);
  });

  testWidgets('matching version and failed catalog make no update claim', (
    tester,
  ) async {
    for (final entry in [
      (
        MemorySavedCaseStore([_saved(versionId: _currentSummary.versionId)]),
        PreviewDecisionRepository(),
      ),
      (
        MemorySavedCaseStore([_saved(versionId: 'old')]),
        _FailingExploreRepository(),
      ),
    ]) {
      await _pump(
        tester,
        store: entry.$1,
        repository: entry.$2,
        locale: const Locale('en', 'US'),
      );
      await tester.pumpAndSettle();

      expect(
        find.byKey(const ValueKey('saved-cases-update-count')),
        findsNothing,
      );
      expect(find.text('Case updated'), findsNothing);
      expect(tester.takeException(), isNull);
    }
  });

  testWidgets('update presentation is compact and enlarged-text safe', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await _pump(
      tester,
      store: MemorySavedCaseStore([_saved(versionId: 'old')]),
      repository: PreviewDecisionRepository(),
      locale: const Locale('en', 'US'),
      themeMode: ThemeMode.dark,
      textScale: 1.6,
    );
    await tester.pumpAndSettle();

    final marker = find.byKey(
      const ValueKey(
        'saved-case-update-${PreviewDecisionRepository.caseId}',
      ),
    );
    await tester.ensureVisible(marker);
    expect(marker, findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

Future<void> _pump(
  WidgetTester tester, {
  required MemorySavedCaseStore store,
  required DecisionRepository repository,
  required Locale locale,
  ThemeMode themeMode = ThemeMode.light,
  double textScale = 1,
}) async {
  tester.platformDispatcher.localeTestValue = locale;
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);
  final router = GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(
        path: '/',
        builder: (_, _) => const Scaffold(
          body: SingleChildScrollView(
            padding: EdgeInsets.all(16),
            child: SavedCasesSection(
              visible: true,
              lifecycleUpdates: true,
            ),
          ),
        ),
      ),
      GoRoute(
        path: '/case/:caseId',
        builder: (_, _) => const Scaffold(
          body: Text(
            'opened',
            key: ValueKey('opened-current-saved-case'),
          ),
        ),
      ),
    ],
  );
  addTearDown(router.dispose);

  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [
        decisionRepositoryProvider.overrideWithValue(repository),
        savedCaseStoreProvider.overrideWithValue(store),
        kefeContentLocalizerProvider.overrideWithValue(
          const PreviewContentLocalizer(),
        ),
      ],
      child: MaterialApp.router(
        debugShowCheckedModeBanner: false,
        locale: locale,
        supportedLocales: KefeStrings.supportedLocales,
        localizationsDelegates: const [
          KefeStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        theme: KefeTheme.light(),
        darkTheme: KefeTheme.dark(),
        themeMode: themeMode,
        routerConfig: router,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        ),
      ),
    ),
  );
}

DecisionCaseSummary get _currentSummary => const DecisionCaseSummary(
  id: PreviewDecisionRepository.caseId,
  versionId: PreviewDecisionRepository.caseVersionId,
  title: 'Son koltuk kime verilmeli?',
  summary: 'Güncel özet',
  format: 'DILEMMA',
  domain: 'DAILY_LIFE',
  risk: 'L0',
);

SavedCase _saved({required String versionId, DateTime? savedAt}) => SavedCase(
  caseId: PreviewDecisionRepository.caseId,
  caseVersionId: versionId,
  title: 'Eski kayıtlı başlık',
  summary: 'Eski kayıtlı özet',
  domain: 'DAILY_LIFE',
  format: 'DILEMMA',
  risk: 'L0',
  savedAt: savedAt ?? DateTime.utc(2026, 8, 20),
);

class _FailingExploreRepository extends PreviewDecisionRepository {
  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) {
    throw const ClientTransportFailure(code: 'NETWORK_UNAVAILABLE');
  }
}
