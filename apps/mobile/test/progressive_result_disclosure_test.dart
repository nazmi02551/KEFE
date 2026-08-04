import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/app/kefe_app.dart';
import 'package:kefe_mobile/core/config/experience_presentation_config.dart';
import 'package:kefe_mobile/features/community_reason/application/community_reason_controller.dart';
import 'package:kefe_mobile/features/community_reason/data/preview_community_reason_repository.dart';
import 'package:kefe_mobile/features/consensus/application/consensus_controller.dart';
import 'package:kefe_mobile/features/consensus/data/preview_consensus_repository.dart';
import 'package:kefe_mobile/features/decision/application/decision_controller.dart';
import 'package:kefe_mobile/features/decision/data/decision_draft_store.dart';
import 'package:kefe_mobile/features/decision/data/decision_repository.dart';
import 'package:kefe_mobile/features/decision/domain/decision_models.dart';
import 'package:kefe_mobile/features/progress/application/progress_controller.dart';
import 'package:kefe_mobile/features/progress/data/preview_progress_repository.dart';
import 'package:kefe_mobile/features/sharing/application/share_controller.dart';
import 'package:kefe_mobile/features/sharing/data/preview_share_repository.dart';

import 'support/flow_runtime_fixture.dart';

const disclosureCaseId = 'ffffffff-1111-4111-8111-ffffffffffff';

class DisclosureRepository
    with StandardFlowRuntimeFake
    implements DecisionRepository, PerspectiveRepository {
  int commitCalls = 0;
  int perspectiveCalls = 0;

  @override
  Future<GuestCredential> ensureGuestCredential() async => GuestCredential(
    actorId: 'disclosure-actor',
    accessToken: 'disclosure-token',
    expiresAt: DateTime.utc(2026, 9),
  );

  @override
  Future<DecisionCase> fetchCase(String caseId) async => const DecisionCase(
    id: disclosureCaseId,
    versionId: 'version-1',
    title: 'Sonuç açıklama testi',
    summary: 'Karar sabitlenmeden sonuç ve bakışlar açılmaz.',
    format: 'DILEMMA',
    domain: 'DAILY_LIFE',
    risk: 'L0',
    questions: [
      DecisionQuestion(
        id: 'disclosure-question',
        prompt: 'Hangisini seçerdin?',
        responseType: 'SINGLE_CHOICE',
        options: ['A', 'B'],
      ),
    ],
  );

  @override
  Future<String> startSession(String caseId) async => 'disclosure-session';

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
    commitCalls += 1;
    flowCommitted = true;
  }

  @override
  Future<RevealResult> reveal(String sessionId) async => const RevealResult(
    layer: 'TRUSTED',
    sampleSize: 128,
    confidence: 'HIGH',
    values: {'A': 0.58, 'B': 0.42},
  );

  @override
  Future<PerspectiveResult> fetchPerspectives(String sessionId) async {
    perspectiveCalls += 1;
    return PerspectiveResult(
      sessionId: sessionId,
      caseVersionId: 'version-1',
      cards: const [
        PerspectiveCard(
          id: 'near',
          slot: PerspectiveSlot.near,
          body: 'Yakın ama aynı olmayan bir gerekçe.',
          sourceKind: 'CURATED',
          provenanceLabel: 'Editoryal seçim',
          moderationState: 'ALLOWED',
        ),
        PerspectiveCard(
          id: 'opposing',
          slot: PerspectiveSlot.opposing,
          body: 'Karşı yöndeki güçlü bir gerekçe.',
          sourceKind: 'CURATED',
          provenanceLabel: 'Editoryal seçim',
          moderationState: 'ALLOWED',
        ),
        PerspectiveCard(
          id: 'bridge',
          slot: PerspectiveSlot.bridge,
          body: 'İki tarafın ortak değer noktası.',
          sourceKind: 'CURATED',
          provenanceLabel: 'Editoryal seçim',
          moderationState: 'ALLOWED',
        ),
        PerspectiveCard(
          id: 'context',
          slot: PerspectiveSlot.alternativeContext,
          body: 'Bağlam değiştiğinde farklılaşabilecek nokta.',
          sourceKind: 'CURATED',
          provenanceLabel: 'Editoryal seçim',
          moderationState: 'ALLOWED',
        ),
      ],
      methodology: PerspectiveMethodology(
        mode: 'DEGRADED_CURATED',
        sampleKind: 'CURATED_FALLBACK',
        sampleSize: 4,
        generatedAt: DateTime.utc(2026, 8, 3),
        provenanceNote: 'Test fixture.',
      ),
    );
  }

  @override
  Future<List<DecisionCaseSummary>> fetchExploreCases({int limit = 20}) async =>
      const [];
}

