import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/impact/domain/action_follow_through_models.dart';
import 'package:kefe_mobile/features/impact/presentation/action_follow_through_card.dart';

void main() {
  group('Community Action Proposal and Follow-through (CAP-051)', () {
    test('ADR-0152 and contract exist and are valid', () {
      final adr = File(
        '../../docs/adr/0152-action-proposal-and-milestone-follow-through.md',
      );
      final contract = File(
        '../../docs/contracts/action-follow-through.v1.json',
      );

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(
        contract.readAsStringSync(),
        contains('KEFE-ACTION-FOLLOW-THROUGH-001'),
      );
      expect(contract.readAsStringSync(), contains('VERIFIED_COMPLETE'));
    });

    test('ActionFollowThroughItem model instantiates properly', () {
      final item = ActionFollowThroughItem(
        id: 'act-1',
        caseVersionId: 'case-v1',
        title: 'Gece Seferleri İyileştirme Planı',
        description:
            'Belediye meclisine resmi başvuru ve komisyon müzakeresi.',
        status: ActionFollowThroughStatus.inProgress,
        progressPercentage: 65,
        createdAt: DateTime.now().toUtc(),
        evidenceSummary: 'Komisyon kararı yayınlandı.',
        evidenceUrl: 'https://belediye.gov.tr/kararlar/2026-44',
      );

      expect(item.title, 'Gece Seferleri İyileştirme Planı');
      expect(item.progressPercentage, 65);
      expect(item.status, ActionFollowThroughStatus.inProgress);
    });

    test('ActionFollowThroughItem serializes and deserializes JSON', () {
      final item = ActionFollowThroughItem(
        id: '99999999-9999-4999-8999-999999999901',
        caseVersionId: '22222222-2222-4222-8222-222222222222',
        title: 'Gece Seferleri İyileştirme Planı',
        description:
            'Belediye meclisine resmi başvuru ve komisyon müzakeresi.',
        status: ActionFollowThroughStatus.inProgress,
        progressPercentage: 65,
        createdAt: DateTime.utc(2026, 8, 29, 10, 0),
        evidenceSummary: 'Komisyon kararı yayınlandı.',
        evidenceUrl: 'https://belediye.gov.tr/kararlar/2026-44',
      );

      final json = item.toJson();
      final reconstituted = ActionFollowThroughItem.fromJson(json);

      expect(reconstituted.id, item.id);
      expect(reconstituted.title, item.title);
      expect(reconstituted.status, ActionFollowThroughStatus.inProgress);
      expect(reconstituted.progressPercentage, 65);
      expect(
        reconstituted.evidenceUrl,
        'https://belediye.gov.tr/kararlar/2026-44',
      );
    });

    test(
      'InternalAlphaStrings contains Action Follow-through localized strings',
      () {
        const tr = KefeStrings(Locale('tr'));
        expect(tr.actionEyebrow, contains('EYLEM'));
        expect(tr.actionStatusInProgress, contains('Devam'));
        expect(tr.actionProgressLabel(65), contains('%65'));

        const en = KefeStrings(Locale('en'));
        expect(en.actionEyebrow, contains('ACTION'));
        expect(en.actionStatusInProgress, contains('Progress'));
        expect(en.actionProgressLabel(65), contains('65%'));
      },
    );

    testWidgets(
      'ActionFollowThroughCard renders title, progress and evidence badge',
      (tester) async {
        final item = ActionFollowThroughItem(
          id: 'act-test-1',
          caseVersionId: 'case-test-1',
          title: 'Gece Seferleri İyileştirme Planı',
          description:
              'Belediye meclisine resmi başvuru ve komisyon müzakeresi.',
          status: ActionFollowThroughStatus.inProgress,
          progressPercentage: 65,
          createdAt: DateTime.utc(2026, 8, 29, 10, 0),
          evidenceSummary: 'Komisyon kararı yayınlandı.',
          evidenceUrl: 'https://belediye.gov.tr/kararlar/2026-44',
        );

        await tester.pumpWidget(
          MaterialApp(
            locale: const Locale('tr', 'TR'),
            supportedLocales: KefeStrings.supportedLocales,
            localizationsDelegates: const [
              KefeStringsDelegate(),
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            home: Scaffold(body: ActionFollowThroughCard(action: item)),
          ),
        );

        await tester.pumpAndSettle();

        expect(
          find.byKey(const ValueKey('action-milestone-act-test-1')),
          findsOneWidget,
        );
        expect(find.text('Gece Seferleri İyileştirme Planı'), findsOneWidget);
        expect(
          find.textContaining('Komisyon kararı yayınlandı.'),
          findsOneWidget,
        );
        expect(find.textContaining('%65'), findsOneWidget);
      },
    );
  });
}
