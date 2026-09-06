import 'package:flutter/foundation.dart';

enum ExplorationModeModel {
  observeOnly,
  studyAndLearn,
  transitionToWeigh,
}

@immutable
class ObserveModeSessionModel {
  const ObserveModeSessionModel({
    required this.sessionId,
    required this.caseVersionId,
    required this.explorationMode,
    required this.isBindingVote,
    required this.viewedArgumentCount,
    required this.viewedEvidenceCount,
  });

  final String sessionId;
  final String caseVersionId;
  final ExplorationModeModel explorationMode;
  final bool isBindingVote;
  final int viewedArgumentCount;
  final int viewedEvidenceCount;
}
