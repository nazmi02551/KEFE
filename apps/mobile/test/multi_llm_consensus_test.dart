import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:kefe_mobile/core/localization/internal_alpha_strings.dart';
import 'package:kefe_mobile/core/localization/kefe_strings.dart';
import 'package:kefe_mobile/features/decision/domain/multi_llm_consensus_models.dart';

void main() {
  group('Cross-Model Multi-LLM Deliberation Consensus (CAP-094)', () {
    test('ADR-0234 and contract exist and are valid', () {
      final adr = File('../../docs/adr/0234-multi-llm-consensus.md');
      final contract = File('../../docs/contracts/multi-llm-consensus.v1.json');

      expect(adr.existsSync(), isTrue);
      expect(contract.existsSync(), isTrue);
      expect(contract.readAsStringSync(), contains('KEFE-MULTI-LLM-001'));
      expect(contract.readAsStringSync(), contains('UNANIMOUS_CROSS_MODEL_CONSENSUS'));
    });

    test('MultiLlmConsensusModel instantiates properly', () {
      const model = MultiLlmConsensusModel(
        consensusId: 'mlm_1',
        promptContextHash: 'hash_1',
        agreementLevel: ModelAgreementLevelModel.unanimousCrossModelConsensus,
        modelsEvaluatedCount: 4,
        semanticConvergenceScore: 0.95,
        synthesizedConsensusOutput: 'Tüm modeller vergilendirme konusunda anlaştı.',
      );

      expect(model.modelsEvaluatedCount, 4);
      expect(model.semanticConvergenceScore, 0.95);
      expect(model.agreementLevel, ModelAgreementLevelModel.unanimousCrossModelConsensus);
    });

    test('InternalAlphaStrings contains Multi LLM localized strings', () {
      const tr = KefeStrings(Locale('tr'));
      expect(tr.multiLlmEyebrow, contains('ÇAPRAZ MODEL ÇOKLU LLM'));
      expect(tr.multiLlmLvlUnanimous, contains('Oybirliğiyle'));

      const en = KefeStrings(Locale('en'));
      expect(en.multiLlmEyebrow, contains('CROSS-MODEL MULTI-LLM'));
      expect(en.multiLlmLvlUnanimous, contains('Unanimous'));
    });
  });
}
