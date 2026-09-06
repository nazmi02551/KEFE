import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/responsibility_analysis_models.dart';
import 'package:kefe_mobile/features/decision/presentation/responsibility_analysis_card.dart';

void main() {
  group('Responsibility Analysis Engine (CAP-020)', () {
    test('ADR-0250 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0250-responsibility-analysis.md');
      final contract = File('../../docs/contracts/responsibility-analysis.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-RESPONSIBILITY-ANALYSIS-001'));
      expect(contract.readAsStringSync(), contains('LEGAL_LIABILITY'));
    });

    test('ResponsibilityAnalysisModel instantiates and serializes properly', () {
      const model = ResponsibilityAnalysisModel(
        analysisId: 'resp-unit-1',
        caseVersionId: 'case-ver-unit',
        clarityScore: 0.88,
        hasAccountabilityGap: false,
        legalRedressChannel: 'İdare Mahkemesi',
        actorAllocations: [
          ActorResponsibilityModel(
            actorKey: 'REGULATOR',
            actorName: 'Denetleme Kurumu',
            responsibilityShare: 0.5,
            dutyNature: 'REGULATORY_OVERSIGHT',
            jurisdictionScope: 'Sektörel standart belirleme',
            accountabilityMechanism: 'Para cezası',
          ),
          ActorResponsibilityModel(
            actorKey: 'OPERATOR',
            actorName: 'Hizmet Sağlayıcı',
            responsibilityShare: 0.5,
            dutyNature: 'OPERATIONAL_EXECUTION',
            jurisdictionScope: 'Saha operasyonları',
          ),
        ],
      );

      expect(model.analysisId, 'resp-unit-1');
      expect(model.clarityScore, 0.88);
      expect(model.actorAllocations.length, 2);

      final json = model.toJson();
      final roundTrip = ResponsibilityAnalysisModel.fromJson(json);
      expect(roundTrip.analysisId, model.analysisId);
      expect(roundTrip.clarityScore, model.clarityScore);
      expect(roundTrip.actorAllocations.first.actorName, 'Denetleme Kurumu');
    });

    test('InternalAlphaStrings contains Responsibility Analysis localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.respAnalysisEyebrow, contains('SORUMLULUK'));
      expect(tr.respAnalysisDutyLegal, contains('Hukuki Sorumluluk'));

      const en = KefeStrings(Locale('en'));
      expect(en.respAnalysisEyebrow, contains('RESPONSIBILITY'));
      expect(en.respAnalysisDutyLegal, contains('Legal Liability'));
    });

    testWidgets('ResponsibilityAnalysisCard renders properly in TR locale', (tester) async {
      const model = ResponsibilityAnalysisModel(
        analysisId: 'resp-widget-tr',
        caseVersionId: 'case-version-tr',
        clarityScore: 0.84,
        hasAccountabilityGap: false,
        legalRedressChannel: 'Danıştay ve Kamu Denetçiliği Kurumu',
        actorAllocations: [
          ActorResponsibilityModel(
            actorKey: 'MINISTRY',
            actorName: 'Çevre ve Şehircilik Bakanlığı',
            responsibilityShare: 0.55,
            dutyNature: 'REGULATORY_OVERSIGHT',
            jurisdictionScope: 'Mevzuat denetimi ve ruhsatlandırma',
          ),
          ActorResponsibilityModel(
            actorKey: 'MUNICIPALITY',
            actorName: 'Büyükşehir Belediyesi',
            responsibilityShare: 0.45,
            dutyNature: 'OPERATIONAL_EXECUTION',
            jurisdictionScope: 'Saha denetimleri ve atık yönetimi',
          ),
        ],
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
              child: ResponsibilityAnalysisCard(analysis: model),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(ResponsibilityAnalysisCard), findsOneWidget);
      expect(find.textContaining('SORUMLULUK'), findsOneWidget);
      expect(find.textContaining('%84'), findsOneWidget);
      expect(find.textContaining('Çevre ve Şehircilik'), findsOneWidget);
      expect(find.textContaining('Danıştay'), findsOneWidget);
    });
  });
}
