import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/consensus_divergence_models.dart';
import 'package:kefe_mobile/features/decision/presentation/consensus_divergence_card.dart';

void main() {
  group('Consensus and Divergence Classification Engine (CAP-039)', () {
    test('ADR-0162 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0162-consensus-and-divergence-classification-engine.md');
      final contract = File('../../docs/contracts/consensus-divergence-classification.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      final contractContent = contract.readAsStringSync();
      expect(contractContent, contains('KEFE-CONSENSUS-DIVERGENCE-001'));
      expect(contractContent, contains('CAP-039'));
      expect(contractContent, contains('BROAD_CONSENSUS'));
      expect(contractContent, contains('BIPOLAR_DIVERGENCE'));
      expect(contractContent, contains('FRAGMENTED_PLURALITY'));
      expect(contractContent, contains('LEANING_MAJORITY'));
      expect(contractContent, contains('purely_descriptive_classification'));
      expect(contractContent, contains('no_normative_judgment'));
    });

    test('ConsensusDivergenceModel serializes and deserializes JSON correctly', () {
      final json = <String, dynamic>{
        'case_version_id': '11111111-1111-4111-8111-111111111111',
        'distribution': {'opt_a': 0.76, 'opt_b': 0.24},
        'classification': 'BROAD_CONSENSUS',
        'leading_share': 0.76,
        'margin_of_divergence': 0.52,
        'label_tr': 'Geniş Toplumsal Uzlaşı',
        'label_en': 'Broad Social Consensus',
        'description_tr': 'Öncü seçenek %70 veya üzeri ağırlıkla net bir ortak zemin oluşturuyor.',
        'description_en': 'The leading option commands 70% or more weight, forming a distinct common ground.',
      };

      final model = ConsensusDivergenceModel.fromJson(json);
      expect(model.caseVersionId, '11111111-1111-4111-8111-111111111111');
      expect(model.classification, DivergenceCategory.broadConsensus);
      expect(model.leadingShare, 0.76);
      expect(model.marginOfDivergence, 0.52);
      expect(model.labelTr, 'Geniş Toplumsal Uzlaşı');
      expect(model.distribution['opt_a'], 0.76);

      final serialized = model.toJson();
      expect(serialized['classification'], 'BROAD_CONSENSUS');
      expect(serialized['leading_share'], 0.76);
    });

    testWidgets('ConsensusDivergenceCard renders properly in TR locale', (tester) async {
      const model = ConsensusDivergenceModel(
        caseVersionId: '11111111-1111-4111-8111-111111111111',
        distribution: {'opt_a': 0.49, 'opt_b': 0.46, 'opt_c': 0.05},
        classification: DivergenceCategory.bipolarDivergence,
        leadingShare: 0.49,
        marginOfDivergence: 0.03,
        labelTr: 'Kutuplu Ayrışma',
        labelEn: 'Bipolar Divergence',
        descriptionTr: 'Toplum iki ana seçenek arasında yakın oranlarla derin bir ayrışma yaşıyor.',
        descriptionEn: 'Society experiences a deep divergence between two main options within a narrow margin.',
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
              child: ConsensusDivergenceCard(model: model),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(ConsensusDivergenceCard), findsOneWidget);
      expect(find.text('UZLAŞI VE AYRIŞMA ANALİZİ'), findsOneWidget);
      expect(find.text('KUTUPLU AYRIŞMA'), findsOneWidget);
      expect(find.text('%49.0'), findsOneWidget);
      expect(find.text('%3.0'), findsOneWidget);
      expect(find.textContaining('normatif bir değer yargısı içermez'), findsOneWidget);
    });

    testWidgets('ConsensusDivergenceCard renders properly in EN locale', (tester) async {
      const model = ConsensusDivergenceModel(
        caseVersionId: '22222222-2222-4222-8222-222222222222',
        distribution: {'opt_a': 0.85, 'opt_b': 0.15},
        classification: DivergenceCategory.broadConsensus,
        leadingShare: 0.85,
        marginOfDivergence: 0.70,
        labelTr: 'Geniş Toplumsal Uzlaşı',
        labelEn: 'Broad Social Consensus',
        descriptionTr: 'Öncü seçenek %70 veya üzeri ağırlıkla net bir ortak zemin oluşturuyor.',
        descriptionEn: 'The leading option commands 70% or more weight, forming a distinct common ground.',
      );

      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData.dark().copyWith(
            extensions: const [KefeVisualTheme.dark],
          ),
          locale: const Locale('en', 'US'),
          supportedLocales: KefeStrings.supportedLocales,
          localizationsDelegates: const [
            KefeStringsDelegate(),
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: const Scaffold(
            body: SingleChildScrollView(
              child: ConsensusDivergenceCard(model: model),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(ConsensusDivergenceCard), findsOneWidget);
      expect(find.text('CONSENSUS & DIVERGENCE ANALYSIS'), findsOneWidget);
      expect(find.text('BROAD SOCIAL CONSENSUS'), findsOneWidget);
      expect(find.text('%85.0'), findsOneWidget);
      expect(find.text('%70.0'), findsOneWidget);
      expect(find.textContaining('carries no normative judgment'), findsOneWidget);
    });
  });
}
