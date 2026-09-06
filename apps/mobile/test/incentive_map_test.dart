import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/incentive_map_models.dart';
import 'package:kefe_mobile/features/decision/presentation/incentive_map_card.dart';

void main() {
  group('Incentive Map Engine (CAP-022)', () {
    test('ADR-0251 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0251-incentive-map.md');
      final contract = File('../../docs/contracts/incentive-map.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-INCENTIVE-MAP-001'));
      expect(contract.readAsStringSync(), contains('FINANCIAL_PROFIT'));
    });

    test('IncentiveMapModel instantiates and serializes properly', () {
      const model = IncentiveMapModel(
        mapId: 'inc-unit-1',
        caseVersionId: 'case-ver-inc-1',
        alignmentIndex: 0.65,
        perverseIncentiveRisk: 'MODERATE',
        primaryDriver: 'Kâr ve Seçim Dengesi',
        mitigationMechanism: 'Bağımsız Denetim',
        incentiveNodes: [
          IncentiveNodeModel(
            stakeholderGroup: 'Hizmet Sağlayıcılar',
            coreIncentive: 'Kâr maksimizasyonu',
            incentiveType: 'FINANCIAL_PROFIT',
            alignmentStatus: 'MISALIGNED',
            intensityScore: 0.8,
            unintendedBehavior: 'Maliyet dışsallaştırma',
          ),
          IncentiveNodeModel(
            stakeholderGroup: 'Vatandaşlar',
            coreIncentive: 'Kamu yararı',
            incentiveType: 'CIVIC_PUBLIC_WELFARE',
            alignmentStatus: 'ALIGNED',
            intensityScore: 0.9,
          ),
        ],
      );

      expect(model.mapId, 'inc-unit-1');
      expect(model.alignmentIndex, 0.65);
      expect(model.incentiveNodes.length, 2);

      final json = model.toJson();
      final roundTrip = IncentiveMapModel.fromJson(json);
      expect(roundTrip.mapId, model.mapId);
      expect(roundTrip.alignmentIndex, model.alignmentIndex);
      expect(roundTrip.incentiveNodes.first.stakeholderGroup, 'Hizmet Sağlayıcılar');
    });

    test('InternalAlphaStrings contains Incentive Map localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.incentiveMapEyebrow, contains('TEŞVİK HARİTASI'));
      expect(tr.incentiveMapStatusAligned, contains('Uyumlu'));

      const en = KefeStrings(Locale('en'));
      expect(en.incentiveMapEyebrow, contains('INCENTIVE MAP'));
      expect(en.incentiveMapStatusAligned, contains('Aligned'));
    });

    testWidgets('IncentiveMapCard renders properly in TR locale', (tester) async {
      const model = IncentiveMapModel(
        mapId: 'inc-widget-tr',
        caseVersionId: 'case-ver-tr-1',
        alignmentIndex: 0.72,
        perverseIncentiveRisk: 'MODERATE',
        primaryDriver: 'Maliyet Optimizasyonu ve Seçim Baskısı',
        mitigationMechanism: 'Performans şartlı kamu sübvansiyonu',
        incentiveNodes: [
          IncentiveNodeModel(
            stakeholderGroup: 'Özel İşletmeler',
            coreIncentive: 'Maliyetleri düşürme',
            incentiveType: 'FINANCIAL_PROFIT',
            alignmentStatus: 'MISALIGNED',
            intensityScore: 0.75,
            unintendedBehavior: 'Güvenlik harcamalarını kısma eğilimi',
          ),
          IncentiveNodeModel(
            stakeholderGroup: 'Kamu Düzenleyicisi',
            coreIncentive: 'Standart denetim',
            incentiveType: 'BUREAUCRATIC_RISK_AVERSION',
            alignmentStatus: 'ALIGNED',
            intensityScore: 0.85,
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
              child: IncentiveMapCard(incentiveMap: model),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.byType(IncentiveMapCard), findsOneWidget);
      expect(find.textContaining('TEŞVİK HARİTASI'), findsOneWidget);
      expect(find.textContaining('%72'), findsOneWidget);
      expect(find.textContaining('Özel İşletmeler'), findsOneWidget);
      expect(find.textContaining('Performans şartlı'), findsOneWidget);
    });
  });
}
