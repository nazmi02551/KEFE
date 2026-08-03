import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/core/config/experience_presentation_config.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';

import 'support/flow_runtime_fixture.dart';

const legacyCaseId = 'dddddddd-1111-4111-8111-dddddddddddd';

class LegacyModeRepository
    with StandardFlowRuntimeFake
    implements DecisionRepository {
  LegacyModeRepository() {
    flowCaseVersionId = 'legacy-version-1';
  }

  @override
  Future<void> answer({
    required String sessionId,
    required String questionId,
    required Object value,
  }) async {}

  @override
  Future<void> savePrivateReason({
    required String sessionId,
    required List<String> tags,
    required String? text,
  }) async {}

  @override
  Future<void> commit({
    required String sessionId,
    required String idempotencyKey,
  }) async {
    flowCommitted = true;
  }

  @override
  Future<GuestCredential> ensureGuestCredential() async => GuestCredential(
        actorId: 'legacy-actor',
        accessToken: 'legacy-token',
        expiresAt: DateTime.utc(2026, 9),
      );

  @override
  Future<DecisionCase> fetchCase(String caseId) async => const DecisionCase(
        id: legacyCaseId,
        versionId: 'legacy-version-1',
        title: 'Legacy sunum testi',
        summary: 'Eski uzun akış geri dönüş için korunur.',
        format: 'DILEMMA',
        domain: 'DAILY_LIFE',
        risk: 'L0',
        questions: [
          DecisionQuestion(
            id: 'legacy-question',
            prompt: 'Bir seçenek seç',
            responseType: 'SINGLE_CHOICE',
            options: ['A', 'B'],
          ),
        ],
      );

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async =>
      const [];

  @override
  Future<RevealResult> reveal(String sessionId) async => const RevealResult(
        layer: 'TRUSTED',
        sampleSize: 10,
        confidence: 'LOW',
        values: {'A': 0.5, 'B': 0.5},
      );

  @override
  Future<String> startSession(String caseId) async => 'legacy-session';
}

void main() {
  testWidgets('legacy long-scroll renderer remains available', (tester) async {
    tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
    addTearDown(tester.platformDispatcher.clearLocaleTestValue);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          decisionRepositoryProvider.overrideWithValue(LegacyModeRepository()),
          decisionDraftStoreProvider.overrideWithValue(
            MemoryDecisionDraftStore(),
          ),
          experiencePresentationConfigProvider.overrideWithValue(
            const ExperiencePresentationConfig(
              decisionJourneyMode:
                  DecisionJourneyPresentationMode.legacyLongScroll,
              onboardingVersion: OnboardingExperienceVersion.legacyV1,
            ),
          ),
        ],
        child: const KefeApp(initialLocation: '/case/$legacyCaseId'),
      ),
    );
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('legacy-decision-long-scroll')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('progressive-decision-journey')),
      findsNothing,
    );
    expect(find.byKey(const ValueKey('commit-button')), findsOneWidget);
  });
}
