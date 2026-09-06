import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/rights_conflict_models.dart';

void main() {
  group('Fundamental Rights & Liberties Conflict (CAP-024)', () {
    test('ADR-0183 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0183-fundamental-rights-and-liberties-conflict-analyzer.md');
      final contract = File('../../docs/contracts/rights-conflict-analyzer.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-RIGHTS-CONFLICT-001'));
      expect(contract.readAsStringSync(), contains('PRIVACY_VS_SECURITY'));
    });

    test('RightsConflictModel instantiates properly', () {
      const model = RightsConflictModel(
        caseVersionId: 'case-1',
        optionCode: 'OPT_A',
        collisionType: RightsCollisionTypeModel.privacyVsSecurity,
        severity: RestrictionSeverityModel.permissibleRestriction,
        inalienableCoreScore: 0.85,
        constitutionalRationale: 'Veri minimizasyonu ile orantılı sınırlama.',
      );

      expect(model.collisionType, RightsCollisionTypeModel.privacyVsSecurity);
      expect(model.severity, RestrictionSeverityModel.permissibleRestriction);
    });

    test('InternalAlphaStrings contains Rights Conflict localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.rightsEyebrow, contains('TEMEL HAKLAR'));
      expect(tr.rightsSevPermissible, contains('Ölçülü'));

      const en = KefeStrings(Locale('en'));
      expect(en.rightsEyebrow, contains('FUNDAMENTAL RIGHTS'));
      expect(en.rightsSevPermissible, contains('Permissible'));
    });
  });
}
