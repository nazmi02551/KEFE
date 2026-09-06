import 'package:flutter/foundation.dart';

enum CitizenJuryStageModel {
  stratifiedPanelAssembly,
  expertHearingsInSession,
  consensusVerdictEmitted,
}

@immutable
class CitizenJuryModel {
  const CitizenJuryModel({
    required this.juryId,
    required this.dilemmaTitle,
    required this.stage,
    required this.jurorCount,
    required this.expertWitnessesCount,
    required this.verdictConsensusRate,
  });

  final String juryId;
  final String dilemmaTitle;
  final CitizenJuryStageModel stage;
  final int jurorCount;
  final int expertWitnessesCount;
  final double verdictConsensusRate;
}
