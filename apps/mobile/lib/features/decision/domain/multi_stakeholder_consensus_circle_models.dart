import 'package:flutter/foundation.dart';

enum ConsensusCircleStateModel {
  stakeholderDiametricImpasse,
  intermediateConcessionBargaining,
  synthesisPactRatified,
}

@immutable
class ConsensusCircleModel {
  const ConsensusCircleModel({
    required this.circleId,
    required this.pactTitle,
    required this.state,
    required this.stakeholderGroupsCount,
    required this.mutualConcessionScore,
    required this.synthesisCovenantSummary,
  });

  final String circleId;
  final String pactTitle;
  final ConsensusCircleStateModel state;
  final int stakeholderGroupsCount;
  final double mutualConcessionScore;
  final String synthesisCovenantSummary;
}
