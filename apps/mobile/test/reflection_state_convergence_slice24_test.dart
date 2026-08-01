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
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/application/reflection_completion_provider.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/data/reflection_completion_store.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/decision/domain/reflection_models.dart';
import 'package:kefe_mobile/features/decision/presentation/reflection_step.dart';

const _sessionId = 'slice-24-session';
const _caseId = 'slice-24-case';
const _caseVersionId = 'slice-24-version';
const _stepCode = 'REFLECTION';

const _caseData = DecisionCase(
  id: _caseId,
  versionId: _caseVersionId,
  title: 'Reflection fixture',
  summary: 'Server-derived descriptive reflection fixture.',
  format: 'DILEMMA',
  domain: 'DAILY_LIFE',
  risk: 'L0',
  questions: [
    DecisionQuestion(
      id: 'slice-24-question',
      prompt: 'Kararın nedir?',
      responseType: 'SINGLE_CHOICE',
      options: ['A', 'B'],
    ),
  ],
);

void main() {
  test('Slice 24 contract preserves non-causal Reflection runtime', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/reflection-state-convergence-slice24.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'reflection-state-convergence-slice24');
    expect(contract['scope']['reflection_presentation_convergence'], isTrue);
    expect(contract['scope']['reflection_runtime_change'], isFalse);
    expect(contract['scope']['decision_lineage_change'], isFalse);
    expect(contract['scope']['completion_store_change'], isFalse);
    expect(contract['authority']['read_model'], 'server_derived_actor_scoped');
    expect(contract['authority']['client_causal_attribution'], isFalse);
    expect(contract['completion']['pending_key_reuse_preserved'], isTrue);
    expect(contract['completion']['creates_decision_revision'], isFalse);
    expect(contract['methodology']['descriptive_non_causal'], isTrue);
    expect(contract['methodology']['intervention_caused_change_claim'], isFalse);
    expect(contract['methodology']['raw_response_values_exposed'], isFalse);
    expect(contract['methodology']['private_reason_text_exposed'], isFalse);
    expect(contract['methodology']['signal_input'], isFalse);
    expect(contract['methodology']['impact_input'], isFalse);
  });

  test('governed Reflection source uses semantic theme-adaptive surfaces', () {
    final source = File(
      'lib/features/decision/presentation/reflection_step.dart',
    ).readAsStringSync();

    expect(
      source,
      contains("import '../../../core/design/kefe_surface.dart';"),
    );
    expect(
      source,
      contains("import '../../../core/design/kefe_visual_system.dart';"),
    );
    expect(source, contains('KefeSurface('));
    expect(source, contains('context.kefeVisual'));
    expect(source, contains("key: const ValueKey('reflection-loading')"));
    expect(source, contains("key: const ValueKey('reflection-error')"));
    expect(
      source,
      contains("key: const ValueKey('reflection-inline-status')"),
    );
    expect(
      source,
      contains("key: const ValueKey('reflection-complete-button')"),
    );
    expect(source, isNot(contains('CircularProgressIndicator')));
    expect(source, isNot(contains('return Card(')));
    expect(source, isNot(contains('child: Card(')));
    expect(source, isNot(contains('KefeColorTokens')));
    expect(source, isNot(contains('surfaceElevatedDark')));
    expect(source, isNot(contains('textMutedDark')));
    expect(source, isNot(contains('LinearGradient(')));
    expect(source, isNot(contains("caseId ==")));
    expect(source, isNot(contains("caseData.domain")));
    expect(source, isNot(contains("caseData.format")));
  });

  testWidgets('Reflection loading and retry are deterministic surfaces', (
    tester,
  ) async {
    final repository = _ReflectionFixtureRepository();
    final loadGate = Completer<ReflectionReadModel>();
    repository.loadGate = loadGate;

    await _pumpReflection(tester, repository: repository);
    await tester.pump();

    expect(find.byKey(const ValueKey('reflection-loading')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.byType(KefeSurface), findsWidgets);
    expect(tester.takeException(), isNull);

    repository.loadGate = null;
    loadGate.complete(repository.readModel());
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('reflection-summary')), findsOneWidget);
    expect(
      find.byKey(const ValueKey('reflection-non-causal-note')),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('reflection-loading')), findsNothing);

    repository.failFetch = true;
    await _pumpReflection(tester, repository: repository);
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('reflection-error')), findsOneWidget);
    expect(find.byKey(const ValueKey('reflection-retry')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    repository.failFetch = false;
    await tester.tap(find.byKey(const ValueKey('reflection-retry')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('reflection-summary')), findsOneWidget);
    expect(find.byKey(const ValueKey('reflection-error')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'completion reuses pending idempotency and shows deterministic working state',
    (tester) async {
      final repository = _ReflectionFixtureRepository();
      final completionGate = Completer<void>();
      repository.completionGate = completionGate;
      final completionStore = MemoryReflectionCompletionStore();
      await completionStore.write(
        const PendingReflectionCompletion(
          sessionId: _sessionId,
          caseVersionId: _caseVersionId,
          stepCode: _stepCode,
          latestRevisionId: 'revision-2',
          idempotencyKey: 'slice-24-reused-key',
        ),
      );

      await _pumpReflection(
        tester,
        repository: repository,
        completionStore: completionStore,
      );
      await tester.pumpAndSettle();

      expect(
        find.byKey(const ValueKey('reflection-complete-button')),
        findsOneWidget,
      );
      await tester.tap(
        find.byKey(const ValueKey('reflection-complete-button')),
      );
      await tester.pump();

      final button = tester.widget<FilledButton>(
        find.byKey(const ValueKey('reflection-complete-button')),
      );
      expect(button.onPressed, isNull);
      expect(find.byType(CircularProgressIndicator), findsNothing);
      expect(repository.completeCalls, 1);
      expect(repository.lastIdempotencyKey, 'slice-24-reused-key');

      await tester.tap(
        find.byKey(const ValueKey('reflection-complete-button')),
        warnIfMissed: false,
      );
      await tester.pump();
      expect(repository.completeCalls, 1);

      completionGate.complete();
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('reflection-completed')), findsOneWidget);
      expect(completionStore.completions, isEmpty);
      expect(repository.completeCalls, 1);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets('Reflection is overflow-free in dark/light and enlarged text', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final darkRepository = _ReflectionFixtureRepository();
    await _pumpReflection(
      tester,
      repository: darkRepository,
      themeMode: ThemeMode.dark,
    );
    await tester.pumpAndSettle();
    expect(
      find.byKey(const ValueKey('reflection-journey-graphic')),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);

    final lightRepository = _ReflectionFixtureRepository();
    await _pumpReflection(
      tester,
      repository: lightRepository,
      themeMode: ThemeMode.light,
      textScale: 1.6,
    );
    await tester.pumpAndSettle();
    expect(
      find.byKey(const ValueKey('reflection-non-causal-note')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('reflection-complete-button')),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });
}

Future<void> _pumpReflection(
  WidgetTester tester, {
  required _ReflectionFixtureRepository repository,
  ReflectionCompletionStore? completionStore,
  ThemeMode themeMode = ThemeMode.dark,
  double textScale = 1,
}) async {
  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [
        decisionRepositoryProvider.overrideWithValue(repository),
        decisionDraftStoreProvider.overrideWithValue(MemoryDecisionDraftStore()),
        reflectionCompletionStoreProvider.overrideWithValue(
          completionStore ?? MemoryReflectionCompletionStore(),
        ),
        decisionControllerProvider.overrideWith(_Slice24DecisionController.new),
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
        home: Scaffold(
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: ReflectionStepCard(
                sessionId: _sessionId,
                caseVersionId: _caseVersionId,
                step: _reflectionStep(),
              ),
            ),
          ),
        ),
      ),
    ),
  );
}

