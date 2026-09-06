import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/appeals_review_panel_models.dart';

void main() {
  group('Appeals & Community Review Panel (CAP-069)', () {
    test('ADR-0202 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0202-appeals-review-panel.md');
      final contract = File('../../docs/contracts/appeals-review-panel.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-APPEAL-PANEL-001'));
      expect(contract.readAsStringSync(), contains('OVERTURNED_RESTORED'));
    });

    test('AppealsReviewModel instantiates properly', () {
      const model = AppealsReviewModel(
        appealId: 'app_1',
        targetResourceId: 'rsn_1',
        appealVerdict: AppealVerdictModel.overturnedRestored,
        panelistCount: 7,
        favorRatio: 0.71,
        resolutionSummary: 'Hakem heyeti kural ihlali olmadığını tespit etmiştir.',
      );

      expect(model.panelistCount, 7);
      expect(model.appealVerdict, AppealVerdictModel.overturnedRestored);
    });

    test('InternalAlphaStrings contains Appeals Review Panel localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.appealPanelEyebrow, contains('TOPLULUK İTİRAZ'));
      expect(tr.appealPanelVerdictOverturned, contains('Karar Bozuldu'));

      const en = KefeStrings(Locale('en'));
      expect(en.appealPanelEyebrow, contains('COMMUNITY APPEALS'));
      expect(en.appealPanelVerdictOverturned, contains('Overturned'));
    });
  });
}
