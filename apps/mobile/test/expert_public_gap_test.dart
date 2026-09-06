import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/expert_public_gap_models.dart';
import 'package:kefe_mobile/features/decision/presentation/expert_public_gap_card.dart';

void main() {
  group('Expert-Public Gap Engine (CAP-041)', () {
    test('ADR-0254 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0254-expert-public-gap.md');
      final contract = File('../../docs/contracts/expert-public-gap.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-EXPERT-PUBLIC-GAP-001'));
      expect(contract.readAsStringSync(), contains('TECHNICAL_TRANSLATION_GAP'));
    });

    test('ExpertPublicGapModel instantiates and round-trips correctly', () {
      const model = ExpertPublicGapModel(
        caseVersionId: 'case-epg-test-1',
        expertSampleSize: 80,
        publicSampleSize: 900,
        expertDistribution: {'A': 0.85, 'B': 0.15},
        publicDistribution: {'A': 0.50, 'B': 0.50},
        gapMagnitudePoints: 35,
        gapClassification: 'NORMATIVE_VALUE_DIVERGENCE',
        keyDivergenceDrivers: ['Teknik risk algısı', 'Maliyet farkı'],
        epistemicBridges: ['Yurttaş panelleri', 'Açık metodoloji'],
        generatedAt: '2026-09-04T11:00:00Z',
      );

      expect(model.caseVersionId, 'case-epg-test-1');
      expect(model.expertSampleSize, 80);
      expect(model.publicSampleSize, 900);
      expect(model.gapMagnitudePoints, 35);
      expect(model.gapClassification, 'NORMATIVE_VALUE_DIVERGENCE');

      final json = model.toJson();
      final roundTrip = ExpertPublicGapModel.fromJson(json);
      expect(roundTrip.caseVersionId, model.caseVersionId);
      expect(roundTrip.expertSampleSize, 80);
      expect(roundTrip.gapMagnitudePoints, 35);
      expect(roundTrip.keyDivergenceDrivers.length, 2);
      expect(roundTrip.epistemicBridges.length, 2);
    });

    test('InternalAlphaStrings contains Expert-Public Gap localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.expertGapEyebrow, contains('UZMAN-KAMU'));
      expect(tr.expertGapTitle, contains('Uzman Mutabakatı'));
      expect(tr.expertGapMagnitude(25), contains('%25'));
      expect(tr.expertGapClassConvergent, contains('Ortak Mutabakat'));

      const en = KefeStrings(Locale('en'));
      expect(en.expertGapEyebrow, contains('EXPERT-PUBLIC'));
      expect(en.expertGapTitle, contains('Domain Consensus'));
      expect(en.expertGapMagnitude(25), contains('25'));
      expect(en.expertGapClassConvergent, contains('Convergent'));
    });

    testWidgets('ExpertPublicGapCard renders properly in TR locale', (tester) async {
      const model = ExpertPublicGapModel(
        caseVersionId: 'case-epg-widget-1',
        expertSampleSize: 60,
        publicSampleSize: 500,
        expertDistribution: {'A': 0.75, 'B': 0.25},
        publicDistribution: {'A': 0.45, 'B': 0.55},
        gapMagnitudePoints: 30,
        gapClassification: 'NORMATIVE_VALUE_DIVERGENCE',
        keyDivergenceDrivers: ['Risk algısındaki fark'],
        epistemicBridges: ['Kademeli pilot deneme'],
        generatedAt: '2026-09-04T11:00:00Z',
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
              child: ExpertPublicGapCard(gap: model),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(ExpertPublicGapCard), findsOneWidget);
      expect(find.textContaining('UZMAN-KAMU'), findsOneWidget);
      expect(find.textContaining('Uzman Mutabakatı'), findsOneWidget);
      expect(find.textContaining('%30'), findsOneWidget);
      expect(find.textContaining('Değer ve Ahlaki Öncelik'), findsOneWidget);
      expect(find.text('Risk algısındaki fark'), findsOneWidget);
      expect(find.text('Kademeli pilot deneme'), findsOneWidget);
    });
  });
}
