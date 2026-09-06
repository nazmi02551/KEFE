import 'package:flutter/foundation.dart';

enum StandingTierModel {
  exemplaryContributor,
  establishedParticipant,
  activeExplorer,
  restrictedOrProbationary,
}

@immutable
class CommunityTrustStandingModel {
  const CommunityTrustStandingModel({
    required this.userPseudonymId,
    required this.trustScore,
    required this.standingTier,
    required this.bridgeArgumentCount,
    required this.verifiedWeighCount,
    required this.infractionCount,
  });

  final String userPseudonymId;
  final double trustScore;
  final StandingTierModel standingTier;
  final int bridgeArgumentCount;
  final int verifiedWeighCount;
  final int infractionCount;
}
