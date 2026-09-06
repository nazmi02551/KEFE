import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/institutional_promise_outcome_matrix_models.dart';

void main() {
  group('Institutional Promise & Outcome Realization Matrix (CAP-108)', () {
    test('ADR-0240 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0240-institutional-promise-outcome-matrix.md');
      final contract = File('../../docs/contracts/institutional-promise-outcome-matrix.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-PROMISE-001'));
      expect(contract.readAsStringSync(), contains('PROMISE_DELIVERED_VERIFIED'));
    });

    test('PromiseOutcomeModel instantiates properly', () {
      const model = PromiseOutcomeModel(
        matrixId: 'mtx_1',
        institutionName: 'İBB Raylı Sistemler',
        promiseTitle: 'Ümraniye Metro Açılışı',
        realizationStatus: PromiseRealizationStatusModel.promiseDeliveredVerified,
        milestoneCompletionPct: 1.00,
        empiricalEvidenceArtifactsCount: 4,
      );

      expect(model.milestoneCompletionPct, 1.00);
      expect(model.empiricalEvidenceArtifactsCount, 4);
      expect(model.realizationStatus, PromiseRealizationStatusModel.promiseDeliveredVerified);
    });

    test('InternalAlphaStrings contains Promise Outcome localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.promMtxEyebrow, contains('KURUMSAL VAAT'));
      expect(tr.promMtxStDelivered, contains('Vaat Tamamlandı'));

      const en = KefeStrings(Locale('en'));
      expect(en.promMtxEyebrow, contains('INSTITUTIONAL PROMISE'));
      expect(en.promMtxStDelivered, contains('Promise Delivered'));
    });
  });
}
