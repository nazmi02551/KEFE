import 'package:flutter/foundation.dart';

enum PacingStatusModel {
  optimalPacing,
  pacingRecommended,
  restIntervalActive,
}

@immutable
class DecisionFatigueModel {
  const DecisionFatigueModel({
    required this.sessionId,
    required this.consecutiveWeighCount,
    required this.sessionDurationMinutes,
    required this.pacingStatus,
    required this.gentleRecommendationPrompt,
  });

  final String sessionId;
  final int consecutiveWeighCount;
  final double sessionDurationMinutes;
  final PacingStatusModel pacingStatus;
  final String gentleRecommendationPrompt;
}
