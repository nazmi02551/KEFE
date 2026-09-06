import 'package:flutter/foundation.dart';

enum OutcomeVerdictModel {
  fullResolution,
  substantialProgress,
  partialSymbolicOnly,
  rejectedNonCompliant,
}

@immutable
class ImpactVerificationModel {
  const ImpactVerificationModel({
    required this.verificationId,
    required this.actionId,
    required this.outcomeVerdict,
    required this.resolutionScore,
    required this.auditorConsensusCount,
    required this.verificationNotes,
  });

  final String verificationId;
  final String actionId;
  final OutcomeVerdictModel outcomeVerdict;
  final double resolutionScore;
  final int auditorConsensusCount;
  final String verificationNotes;
}
