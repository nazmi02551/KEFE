import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/source_diversity_models.dart';
import 'package:kefe_mobile/features/decision/presentation/source_diversity_badge.dart';

void main() {
  group('Source Diversity Indicator (CAP-071)', () {
    test('ADR-0170 and contract exist and are valid', () {
      final adr = File(
        '../../docs/adr/0170-source-diversity-indicator-and-spectrum-engine.md',
      );
      final contract = File(
        '../../docs/contracts/source-diversity-indicator.v1.json',
      );

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(
        contract.readAsStringSync(),
        contains('KEFE-SOURCE-DIVERSITY-001'),
      );
      expect(contract.readAsStringSync(), contains('HIGH_DIVERSITY'));
    });

    test('SourceDiversityModel instantiates properly and serializes JSON', () {
      const model = SourceDiversityModel(
        caseVersionId: 'case-1',
        totalSources: 4,
        diversityLevel: DiversityLevelModel.highDiversity,
        breakdown: [
          SourceCategoryBreakdownModel(
            category: SourcePluralityCategoryModel.academicScientific,
            count: 2,
            percentage: 50.0,
          ),
          SourceCategoryBreakdownModel(
            category: SourcePluralityCategoryModel.officialGovernment,
            count: 2,
            percentage: 50.0,
          ),
        ],
      );

      expect(model.totalSources, 4);
      expect(model.diversityLevel, DiversityLevelModel.highDiversity);
      expect(model.breakdown.length, 2);

      final json = model.toJson();
      final reconstituted = SourceDiversityModel.fromJson(json);
      expect(reconstituted.caseVersionId, 'case-1');
      expect(reconstituted.totalSources, 4);
      expect(reconstituted.diversityLevel, DiversityLevelModel.highDiversity);
      expect(reconstituted.breakdown.length, 2);
      expect(
        reconstituted.breakdown[0].category,
        SourcePluralityCategoryModel.academicScientific,
      );
    });

    test(
      'InternalAlphaStrings contains Source Diversity localized strings',
      () {
        const tr = KefeStrings(Locale('tr'));
        expect(tr.diversityEyebrow, contains('KAYNAK ÇEŞİTLİLİĞİ'));
        expect(tr.diversityLevelHigh, contains('Çoğulcu'));

        const en = KefeStrings(Locale('en'));
        expect(en.diversityEyebrow, contains('SOURCE PLURALITY'));
        expect(en.diversityLevelHigh, contains('Pluralism'));
      },
    );

    testWidgets(
      'SourceDiversityBadge renders pluralism badges, count and breakdown',
      (tester) async {
        const model = SourceDiversityModel(
          caseVersionId: 'case-test-1',
          totalSources: 4,
          diversityLevel: DiversityLevelModel.highDiversity,
          breakdown: [
            SourceCategoryBreakdownModel(
              category: SourcePluralityCategoryModel.academicScientific,
              count: 2,
              percentage: 50.0,
            ),
            SourceCategoryBreakdownModel(
              category: SourcePluralityCategoryModel.officialGovernment,
              count: 2,
              percentage: 50.0,
            ),
          ],
        );

        await tester.pumpWidget(
          const MaterialApp(
            locale: Locale('tr', 'TR'),
            supportedLocales: KefeStrings.supportedLocales,
            localizationsDelegates: [
              KefeStringsDelegate(),
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            home: Scaffold(body: SourceDiversityBadge(diversity: model)),
          ),
        );

        await tester.pumpAndSettle();

        expect(
          find.byKey(const ValueKey('source-diversity-case-test-1')),
          findsOneWidget,
        );
        expect(find.text('4 kaynak'), findsOneWidget);
        expect(find.textContaining('KAYNAK ÇEŞİTLİLİĞİ'), findsOneWidget);
        expect(find.textContaining('Yüksek Çeşitlilik ve Çoğulcu Yapı'), findsOneWidget);
        expect(find.textContaining('%50'), findsNWidgets(2));
      },
    );
  });
}