FlowRuntimeStep _reflectionStep({
  FlowStepRuntimeState state = FlowStepRuntimeState.ready,
}) {
  return FlowRuntimeStep(
    code: _stepCode,
    primitiveCode: _stepCode,
    capabilityCodes: const [_stepCode],
    nextStepCodes: const [],
    state: state,
  );
}

FlowRuntimeSnapshot _runtime({bool completed = false}) {
  return FlowRuntimeSnapshot(
    sessionId: _sessionId,
    caseVersionId: _caseVersionId,
    sessionState: 'COMMITTED',
    templateCode: 'SLICE_24_REFLECTION',
    templateVersionNo: 1,
    entryStepCode: _stepCode,
    executionSupport: FlowExecutionSupport.full,
    steps: [
      _reflectionStep(
        state: completed
            ? FlowStepRuntimeState.completed
            : FlowStepRuntimeState.ready,
      ),
    ],
  );
}

class _Slice24DecisionController extends DecisionController {
  @override
  DecisionState build() => DecisionState(
    caseData: _caseData,
    sessionId: _sessionId,
    flowRuntime: _runtime(),
  );

  @override
  Future<void> load(String caseId) async {}
}

class _ReflectionFixtureRepository
    implements DecisionRepository, FlowRuntimeRepository, ReflectionRepository {
  Completer<ReflectionReadModel>? loadGate;
  Completer<void>? completionGate;
  bool failFetch = false;
  bool completed = false;
  int fetchCalls = 0;
  int completeCalls = 0;
  String? lastIdempotencyKey;

  ReflectionReadModel readModel() => ReflectionReadModel(
    sessionId: _sessionId,
    caseVersionId: _caseVersionId,
    flowStepCode: _stepCode,
    revisionCount: 2,
    latestRevisionId: 'revision-2',
    latestDeltaId: 'delta-1',
    decisionChanged: true,
    changedQuestionCount: 1,
    interventionCount: 1,
    interventionTypeCodes: const ['CONTEXT_REVEAL'],
    fromContributionClass: 'CORE_PRE_RESULT',
    toContributionClass: 'CORE_PRE_RESULT',
    completed: completed,
  );

  @override
  Future<ReflectionReadModel> fetchReflection({
    required String sessionId,
    required String stepCode,
  }) async {
    fetchCalls += 1;
    if (failFetch) {
      throw const ClientTransportFailure(code: 'NETWORK_UNAVAILABLE');
    }
    final gate = loadGate;
    if (gate != null && !gate.isCompleted) return gate.future;
    return readModel();
  }

  @override
  Future<void> completeReflection({
    required String sessionId,
    required String stepCode,
    required String idempotencyKey,
  }) async {
    completeCalls += 1;
    lastIdempotencyKey = idempotencyKey;
    final gate = completionGate;
    if (gate != null && !gate.isCompleted) await gate.future;
    completed = true;
  }

  @override
  Future<FlowRuntimeSnapshot> fetchFlowRuntime(String sessionId) async =>
      _runtime(completed: completed);

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
    actorId: 'slice-24-actor',
    accessToken: 'slice-24-token',
    expiresAt: DateTime.utc(2026, 8, 2),
  );

  @override
  Future<DecisionCase> fetchCase(String caseId) async => _caseData;

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async =>
      const [];

  @override
  Future<RevealResult> reveal(String sessionId) async => const RevealResult(
    layer: 'TRUSTED',
    sampleSize: 0,
    confidence: 'LOW',
    values: {},
  );

  @override
  Future<void> savePrivateReason({
    required String sessionId,
    required List<String> tags,
    required String? text,
  }) async {}

  @override
  Future<String> startSession(String caseId) async => _sessionId;
}
