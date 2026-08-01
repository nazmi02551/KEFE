import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_surface.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/preview_decision_repository.dart';
import 'package:kefe_mobile/features/explore/application/explore_controller.dart';
import 'package:kefe_mobile/features/explore/presentation/discovery_explore_screen.dart';
import 'package:kefe_mobile/features/media_presentation/application/case_media_provider.dart';
import 'package:kefe_mobile/features/media_presentation/data/preview_case_media_repository.dart';
import 'package:kefe_mobile/features/saved_cases/application/saved_cases_controller.dart';
import 'package:kefe_mobile/features/saved_cases/data/saved_case_store.dart';

const _firstCaseId = '11111111-1111-4111-8111-111111111111';

enum _ExploreFixture { normal, loading, empty, error }

void main() {
  test('Slice 22 contract locks presentation-only discovery convergence', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/premium-explore-discovery-slice22.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'premium-explore-discovery-slice22');
    expect(contract['scope']['explore_presentation_convergence'], isTrue);
    expect(contract['scope']['repository_change'], isFalse);
    expect(contract['scope']['filter_algorithm_change'], isFalse);
    expect(contract['scope']['item_order_change'], isFalse);
    expect(contract['scope']['route_change'], isFalse);
    expect(
      contract['discovery_truth']['repository_order_authoritative'],
      isTrue,
    );
    expect(
      contract['discovery_truth']['first_item_featured_implies_recommendation'],
      isFalse,
    );
    expect(contract['discovery_truth']['personalization_added'], isFalse);
    expect(contract['search_filters']['filters_compose'], isTrue);
    expect(
      contract['saved_navigation']['save_action_must_not_trigger_case_navigation'],
      isTrue,
    );
    expect(
      contract['presentation']['direct_dark_only_tokens_forbidden'],
      isTrue,
    );
    expect(
      contract['presentation']['screen_local_fixed_rgb_gradient_forbidden'],
      isTrue,
    );
    expect(
      contract['states']['indeterminate_loading_spinner_in_governed_surface_forbidden'],
      isTrue,
    );
    expect(contract['invariants']['commit_first'], isTrue);
    expect(contract['invariants']['blind_first'], isTrue);
    expect(contract['invariants']['signal_in_scope'], isFalse);
    expect(contract['invariants']['impact_in_scope'], isFalse);
  });

  test(
    'governed Explore source uses semantic surfaces without legacy chrome',
    () {
      final source = File(
        'lib/features/explore/presentation/discovery_explore_screen.dart',
      ).readAsStringSync();

      expect(
        source,
        contains("import '../../../core/design/kefe_surface.dart';"),
      );
      expect(source, contains('KefeSurfaceTone.premium'));
      expect(source, contains('KefeSurfaceTone.raised'));
      expect(source, isNot(contains('KefeColorTokens')));
      expect(source, isNot(contains('return Card(')));
      expect(source, isNot(contains('child: Card(')));
      expect(source, isNot(contains('LinearGradient(')));
      expect(source, isNot(contains('CircularProgressIndicator')));
      expect(source, isNot(contains("item.id == '")));
      expect(source, isNot(contains('caseData.title ==')));
      expect(source, isNot(contains('recommendationScore')));
      expect(source, isNot(contains('popularity')));
    },
  );

  testWidgets('first repository item remains featured without new ranking UI', (
    tester,
  ) async {
    final repository = PreviewDecisionRepository();
    final items = await repository.fetchExploreCases();
    expect(items.first.id, _firstCaseId);

    await _pumpExplore(tester);

    final featured = find.byKey(const ValueKey('explore-featured-surface'));
    final firstCase = find.byKey(const ValueKey('explore-case-$_firstCaseId'));
    expect(featured, findsOneWidget);
    expect(firstCase, findsOneWidget);
    expect(find.descendant(of: featured, matching: firstCase), findsOneWidget);
    expect(find.textContaining('%'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'save control remains local and does not trigger Case navigation',
    (tester) async {
      final container = await _pumpExplore(tester);

      expect(
        container.read(savedCasesControllerProvider).contains(_firstCaseId),
        isFalse,
      );
      await tester.tap(find.byKey(const ValueKey('save-case-$_firstCaseId')));
      await tester.pumpAndSettle();

      expect(
        container.read(savedCasesControllerProvider).contains(_firstCaseId),
        isTrue,
      );
      expect(
        find.byKey(const ValueKey('explore-case-$_firstCaseId')),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('loading, empty and error states are deterministic surfaces', (
    tester,
  ) async {
    await _pumpExplore(tester, fixture: _ExploreFixture.loading);
    expect(find.byKey(const ValueKey('explore-loading')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.byType(KefeSurface), findsWidgets);
    expect(tester.takeException(), isNull);

    await _pumpExplore(tester, fixture: _ExploreFixture.empty);
    expect(find.byKey(const ValueKey('explore-empty')), findsOneWidget);
    expect(find.byKey(const ValueKey('explore-no-results')), findsNothing);
    expect(tester.takeException(), isNull);

    await _pumpExplore(tester, fixture: _ExploreFixture.error);
    expect(find.byKey(const ValueKey('explore-error')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Explore remains overflow-free in dark/light and enlarged text', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await _pumpExplore(tester, themeMode: ThemeMode.dark);
    expect(find.byKey(const ValueKey('explore-search-field')), findsOneWidget);
    expect(find.byKey(const ValueKey('saved-only-filter')), findsOneWidget);
    expect(tester.takeException(), isNull);

    await _pumpExplore(tester, themeMode: ThemeMode.light, textScale: 1.6);
    expect(
      find.byKey(const ValueKey('explore-discovery-controls')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('explore-featured-surface')),
      findsOneWidget,
    );
    await tester.drag(
      find.byKey(const ValueKey('explore-list')),
      const Offset(0, -620),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });
}

Future<ProviderContainer> _pumpExplore(
  WidgetTester tester, {
  _ExploreFixture fixture = _ExploreFixture.normal,
  ThemeMode themeMode = ThemeMode.dark,
  double textScale = 1,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        decisionRepositoryProvider.overrideWithValue(
          PreviewDecisionRepository(),
        ),
        caseMediaRepositoryProvider.overrideWithValue(
          const PreviewCaseMediaRepository(),
        ),
        savedCaseStoreProvider.overrideWithValue(MemorySavedCaseStore()),
        if (fixture == _ExploreFixture.loading)
          exploreControllerProvider.overrideWith(_LoadingExploreController.new),
        if (fixture == _ExploreFixture.empty)
          exploreControllerProvider.overrideWith(_EmptyExploreController.new),
        if (fixture == _ExploreFixture.error)
          exploreControllerProvider.overrideWith(_ErrorExploreController.new),
      ],
      child: MaterialApp(
        debugShowCheckedModeBanner: false,
        locale: const Locale('tr', 'TR'),
        theme: KefeTheme.light(),
        darkTheme: KefeTheme.dark(),
        themeMode: themeMode,
        supportedLocales: KefeStrings.supportedLocales,
        localizationsDelegates: const [
          KefeStringsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(
            context,
          ).copyWith(textScaler: TextScaler.linear(textScale)),
          child: child!,
        ),
        home: const DiscoveryExploreScreen(),
      ),
    ),
  );
  await tester.pumpAndSettle();

  return ProviderScope.containerOf(
    tester.element(find.byType(DiscoveryExploreScreen)),
    listen: false,
  );
}

class _LoadingExploreController extends ExploreController {
  @override
  ExploreState build() => const ExploreState(loading: true);

  @override
  Future<void> load() async {}
}

class _EmptyExploreController extends ExploreController {
  @override
  ExploreState build() => const ExploreState();

  @override
  Future<void> load() async {}
}

class _ErrorExploreController extends ExploreController {
  @override
  ExploreState build() =>
      const ExploreState(errorCode: 'UNEXPECTED_CLIENT_ERROR');

  @override
  Future<void> load() async {}
}
