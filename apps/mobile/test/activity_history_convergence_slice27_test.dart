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
import 'package:kefe_mobile/features/activity/presentation/activity_screen.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/progress/application/progress_controller.dart';
import 'package:kefe_mobile/features/progress/data/progress_repository.dart';
import 'package:kefe_mobile/features/progress/domain/progress_models.dart';
import 'package:kefe_mobile/features/saved_cases/application/saved_cases_controller.dart';
import 'package:kefe_mobile/features/saved_cases/data/saved_case_store.dart';

const _caseId = '11111111-1111-4111-8111-111111111111';

void main() {
  test('Slice 27 contract keeps Activity boundaries closed', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/activity-history-convergence-slice27.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'activity-history-convergence-slice27');
    expect(contract['scope']['presentation_only'], isTrue);
    expect(contract['scope']['controller_change'], isFalse);
    expect(contract['scope']['repository_change'], isFalse);
    expect(contract['states']['loading']['key'], 'activity-loading');
    expect(
      contract['states']['error_retryable']['retry_key'],
      'activity-retry',
    );
    expect(contract['localization']['enriched_rows'], isTrue);
    expect(contract['localization']['legacy_rows'], isTrue);
    expect(contract['localization']['raw_value_mutation'], isFalse);
    expect(contract['preserved']['activity_descriptive_only'], isTrue);
    for (final key in [
      'personality_inference',
      'ideology_inference',
      'psychometric_inference',
      'bias_inference',
      'causal_inference',
      'normative_inference',
      'signal_in_scope',
      'impact_in_scope',
    ]) {
      expect(contract['preserved'][key], isFalse);
    }
  });

  test('Activity source uses shared states and display-time localization', () {
    final source = File(
      'lib/features/activity/presentation/activity_screen.dart',
    ).readAsStringSync();

    for (final token in [
      'ProgressAsyncStateSurface.loading',
      'ProgressAsyncStateSurface.error',
      "surfaceKey: 'activity-loading'",
      "surfaceKey: 'activity-error'",
      "retryKey: 'activity-retry'",
      'kefeContentLocalizerProvider',
      'KefeContentNamespace.caseTitle',
      'label: displayTitle',
    ]) {
      expect(source, contains(token));
    }
    expect(source, isNot(contains('CircularProgressIndicator')));
    expect(source, isNot(contains('LinearProgressIndicator')));
    expect(source, isNot(contains('class _ActivityError')));
  });

  testWidgets('Activity loading is deterministic', (tester) async {
    final repository = _Repository(_enrichedEnvelope())
      ..gate = Completer<ProgressEnvelope>();

    await _pump(
      tester,
      repository: repository,
      locale: const Locale('tr', 'TR'),
      themeMode: ThemeMode.dark,
    );
    await tester.pump();
    await tester.pump();

    expect(find.byKey(const ValueKey('activity-loading')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.byType(LinearProgressIndicator), findsNothing);
    expect(repository.calls, 1);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Activity retry invokes one additional progress load', (
    tester,
  ) async {
    final repository = _Repository(_enrichedEnvelope())..failuresRemaining = 1;

    await _pump(
      tester,
      repository: repository,
      locale: const Locale('tr', 'TR'),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('activity-error')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('activity-retry')));
    await tester.pumpAndSettle();

    expect(repository.calls, 2);
    expect(find.byKey(const ValueKey('activity-error')), findsNothing);
    expect(find.byKey(const ValueKey('activity-history')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  for (final entry in [
    (_enrichedEnvelope(), 'Ham zenginleştirilmiş başlık'),
    (_legacyEnvelope(), 'Ham eski başlık'),
  ]) {
    testWidgets('Activity localizes ${entry.$2} at display time', (
      tester,
    ) async {
      await _pump(
        tester,
        repository: _Repository(entry.$1),
        locale: const Locale('en', 'US'),
      );
      await tester.pumpAndSettle();

      expect(find.text('Who should get the last seat?'), findsOneWidget);
      expect(find.text(entry.$2), findsNothing);
      expect(
        find.byKey(const ValueKey('activity-case-$_caseId')),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets(
    'Activity empty state is reachable on compact phone with enlarged text',
    (tester) async {
      tester.view.physicalSize = const Size(360, 800);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await _pump(
        tester,
        repository: _Repository(_emptyEnvelope()),
        locale: const Locale('tr', 'TR'),
        themeMode: ThemeMode.light,
        textScale: 1.6,
      );
      await tester.pumpAndSettle();

      final empty = find.byKey(const ValueKey('activity-empty'));
      final activityScroll = find.descendant(
        of: find.byKey(const ValueKey('activity-screen')),
        matching: find.byType(Scrollable),
      );
      await tester.scrollUntilVisible(
        empty,
        250,
        scrollable: activityScroll,
      );

      expect(empty, findsOneWidget);
      expect(find.byKey(const ValueKey('saved-cases-section')), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}

Future<void> _pump(
  WidgetTester tester, {
  required _Repository repository,
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
        progressRepositoryProvider.overrideWithValue(repository),
        savedCaseStoreProvider.overrideWithValue(MemorySavedCaseStore()),
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
        home: const Scaffold(body: ActivityScreen(embedded: true)),
      ),
    ),
  );
}

ProgressEnvelope _enrichedEnvelope() => _envelope(
  journey: MyKefeJourney(
    decisionUpdateCount: 1,
    revisitedCaseCount: 1,
    reflectionCompletionCount: 1,
    domainActivity: const [],
    recentJourneys: [
      MyKefeRecentJourney(
        caseId: _caseId,
        caseVersionId: 'activity-version',
        title: 'Ham zenginleştirilmiş başlık',
        primaryDomain: 'DAILY_LIFE',
        initialCommittedAt: DateTime.utc(2026, 8, 1),
        latestDecisionAt: DateTime.utc(2026, 8, 1),
        decisionUpdateCount: 1,
        reflectionCompleted: true,
      ),
    ],
  ),
);

ProgressEnvelope _legacyEnvelope() => _envelope();

ProgressEnvelope _envelope({
  MyKefeJourney journey = const MyKefeJourney.empty(),
}) => ProgressEnvelope(
  accountOffer: const AccountOffer(
    eligible: false,
    placement: 'NONE',
    blocking: false,
    dismissible: true,
    continueAsGuestAvailable: true,
    accountCreationAvailable: false,
  ),
  progress: MyKefeProgress(
    readiness: 'INSUFFICIENT_DATA',
    meaningfulWeighCount: 1,
    distinctCaseCount: 1,
    distinctDomainCount: 1,
    firstCommittedAt: DateTime.utc(2026, 8, 1),
    lastCommittedAt: DateTime.utc(2026, 8, 1),
    recentCases: [
      RecentProgressCase(
        caseId: _caseId,
        caseVersionId: 'activity-version',
        title: 'Ham eski başlık',
        primaryDomain: 'DAILY_LIFE',
        committedAt: DateTime.utc(2026, 8, 1),
      ),
    ],
  ),
  journey: journey,
  methodology: const {
    'sample_scope': 'CURRENT_ACTOR_COMMITTED_HISTORY',
    'readiness_note': 'PRESENTATION_ONLY_NOT_RESEARCH_VALIDATED',
  },
);

ProgressEnvelope _emptyEnvelope() => const ProgressEnvelope(
  accountOffer: AccountOffer(
    eligible: false,
    placement: 'NONE',
    blocking: false,
    dismissible: true,
    continueAsGuestAvailable: true,
    accountCreationAvailable: false,
  ),
  progress: MyKefeProgress(
    readiness: 'STARTING',
    meaningfulWeighCount: 0,
    distinctCaseCount: 0,
    distinctDomainCount: 0,
    firstCommittedAt: null,
    lastCommittedAt: null,
    recentCases: [],
  ),
  methodology: {
    'sample_scope': 'CURRENT_ACTOR_COMMITTED_HISTORY',
    'readiness_note': 'PRESENTATION_ONLY_NOT_RESEARCH_VALIDATED',
  },
);

class _Repository implements ProgressRepository {
  _Repository(this.envelope);

  final ProgressEnvelope envelope;
  Completer<ProgressEnvelope>? gate;
  int failuresRemaining = 0;
  int calls = 0;

  @override
  Future<ProgressEnvelope> fetchProgress() async {
    calls += 1;
    final activeGate = gate;
    if (activeGate != null && !activeGate.isCompleted) {
      return activeGate.future;
    }
    if (failuresRemaining > 0) {
      failuresRemaining -= 1;
      throw const ClientTransportFailure(code: 'NETWORK_UNAVAILABLE');
    }
    return envelope;
  }
}
