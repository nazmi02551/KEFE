import 'package:flutter/foundation.dart';

enum ReasoningTransparencyTierModel {
  fullAxiomaticProvenance,
  simplifiedCausalTree,
  evidentiaryWeightDecomposition,
}

@immutable
class XaiProvenanceModel {
  const XaiProvenanceModel({
    required this.provenanceId,
    required this.targetSynthesisId,
    required this.transparencyTier,
    required this.causalStepsCount,
    required this.axiomaticGroundingScore,
    required this.rootAxiomSummary,
  });

  final String provenanceId;
  final String targetSynthesisId;
  final ReasoningTransparencyTierModel transparencyTier;
  final int causalStepsCount;
  final double axiomaticGroundingScore;
  final String rootAxiomSummary;
}