Future<void> tapVisible(WidgetTester tester, Finder finder) async {
  await tester.scrollUntilVisible(
    finder,
    300,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.pump();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

Future<void> expectReachable(WidgetTester tester, Key key) async {
  final matches = find.byKey(key);
  expect(matches, findsWidgets);
  final finder = matches.last;
  await tester.scrollUntilVisible(
    finder,
    400,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.pumpAndSettle();
  expect(finder, findsOneWidget);
}

void main() {
  testWidgets(
    'Reveal precedes Perspective and post-Commit capabilities remain reachable',
    (tester) async {
      tester.platformDispatcher.localeTestValue = const Locale('tr', 'TR');
      addTearDown(tester.platformDispatcher.clearLocaleTestValue);
      final repository = DisclosureRepository();

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            decisionRepositoryProvider.overrideWithValue(repository),
            decisionDraftStoreProvider.overrideWithValue(
              MemoryDecisionDraftStore(),
            ),
            experiencePresentationConfigProvider.overrideWithValue(
              const ExperiencePresentationConfig.progressive(),
            ),
            consensusExperienceEnabledProvider.overrideWithValue(true),
            consensusRepositoryProvider.overrideWithValue(
              PreviewConsensusRepository(),
            ),
            communityReasonExperienceEnabledProvider.overrideWithValue(true),
            communityReasonRepositoryProvider.overrideWithValue(
              PreviewCommunityReasonRepository(),
            ),
            shareExperienceEnabledProvider.overrideWithValue(true),
            shareRepositoryProvider.overrideWithValue(PreviewShareRepository()),
            progressRepositoryProvider.overrideWithValue(
              PreviewProgressRepository(),
            ),
          ],
          child: const KefeApp(initialLocation: '/case/$disclosureCaseId'),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('reveal-card')), findsNothing);
      expect(find.byKey(const ValueKey('perspective-section')), findsNothing);

      await tapVisible(tester, find.byKey(const ValueKey('option-A')));
      await tapVisible(tester, find.byKey(const ValueKey('commit-button')));

      expect(repository.commitCalls, 1);
      expect(repository.perspectiveCalls, 1);
      expect(find.byKey(const ValueKey('reveal-card')), findsOneWidget);
      expect(
        find.byKey(const ValueKey('perspective-disclosure-prompt')),
        findsOneWidget,
      );
      expect(find.byKey(const ValueKey('perspective-section')), findsNothing);

      await expectReachable(tester, const ValueKey('consensus-section'));
      await expectReachable(tester, const ValueKey('community-reason-section'));
      await expectReachable(tester, const ValueKey('my-kefe-progress'));
      await expectReachable(tester, const ValueKey('share-section'));

      await tester.scrollUntilVisible(
        find.byKey(const ValueKey('show-perspectives-button')),
        -400,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pump();
      await tester.tap(find.byKey(const ValueKey('show-perspectives-button')));
      await tester.pumpAndSettle();

      expect(find.byKey(const ValueKey('perspective-section')), findsOneWidget);
      expect(
        find.byKey(const ValueKey('perspective-disclosure-prompt')),
        findsNothing,
      );

      await expectReachable(tester, const ValueKey('consensus-section'));
      await expectReachable(tester, const ValueKey('community-reason-section'));
      await expectReachable(tester, const ValueKey('my-kefe-progress'));
      await expectReachable(tester, const ValueKey('share-section'));
    },
  );
}
