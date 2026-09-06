import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/correction_history_models.dart';
import 'package:kefe_mobile/features/decision/presentation/correction_history_sheet.dart';

void main() {
  group('Case Correction and Version History Engine (CAP-072)', () {
    test('ADR-0171 and contract exist and are valid', () {
      final adr = File(
        '../../docs/adr/0171-case-correction-and-version-history-engine.md',
      );
      final contract = File(
        '../../docs/contracts/case-correction-history.v1.json',
      );

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(
        contract.readAsStringSync(),
        contains('KEFE-CASE-CORRECTION-001'),
      );
      expect(contract.readAsStringSync(), contains('FACTUAL_UPDATE'));
    });

    test('CaseCorrectionHistoryModel instantiates properly', () {
      final model = CaseCorrectionHistoryModel(
        caseVersionId: 'case-1',
        corrections: [
          CaseCorrectionItemModel(
            correctionId: 'c-1',
            caseVersionId: 'case-1',
            correctionType: CorrectionTypeModel.factualUpdate,
            severity: CorrectionSeverityModel.material,
            summary: 'Rakam güncellendi.',
            editorialRationale: 'Belediye ek bütçe kararı.',
            timestamp: DateTime.now().toUtc(),
          ),
        ],
      );

      expect(model.corrections.length, 1);
      expect(
        model.corrections.first.severity,
        CorrectionSeverityModel.material,
      );
    });

    test('CaseCorrectionHistoryModel serializes and deserializes JSON', () {
      final model = CaseCorrectionHistoryModel(
        caseVersionId: 'case-1',
        corrections: [
          CaseCorrectionItemModel(
            correctionId: 'c-1',
            caseVersionId: 'case-1',
            correctionType: CorrectionTypeModel.factualUpdate,
            severity: CorrectionSeverityModel.minor,
            summary: 'Yolcu hakları yönetmeliği güncellendi.',
            editorialRationale:
                '2026 revizyonu gereğince mülga madde referansı güncellendi.',
            timestamp: DateTime.utc(2026, 8, 29, 14, 0),
            previousText: 'Madde 14 uyarınca',
            correctedText: 'Madde 16/A uyarınca',
          ),
        ],
      );

      final json = model.toJson();
      final reconstituted = CaseCorrectionHistoryModel.fromJson(json);

      expect(reconstituted.caseVersionId, model.caseVersionId);
      expect(reconstituted.corrections.length, 1);
      expect(
        reconstituted.corrections.first.correctionType,
        CorrectionTypeModel.factualUpdate,
      );
      expect(
        reconstituted.corrections.first.summary,
        'Yolcu hakları yönetmeliği güncellendi.',
      );
      expect(
        reconstituted.corrections.first.previousText,
        'Madde 14 uyarınca',
      );
    });

    test(
      'InternalAlphaStrings contains Correction History localized strings',
      () {
        const tr = KefeStrings(Locale('tr'));
        expect(tr.correctionSheetTitle, contains('Düzeltme'));
        expect(tr.correctionTypeFactual, contains('Olgusal'));

        const en = KefeStrings(Locale('en'));
        expect(en.correctionSheetTitle, contains('Correction'));
        expect(en.correctionTypeFactual, contains('Factual'));
      },
    );

    testWidgets(
      'CorrectionHistorySheet renders correction cards and rationale',
      (tester) async {
        final model = CaseCorrectionHistoryModel(
          caseVersionId: 'case-1',
          corrections: [
            CaseCorrectionItemModel(
              correctionId: 'c-1',
              caseVersionId: 'case-1',
              correctionType: CorrectionTypeModel.factualUpdate,
              severity: CorrectionSeverityModel.minor,
              summary: 'Yolcu hakları yönetmeliği güncellendi.',
              editorialRationale:
                  '2026 revizyonu gereğince mülga madde referansı güncellendi.',
              timestamp: DateTime.utc(2026, 8, 29, 14, 0),
              previousText: 'Madde 14 uyarınca',
              correctedText: 'Madde 16/A uyarınca',
            ),
          ],
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
                child: CorrectionHistorySheet(history: model),
              ),
            ),
          ),
        );

        await tester.pumpAndSettle();

        expect(find.byType(CorrectionHistorySheet), findsOneWidget);
        expect(find.textContaining('Düzeltme'), findsWidgets);
        expect(
          find.text('Yolcu hakları yönetmeliği güncellendi.'),
          findsOneWidget,
        );
        expect(
          find.textContaining('2026 revizyonu gereğince'),
          findsOneWidget,
        );
      },
    );
  });
}
