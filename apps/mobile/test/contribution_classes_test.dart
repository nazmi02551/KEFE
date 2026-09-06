import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/signal/domain/contribution_classes_models.dart';
import 'package:kefe_mobile/features/signal/presentation/contribution_classes_card.dart';

void main() {
  group('Contribution Classes Separation (CAP-043)', () {
    test('ADR-0256 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0256-contribution-classes-separation.md');
      final contract = File('../../docs/contracts/contribution-classes.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-CONTRIBUTION-CLASSES-001'));
      expect(contract.readAsStringSync(), contains('CORE_PRE_RESULT'));
      expect(contract.readAsStringSync(), contains('ADVOCACY_SUPPORT'));
    });

    test('ContributionClassesReportModel instantiates and round-trips correctly', () {
      const cCore = ContributionClassSummaryModel(
        classId: ContributionClassIdModel.corePreResult,
        nameTr: 'Körleme Öncesi Asil Katılım',
        nameEn: 'Core Pre-Result Deliberation',
        count: 1420,
        percentage: 72.82,
        isSignalEligible: true,
        description: 'Bağımsız ilk karar girdileri.',
      );

      const cExposed = ContributionClassSummaryModel(
        classId: ContributionClassIdModel.exposed,
        nameTr: 'İfşa Sonrası / Fikir Değişimi',
        nameEn: 'Post-Reveal Shift of Mind',
        count: 380,
        percentage: 19.49,
        isSignalEligible: false,
        description: 'Karşı argümanlar sonrası güncellenen girdiler.',
      );

      const cAdvocacy = ContributionClassSummaryModel(
        classId: ContributionClassIdModel.advocacySupport,
        nameTr: 'Savunuculuk ve Eylem Desteği',
        nameEn: 'Advocacy & Action Mobilization',
        count: 150,
        percentage: 7.69,
        isSignalEligible: false,
        description: 'Dilekçe ve topluluk eylem taahhütleri.',
      );

      const report = ContributionClassesReportModel(
        caseVersionId: '22222222-2222-4222-8222-222222222222',
        totalContributions: 1950,
        classes: [cCore, cExposed, cAdvocacy],
        contaminationRiskIndex: 0.0,
        isolationAuditStatus: 'ENFORCED',
        certifiedAt: '2026-08-20T10:00:00Z',
        isolationProofHash: '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
      );

      final json = report.toJson();
      final roundTrip = ContributionClassesReportModel.fromJson(json);

      expect(roundTrip.caseVersionId, report.caseVersionId);
      expect(roundTrip.totalContributions, 1950);
      expect(roundTrip.classes.length, 3);
      expect(roundTrip.classes.first.isSignalEligible, isTrue);
      expect(roundTrip.isolationAuditStatus, 'ENFORCED');
    });

    test('InternalAlphaStrings contains contribution classes localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.contribClassesEyebrow, contains('KATKI SINIFLARI'));
      expect(tr.contribClassesTitle, contains('Körleme Öncesi'));
      expect(tr.contribClassesIsolationEnforced, contains('AKTİF'));
      expect(tr.contribClassesEligibleBadge, contains('Sinyale Uygun'));

      const en = KefeStrings(Locale('en'));
      expect(en.contribClassesEyebrow, contains('CONTRIBUTION CLASSES'));
      expect(en.contribClassesTitle, contains('Pre-Result'));
      expect(en.contribClassesIsolationEnforced, contains('ENFORCED'));
      expect(en.contribClassesEligibleBadge, contains('Signal Eligible'));
    });

    testWidgets('ContributionClassesCard renders correctly in TR locale', (tester) async {
      const cCore = ContributionClassSummaryModel(
        classId: ContributionClassIdModel.corePreResult,
        nameTr: 'Körleme Öncesi Asil Katılım',
        nameEn: 'Core Pre-Result Deliberation',
        count: 1420,
        percentage: 72.82,
        isSignalEligible: true,
        description: 'Bağımsız ilk karar girdileri.',
      );

      const cExposed = ContributionClassSummaryModel(
        classId: ContributionClassIdModel.exposed,
        nameTr: 'İfşa Sonrası / Fikir Değişimi',
        nameEn: 'Post-Reveal Shift of Mind',
        count: 380,
        percentage: 19.49,
        isSignalEligible: false,
        description: 'Karşı argümanlar sonrası güncellenen girdiler.',
      );

      const cAdvocacy = ContributionClassSummaryModel(
        classId: ContributionClassIdModel.advocacySupport,
        nameTr: 'Savunuculuk ve Eylem Desteği',
        nameEn: 'Advocacy & Action Mobilization',
        count: 150,
        percentage: 7.69,
        isSignalEligible: false,
        description: 'Dilekçe ve topluluk eylem taahhütleri.',
      );

      const report = ContributionClassesReportModel(
        caseVersionId: '22222222-2222-4222-8222-222222222222',
        totalContributions: 1950,
        classes: [cCore, cExposed, cAdvocacy],
        contaminationRiskIndex: 0.0,
        isolationAuditStatus: 'ENFORCED',
        certifiedAt: '2026-08-20T10:00:00Z',
        isolationProofHash: '1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
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
              child: ContributionClassesCard(report: report),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(ContributionClassesCard), findsOneWidget);
      expect(find.textContaining('KATKI SINIFLARI AYRIŞTIRMASI'), findsOneWidget);
      expect(find.textContaining('Körleme Öncesi Asil Katılım'), findsOneWidget);
      expect(find.textContaining('İfşa Sonrası / Fikir Değişimi'), findsOneWidget);
      expect(find.textContaining('Savunuculuk ve Eylem Desteği'), findsOneWidget);
      expect(find.textContaining('Sinyale Uygun'), findsOneWidget);
    });
  });
}
