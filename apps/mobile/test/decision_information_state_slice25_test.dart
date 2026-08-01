import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_surface.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/context/data/context_repository.dart';
import 'package:kefe_mobile/features/context/domain/context_models.dart';
import 'package:kefe_mobile/features/context/presentation/context_section.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/decision/presentation/perspective_section.dart';
import 'package:kefe_mobile/features/progress/application/progress_controller.dart';
import 'package:kefe_mobile/features/progress/domain/progress_models.dart';

const _caseVersionId = 'slice-25-version';

void main() {
  test('Slice 25 contract preserves Context and Perspective boundaries', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/decision-information-state-slice25.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'decision-information-state-slice25');
    expect(contract['scope']['context_async_state_convergence'], isTrue);
    expect(contract['scope']['perspective_async_state_convergence'], isTrue);
    expect(contract['scope']['controller_change'], isFalse);
    expect(contract['scope']['repository_change'], isFalse);
    expect(contract['context']['availability'], 'pre_commit_safe_optional');
    expect(contract['context']['empty_snapshot_omitted'], isTrue);
    expect(contract['context']['placeholder_context_fabrication'], isFalse);
    expect(contract['perspective']['availability'], 'post_commit_reveal_only');
    expect(contract['perspective']['requested_before_commit'], isFalse);
    expect(contract['perspective']['retry_replays_answer'], isFalse);
    expect(contract['perspective']['retry_replays_private_reason'], isFalse);
    expect(contract['perspective']['retry_replays_commit'], isFalse);
    expect(contract['perspective']['retry_replays_reveal'], isFalse);
    expect(contract['runtime_continuity']['commit_first'], isTrue);
    expect(contract['runtime_continuity']['blind_first'], isTrue);
    expect(contract['runtime_continuity']['signal_in_scope'], isFalse);
    expect(contract['runtime_continuity']['impact_in_scope'], isFalse);
  });

  test('governed information-state sources have no indeterminate spinner', () {
    final contextSource = File(
      'lib/features/context/presentation/context_section.dart',
    ).readAsStringSync();
    final perspectiveSource = File(
      'lib/features/decision/presentation/perspective_section.dart',
    ).readAsStringSync();

    expect(contextSource, isNot(contains('CircularProgressIndicator')));
    expect(perspectiveSource, isNot(contains('CircularProgressIndicator')));
    expect(contextSource, contains("ValueKey('context-loading')"));
    expect(contextSource, contains("ValueKey('context-error')"));
    expect(contextSource, contains("ValueKey('context-retry')"));
    expect(
      contextSource,
      contains('ref.invalidate(contextSnapshotProvider(caseVersionId))'),
    );
    expect(perspectiveSource, contains("ValueKey('perspective-loading')"));
    expect(perspectiveSource, contains("ValueKey('perspective-error')"));
    expect(perspectiveSource, contains("ValueKey('perspective-retry')"));
    expect(perspectiveSource, contains("ValueKey('perspective-unavailable')"));
    expect(contextSource, isNot(contains('LinearProgressIndicator')));
  });

  testWidgets('Context loading, error and retry are deterministic', (
    tester,
  ) async {
    final repository = _InformationStateRepository();
    final gate = Completer<CaseContextSnapshot>();
    repository.contextGate = gate;

    await _pumpContext(tester, repository: repository);
    await tester.pump();
    await tester.pump();

    expect(find.byKey(const ValueKey('context-loading')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.byType(KefeSurface), findsWidgets);
    expect(tester.takeException(), isNull);

    repository.contextGate = null;
    gate.complete(repository.contextSnapshot());
    await tester.pumpAndSettle();

    expect(find.text('Temel bağlam'), findsOneWidget);
    expect(find.byKey(const ValueKey('context-loading')), findsNothing);

    final errorRepository = _InformationStateRepository()..failContext = true;
    await _pumpContext(tester, repository: errorRepository);
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('context-error')), findsOneWidget);
    expect(find.byKey(const ValueKey('context-retry')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    errorRepository.failContext = false;
    await tester.tap(find.byKey(const ValueKey('context-retry')));
    await tester.pumpAndSettle();

    expect(errorRepository.contextCalls, 2);
    expect(find.text('Temel bağlam'), findsOneWidget);
    expect(find.byKey(const ValueKey('context-error')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('empty optional Context remains omitted', (tester) async {
    final repository = _InformationStateRepository()..emptyContext = true;

    await _pumpContext(tester, repository: repository);
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('context-section')), findsNothing);
    expect(find.byKey(const ValueKey('context-loading')), findsNothing);
    expect(find.byKey(const ValueKey('context-error')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Perspective loading, error and null-result are semantic', (
    tester,
  ) async {
    var retries = 0;

    await _pumpPerspective(
      tester,
      state: PerspectiveUiState.loading,
      onRetry: () => retries += 1,
    );

    expect(find.byKey(const ValueKey('perspective-loading')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(tester.takeException(), isNull);

    await _pumpPerspective(
      tester,
      state: PerspectiveUiState.errorRetryable,
      onRetry: () => retries += 1,
    );

    expect(find.byKey(const ValueKey('perspective-error')), findsOneWidget);
    expect(find.byKey(const ValueKey('perspective-retry')), findsOneWidget);
    await tester.tap(find.byKey(const ValueKey('perspective-retry')));
    await tester.pump();
    expect(retries, 1);

    await _pumpPerspective(
      tester,
      state: PerspectiveUiState.ready,
      onRetry: () => retries += 1,
    );

    expect(
      find.byKey(const ValueKey('perspective-unavailable')),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('perspective-card-stack')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'information states are overflow-free in dark/light and enlarged text',
    (tester) async {
      tester.view.physicalSize = const Size(360, 800);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      final loadingRepository = _InformationStateRepository();
      loadingRepository.contextGate = Completer<CaseContextSnapshot>();
      await _pumpContext(
        tester,
        repository: loadingRepository,
        themeMode: ThemeMode.dark,
      );
      await tester.pump();
      await tester.pump();
      expect(find.byKey(const ValueKey('context-loading')), findsOneWidget);
      expect(tester.takeException(), isNull);

      await _pumpPerspective(
        tester,
        state: PerspectiveUiState.errorRetryable,
        onRetry: () {},
        themeMode: ThemeMode.light,
        textScale: 1.6,
      );
      expect(find.byKey(const ValueKey('perspective-error')), findsOneWidget);
      expect(find.byKey(const ValueKey('perspective-retry')), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
}

Future<void> _pumpContext(
  WidgetTester tester, {
  required _InformationStateRepository repository,
  ThemeMode themeMode = ThemeMode.dark,
  double textScale = 1,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [decisionRepositoryProvider.overrideWithValue(repository)],
      child: _TestApp(
        themeMode: themeMode,
        textScale: textScale,
        child: const ContextSection(caseVersionId: _caseVersionId),
      ),
    ),
  );
}

Future<void> _pumpPerspective(
  WidgetTester tester, {
  required PerspectiveUiState state,
  required VoidCallback onRetry,
  ThemeMode themeMode = ThemeMode.dark,
  double textScale = 1,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [
        progressControllerProvider.overrideWith(_ReadyProgressController.new),
      ],
      child: _TestApp(
        themeMode: themeMode,
        textScale: textScale,
        child: PerspectiveSection(
          state: state,
          result: null,
          reasonPendingModeration: false,
          onRetry: onRetry,
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

class _TestApp extends StatelessWidget {
  const _TestApp({
    required this.child,
    required this.themeMode,
    required this.textScale,
  });

  final Widget child;
  final ThemeMode themeMode;
  final double textScale;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
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
      home: Scaffold(
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: child,
          ),
        ),
      ),
    );
  }
}

class _ReadyProgressController extends ProgressController {
  @override
  ProgressState build() => const ProgressState(
    uiState: ProgressUiState.ready,
    envelope: ProgressEnvelope(
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
      methodology: {},
    ),
  );

  @override
  Future<void> load() async {}
}

class _InformationStateRepository
    implements DecisionRepository, ContextRepository {
  Completer<CaseContextSnapshot>? contextGate;
  bool failContext = false;
  bool emptyContext = false;
  int contextCalls = 0;

  CaseContextSnapshot contextSnapshot() => CaseContextSnapshot(
    caseVersionId: _caseVersionId,
    blocks: emptyContext
        ? const []
        : const [
            CaseContextBlock(
              id: 'essential',
              displayOrder: 0,
              disclosureLevel: 'ESSENTIAL',
              title: 'Durum',
              body: 'Temel bağlam',
              claimStatus: 'VERIFIED',
              sourceIds: ['source-1'],
            ),
          ],
    sources: emptyContext
        ? const []
        : const [
            CaseContextSource(
              id: 'source-1',
              title: 'Kaynak',
              publisher: 'KEFE Editorial',
              sourceKind: 'EDITORIAL',
              url: null,
              publishedAt: null,
            ),
          ],
  );

  @override
  Future<CaseContextSnapshot> fetchContext(String caseVersionId) async {
    contextCalls += 1;
    if (failContext) {
      throw const ClientTransportFailure(code: 'NETWORK_UNAVAILABLE');
    }
    final gate = contextGate;
    if (gate != null && !gate.isCompleted) return gate.future;
    return contextSnapshot();
  }

  @override
  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  }) async {}

  @override
  Future<void> commit({
    required String sessionId,
    required String idempotencyKey,
  }) async {}

  @override
  Future<GuestCredential> ensureGuestCredential() async => GuestCredential(
    actorId: 'slice-25-actor',
    accessToken: 'slice-25-token',
    expiresAt: DateTime.utc(2026, 8, 2),
  );

  @override
  Future<DecisionCase> fetchCase(String caseId) => throw UnimplementedError();

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async =>
      const [];

  @override
  Future<RevealResult> reveal(String sessionId) => throw UnimplementedError();

  @override
  Future<void> savePrivateReason({
    required String sessionId,
    required List<String> tags,
    required String? text,
  }) async {}

  @override
  Future<String> startSession(String caseId) async => 'slice-25-session';
}
