import 'package:flutter/foundation.dart';

enum MilestoneStatusModel {
  promised,
  inProgress,
  deliveredVerified,
  delayedOrBroken,
}

@immutable
class ImpactActionModel {
  const ImpactActionModel({
    required this.actionId,
    required this.institutionName,
    required this.pledgeTitle,
    required this.milestoneStatus,
    required this.completionPercentage,
    required this.targetCompletionUtc,
  });

  final String actionId;
  final String institutionName;
  final String pledgeTitle;
  final MilestoneStatusModel milestoneStatus;
  final int completionPercentage;
  final String targetCompletionUtc;
}
