import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/community_dilemma_proposals_models.dart';
import 'package:kefe_mobile/features/decision/presentation/community_dilemma_proposals_card.dart';

void main() {
  group('Community Dilemma Proposals & Curation (CAP-030)', () {
    test('ADR-0200 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0200-community-dilemma-proposals.md');
      final contract = File('../../docs/contracts/community-dilemma-proposals.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-COMMUNITY-UGC-001'));
      expect(contract.readAsStringSync(), contains('COMMUNITY_PEER_REVIEW'));
    });

    test('CommunityDilemmaProposalModel instantiates properly', () {
      const model = CommunityDilemmaProposalModel(
        proposalId: 'prop_1',
        proposedTitle: 'Yapay Zeka Telif Hakları',
        proposedContext: 'Üretken modellerin eğitimi telife tabi olmalı mıdır?',
        curationState: CurationStateModel.communityPeerReview,
        neutralityScore: 0.88,
        supporterCount: 42,
      );

      expect(model.neutralityScore, 0.88);
      expect(model.curationState, CurationStateModel.communityPeerReview);
    });

    test('InternalAlphaStrings contains Community Dilemma localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.ugcPropEyebrow, contains('TOPLULUK İKİLEM'));
      expect(tr.ugcPropStateReview, contains('Hakem'));

      const en = KefeStrings(Locale('en'));
      expect(en.ugcPropEyebrow, contains('COMMUNITY DILEMMA'));
      expect(en.ugcPropStateReview, contains('Peer Review'));
    });

    testWidgets('CommunityDilemmaProposalsCard renders correctly', (tester) async {
      const model = CommunityDilemmaProposalModel(
        proposalId: 'prop_1',
        proposedTitle: 'Yapay Zeka Telif Hakları',
        proposedContext: 'Üretken modellerin eğitimi telife tabi olmalı mıdır?',
        curationState: CurationStateModel.communityPeerReview,
        neutralityScore: 0.88,
        supporterCount: 42,
      );

      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData.dark().copyWith(
            extensions: const [KefeVisualTheme.dark],
          ),
          locale: const Locale('tr', 'TR'),
          supportedLocales: KefeStrings.supportedLocales,
          localizationsDelegates: const [
            KefeStringsDelegate(),
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: const Scaffold(
            body: SingleChildScrollView(
              child: CommunityDilemmaProposalsCard(proposal: model),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(CommunityDilemmaProposalsCard), findsOneWidget);
      expect(find.text('Yapay Zeka Telif Hakları'), findsOneWidget);
    });
  });
}


