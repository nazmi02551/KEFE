import 'package:flutter/foundation.dart';

enum PetitionStageModel {
  draftImpactSimulation,
  signatureGatheringCampaign,
  submittedToParliament,
}

@immutable
class CivicPetitionModel {
  const CivicPetitionModel({
    required this.petitionId,
    required this.billTitle,
    required this.stage,
    required this.signaturesCount,
    required this.signatureTargetThreshold,
    required this.projectedNetBenefitScore,
  });

  final String petitionId;
  final String billTitle;
  final PetitionStageModel stage;
  final int signaturesCount;
  final int signatureTargetThreshold;
  final double projectedNetBenefitScore;
}
