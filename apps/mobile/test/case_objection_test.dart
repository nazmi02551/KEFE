import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/case_objection_models.dart';
import 'package:kefe_mobile/features/decision/presentation/case_objection_dialog.dart';

void main() {
  group('Case Objection and Challenge Engine (CAP-068)', () {
    test('ADR-0172 and contract exist and are valid', () {
      final adr = File(
        '../../docs/adr/0172-case-objection-and-challenge-engine.md',
      );
      final contract = File(
        '../../docs/contracts/case-objection-challenge.v1.json',
      );

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(
        contract.readAsStringSync(),
        contains('KEFE-CASE-OBJECTION-001'),
      );
      expect(contract.readAsStringSync(), contains('EDITORIAL_BIAS_FRAMING'));
    });

    test('CaseObjectionItemModel instantiates properly', () {
      final item = CaseObjectionItemModel(
        objectionId: 'obj-1',
        caseVersionId: 'case-1',
        reasonCategory: ObjectionCategoryModel.excludedStakeholder,
        statement: 'Gece çalışan sağlık personeli dışlanmıştır.',
        status: ObjectionStatusModel.submitted,
        createdAt: DateTime.now().toUtc(),
      );

      expect(item.objectionId, 'obj-1');
      expect(item.reasonCategory, ObjectionCategoryModel.excludedStakeholder);
      expect(item.status, ObjectionStatusModel.submitted);
    });

    test('CaseObjectionItemModel serializes and deserializes JSON', () {
      final item = CaseObjectionItemModel(
        objectionId: 'obj-1',
        caseVersionId: 'case-1',
        reasonCategory: ObjectionCategoryModel.excludedStakeholder,
        statement: 'Gece çalışan sağlık personeli dışlanmıştır.',
        status: ObjectionStatusModel.submitted,
        createdAt: DateTime.utc(2026, 8, 30, 12, 0),
        supportingEvidenceUrl: 'https://kefe.org/delil/engelli-haklari',
      );

      final json = item.toJson();
      final reconstituted = CaseObjectionItemModel.fromJson(json);

      expect(reconstituted.objectionId, item.objectionId);
      expect(
        reconstituted.reasonCategory,
        ObjectionCategoryModel.excludedStakeholder,
      );
      expect(reconstituted.statement, item.statement);
      expect(reconstituted.status, ObjectionStatusModel.submitted);
      expect(reconstituted.supportingEvidenceUrl, item.supportingEvidenceUrl);
    });

    test('InternalAlphaStrings contains Objection localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.objectionDialogTitle, contains('İtiraz'));
      expect(tr.objectionCategoryBias, contains('Çerçeveleme'));

      const en = KefeStrings(Locale('en'));
      expect(en.objectionDialogTitle, contains('Objection'));
      expect(en.objectionCategoryBias, contains('Framing'));
    });

    testWidgets(
      'CaseObjectionDialog renders input fields and dropdown',
      (tester) async {
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
              body: CaseObjectionDialog(caseVersionId: 'case-1'),
            ),
          ),
        );

        await tester.pumpAndSettle();

        expect(find.byType(CaseObjectionDialog), findsOneWidget);
        expect(find.textContaining('İtiraz'), findsWidgets);
        expect(
          find.byType(DropdownButtonFormField<ObjectionCategoryModel>),
          findsOneWidget,
        );
      },
    );
  });
}
