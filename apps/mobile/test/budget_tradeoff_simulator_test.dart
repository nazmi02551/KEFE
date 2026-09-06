import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/budget_tradeoff_simulator_models.dart';
import 'package:kefe_mobile/features/decision/presentation/budget_tradeoff_simulator_card.dart';

void main() {
  group('Resource Allocation & Budget Tradeoff Simulator (CAP-027)', () {
    test('ADR-0197 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0197-budget-tradeoff-simulator.md');
      final contract = File('../../docs/contracts/budget-tradeoff-simulator.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-DECIDE-BUDGET-001'));
      expect(contract.readAsStringSync(), contains('HEALTH_EDUCATION_PRIORITY'));
    });

    test('BudgetTradeoffModel instantiates properly', () {
      const model = BudgetTradeoffModel(
        tradeoffId: 'trade_1',
        caseVersionId: 'case-1',
        healthcarePct: 35,
        educationPct: 30,
        infrastructurePct: 20,
        greenTransitionPct: 15,
        unallocatedPct: 0,
        tradeoffProfile: TradeoffProfileModel.healthEducationPriority,
      );

      expect(model.healthcarePct, 35);
      expect(model.tradeoffProfile, TradeoffProfileModel.healthEducationPriority);
    });

    test('InternalAlphaStrings contains Budget Tradeoff localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.budgetSimEyebrow, contains('KAYNAK DEĞİŞ-TOKUŞ'));
      expect(tr.budgetSimProfileHuman, contains('İnsani Sermaye'));

      const en = KefeStrings(Locale('en'));
      expect(en.budgetSimEyebrow, contains('RESOURCE TRADEOFF'));
      expect(en.budgetSimProfileHuman, contains('Human Capital'));
    });

    testWidgets('BudgetTradeoffSimulatorCard renders correctly', (tester) async {
      const model = BudgetTradeoffModel(
        tradeoffId: 'trade_1',
        caseVersionId: 'case-1',
        healthcarePct: 35,
        educationPct: 30,
        infrastructurePct: 20,
        greenTransitionPct: 15,
        unallocatedPct: 0,
        tradeoffProfile: TradeoffProfileModel.healthEducationPriority,
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
              child: BudgetTradeoffSimulatorCard(tradeoff: model),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(BudgetTradeoffSimulatorCard), findsOneWidget);
      expect(find.textContaining('KAYNAK DEĞİŞ-TOKUŞ'), findsOneWidget);
      expect(find.textContaining('%35'), findsOneWidget);
    });
  });
}


