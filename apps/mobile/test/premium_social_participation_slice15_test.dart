import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_surface.dart';
import 'package:kefe_mobile/core/design/kefe_theme.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/community_reason/application/community_reason_controller.dart';
import 'package:kefe_mobile/features/community_reason/data/community_reason_repository.dart';
import 'package:kefe_mobile/features/community_reason/presentation/community_reason_section.dart';
import 'package:kefe_mobile/features/consensus/application/consensus_controller.dart';
import 'package:kefe_mobile/features/consensus/data/consensus_repository.dart';
import 'package:kefe_mobile/features/consensus/domain/consensus_models.dart';
import 'package:kefe_mobile/features/consensus/presentation/consensus_section.dart';

void main() {
  test(
    'slice 15 contract locks post-Commit social participation boundaries',
    () {
      final contractFile = File(
        '../../docs/contracts/premium-social-participation-slice15.v1.json',
      );
      expect(contractFile.existsSync(), isTrue);

      final contract =
          jsonDecode(contractFile.readAsStringSync()) as Map<String, Object?>;
      final scope = contract['scope']! as Map<String, Object?>;
      final postCommit =
          contract['post_commit_boundary']! as Map<String, Object?>;
      final consensus = contract['consensus']! as Map<String, Object?>;
      final community = contract['community_reason']! as Map<String, Object?>;
      final presentation = contract['presentation']! as Map<String, Object?>;
      final invariants = contract['invariants']! as Map<String, Object?>;

      expect(scope['consensus_visual_convergence'], isTrue);
      expect(scope['community_reason_visual_convergence'], isTrue);
      expect(scope['new_consensus_methodology'], isFalse);
      expect(scope['new_community_distribution'], isFalse);
      expect(scope['backend_change'], isFalse);
      expect(scope['schema_change'], isFalse);
      expect(postCommit['committed_session_required'], isTrue);
      expect(postCommit['case_version_binding_preserved'], isTrue);
      expect(postCommit['pre_commit_exposure_added'], isFalse);
      expect(consensus['existing_aggregate_display_only'], isTrue);
      expect(consensus['new_metric_forbidden'], isTrue);
      expect(consensus['ranking_forbidden'], isTrue);
      expect(consensus['inference_forbidden'], isTrue);
      expect(community['feature_gate_preserved'], isTrue);
      expect(community['optional_text_max_length'], 300);
      expect(community['author_identity_added'], isFalse);
      expect(community['social_graph_added'], isFalse);
      expect(community['ranking_added'], isFalse);
      expect(community['recommendation_added'], isFalse);
      expect(presentation['semantic_kefe_surfaces_required'], isTrue);
      expect(presentation['direct_dark_only_tokens_forbidden'], isTrue);
      expect(presentation['continuous_loading_animation_added'], isFalse);
      expect(invariants['commit_first'], isTrue);
      expect(invariants['blind_first'], isTrue);
      expect(invariants['preview_production_isolation'], isTrue);
      expect(invariants['personality_inference'], isFalse);
      expect(invariants['causal_inference'], isFalse);
      expect(invariants['signal_in_scope'], isFalse);
      expect(invariants['impact_in_scope'], isFalse);
    },
  );

  testWidgets(
    'Community Reasons remains hidden while its feature gate is off',
    (tester) async {
      await _pumpLocalized(
        tester,
        locale: const Locale('en', 'US'),
        dark: false,
        consensusRepository: _FakeConsensusRepository(),
        communityRepository: _FakeCommunityReasonRepository(),
        communityEnabled: false,
      );

      expect(
        find.byKey(const ValueKey('community-reason-section')),
        findsNothing,
      );
    },
  );

  for (final locale in const [Locale('tr', 'TR'), Locale('en', 'US')]) {
    for (final dark in const [false, true]) {
      testWidgets(
        'social participation renders premium committed states in ${locale.languageCode} ${dark ? 'dark' : 'light'}',
        (tester) async {
          await _pumpLocalized(
            tester,
            locale: locale,
            dark: dark,
            consensusRepository: _FakeConsensusRepository(),
            communityRepository: _FakeCommunityReasonRepository(),
          );

          expect(
            find.byKey(const ValueKey('consensus-section')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('consensus-card-card-v1')),
            findsOneWidget,
          );
          expect(
            find.byKey(const ValueKey('community-reason-section')),
            findsOneWidget,
          );
          expect(find.byType(KefeSurface), findsWidgets);
          expect(
            Theme.of(
              tester.element(find.byKey(const ValueKey('consensus-section'))),
            ).brightness,
            dark ? Brightness.dark : Brightness.light,
          );
          expect(tester.takeException(), isNull);
        },
      );
    }
  }

  testWidgets(
    'existing Consensus submit and Community publish flows remain intact',
    (tester) async {
      final consensusRepository = _FakeConsensusRepository();
      final communityRepository = _FakeCommunityReasonRepository();

      await _pumpLocalized(
        tester,
        locale: const Locale('en', 'US'),
        dark: true,
        consensusRepository: consensusRepository,
        communityRepository: communityRepository,
      );

      await tester.tap(find.byKey(const ValueKey('consensus-stance-AGREE')));
      await tester.pump();
      await tester.tap(find.byKey(const ValueKey('consensus-submit')));
      await tester.pumpAndSettle();

      expect(consensusRepository.participateCalls, 1);
      expect(consensusRepository.lastSessionId, 'session-1');
      expect(consensusRepository.lastCaseVersionId, 'case-version-1');
      expect(consensusRepository.lastStanceCode, 'AGREE');
      expect(
        find.byKey(const ValueKey('consensus-result-card-v1')),
        findsOneWidget,
      );
      expect(
        find.byKey(const ValueKey('consensus-methodology-note')),
        findsOneWidget,
      );

      final communityTag = find.byKey(
        const ValueKey('community-reason-tag-FAIRNESS'),
      );
      await tester.ensureVisible(communityTag);
      await tester.pumpAndSettle();
      await tester.tap(communityTag);
      await tester.pump();

      final communityText = find.byKey(
        const ValueKey('community-reason-text'),
      );
      await tester.ensureVisible(communityText);
      await tester.enterText(communityText, 'A concise public reason');

      final communityPublish = find.byKey(
        const ValueKey('community-reason-publish'),
      );
      await tester.ensureVisible(communityPublish);
      await tester.pumpAndSettle();
      await tester.tap(communityPublish);
      await tester.pumpAndSettle();

      expect(communityRepository.publishCalls, 1);
      expect(communityRepository.lastSessionId, 'session-1');
      expect(communityRepository.lastTags, ['FAIRNESS']);
      expect(communityRepository.lastText, 'A concise public reason');
      expect(
        find.byKey(const ValueKey('community-reason-receipt')),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    },
  );

  test('governed social presentation rejects dark-only and spinner debt', () {
    final consensusSource = File(
      'lib/features/consensus/presentation/consensus_section.dart',
    ).readAsStringSync();
    final communitySource = File(
      'lib/features/community_reason/presentation/community_reason_section.dart',
    ).readAsStringSync();

    for (final source in [consensusSource, communitySource]) {
      expect(source, contains('kefeVisual'));
      expect(source, contains('KefeSurface'));
      expect(source, isNot(contains('KefeColorTokens.surfaceElevatedDark')));
      expect(source, isNot(contains('KefeColorTokens.borderDark')));
      expect(source, isNot(contains('KefeColorTokens.textMutedDark')));
      expect(source, isNot(contains('CircularProgressIndicator')));
    }
    expect(communitySource, isNot(contains('LinearProgressIndicator')));
    expect(consensusSource, contains('LinearProgressIndicator('));
    expect(consensusSource, contains('value: normalized'));
  });

  test(
    'Perspective keeps Consensus and Community behind committed context',
    () {
      final source = File(
        'lib/features/decision/presentation/perspective_section.dart',
      ).readAsStringSync();

      expect(source, contains('final hasCommittedContext ='));
      expect(source, contains('decision.reveal != null'));
      expect(source, contains('ConsensusSection(sessionId: sessionId'));
      expect(source, contains('CommunityReasonSection('));
      expect(source, contains('final consensus = hasCommittedContext'));
      expect(source, contains('final community = hasCommittedContext'));
    },
  );
}

Future<void> _pumpLocalized(
  WidgetTester tester, {
  required Locale locale,
  required bool dark,
  required ConsensusRepository consensusRepository,
  required CommunityReasonRepository communityRepository,
  bool communityEnabled = true,
}) async {
  tester.platformDispatcher.localeTestValue = locale;
  addTearDown(tester.platformDispatcher.clearLocaleTestValue);

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        consensusExperienceEnabledProvider.overrideWithValue(true),
        consensusRepositoryProvider.overrideWithValue(consensusRepository),
        communityReasonExperienceEnabledProvider.overrideWithValue(
          communityEnabled,
        ),
        communityReasonRepositoryProvider.overrideWithValue(
          communityRepository,
        ),
      ],
      child: MaterialApp(
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
        themeMode: dark ? ThemeMode.dark : ThemeMode.light,
        home: const Scaffold(
          body: SafeArea(
            child: SingleChildScrollView(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  ConsensusSection(
                    sessionId: 'session-1',
                    caseVersionId: 'case-version-1',
                  ),
                  SizedBox(height: 20),
                  CommunityReasonSection(
                    sessionId: 'session-1',
                    caseVersionId: 'case-version-1',
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

class _FakeConsensusRepository implements ConsensusRepository {
  int participateCalls = 0;
  String? lastSessionId;
  String? lastCaseVersionId;
  String? lastStanceCode;

  @override
  Future<List<ConsensusCard>> fetchCards({
    required String sessionId,
    required String caseVersionId,
  }) async => [_eligibleCard(caseVersionId)];

  @override
  Future<ConsensusCard> participate({
    required String sessionId,
    required String caseVersionId,
    required String cardId,
    required String cardVersionId,
    required String stanceCode,
    required List<String> reasonTagCodes,
    required String idempotencyKey,
  }) async {
    participateCalls += 1;
    lastSessionId = sessionId;
    lastCaseVersionId = caseVersionId;
    lastStanceCode = stanceCode;
    final card = _eligibleCard(caseVersionId);
    return card.copyWith(
      participationState: 'PARTICIPATED',
      participation: ConsensusParticipation(
        stanceCode: stanceCode,
        reasonTagCodes: reasonTagCodes,
        contributionClass: 'REPRESENTATIVE_PREVIEW',
        participatedAt: DateTime.utc(2026, 7, 31),
      ),
      aggregate: ConsensusAggregate(
        sampleSize: 42,
        stanceDistribution: const {'AGREE': 0.62, 'DISAGREE': 0.38},
        reasonPatternDistribution: const {'FAIRNESS': 0.55, 'RULES': 0.45},
        contributionClass: 'REPRESENTATIVE_PREVIEW',
        methodologyVersion: 'preview-v1',
        generatedAt: DateTime.utc(2026, 7, 31),
        provenanceNote: 'Representative preview methodology note.',
      ),
    );
  }

  ConsensusCard _eligibleCard(String caseVersionId) => ConsensusCard(
    id: 'card-1',
    versionId: 'card-v1',
    caseVersionId: caseVersionId,
    proposition: 'A representative consensus proposition',
    stanceCodes: const ['AGREE', 'DISAGREE'],
    reasonTagCodes: const ['FAIRNESS', 'RULES'],
    maxReasonTags: 2,
    methodologyVersion: 'preview-v1',
    participationState: 'ELIGIBLE',
    contributionClass: 'REPRESENTATIVE_PREVIEW',
  );
}

class _FakeCommunityReasonRepository implements CommunityReasonRepository {
  int publishCalls = 0;
  String? lastSessionId;
  List<String>? lastTags;
  String? lastText;

  @override
  Future<CommunityReasonSnapshot> fetch(String sessionId) async =>
      const CommunityReasonSnapshot(
        items: [
          CommunityReasonItem(
            id: 'reason-1',
            tags: ['FAIRNESS'],
            text: 'Existing moderated public reason',
            reactionCounts: {'RESONATES': 3, 'USEFUL': 2},
          ),
        ],
        tagPatternCounts: {'FAIRNESS': 3, 'RULES': 2},
        sampleSize: 5,
        methodologyNote: 'Representative preview methodology note.',
      );

  @override
  Future<CommunityReasonReceipt> publish({
    required String sessionId,
    required List<String> tags,
    String? text,
  }) async {
    publishCalls += 1;
    lastSessionId = sessionId;
    lastTags = List<String>.from(tags);
    lastText = text;
    return CommunityReasonReceipt(
      id: 'receipt-1',
      tags: tags,
      text: text,
      moderationState: 'PENDING',
    );
  }

  @override
  Future<void> react({
    required String reasonId,
    required String reaction,
  }) async {}

  @override
  Future<void> report({required String reasonId, required String code}) async {}
}
