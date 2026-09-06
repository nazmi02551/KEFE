import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/design/kefe_visual_system.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/policy_simulator_models.dart';
import 'package:kefe_mobile/features/decision/presentation/policy_simulator_card.dart';

void main() {
  group('Policy Simulator & Parameter Tuning Engine (CAP-017)', () {
    test('ADR-0196 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0196-policy-simulator.md');
      final contract = File('../../docs/contracts/policy-simulator.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-POLICY-SIM-001'));
      expect(contract.readAsStringSync(), contains('OPTIMAL_BALANCE'));
    });

    test('PolicySimulatorModel instantiates properly', () {
      const model = PolicySimulatorModel(
        simulationId: 'sim_1',
        caseVersionId: 'case-1',
        policyKnobName: 'Karbon Vergisi',
        knobValue: 25.0,
        fiscalScore: 0.75,
        socialScore: 0.68,
        environmentalScore: 0.82,
        equilibriumState: EquilibriumStateModel.optimalBalance,
      );

      expect(model.policyKnobName, 'Karbon Vergisi');
      expect(model.equilibriumState, EquilibriumStateModel.optimalBalance);
    });

    test('InternalAlphaStrings contains Policy Simulator localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.policySimEyebrow, contains('POLİTİKA SİMÜLATÖRÜ'));
      expect(tr.policySimStateOptimal, contains('Optimal'));

      const en = KefeStrings(Locale('en'));
      expect(en.policySimEyebrow, contains('POLICY SIMULATOR'));
      expect(en.policySimStateOptimal, contains('Optimal'));
    });

    testWidgets('PolicySimulatorCard renders properly in TR locale', (tester) async {
      const model = PolicySimulatorModel(
        simulationId: 'sim_live_1',
        caseVersionId: 'case-version-001',
        policyKnobName: 'Karbon Vergisi ve Emisyon Bedeli',
        knobValue: 35.0,
        fiscalScore: 0.78,
        socialScore: 0.72,
        environmentalScore: 0.85,
        equilibriumState: EquilibriumStateModel.optimalBalance,
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
              child: PolicySimulatorCard(simulation: model),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.byType(PolicySimulatorCard), findsOneWidget);
      expect(find.textContaining('Karbon Vergisi ve Emisyon Bedeli'), findsOneWidget);
      expect(find.textContaining('POLİTİKA SİMÜLATÖRÜ'), findsOneWidget);
    });
  });
}

