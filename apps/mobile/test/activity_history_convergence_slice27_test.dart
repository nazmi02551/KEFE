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
    expect(contract['preserved']['personality_inference'], isFalse);
    expect(contract['preserved']['ideology_inference'], isFalse);
    expect(contract['preserved']['psychometric_inference'], isFalse);
    expect(contract['preserved']['bias_inference'], isFalse);
    expect(contract['preserved']['causal_inference'], isFalse);
    expect(contract['preserved']['normative_inference'], isFalse);
    expect(contract['preserved']['signal_in_scope'], isFalse);
    expect(contract['preserved']['impact_in_scope'], isFalse);
  });

  test('Activity source uses shared states and display-time localization', () {
    final source = File(
      'lib/features/activity/presentation/activity_screen.dart',
    ).readAsStringSync();

    expect(source, contains('ProgressAsyncStateSurface.loading'));
    expect(source, contains('ProgressAsyncStateSurface.error'));
    expect(source, contains("surfaceKey: 'activity-loading'"));
    expect(source, contains("surfaceKey: 'activity-error'"));
    expect(source, contains("retryKey: 'activity-retry'"));
    expect(source, contains('kefeContentLocalizerProvider'));
    expect(source, contains('KefeContentNamespace.caseTitle'));
    expect(source, contains('label: displayTitle'));
    expect(source, isNot(contains('CircularProgressIndicator')));
    expect(source, isNot(contains('LinearProgressIndicator')));
    expect(source, isNot(contains('class _ActivityError')));
  });

  testWidgets('Activity loading is deterministic', (tester) async {
    final repository = _ControllableProgressRepository(_enrichedEnvelope())
      ..gate = Completer<ProgressEnvelope>();

    await _pumpActivity(
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
    final repository = _ControllableProgressRepository(_enrichedEnvelope())
      ..failuresRemaining = 1;

    await _pumpActivity(
      tester,
      repository: repository,
      locale: const Locale('tr', 'TR'),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('activity-error')), findsOneWidget);
    expect(find.byKey(const ValueKey('activity-retry')), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('activity-retry')));
    await tester.pumpAndSettle();

    expect(repository.calls, 2);
    expect(find.byKey(const ValueKey('activity-error')), findsNothing);
    expect(find.byKey(const ValueKey('activity-history')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('enriched Activity rows localize Case titles at display time', (
    tester,
  ) async {
    await _pumpActivity(
      tester,
      repository: _ControllableProgressRepository(_enrichedEnvelope()),
      locale: const Locale('en', 'US'),
    );
    await tester.pumpAndSettle();

    expect(find.text('Who should get the last seat?'), findsOneWidget);
    expect(find.text('Ham zenginleştirilmiş başlık'), findsNothing);
    expect(
      find.byKey(const ValueKey('activity-case-$_caseId')),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets('legacy Activity rows localize Case titles at display time', (
    tester,
  ) async {
    await _pumpActivity(
      tester,
      repository: _ControllableProgressRepository(_legacyEnvelope()),
      locale: const Locale('en', 'US'),
    );
    await tester.pumpAndSettle();

    expect(find.text('Who should get the last seat?'), findsOneWidget);
    expect(find.text('Ham eski başlık'), findsNothing);
    expect(
      find.byKey(const ValueKey('activity-case-$_caseId')),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'Activity empty state is overflow-free on compact phone with enlarged text',
    (tester) async {
      tester.view.physicalSize = const Size(360, 800);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await _pumpActivity(
        tester,
        repository: _ControllableProgressRepository(_emptyEnvelope()),
        locale: const Locale('tr', 'TR'),
        themeMode: ThemeMode.light,
        textScale: 1.6,
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('activity-empty')), findsOneWidget);
      expect(find.byKey(const ValueKey('saved-cases-section')), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}

Future<void> _pumpActivity(
  WidgetTester tester, {
  required _ControllableProgressRepository repository,
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

ProgressEnvelope _enrichedEnvelope() => ProgressEnvelope(
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
  methodology: const {
    'sample_scope': 'CURRENT_ACTOR_COMMITTED_HISTORY',
    'readiness_note': 'PRESENTATION_ONLY_NOT_RESEARCH_VALIDATED',
  },
);

ProgressEnvelope _legacyEnvelope() => ProgressEnvelope(
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

class _ControllableProgressRepository implements ProgressRepository {
  _ControllableProgressRepository(this.envelope);

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
