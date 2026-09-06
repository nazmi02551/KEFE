import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/privacy_budget_monitor_models.dart';

void main() {
  group('Privacy Budget Consumption Monitor (CAP-090)', () {
    test('ADR-0220 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0220-privacy-budget-monitor.md');
      final contract = File('../../docs/contracts/privacy-budget-monitor.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-PRIV-BUDGET-001'));
      expect(contract.readAsStringSync(), contains('BUDGET_HEALTHY_AMPLE'));
    });

    test('PrivacyBudgetModel instantiates properly', () {
      const model = PrivacyBudgetModel(
        monitorId: 'pbm_1',
        totalEpsilonBudget: 1.0,
        consumedEpsilon: 0.25,
        deltaParameter: 1e-5,
        budgetState: PrivacyBudgetStateModel.budgetHealthyAmple,
        queriesExecutedCount: 120,
      );

      expect(model.consumedEpsilon, 0.25);
      expect(model.budgetState, PrivacyBudgetStateModel.budgetHealthyAmple);
    });

    test('InternalAlphaStrings contains Privacy Budget localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.privBudEyebrow, contains('DİFERANSİYEL GİZLİLİK'));
      expect(tr.privBudStHealthy, contains('Gizlilik Bütçesi Sağlıklı'));

      const en = KefeStrings(Locale('en'));
      expect(en.privBudEyebrow, contains('DIFFERENTIAL PRIVACY'));
      expect(en.privBudStHealthy, contains('Privacy Budget Healthy'));
    });
  });
}
