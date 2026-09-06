import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/process_analysis_models.dart';
import 'package:kefe_mobile/features/decision/presentation/process_analysis_card.dart';

void main() {
  group('Process Analysis Engine (CAP-021)', () {
    test('ADR-0249 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0249-process-analysis.md');
      final contract = File('../../docs/contracts/process-analysis.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-PROCESS-ANALYSIS-001'));
      expect(contract.readAsStringSync(), contains('PUBLIC_HEARING'));
    });

    test('ProcessAnalysisModel instantiates and serializes properly', () {
      const model = ProcessAnalysisModel(
        analysisId: 'proc-test-1',
        caseVersionId: 'case-ver-1',
        currentStage: 'PUBLIC_HEARING',
        proceduralIntegrityScore: 0.85,
        transparencyLevel: 'HIGH',
        publicParticipationStatus: 'OPEN_CONSULTATION',
        oversightBody: 'Sayıştay',
        stages: [
          ProcessStageModel(
            stageKey: 'CONSULTATION',
            stageTitle: 'Kamu İstişaresi',
            isCompleted: true,
            durationDays: 20,
            hasPublicInput: true,
            notes: 'Açık çağrı',
          ),
          ProcessStageModel(
            stageKey: 'LEGAL_REVIEW',
            stageTitle: 'Hukuk İncelemesi',
            isCompleted: true,
            durationDays: 14,
            hasPublicInput: false,
          ),
        ],
      );

      expect(model.analysisId, 'proc-test-1');
      expect(model.proceduralIntegrityScore, 0.85);
      expect(model.stages.length, 2);
      expect(model.stages.first.isCompleted, isTrue);

      final json = model.toJson();
      final roundTrip = ProcessAnalysisModel.fromJson(json);
      expect(roundTrip.analysisId, model.analysisId);
      expect(roundTrip.proceduralIntegrityScore, model.proceduralIntegrityScore);
      expect(roundTrip.stages.length, 2);
    });

    test('InternalAlphaStrings contains Process Analysis localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.processAnalysisEyebrow, contains('SÜREÇ ANALİZİ'));
      expect(tr.processAnalysisCompleted, contains('Tamamlandı'));

      const en = KefeStrings(Locale('en'));
      expect(en.processAnalysisEyebrow, contains('PROCESS ANALYSIS'));
      expect(en.processAnalysisCompleted, contains('Completed'));
    });

    testWidgets('ProcessAnalysisCard renders properly in TR locale', (tester) async {
      const model = ProcessAnalysisModel(
        analysisId: 'proc-card-tr',
        caseVersionId: 'case-card-tr-1',
        currentStage: 'DECISION_ENACTED',
        proceduralIntegrityScore: 0.82,
        transparencyLevel: 'HIGH',
        publicParticipationStatus: 'OPEN_CONSULTATION',
        oversightBody: 'Bağımsız Etik ve Hukuk Komisyonu',
        stages: [
          ProcessStageModel(
            stageKey: 'CONSULTATION',
            stageTitle: 'Kamu Danışması ve Paydaş Katılımı',
            isCompleted: true,
            durationDays: 30,
            hasPublicInput: true,
            notes: 'Açık çağrı yapıldı.',
          ),
          ProcessStageModel(
            stageKey: 'LEGAL_REVIEW',
            stageTitle: 'Hukuki Uyum ve Norm Denetimi',
            isCompleted: true,
            durationDays: 14,
            hasPublicInput: false,
            notes: 'Anayasal haklar incelendi.',
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
              child: ProcessAnalysisCard(analysis: model),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(ProcessAnalysisCard), findsOneWidget);
      expect(find.textContaining('SÜREÇ ANALİZİ'), findsOneWidget);
      expect(find.textContaining('%82'), findsOneWidget);
      expect(find.textContaining('Kamu Danışması'), findsOneWidget);
      expect(find.textContaining('Bağımsız Etik'), findsOneWidget);
    });
  });
}
