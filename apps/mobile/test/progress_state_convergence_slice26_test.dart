import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/product_preview/preview_content_localizer.dart';
import 'package:kefe_mobile/core/design/kefe_surface.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_content_localizer.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/progress/application/progress_controller.dart';
import 'package:kefe_mobile/features/progress/data/progress_repository.dart';
import 'package:kefe_mobile/features/progress/domain/progress_models.dart';
import 'package:kefe_mobile/features/progress/presentation/my_kefe_journey_screen.dart';
import 'package:kefe_mobile/features/progress/presentation/progress_section.dart';
import 'package:kefe_mobile/features/saved_cases/application/saved_cases_controller.dart';
import 'package:kefe_mobile/features/saved_cases/data/saved_case_store.dart';

void main() {
  test('Slice 26 contract keeps progress and My KEFE boundaries closed', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/progress-state-convergence-slice26.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'progress-state-convergence-slice26');
    expect(contract['scope']['presentation_only'], isTrue);
    expect(contract['scope']['shared_async_state_primitive'], isTrue);
    expect(contract['scope']['controller_change'], isFalse);
    expect(contract['scope']['repository_change'], isFalse);
    expect(contract['states']['loading']['indeterminate_spinner'], isFalse);
    expect(contract['states']['loading']['artificial_progress'], isFalse);
    expect(
      contract['states']['error_retryable']['retry_path'],
      'ProgressController.load',
    );
    expect(contract['preserved']['my_kefe_descriptive_only'], isTrue);
    expect(contract['preserved']['personality_inference'], isFalse);
    expect(contract['preserved']['ideology_inference'], isFalse);
    expect(contract['preserved']['psychometric_inference'], isFalse);
    expect(contract['preserved']['bias_inference'], isFalse);
    expect(contract['preserved']['causal_inference'], isFalse);
    expect(contract['preserved']['signal_in_scope'], isFalse);
    expect(contract['preserved']['impact_in_scope'], isFalse);
  });

  test('both consumers use the shared semantic state primitive', () {
    final helper = File(
      'lib/features/progress/presentation/progress_async_state_surface.dart',
    ).readAsStringSync();
    final progress = File(
      'lib/features/progress/presentation/progress_section.dart',
    ).readAsStringSync();
    final myKefe = File(
      'lib/features/progress/presentation/my_kefe_journey_screen.dart',
    ).readAsStringSync();

    expect(progress, contains('ProgressAsyncStateSurface.loading'));
    expect(progress, contains('ProgressAsyncStateSurface.error'));
    expect(myKefe, contains('ProgressAsyncStateSurface.loading'));
    expect(myKefe, contains('ProgressAsyncStateSurface.error'));
    expect(helper, contains('KefeSurface'));
    expect(helper, contains('liveRegion: true'));
    expect(helper, contains('ExcludeSemantics'));
    expect(helper, isNot(contains('CircularProgressIndicator')));
    expect(helper, isNot(contains('LinearProgressIndicator')));
    expect(helper, isNot(contains('Card(')));
    expect(progress, isNot(contains('CircularProgressIndicator')));
    expect(myKefe, isNot(contains('CircularProgressIndicator')));
    expect(myKefe, contains("ValueKey('my-kefe-empty')"));
  });

  testWidgets('ProgressSection loading is deterministic', (tester) async {
    final repository = _ControllableProgressRepository(_readyEnvelope());
    repository.gate = Completer<ProgressEnvelope>();

    await _pumpSurface(
      tester,
      repository: repository,
      child: const SingleChildScrollView(child: ProgressSection()),
      themeMode: ThemeMode.dark,
    );
    await tester.pump();
    await tester.pump();

    expect(find.byKey(const ValueKey('progress-loading')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.byType(KefeSurface), findsWidgets);
    expect(repository.calls, 1);
    expect(tester.takeException(), isNull);
  });

  testWidgets('ProgressSection retry dispatches one load and restores ready', (
    tester,
  ) async {
    final repository = _ControllableProgressRepository(_readyEnvelope())
      ..failuresRemaining = 1;

    await _pumpSurface(
      tester,
      repository: repository,
      child: const SingleChildScrollView(child: ProgressSection()),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('progress-error')), findsOneWidget);
    expect(find.byKey(const ValueKey('progress-retry')), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('progress-retry')));
    await tester.pumpAndSettle();

    expect(repository.calls, 2);
    expect(find.byKey(const ValueKey('progress-error')), findsNothing);
    expect(find.byKey(const ValueKey('my-kefe-progress')), findsOneWidget);
    expect(find.byKey(const ValueKey('account-offer')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('My KEFE error retry preserves descriptive ready state', (
    tester,
  ) async {
    final repository = _ControllableProgressRepository(_readyEnvelope())
      ..failuresRemaining = 1;

    await _pumpSurface(
      tester,
      repository: repository,
      child: const MyKefeJourneyScreen(embedded: true),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('my-kefe-error')), findsOneWidget);
    expect(find.byKey(const ValueKey('my-kefe-retry')), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('my-kefe-retry')));
    await tester.pumpAndSettle();

    expect(repository.calls, 2);
    expect(find.byKey(const ValueKey('my-kefe-error')), findsNothing);
    expect(find.byKey(const ValueKey('my-kefe-weigh-count')), findsOneWidget);
    expect(find.byKey(const ValueKey('my-kefe-journey')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('My KEFE empty state retains the non-inference disclosure', (
    tester,
  ) async {
    final repository = _ControllableProgressRepository(_emptyEnvelope());

    await _pumpSurface(
      tester,
      repository: repository,
      child: const MyKefeJourneyScreen(embedded: true),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('my-kefe-empty')), findsOneWidget);
    final footnote = find.byKey(const ValueKey('my-kefe-no-inference-note'));
    final scrollable = find.descendant(
      of: find.byKey(const ValueKey('my-kefe-journey')),
      matching: find.byType(Scrollable),
    );
    await tester.scrollUntilVisible(footnote, 250, scrollable: scrollable);
    expect(footnote, findsOneWidget);
    expect(find.byKey(const ValueKey('account-offer')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'shared states are overflow-free on compact phone with enlarged text',
    (tester) async {
      tester.view.physicalSize = const Size(360, 800);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final loadingRepository = _ControllableProgressRepository(
        _readyEnvelope(),
      )..gate = Completer<ProgressEnvelope>();
      await _pumpSurface(
        tester,
        repository: loadingRepository,
        child: const SingleChildScrollView(child: ProgressSection()),
        themeMode: ThemeMode.dark,
        textScale: 1.6,
      );
      await tester.pump();
      await tester.pump();
      expect(find.byKey(const ValueKey('progress-loading')), findsOneWidget);
      expect(tester.takeException(), isNull);

      final errorRepository = _ControllableProgressRepository(_readyEnvelope())
        ..failuresRemaining = 1;
      await _pumpSurface(
        tester,
        repository: errorRepository,
        child: const MyKefeJourneyScreen(embedded: true),
        themeMode: ThemeMode.light,
        textScale: 1.6,
      );
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('my-kefe-error')), findsOneWidget);
      expect(find.byKey(const ValueKey('my-kefe-retry')), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}

Future<void> _pumpSurface(
  WidgetTester tester, {
  required _ControllableProgressRepository repository,
  required Widget child,
  ThemeMode themeMode = ThemeMode.light,
  double textScale = 1,
}) async {
  tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
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
        locale: const Locale('tr', 'TR'),
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
        home: Scaffold(body: child),
      ),
    ),
  );
}

ProgressEnvelope _readyEnvelope() => ProgressEnvelope(
  accountOffer: const AccountOffer(
    eligible: true,
    placement: 'POST_REVEAL',
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
        caseId: 'slice-26-case',
        caseVersionId: 'slice-26-version',
        title: 'Temsili vaka',
        primaryDomain: 'DAILY_LIFE',
        committedAt: DateTime.utc(2026, 8, 1),
      ),
    ],
  ),
  journey: MyKefeJourney(
    decisionUpdateCount: 1,
    revisitedCaseCount: 1,
    reflectionCompletionCount: 1,
    domainActivity: [
      MyKefeDomainActivity(
        primaryDomain: 'DAILY_LIFE',
        committedWeighCount: 1,
        lastCommittedAt: DateTime.utc(2026, 8, 1),
      ),
    ],
    recentJourneys: [
      MyKefeRecentJourney(
        caseId: 'slice-26-case',
        caseVersionId: 'slice-26-version',
        title: 'Temsili vaka',
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
