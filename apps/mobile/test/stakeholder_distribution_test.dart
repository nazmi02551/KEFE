import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/stakeholder_distribution_models.dart';
import 'package:kefe_mobile/features/decision/presentation/stakeholder_distribution_card.dart';

void main() {
  group('Stakeholder Distribution Engine (CAP-037)', () {
    test('ADR-0253 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0253-stakeholder-distribution.md');
      final contract = File('../../docs/contracts/stakeholder-distribution.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-STAKEHOLDER-DISTRIBUTION-001'));
      expect(contract.readAsStringSync(), contains('DIRECTLY_IMPACTED'));
    });

    test('StakeholderDistributionModel instantiates and round-trips correctly', () {
      const model = StakeholderDistributionModel(
        caseVersionId: 'case-ver-sh-1',
        totalStakeholdersRepresented: 890,
        activeCategoriesCount: 2,
        stakeholderDistributions: [
          StakeholderDistributionItemModel(
            category: 'DIRECTLY_IMPACTED',
            name: 'Doğrudan Etkilenen Yurttaşlar',
            participantCount: 350,
            sampleShare: 0.393,
            optionShares: {'A': 0.7, 'B': 0.3},
            primaryChoice: 'A',
            cohesionIndex: 0.58,
            divergenceFromOverallPoints: 18,
          ),
          StakeholderDistributionItemModel(
            category: 'COMMERCIAL_ENTERPRISES',
            name: 'Sektörel İşletmeler',
            participantCount: 540,
            sampleShare: 0.607,
            optionShares: {'A': 0.35, 'B': 0.65},
            primaryChoice: 'B',
            cohesionIndex: 0.54,
            divergenceFromOverallPoints: -17,
          ),
        ],
        pluralismScore: 0.786,
        generatedAt: '2026-09-04T10:30:00Z',
      );

      expect(model.caseVersionId, 'case-ver-sh-1');
      expect(model.totalStakeholdersRepresented, 890);
      expect(model.activeCategoriesCount, 2);
      expect(model.stakeholderDistributions.length, 2);
      expect(model.stakeholderDistributions.first.category, 'DIRECTLY_IMPACTED');
      expect(model.stakeholderDistributions.first.divergenceFromOverallPoints, 18);

      final json = model.toJson();
      final roundTrip = StakeholderDistributionModel.fromJson(json);
      expect(roundTrip.caseVersionId, model.caseVersionId);
      expect(roundTrip.totalStakeholdersRepresented, 890);
      expect(roundTrip.stakeholderDistributions.first.primaryChoice, 'A');
      expect(roundTrip.stakeholderDistributions.last.category, 'COMMERCIAL_ENTERPRISES');
    });

    test('InternalAlphaStrings contains Stakeholder Distribution localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.stakeholderDistEyebrow, contains('ÇOK PAYDAŞLI'));
      expect(tr.stakeholderDistTitle, contains('Müzakere Topolojisi'));
      expect(tr.stakeholderDistTotalRepresented(500), contains('500'));
      expect(tr.stakeholderDistRoleDirectlyImpacted, contains('Doğrudan'));

      const en = KefeStrings(Locale('en'));
      expect(en.stakeholderDistEyebrow, contains('MULTI-STAKEHOLDER'));
      expect(en.stakeholderDistTitle, contains('Deliberation Topology'));
      expect(en.stakeholderDistTotalRepresented(500), contains('500'));
      expect(en.stakeholderDistRoleDirectlyImpacted, contains('Directly Impacted'));
    });

    testWidgets('StakeholderDistributionCard renders properly in TR locale', (tester) async {
      const model = StakeholderDistributionModel(
        caseVersionId: 'case-widget-sh-1',
        totalStakeholdersRepresented: 450,
        activeCategoriesCount: 2,
        stakeholderDistributions: [
          StakeholderDistributionItemModel(
            category: 'DIRECTLY_IMPACTED',
            name: 'Doğrudan Etkilenenler Grubu',
            participantCount: 200,
            sampleShare: 0.444,
            optionShares: {'A': 0.65, 'B': 0.35},
            primaryChoice: 'A',
            cohesionIndex: 0.55,
            divergenceFromOverallPoints: 13,
          ),
          StakeholderDistributionItemModel(
            category: 'REGULATORY_OVERSIGHT',
            name: 'Denetleyici Kurullar',
            participantCount: 250,
            sampleShare: 0.556,
            optionShares: {'A': 0.40, 'B': 0.60},
            primaryChoice: 'B',
            cohesionIndex: 0.52,
            divergenceFromOverallPoints: -12,
          ),
        ],
        pluralismScore: 0.888,
        generatedAt: '2026-09-04T10:30:00Z',
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
              child: StakeholderDistributionCard(
                distribution: model,
              ),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(StakeholderDistributionCard), findsOneWidget);
      expect(find.textContaining('ÇOK PAYDAŞLI'), findsOneWidget);
      expect(find.textContaining('Müzakere Topolojisi'), findsOneWidget);
      expect(find.textContaining('450'), findsOneWidget);
      expect(find.text('Doğrudan Etkilenenler Grubu'), findsOneWidget);
      expect(find.text('Denetleyici Kurullar'), findsOneWidget);
      expect(find.textContaining('+%13'), findsOneWidget);
      expect(find.textContaining('-%12'), findsOneWidget);
    });
  });
}
