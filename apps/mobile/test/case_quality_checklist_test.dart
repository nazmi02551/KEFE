import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/case_quality_checklist_models.dart';
import 'package:kefe_mobile/features/decision/presentation/case_quality_checklist_sheet.dart';

void main() {
  group('Case Quality Checklist Instead of Magic Score (CAP-075)', () {
    test('ADR-0246 and contract exist and are valid', () {
      final adr = File(
        '../../docs/adr/0246-case-quality-checklist.md',
      );
      final contract = File(
        '../../docs/contracts/case-quality-checklist.v1.json',
      );

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(
        contract.readAsStringSync(),
        contains('KEFE-CASE-QUALITY-CHECKLIST-001'),
      );
      expect(contract.readAsStringSync(), contains('BALANCED_OPTIONS'));
      expect(contract.readAsStringSync(), contains('METHODOLOGY_TRANSPARENCY'));
    });

    test('CaseQualityChecklistModel instantiates properly', () {
      final model = CaseQualityChecklistModel(
        caseVersionId: 'case-test-1',
        overallStatus: 'FULLY_AUDITED_PASS',
        verifiedCount: 8,
        totalCount: 8,
        items: const [
          QualityChecklistItemModel(
            dimensionId: 'BALANCED_OPTIONS',
            nameTr: 'Dengeli Seçenekler',
            nameEn: 'Balanced Options',
            criterionTr: 'Seçenekler kutuplaştırıcı veya kukla argüman olmaksızın gerçek normatif gerilimi temsil eder.',
            criterionEn: 'Options represent genuine normative tension without strawman framing.',
            status: QualityAuditStatusModel.verified,
            reviewerNote: 'Doğrulandı',
          ),
        ],
        methodologyHash: 'sha256-test-hash',
      );

      expect(model.isFullyAudited, isTrue);
      expect(model.verifiedCount, 8);
      expect(model.totalCount, 8);
      expect(model.items.first.dimensionId, 'BALANCED_OPTIONS');
      expect(model.items.first.status, QualityAuditStatusModel.verified);
    });

    test('CaseQualityChecklistModel serializes and deserializes JSON', () {
      final model = CaseQualityChecklistModel(
        caseVersionId: 'case-test-json',
        overallStatus: 'FULLY_AUDITED_PASS',
        verifiedCount: 8,
        totalCount: 8,
        items: const [
          QualityChecklistItemModel(
            dimensionId: 'NEUTRAL_PROVENANCE',
            nameTr: 'Tarafsız Kaynak Kökeni',
            nameEn: 'Neutral Provenance',
            criterionTr: 'Metin yönlendirici dil içermez.',
            criterionEn: 'Text contains no leading phrasing.',
            status: QualityAuditStatusModel.verified,
            reviewerNote: 'Tarafsızlık kriteri onaylandı.',
          ),
        ],
        methodologyHash: 'sha256-kefe-cqb-chk-8dim-7a19c',
      );

      final json = model.toJson();
      final decoded = CaseQualityChecklistModel.fromJson(json);

      expect(decoded.caseVersionId, model.caseVersionId);
      expect(decoded.overallStatus, model.overallStatus);
      expect(decoded.verifiedCount, 8);
      expect(decoded.totalCount, 8);
      expect(decoded.items.first.dimensionId, 'NEUTRAL_PROVENANCE');
      expect(decoded.items.first.status, QualityAuditStatusModel.verified);
      expect(decoded.methodologyHash, 'sha256-kefe-cqb-chk-8dim-7a19c');
    });

    testWidgets(
      'CaseQualityChecklistSheet renders properly in TR locale',
      (tester) async {
        const model = CaseQualityChecklistModel(
          caseVersionId: 'case-widget-test',
          overallStatus: 'FULLY_AUDITED_PASS',
          verifiedCount: 8,
          totalCount: 8,
          items: [
            QualityChecklistItemModel(
              dimensionId: 'BALANCED_OPTIONS',
              nameTr: 'Dengeli Seçenekler',
              nameEn: 'Balanced Options',
              criterionTr: 'Seçenekler gerçek normatif gerilimi temsil eder.',
              criterionEn: 'Options represent genuine normative tension.',
              status: QualityAuditStatusModel.verified,
              reviewerNote: 'Standart editörlük denetiminden başarıyla geçti.',
            ),
          ],
          methodologyHash: 'sha256-kefe-cqb-chk-8dim-7a19c',
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
            home: const Scaffold(
              body: SingleChildScrollView(
                child: CaseQualityChecklistSheet(checklist: model),
              ),
            ),
          ),
        );

        await tester.pumpAndSettle();

        expect(find.byType(CaseQualityChecklistSheet), findsOneWidget);
        expect(find.text('Dengeli Seçenekler'), findsOneWidget);
        expect(find.text('DOĞRULANDI'), findsOneWidget);
        expect(
          find.text('Standart editörlük denetiminden başarıyla geçti.'),
          findsOneWidget,
        );
      },
    );
  });
}
