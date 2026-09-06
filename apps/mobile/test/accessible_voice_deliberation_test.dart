import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/accessible_voice_deliberation_models.dart';

void main() {
  group('Accessible Voice Deliberation & Audio Interface (CAP-082)', () {
    test('ADR-0228 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0228-accessible-voice-deliberation.md');
      final contract = File('../../docs/contracts/accessible-voice-deliberation.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-ACC-VOICE-001'));
      expect(contract.readAsStringSync(), contains('ANONYMIZED_VOICE_DICTATION'));
    });

    test('VoiceDeliberationModel instantiates properly', () {
      const model = VoiceDeliberationModel(
        sessionId: 'aud_1',
        mode: VoiceDeliberationModeModel.anonymizedVoiceDictation,
        audioDurationSeconds: 42.5,
        speechConfidenceScore: 0.94,
        isVoiceprintStripped: true,
        transcriptPreview: 'Kamu yararı gözetilerek şeffaf bir denetim kurulmalı.',
      );

      expect(model.audioDurationSeconds, 42.5);
      expect(model.speechConfidenceScore, 0.94);
      expect(model.isVoiceprintStripped, isTrue);
    });

    test('InternalAlphaStrings contains Accessible Voice localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.accVoiceEyebrow, contains('ERİŞİLEBİLİR SESLİ'));
      expect(tr.accVoiceModeDictation, contains('Anonimleştirilmiş'));

      const en = KefeStrings(Locale('en'));
      expect(en.accVoiceEyebrow, contains('ACCESSIBLE VOICE'));
      expect(en.accVoiceModeDictation, contains('Anonymized Voice'));
    });
  });
}
