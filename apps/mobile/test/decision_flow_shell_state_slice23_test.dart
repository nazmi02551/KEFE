import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_surface.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/design/product_preview_visual_mode.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/decision/presentation/case_hero_header.dart';
import 'package:kefe_mobile/features/decision/presentation/decision_flow_screen.dart';
import 'package:kefe_mobile/features/media_presentation/application/case_media_provider.dart';
import 'package:kefe_mobile/features/media_presentation/data/preview_case_media_repository.dart';
import 'package:kefe_mobile/features/media_presentation/presentation/case_media_surface.dart';

const _caseId = 'slice-23-case';
const _caseVersionId = 'slice-23-version';

const _sampleCase = DecisionCase(
  id: _caseId,
  versionId: _caseVersionId,
  title: 'Kaynak nasıl paylaşılmalı?',
  summary: 'İki makul seçenek arasında kendi kararını tart.',
  format: 'DILEMMA',
  domain: 'DAILY_LIFE',
  risk: 'L0',
  questions: [
    DecisionQuestion(
      id: 'slice-23-question',
      prompt: 'Hangi seçeneği tercih edersin?',
      responseType: 'SINGLE_CHOICE',
      options: ['A', 'B'],
    ),
  ],
);

enum _DecisionFixture { loading, error, ready, submitting, offline, unsupported }

