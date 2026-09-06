import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/signal/domain/signal_health_models.dart';
import 'package:kefe_mobile/features/signal/presentation/signal_health_card.dart';

void main() {
  group('Signal Health Card (CAP-044)', () {
    test('ADR-0248 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0248-signal-health-card.md');
      final contract = File('../../docs/contracts/signal-health-card.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-SIGNAL-HEALTH-001'));
      expect(contract.readAsStringSync(), contains('QUALIFIED_SIGNAL'));
      expect(contract.readAsStringSync(), contains('BOT_ANOMALY_RESISTANCE'));
    });

    test('SignalHealthReportModel instantiates properly', () {
      final report = SignalHealthReportModel(
        signalId: 'sig-123',
        caseVersionId: 'case-456',
        overallQualification: SignalQualificationStatusModel.qualifiedSignal,
        overallHealthScore: 88.5,
        sampleSize: 1420,
        dimensions: const [
          SignalHealthDimensionModel(
            dimensionId: 'SAMPLE_SIZE',
            titleTr: 'Örneklem Yeterliliği',
            titleEn: 'Sample Size Sufficiency',
            score: 1420.0,
            threshold: 100.0,
            isPassed: true,
            detail: '1420 katılımcı ile geçerli.',
          ),
        ],
        certifiedAt: DateTime.utc(2026, 8, 30),
        methodologyHash: 'sha256-test-sig-hash',
      );

      expect(report.isQualified, isTrue);
      expect(report.overallHealthScore, 88.5);
      expect(report.sampleSize, 1420);
      expect(report.dimensions.length, 1);
      expect(report.dimensions.first.isPassed, isTrue);
    });

    test('SignalHealthReportModel serializes and deserializes JSON correctly', () {
      final report = SignalHealthReportModel(
        signalId: 'sig-json',
        caseVersionId: 'case-json',
        overallQualification: SignalQualificationStatusModel.qualifiedSignal,
        overallHealthScore: 92.0,
        sampleSize: 850,
        dimensions: const [
          SignalHealthDimensionModel(
            dimensionId: 'BOT_RESISTANCE',
            titleTr: 'Bot Kalkanı',
            titleEn: 'Bot Shield',
            score: 0.95,
            threshold: 0.85,
            isPassed: true,
            detail: 'Doğrulandı.',
          ),
        ],
        certifiedAt: DateTime.utc(2026, 9, 1, 10, 0),
        methodologyHash: 'sha256-sig-health-5dim-9f82a',
      );

      final json = report.toJson();
      final decoded = SignalHealthReportModel.fromJson(json);

      expect(decoded.signalId, report.signalId);
      expect(decoded.caseVersionId, report.caseVersionId);
      expect(decoded.overallQualification, SignalQualificationStatusModel.qualifiedSignal);
      expect(decoded.overallHealthScore, 92.0);
      expect(decoded.sampleSize, 850);
      expect(decoded.dimensions.first.dimensionId, 'BOT_RESISTANCE');
      expect(decoded.dimensions.first.isPassed, isTrue);
      expect(decoded.methodologyHash, 'sha256-sig-health-5dim-9f82a');
    });

    testWidgets('SignalHealthCard renders properly in TR locale', (tester) async {
      final report = SignalHealthReportModel(
        signalId: 'sig-widget-test',
        caseVersionId: 'case-widget-test',
        overallQualification: SignalQualificationStatusModel.qualifiedSignal,
        overallHealthScore: 89.0,
        sampleSize: 1200,
        dimensions: const [
          SignalHealthDimensionModel(
            dimensionId: 'SAMPLE_SIZE',
            titleTr: 'Örneklem Yeterliliği',
            titleEn: 'Sample Size Sufficiency',
            score: 1200.0,
            threshold: 100.0,
            isPassed: true,
            detail: '1200 çekirdek katılımcı doğrulandı.',
          ),
        ],
        certifiedAt: DateTime.utc(2026, 9, 1),
        methodologyHash: 'sha256-sig-health-5dim-9f82a',
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
          home: Scaffold(
            body: SingleChildScrollView(
              child: SignalHealthCard(report: report),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(SignalHealthCard), findsOneWidget);
      expect(find.text('SİNYAL SAĞLIK DENETİMİ'), findsOneWidget);
      expect(find.text('NİTELİKLİ YURTTAŞLIK SİNYALİ'), findsOneWidget);
      expect(find.text('Örneklem Yeterliliği'), findsOneWidget);
      expect(find.text('GEÇTİ'), findsOneWidget);
      expect(find.text('1200 çekirdek katılımcı doğrulandı.'), findsOneWidget);
    });
  });
}
