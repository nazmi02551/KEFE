import 'package:flutter/foundation.dart';

enum ModelAgreementLevelModel {
  unanimousCrossModelConsensus,
  majorityConvergentSynthesis,
  modelDivergenceReviewRequired,
}

@immutable
class MultiLlmConsensusModel {
  const MultiLlmConsensusModel({
    required this.consensusId,
    required this.promptContextHash,
    required this.agreementLevel,
    required this.modelsEvaluatedCount,
    required this.semanticConvergenceScore,
    required this.synthesizedConsensusOutput,
  });

  final String consensusId;
  final String promptContextHash;
  final ModelAgreementLevelModel agreementLevel;
  final int modelsEvaluatedCount;
  final double semanticConvergenceScore;
  final String synthesizedConsensusOutput;
}
