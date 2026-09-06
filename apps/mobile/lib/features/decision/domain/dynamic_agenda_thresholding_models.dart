import 'package:flutter/foundation.dart';

enum AgendaPriorityTierModel {
  nationalUrgencySpike,
  regionalEmergentTopic,
  monitoredIncubation,
}

@immutable
class DynamicAgendaModel {
  const DynamicAgendaModel({
    required this.topicId,
    required this.topicTitle,
    required this.priorityTier,
    required this.resonanceVelocityIndex,
    required this.viewpointDiversityEntropy,
    required this.isFeaturedOnNationalBallot,
  });

  final String topicId;
  final String topicTitle;
  final AgendaPriorityTierModel priorityTier;
  final double resonanceVelocityIndex;
  final double viewpointDiversityEntropy;
  final bool isFeaturedOnNationalBallot;
}