void main() {
  test('Slice 23 contract locks presentation-only shell convergence', () {
    final contract =
        jsonDecode(
              File(
                '../../docs/contracts/decision-flow-shell-state-slice23.v1.json',
              ).readAsStringSync(),
            )
            as Map<String, dynamic>;

    expect(contract['contract'], 'decision-flow-shell-state-slice23');
    expect(contract['scope']['decision_flow_shell_convergence'], isTrue);
    expect(contract['scope']['decision_controller_change'], isFalse);
    expect(contract['scope']['flow_runtime_change'], isFalse);
    expect(contract['scope']['route_change'], isFalse);
    expect(contract['root_state_transition']['uses_kefe_motion_resolve'], isTrue);
    expect(
      contract['states']['indeterminate_spinner_in_governed_source_forbidden'],
      isTrue,
    );
    expect(contract['production_case_header']['text_only'], isTrue);
    expect(
      contract['production_case_header']['preview_fixture_fallback'],
      isFalse,
    );
    expect(
      contract['product_preview']['existing_case_hero_header_preserved'],
      isTrue,
    );
    expect(contract['commit']['commit_button_key'], 'commit-button');
    expect(contract['commit']['reveal_before_commit'], isFalse);
    expect(contract['commit']['perspective_before_commit'], isFalse);
    expect(contract['invariants']['commit_first'], isTrue);
    expect(contract['invariants']['blind_first'], isTrue);
    expect(contract['invariants']['signal_in_scope'], isFalse);
    expect(contract['invariants']['impact_in_scope'], isFalse);
  });

  test('governed Decision Flow source has no legacy state chrome', () {
    final source = File(
      'lib/features/decision/presentation/decision_flow_screen.dart',
    ).readAsStringSync();

    expect(
      source,
      contains("import '../../../core/design/kefe_surface.dart';"),
    );
    expect(source, contains('KefeMotion.resolve('));
    expect(source, contains('_ProductionCaseSummaryHeader'));
    expect(source, contains('_CommitActionPanel'));
    expect(source, contains('CaseHeroHeader('));
    expect(source, contains('productPreviewVisualModeProvider'));
    expect(source, isNot(contains('CircularProgressIndicator')));
    expect(source, isNot(contains('return Card(')));
    expect(source, isNot(contains('child: Card(')));
    expect(
      source,
      isNot(contains('duration: const Duration(milliseconds: 220)')),
    );
    expect(source, isNot(contains('PreviewDecisionRepository')));
    expect(source, isNot(contains('PreviewCaseMediaRepository')));
    expect(source, contains("key: const ValueKey('commit-button')"));
    expect(source, contains('controller.retryPending'));
    expect(source, contains('controller.commit'));
  });

  testWidgets('loading, error and unsupported states are deterministic surfaces', (
    tester,
  ) async {
    await _pumpDecision(tester, fixture: _DecisionFixture.loading);
    expect(find.byKey(const ValueKey('loading')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.byType(KefeSurface), findsWidgets);
    expect(tester.takeException(), isNull);

    await _pumpDecision(tester, fixture: _DecisionFixture.error);
    expect(find.byKey(const ValueKey('error')), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(tester.takeException(), isNull);

    await _pumpDecision(tester, fixture: _DecisionFixture.unsupported);
    expect(
      find.byKey(const ValueKey('capability-pending-DECISION')),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('commit-button')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('production header stays text-only and Commit First remains intact', (
    tester,
  ) async {
    await _pumpDecision(tester, fixture: _DecisionFixture.ready);

    expect(
      find.byKey(const ValueKey('production-case-summary-header')),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
    expect(find.text(_sampleCase.title), findsOneWidget);
    expect(find.text(_sampleCase.summary), findsOneWidget);
    expect(find.byType(CaseHeroHeader), findsNothing);
    expect(find.byType(CaseMediaSurface), findsNothing);
    expect(find.byKey(const ValueKey('reveal-card')), findsNothing);

    await _scrollTo(tester, find.byKey(const ValueKey('commit-button')));
    expect(find.byKey(const ValueKey('commit-button')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Product Preview keeps the existing Case hero without pre-Commit result', (
    tester,
  ) async {
    await _pumpDecision(
      tester,
      fixture: _DecisionFixture.ready,
      productPreviewVisual: true,
    );

    expect(find.byType(CaseHeroHeader), findsOneWidget);
    expect(
      find.byKey(const ValueKey('production-case-summary-header')),
      findsNothing,
    );
    expect(find.byType(CaseMediaSurface), findsOneWidget);
    expect(find.byKey(const ValueKey('case-title')), findsOneWidget);
    expect(find.byKey(const ValueKey('reveal-card')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Commit-working and offline status preserve stable keys', (
    tester,
  ) async {
    await _pumpDecision(tester, fixture: _DecisionFixture.submitting);
    await _scrollTo(tester, find.byKey(const ValueKey('commit-button')));
    final button = tester.widget<FilledButton>(
      find.byKey(const ValueKey('commit-button')),
    );
    expect(button.onPressed, isNull);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(find.byKey(const ValueKey('reveal-card')), findsNothing);
    expect(tester.takeException(), isNull);

    await _pumpDecision(tester, fixture: _DecisionFixture.offline);
    await _scrollTo(
      tester,
      find.byKey(const ValueKey('decision-status-message')),
    );
    expect(
      find.byKey(const ValueKey('decision-status-message')),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('reveal-card')), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Decision shell is overflow-free in dark/light and enlarged text', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(360, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await _pumpDecision(
      tester,
      fixture: _DecisionFixture.ready,
      themeMode: ThemeMode.dark,
    );
    expect(
      find.byKey(const ValueKey('production-case-summary-header')),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);

    await _pumpDecision(
      tester,
      fixture: _DecisionFixture.ready,
      themeMode: ThemeMode.light,
      textScale: 1.6,
    );
    await _scrollTo(tester, find.byKey(const ValueKey('commit-button')));
    expect(find.byKey(const ValueKey('commit-action-panel')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

Future<void> _pumpDecision(
  WidgetTester tester, {
  required _DecisionFixture fixture,
  ThemeMode themeMode = ThemeMode.dark,
  double textScale = 1,
  bool productPreviewVisual = false,
}) async {
  final decisionOverride = switch (fixture) {
    _DecisionFixture.loading => decisionControllerProvider.overrideWith(
      _LoadingDecisionController.new,
    ),
    _DecisionFixture.error => decisionControllerProvider.overrideWith(
      _ErrorDecisionController.new,
    ),
    _DecisionFixture.ready => decisionControllerProvider.overrideWith(
      _ReadyDecisionController.new,
    ),
    _DecisionFixture.submitting => decisionControllerProvider.overrideWith(
      _SubmittingDecisionController.new,
    ),
    _DecisionFixture.offline => decisionControllerProvider.overrideWith(
      _OfflineDecisionController.new,
    ),
    _DecisionFixture.unsupported => decisionControllerProvider.overrideWith(
      _UnsupportedDecisionController.new,
    ),
  };

  await tester.pumpWidget(
    ProviderScope(
      key: UniqueKey(),
      overrides: [
        decisionOverride,
        productPreviewVisualModeProvider.overrideWithValue(
          productPreviewVisual,
        ),
        if (productPreviewVisual)
          caseMediaRepositoryProvider.overrideWithValue(
            const PreviewCaseMediaRepository(),
          ),
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
        home: const DecisionFlowScreen(caseId: _caseId),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> _scrollTo(WidgetTester tester, Finder finder) async {
  await tester.scrollUntilVisible(
    finder,
    280,
    scrollable: find.byType(Scrollable).last,
  );
  await tester.pumpAndSettle();
}

FlowRuntimeSnapshot _decisionRuntime({
  FlowStepRuntimeState state = FlowStepRuntimeState.ready,
  String? reasonCode,
}) {
  return FlowRuntimeSnapshot(
    sessionId: 'slice-23-session',
    caseVersionId: _caseVersionId,
    sessionState: 'DRAFT',
    templateCode: 'SLICE_23_TEST',
    templateVersionNo: 1,
    entryStepCode: 'DECISION',
    executionSupport: FlowExecutionSupport.full,
    steps: [
      FlowRuntimeStep(
        code: 'DECISION',
        primitiveCode: 'DECISION',
        capabilityCodes: const ['COMMIT_FIRST'],
        nextStepCodes: const [],
        state: state,
        reasonCode: reasonCode,
      ),
    ],
  );
}

abstract class _FixedDecisionController extends DecisionController {
  @override
  Future<void> load(String caseId) async {}
}

class _LoadingDecisionController extends _FixedDecisionController {
  @override
  DecisionState build() => const DecisionState(loading: true);
}

class _ErrorDecisionController extends _FixedDecisionController {
  @override
  DecisionState build() =>
      const DecisionState(errorCode: 'UNEXPECTED_CLIENT_ERROR');
}

class _ReadyDecisionController extends _FixedDecisionController {
  @override
  DecisionState build() => DecisionState(
    caseData: _sampleCase,
    sessionId: 'slice-23-session',
    flowRuntime: _decisionRuntime(),
  );
}

class _SubmittingDecisionController extends _FixedDecisionController {
  @override
  DecisionState build() => DecisionState(
    submitting: true,
    caseData: _sampleCase,
    sessionId: 'slice-23-session',
    flowRuntime: _decisionRuntime(),
    responses: const {'slice-23-question': 'A'},
  );
}

class _OfflineDecisionController extends _FixedDecisionController {
  @override
  DecisionState build() => DecisionState(
    offlineDraft: true,
    caseData: _sampleCase,
    sessionId: 'slice-23-session',
    flowRuntime: _decisionRuntime(),
    responses: const {'slice-23-question': 'A'},
    errorCode: 'NETWORK_UNAVAILABLE',
  );
}

class _UnsupportedDecisionController extends _FixedDecisionController {
  @override
  DecisionState build() => DecisionState(
    caseData: _sampleCase,
    sessionId: 'slice-23-session',
    flowRuntime: _decisionRuntime(
      state: FlowStepRuntimeState.unsupported,
      reasonCode: 'FLOW_DECISION_REVISION_REQUIRED',
    ),
  );
}
