import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview/preview_content_localizer.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_content_localizer.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/saved_cases/application/saved_cases_controller.dart';
import 'package:kefe_mobile/features/saved_cases/data/saved_case_store.dart';
import 'package:kefe_mobile/features/saved_cases/domain/saved_case.dart';
import 'package:kefe_mobile/features/saved_cases/presentation/saved_cases_section.dart';

void main() {
  test('Slice 28 contract keeps persistence boundaries closed', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/saved-cases-reliability-slice28.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'saved-cases-reliability-slice28');
    expect(contract['scope']['controller_change'], isFalse);
    expect(contract['scope']['store_change'], isFalse);
    expect(contract['scope']['persistence_format_change'], isFalse);
    expect(contract['states']['loading_empty']['key'], 'saved-cases-loading');
    expect(
      contract['states']['error_empty']['empty_claim_visible'],
      isFalse,
    );
    expect(
      contract['states']['error_with_items']['items_remain_visible'],
      isTrue,
    );
    expect(contract['retry']['path'], 'SavedCasesController.load');
    expect(contract['preserved']['optimistic_toggle'], isTrue);
    expect(contract['preserved']['optimistic_remove'], isTrue);
    expect(contract['preserved']['signal_in_scope'], isFalse);
    expect(contract['preserved']['impact_in_scope'], isFalse);
  });

  test('Saved Cases source has explicit truthful state composition', () {
    final section = File(
      'lib/features/saved_cases/presentation/saved_cases_section.dart',
    ).readAsStringSync();
    final stateSurface = File(
      'lib/features/saved_cases/presentation/saved_cases_state_surface.dart',
    ).readAsStringSync();

    for (final token in [
      "ValueKey('saved-cases-loading')",
      "ValueKey('saved-cases-error')",
      "ValueKey('saved-cases-retry')",
      "ValueKey('saved-cases-empty')",
      'SavedCasesUiState.ready && state.items.isEmpty',
    ]) {
      expect(section, contains(token));
    }
    expect(section, isNot(contains('LinearProgressIndicator')));
    expect(section, isNot(contains('CircularProgressIndicator')));
    expect(stateSurface, contains('liveRegion: true'));
    expect(stateSurface, contains('ExcludeSemantics'));
    expect(stateSurface, isNot(contains('LinearProgressIndicator')));
    expect(stateSurface, isNot(contains('CircularProgressIndicator')));
  });

  testWidgets('first load is deterministic and does not claim empty', (
    tester,
  ) async {
    final store = _ControllableStore()..gate = Completer<List<SavedCase>>();

    await _pump(tester, store: store, locale: const Locale('tr', 'TR'));
    await tester.pump();
    await tester.pump();

    expect(find.byKey(const ValueKey('saved-cases-loading')), findsOneWidget);
    expect(find.byKey(const ValueKey('saved-cases-empty')), findsNothing);
    expect(find.byType(LinearProgressIndicator), findsNothing);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(store.reads, 1);
    expect(tester.takeException(), isNull);
  });

  testWidgets('error with no items is retryable and distinct from empty', (
    tester,
  ) async {
    final store = _ControllableStore()..failuresRemaining = 1;

    await _pump(tester, store: store, locale: const Locale('en', 'US'));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('saved-cases-error')), findsOneWidget);
    expect(find.byKey(const ValueKey('saved-cases-retry')), findsOneWidget);
    expect(find.byKey(const ValueKey('saved-cases-empty')), findsNothing);
    expect(find.text('Try again'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('saved-cases-retry')));
    await tester.pumpAndSettle();

    expect(store.reads, 2);
    expect(find.byKey(const ValueKey('saved-cases-error')), findsNothing);
    expect(find.byKey(const ValueKey('saved-cases-empty')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('stale items remain visible during refresh loading', (
    tester,
  ) async {
    final store = _ControllableStore(items: [_savedCase]);

    await _pump(tester, store: store, locale: const Locale('tr', 'TR'));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('open-saved-case-case-1')), findsOneWidget);

    store.gate = Completer<List<SavedCase>>();
    final container = ProviderScope.containerOf(
      tester.element(find.byType(SavedCasesSection)),
    );
    unawaited(container.read(savedCasesControllerProvider.notifier).load());
    await tester.pump();

    expect(find.byKey(const ValueKey('saved-cases-loading')), findsOneWidget);
    expect(find.byKey(const ValueKey('open-saved-case-case-1')), findsOneWidget);
    expect(find.byKey(const ValueKey('saved-cases-empty')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('stale items remain visible after refresh failure', (
    tester,
  ) async {
    final store = _ControllableStore(items: [_savedCase]);

    await _pump(tester, store: store, locale: const Locale('tr', 'TR'));
    await tester.pumpAndSettle();

    store.failuresRemaining = 1;
    final container = ProviderScope.containerOf(
      tester.element(find.byType(SavedCasesSection)),
    );
    await container.read(savedCasesControllerProvider.notifier).load();
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('saved-cases-error')), findsOneWidget);
    expect(find.byKey(const ValueKey('open-saved-case-case-1')), findsOneWidget);
    expect(find.byKey(const ValueKey('saved-cases-empty')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('remove keeps existing optimistic persistence behavior', (
    tester,
  ) async {
    final store = _ControllableStore(items: [_savedCase]);

    await _pump(tester, store: store, locale: const Locale('tr', 'TR'));
    await tester.pumpAndSettle();

    await tester.tap(
      find.byKey(const ValueKey('remove-saved-case-case-1')),
    );
    await tester.pumpAndSettle();

    expect(store.writes, 1);
    expect(store.items, isEmpty);
    expect(find.byKey(const ValueKey('open-saved-case-case-1')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  for (final themeMode in [ThemeMode.light, ThemeMode.dark]) {
    testWidgets(
      'Saved Cases error is compact-safe in ${themeMode.name} theme',
      (tester) async {
        tester.view.physicalSize = const Size(360, 800);
        tester.view.devicePixelRatio = 1;
        addTearDown(tester.view.resetPhysicalSize);
        addTearDown(tester.view.resetDevicePixelRatio);

        final store = _ControllableStore()..failuresRemaining = 1;
        await _pump(
          tester,
          store: store,
          locale: const Locale('tr', 'TR'),
          themeMode: themeMode,
          textScale: 1.6,
        );
        await tester.pumpAndSettle();

        expect(find.byKey(const ValueKey('saved-cases-error')), findsOneWidget);
        expect(find.byKey(const ValueKey('saved-cases-retry')), findsOneWidget);
        expect(tester.takeException(), isNull);
      },
    );
  }
}

Future<void> _pump(
  WidgetTester tester, {
  required _ControllableStore store,
  required Locale locale,
  ThemeMode themeMode = ThemeMode.light,
  double textScale = 1,
}) async {
  tester.platformDispatcher.localeTestValue = locale;
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);

  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [
        savedCaseStoreProvider.overrideWithValue(store),
        kefeContentLocalizerProvider.overrideWithValue(
          const PreviewContentLocalizer(),
        ),
      ],
      child: MaterialApp(
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
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        ),
        home: const Scaffold(
          body: SingleChildScrollView(
            padding: EdgeInsets.all(16),
            child: SavedCasesSection(visible: true),
          ),
        ),
      ),
    ),
  );
}

final _savedCase = SavedCase(
  caseId: 'case-1',
  caseVersionId: 'version-1',
  title: 'Kaydedilmiş vaka',
  summary: 'Kaydedilmiş vaka özeti',
  domain: 'DAILY_LIFE',
  format: 'DILEMMA',
  risk: 'L0',
  savedAt: DateTime.utc(2026, 8, 1),
);

class _ControllableStore implements SavedCaseStore {
  _ControllableStore({List<SavedCase> items = const []})
    : items = List<SavedCase>.from(items);

  List<SavedCase> items;
  Completer<List<SavedCase>>? gate;
  int failuresRemaining = 0;
  int reads = 0;
  int writes = 0;

  @override
  Future<List<SavedCase>> readAll() async {
    reads += 1;
    final activeGate = gate;
    if (activeGate != null && !activeGate.isCompleted) {
      return activeGate.future;
    }
    if (failuresRemaining > 0) {
      failuresRemaining -= 1;
      throw StateError('saved cases unavailable');
    }
    return List<SavedCase>.unmodifiable(items);
  }

  @override
  Future<void> writeAll(List<SavedCase> value) async {
    writes += 1;
    items = List<SavedCase>.from(value);
  }
}
