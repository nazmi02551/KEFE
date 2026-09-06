import 'package:flutter/foundation.dart';

enum CognitiveDensityModeModel {
  streamlinedEssentials,
  balancedDeliberative,
  scholarlyExhaustive,
}

@immutable
class AdaptiveCognitiveLoadModel {
  const AdaptiveCognitiveLoadModel({
    required this.profileId,
    required this.densityMode,
    required this.readingTimeReductionPct,
    required this.comprehensionRetentionIndex,
    required this.isFatigueMitigationActive,
  });

  final String profileId;
  final CognitiveDensityModeModel densityMode;
  final double readingTimeReductionPct;
  final double comprehensionRetentionIndex;
  final bool isFatigueMitigationActive;
}
