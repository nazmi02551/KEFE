import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/normative_models.dart';
import 'package:kefe_mobile/features/decision/presentation/normative_models_card.dart';

void main() {
  group('Fairness and Normative Models Comparison Engine (CAP-019)', () {
    test('ADR-0175 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0175-fairness-and-normative-models-comparison-engine.md');
      final contract = File('../../docs/contracts/fairness-normative-models.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      final contractContent = contract.readAsStringSync();
      expect(contractContent, contains('KEFE-NORMATIVE-MODELS-001'));
      expect(contractContent, contains('CAP-019'));
      expect(contractContent, contains('UTILITARIAN_MAX_WELFARE'));
      expect(contractContent, contains('DEONTOLOGICAL_CATEGORICAL_RIGHTS'));
      expect(contractContent, contains('RAWLSIAN_MAXIMIN_EQUITY'));
      expect(contractContent, contains('VIRTUE_ETHICS_CHARACTER'));
      expect(contractContent, contains('four_philosophical_traditions'));
      expect(contractContent, contains('normalized_scoring_zero_to_one'));
    });

    test('CaseNormativeModelsModel serializes and deserializes JSON correctly', () {
      final json = <String, dynamic>{
        'case_version_id': '11111111-1111-4111-8111-111111111111',
        'evaluations': [
          {
            'option_code': 'OPTION_A',
            'utilitarian_score': 0.85,
            'deontological_score': 0.45,
            'rawlsian_score': 0.55,
            'virtue_score': 0.70,
            'dominant_philosophy': 'UTILITARIAN_MAX_WELFARE',
          },
        ],
        'philosophies_explained_tr': {
          'UTILITARIAN_MAX_WELFARE': 'Faydacılık açıklaması',
        },
        'philosophies_explained_en': {
          'UTILITARIAN_MAX_WELFARE': 'Utilitarianism description',
        },
      };

      final model = CaseNormativeModelsModel.fromJson(json);
      expect(model.caseVersionId, '11111111-1111-4111-8111-111111111111');
      expect(model.evaluations.length, 1);
      final eval = model.evaluations.first;
      expect(eval.optionCode, 'OPTION_A');
      expect(eval.utilitarianScore, 0.85);
      expect(eval.dominantPhilosophy, NormativePhilosophyType.utilitarianMaxWelfare);
      expect(model.philosophiesExplainedTr['UTILITARIAN_MAX_WELFARE'], 'Faydacılık açıklaması');

      final serialized = model.toJson();
      expect(serialized['case_version_id'], '11111111-1111-4111-8111-111111111111');
      expect((serialized['evaluations'] as List).length, 1);
    });

    testWidgets('NormativeModelsCard renders properly in TR locale', (tester) async {
      const model = CaseNormativeModelsModel(
        caseVersionId: '11111111-1111-4111-8111-111111111111',
        evaluations: [
          OptionNormativeEvaluationModel(
            optionCode: 'SEÇENEK A: HIZLI UYGULAMA',
            utilitarianScore: 0.88,
            deontologicalScore: 0.40,
            rawlsianScore: 0.50,
            virtueScore: 0.65,
            dominantPhilosophy: NormativePhilosophyType.utilitarianMaxWelfare,
          ),
        ],
        philosophiesExplainedTr: {
          'UTILITARIAN_MAX_WELFARE': 'Faydacılık: En büyük sayıda insan için en yüksek toplam refahı hedefler.',
        },
        philosophiesExplainedEn: {
          'UTILITARIAN_MAX_WELFARE': 'Utilitarianism: Maximizes overall welfare for the greatest number.',
        },
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
              child: NormativeModelsCard(model: model),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(NormativeModelsCard), findsOneWidget);
      expect(find.text('NORMATİF ETİK MODELLERİ'), findsOneWidget);
      expect(find.text('SEÇENEK A: HIZLI UYGULAMA'), findsOneWidget);
      expect(find.text('FAYDACILIK'), findsOneWidget);
      expect(find.text('%88'), findsOneWidget);
      expect(find.textContaining('En büyük sayıda insan için en yüksek toplam refahı hedefler.'), findsOneWidget);
    });

    testWidgets('NormativeModelsCard renders properly in EN locale', (tester) async {
      const model = CaseNormativeModelsModel(
        caseVersionId: '22222222-2222-4222-8222-222222222222',
        evaluations: [
          OptionNormativeEvaluationModel(
            optionCode: 'OPTION B: CATEGORICAL MANDATE',
            utilitarianScore: 0.35,
            deontologicalScore: 0.95,
            rawlsianScore: 0.80,
            virtueScore: 0.70,
            dominantPhilosophy: NormativePhilosophyType.deontologicalCategoricalRights,
          ),
        ],
        philosophiesExplainedTr: {
          'DEONTOLOGICAL_CATEGORICAL_RIGHTS': 'Ödev Etiği: Temel hakları korur.',
        },
        philosophiesExplainedEn: {
          'DEONTOLOGICAL_CATEGORICAL_RIGHTS': 'Deontological Ethics: Protects fundamental rights regardless of outcome.',
        },
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
              child: NormativeModelsCard(model: model),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(NormativeModelsCard), findsOneWidget);
      expect(find.text('NORMATIVE ETHICAL MODELS'), findsOneWidget);
      expect(find.text('OPTION B: CATEGORICAL MANDATE'), findsOneWidget);
      expect(find.text('DEONTOLOGICAL RIGHTS'), findsOneWidget);
      expect(find.text('%95'), findsOneWidget);
      expect(find.textContaining('Protects fundamental rights regardless of outcome.'), findsOneWidget);
    });
  });
}
