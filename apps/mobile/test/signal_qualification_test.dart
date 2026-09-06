import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/signal/domain/signal_qualification_models.dart';
import 'package:kefe_mobile/features/signal/presentation/signal_qualification_card.dart';

void main() {
  group('Signal Qualification Engine (CAP-042)', () {
    test('ADR-0255 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0255-signal-qualification-engine.md');
      final contract = File('../../docs/contracts/signal-qualification.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-SIGNAL-QUALIFICATION-001'));
      expect(contract.readAsStringSync(), contains('GOLD_STANDARD'));
    });

    test('SignalQualificationReportModel instantiates and round-trips properly', () {
      const criterion = QualificationCriterionModel(
        criterionId: 'sample_sufficiency',
        nameTr: 'Örneklem Yeterliliği',
        nameEn: 'Sample Sufficiency',
        score: 0.95,
        threshold: 0.20,
        isPassed: true,
        auditNote: 'Sample exceeds 100 threshold',
      );

      const model = SignalQualificationReportModel(
        signalId: '77777777-7777-4777-8777-777777777701',
        caseVersionId: '22222222-2222-4222-8222-222222222222',
        caseTitle: 'Son koltuk kime verilmeli?',
        qualificationStatus: SignalQualificationStatusModel.qualified,
        qualificationTier: SignalQualificationTierModel.goldStandard,
        overallScore: 0.92,
        sampleSize: 1420,
        criteria: [criterion],
        eligibleChannels: ['CIVIC_PUBLIC_DASHBOARD', 'POLICY_DELIBERATION_REPORT'],
        certifiedAt: '2026-08-15T12:00:00Z',
        qualificationAuditHash: 'a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890',
      );

      final json = model.toJson();
      final roundTrip = SignalQualificationReportModel.fromJson(json);

      expect(roundTrip.signalId, model.signalId);
      expect(roundTrip.qualificationStatus, SignalQualificationStatusModel.qualified);
      expect(roundTrip.qualificationTier, SignalQualificationTierModel.goldStandard);
      expect(roundTrip.overallScore, 0.92);
      expect(roundTrip.criteria.length, 1);
      expect(roundTrip.criteria.first.isPassed, isTrue);
    });

    test('InternalAlphaStrings contains signal qualification localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.signalQualEyebrow, contains('METODOLOJİK'));
      expect(tr.signalQualTierGold, contains('Altın Standart'));
      expect(tr.signalQualScoreLabel(92), contains('%92'));

      const en = KefeStrings(Locale('en'));
      expect(en.signalQualEyebrow, contains('METHODOLOGY-QUALIFIED'));
      expect(en.signalQualTierGold, contains('Gold Standard'));
      expect(en.signalQualScoreLabel(92), contains('92%'));
    });

    testWidgets('SignalQualificationCard renders correctly in TR locale', (tester) async {
      const criterion = QualificationCriterionModel(
        criterionId: 'sample_sufficiency',
        nameTr: 'Örneklem Yeterliliği',
        nameEn: 'Sample Sufficiency',
        score: 0.95,
        threshold: 0.20,
        isPassed: true,
        auditNote: 'Örneklem yeterli',
      );

      const model = SignalQualificationReportModel(
        signalId: '77777777-7777-4777-8777-777777777701',
        caseVersionId: '22222222-2222-4222-8222-222222222222',
        caseTitle: 'Son koltuk kime verilmeli?',
        qualificationStatus: SignalQualificationStatusModel.qualified,
        qualificationTier: SignalQualificationTierModel.goldStandard,
        overallScore: 0.92,
        sampleSize: 1420,
        criteria: [criterion],
        eligibleChannels: ['CIVIC_PUBLIC_DASHBOARD', 'POLICY_DELIBERATION_REPORT'],
        certifiedAt: '2026-08-15T12:00:00Z',
        qualificationAuditHash: 'a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890',
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
              child: SignalQualificationCard(report: model),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(SignalQualificationCard), findsOneWidget);
      expect(find.textContaining('METODOLOJİK DOĞRULANMIŞ SİNYAL'), findsOneWidget);
      expect(find.textContaining('Altın Standart Sinyal'), findsOneWidget);
      expect(find.textContaining('Son koltuk kime verilmeli?'), findsOneWidget);
      expect(find.text('Örneklem Yeterliliği'), findsOneWidget);
      expect(find.text('95%'), findsOneWidget);
    });
  });
}
