import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/xai_reasoning_provenance_models.dart';

void main() {
  group('Explainable AI & Reasoning Provenance Graph (CAP-095)', () {
    test('ADR-0235 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0235-xai-reasoning-provenance.md');
      final contract = File('../../docs/contracts/xai-reasoning-provenance.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-XAI-PROV-001'));
      expect(contract.readAsStringSync(), contains('FULL_AXIOMATIC_PROVENANCE'));
    });

    test('XaiProvenanceModel instantiates properly', () {
      const model = XaiProvenanceModel(
        provenanceId: 'xai_1',
        targetSynthesisId: 'synth_1',
        transparencyTier: ReasoningTransparencyTierModel.fullAxiomaticProvenance,
        causalStepsCount: 6,
        axiomaticGroundingScore: 0.96,
        rootAxiomSummary: 'Anayasal orantılılık ve en az müdahaleci araç ilkesinden türetilmiştir.',
      );

      expect(model.causalStepsCount, 6);
      expect(model.axiomaticGroundingScore, 0.96);
      expect(model.transparencyTier, ReasoningTransparencyTierModel.fullAxiomaticProvenance);
    });

    test('InternalAlphaStrings contains XAI Provenance localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.xaiProvEyebrow, contains('AÇIKLANABİLİR YAPAY ZEKA'));
      expect(tr.xaiProvTierAxiomatic, contains('Aksiyomatik Köken'));

      const en = KefeStrings(Locale('en'));
      expect(en.xaiProvEyebrow, contains('XAI REASONING'));
      expect(en.xaiProvTierAxiomatic, contains('Full Axiomatic'));
    });
  });
}
