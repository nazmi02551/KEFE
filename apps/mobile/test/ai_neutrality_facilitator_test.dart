import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/ai_neutrality_facilitator_models.dart';

void main() {
  group('Neutrality-Guaranteed AI Deliberation Facilitator (CAP-093)', () {
    test('ADR-0233 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0233-ai-neutrality-facilitator.md');
      final contract = File('../../docs/contracts/ai-neutrality-facilitator.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-AI-FACILITATE-001'));
      expect(contract.readAsStringSync(), contains('SOCRATIC_INQUIRY_PROMPT'));
    });

    test('FacilitationModel instantiates properly', () {
      const model = FacilitationModel(
        interventionId: 'fac_1',
        deliberationRoomId: 'room_1',
        mode: FacilitationModeModel.socraticInquiryPrompt,
        neutralityIndex: 0.98,
        deescalationEfficacyScore: 0.88,
        facilitationPromptText: 'Her iki taraf da kamu yararını amaçlıyor; peki kısa vadeli maliyetler nasıl dengelenebilir?',
      );

      expect(model.neutralityIndex, 0.98);
      expect(model.deescalationEfficacyScore, 0.88);
      expect(model.mode, FacilitationModeModel.socraticInquiryPrompt);
    });

    test('InternalAlphaStrings contains AI Facilitator localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.aiFacEyebrow, contains('TARAFSIZLIK GÜVENCELİ'));
      expect(tr.aiFacModeSocratic, contains('Sokratik Sorgulama'));

      const en = KefeStrings(Locale('en'));
      expect(en.aiFacEyebrow, contains('NEUTRALITY-GUARANTEED'));
      expect(en.aiFacModeSocratic, contains('Socratic Inquiry'));
    });
  });
}
