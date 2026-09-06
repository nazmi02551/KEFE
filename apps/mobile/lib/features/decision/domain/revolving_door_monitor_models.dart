import 'package:flutter/foundation.dart';

enum TransitionStatusModel {
  coolingOffCompliant,
  rapidRegulatoryTransitionAlert,
  provenCaptureVulnerability,
}

@immutable
class RevolvingDoorModel {
  const RevolvingDoorModel({
    required this.transitionId,
    required this.officialNameAnonymized,
    required this.status,
    required this.coolingOffMonthsObserved,
    required this.captureRiskScore,
    required this.regulatoryAgencySource,
  });

  final String transitionId;
  final String officialNameAnonymized;
  final TransitionStatusModel status;
  final int coolingOffMonthsObserved;
  final double captureRiskScore;
  final String regulatoryAgencySource;
}
